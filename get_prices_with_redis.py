import asyncio
import time
from datetime import UTC, datetime, timedelta

import redis.asyncio as aioredis

from database import async_session_maker
from portfolio_math import calculate_portfolio_metrics
from repository import PortfolioRepository
from yfinance_api import get_ticker_data


# Initialize Async Redis Connection
async def get_redis_client():
    return aioredis.Redis(host="localhost", port=6379, db=0, decode_responses=True)


async def get_prices_with_redis(
    redis_client: aioredis.Redis,
    ticker_map: dict[str, str],
    ttl_seconds: int = 300,
) -> dict[str, float]:
    """Fetches ticker prices from Redis via MGET.

    Falls back to yfinance for missing/expired keys and caches the new prices.
    """
    prices = {}
    missing_db_tickers = []
    missing_yf_tickers = []

    # 1. Prepare Redis keys
    # ticker_map is { 'BRK.B': 'BRK-B', 'AAPL': 'AAPL' }
    db_tickers = list(ticker_map.keys())
    redis_keys = [f"price:{db_t}" for db_t in db_tickers]

    # 2. Batch lookup in Redis (Sub-millisecond)
    cached_values = await redis_client.mget(redis_keys)

    for db_t, yf_t, val in zip(db_tickers, ticker_map.values(), cached_values):
        if val is not None:
            prices[db_t] = float(val)
        else:
            missing_db_tickers.append(db_t)
            missing_yf_tickers.append(yf_t)

    # 3. Cache Miss Handler: Fetch missing tickers from yfinance
    if missing_yf_tickers:
        start_date = (datetime.now(tz=UTC) - timedelta(days=4)).strftime("%Y-%m-%d")
        raw_data = get_ticker_data(missing_yf_tickers, start_date)

        if raw_data is not None and not raw_data.empty:
            latest_prices = raw_data.iloc[-1]["Close"]

            # Store missing prices in Redis using a Pipeline for performance
            async with redis_client.pipeline(transaction=True) as pipe:
                for db_t, yf_t in zip(missing_db_tickers, missing_yf_tickers):
                    if yf_t in latest_prices:
                        price = float(latest_prices[yf_t])
                        prices[db_t] = price

                        # Set key with TTL (e.g., 300 seconds / 5 mins)
                        pipe.setex(f"price:{db_t}", ttl_seconds, str(price))

                await pipe.execute()

    return prices


async def get_transaction_for_user_cached(user_id: int, redis_client: aioredis.Redis):
    """Full workflow: DB aggregation + Redis cached price lookup + PnL math."""
    async with async_session_maker() as session:
        # Step 1: DB Query (~12-13ms)
        repo = PortfolioRepository(session)
        rows = await repo.get_user_portfolio(user_id)

        if not rows:
            return []

        # Step 2: Build ticker mapping (BRK.B -> BRK-B)
        ticker_map = {row.ticker: row.ticker.replace(".", "-") for row in rows}

        # Step 3: Fetch Prices via Redis Cache (~1-2ms)
        prices = await get_prices_with_redis(redis_client, ticker_map, ttl_seconds=300)

        # Step 4: Pure In-Memory PnL & Weight Math (<0.1ms)
        return calculate_portfolio_metrics(rows, prices)
