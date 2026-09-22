import asyncio
import time
from datetime import UTC, datetime, timedelta

from database import async_session_maker
from portfolio_math import calculate_portfolio_metrics
from repository import PortfolioRepository
from yfinance_api import get_ticker_data

DB_PATH = "./mydb.db"


async def get_transaction_for_user(user_id: int):
    async with async_session_maker() as session:
        repo = PortfolioRepository(session)
        rows = await repo.get_user_portfolio(user_id)

        if not rows:
            return []

        ticker_map = {row.ticker: row.ticker.replace(".", "-") for row in rows}
        yf_tickers = list(ticker_map.values())

        start_date = (datetime.now(tz=UTC) - timedelta(days=4)).strftime("%Y-%m-%d")

        raw_data = get_ticker_data(yf_tickers, start_date)

        if raw_data is None or raw_data.empty:
            raise ValueError("Failed to fetch market data")
        latest_prices_yf = raw_data.iloc[-1]["Close"]

        prices = {}
        for db_ticker, yf_ticker in ticker_map.items():
            if yf_ticker in latest_prices_yf:
                prices[db_ticker] = float(latest_prices_yf[yf_ticker])

        portfolio_positions = calculate_portfolio_metrics(rows, prices)

        print(portfolio_positions)
        return portfolio_positions


if __name__ == "__main__":
    start = time.perf_counter()
    asyncio.run(get_transaction_for_user(2))
    pt = time.perf_counter() - start
    print("Time taken:", pt * 1000)
