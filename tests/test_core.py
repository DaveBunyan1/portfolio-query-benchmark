from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from models import Base, Transaction, User
from portfolio_math import calculate_portfolio_metrics
from repository import PortfolioRepository


# ---------- Pure math tests ----------
def test_calculate_portfolio_metrics_basic():
    """Verify PnL, current value and weights on a known example."""
    rows = [
        SimpleNamespace(
            ticker="AAPL", shares=10.0, cost_basis=1500.0, price_per_share=150.0
        ),
        SimpleNamespace(
            ticker="MSFT", shares=5.0, cost_basis=1000.0, price_per_share=200.0
        ),
    ]
    prices = {"AAPL": 180.0, "MSFT": 220.0}

    result = calculate_portfolio_metrics(rows, prices)

    assert len(result) == 2

    aapl = next(p for p in result if p["ticker"] == "AAPL")
    assert aapl["shares"] == 10.0
    assert aapl["current_price"] == 180.0
    assert aapl["current_value"] == 1800.0
    assert aapl["unrealized_pnl"] == 300.0  # 1800 - 1500
    assert aapl["weight"] == pytest.approx(0.6207, abs=1e-4)  # 1800 / 2900

    msft = next(p for p in result if p["ticker"] == "MSFT")
    assert msft["current_value"] == 1100.0
    assert msft["unrealized_pnl"] == 100.0
    assert msft["weight"] == pytest.approx(0.3793, abs=1e-4)


def test_calculate_portfolio_metrics_zero_shares():
    """Edge case: zero shares should not blow up."""
    rows = [
        SimpleNamespace(ticker="AAPL", shares=0.0, cost_basis=0.0, price_per_share=0.0),
    ]
    prices = {"AAPL": 180.0}

    result = calculate_portfolio_metrics(rows, prices)
    assert result[0]["current_value"] == 0.0
    assert result[0]["unrealized_pnl"] == 0.0
    assert result[0]["weight"] == 0.0


def test_calculate_portfolio_metrics_missing_price():
    """Missing price should default to 0."""
    rows = [
        SimpleNamespace(
            ticker="AAPL", shares=10.0, cost_basis=1500.0, price_per_share=150.0
        ),
    ]
    prices = {}  # no price for AAPL

    result = calculate_portfolio_metrics(rows, prices)
    assert result[0]["current_price"] == 0.0
    assert result[0]["current_value"] == 0.0
    assert result[0]["unrealized_pnl"] == -1500.0


# ---------- Repository aggregation test (in-memory SQLite) ----------
@pytest_asyncio.fixture
async def async_session():
    """In-memory SQLite session for isolated tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )
    async with session_maker() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_get_user_portfolio_aggregation(async_session: AsyncSession):
    """Verify the SQL aggregation produces correct totals."""
    user = User(username="testuser")
    async_session.add(user)
    await async_session.flush()

    transactions = [
        Transaction(
            user_id=user.id,
            ticker="AAPL",
            shares=5.0,
            price_per_share=150.0,
            transaction_at=datetime.now(timezone.utc),
        ),
        Transaction(
            user_id=user.id,
            ticker="AAPL",
            shares=5.0,
            price_per_share=160.0,
            transaction_at=datetime.now(timezone.utc),
        ),
        Transaction(
            user_id=user.id,
            ticker="MSFT",
            shares=10.0,
            price_per_share=200.0,
            transaction_at=datetime.now(timezone.utc),
        ),
    ]
    async_session.add_all(transactions)
    await async_session.commit()

    repo = PortfolioRepository(async_session)
    rows = await repo.get_user_portfolio(user.id)

    by_ticker = {r.ticker: r for r in rows}

    assert "AAPL" in by_ticker
    assert by_ticker["AAPL"].shares == 10.0
    assert by_ticker["AAPL"].cost_basis == 1550.0  # 5*150 + 5*160
    assert by_ticker["AAPL"].price_per_share == 155.0

    assert "MSFT" in by_ticker
    assert by_ticker["MSFT"].shares == 10.0
    assert by_ticker["MSFT"].cost_basis == 2000.0
