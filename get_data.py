import asyncio
import time

from sqlalchemy import case, func, select

from database import async_session_maker
from models import Transaction


async def get_transaction_for_user(user_id: int):
    total_shares = func.sum(Transaction.shares)
    cost_basis = func.sum(Transaction.shares * Transaction.price_per_share)
    avg_price_per_share = case((total_shares == 0, 0), else_=cost_basis / total_shares)
    query = (
        select(
            Transaction.ticker.label("ticker"),
            total_shares.label("shares"),
            cost_basis.label("cost_basis"),
            avg_price_per_share.label("price_per_share"),
        )
        .where(Transaction.user_id == user_id)
        .group_by(Transaction.ticker)
    )

    async with async_session_maker() as session:
        result = await session.execute(query)
        rows = result.all()

        for row in rows:
            print(f"{row.ticker}: {row.shares} {row.cost_basis} {row.price_per_share}")


if __name__ == "__main__":
    start = time.perf_counter()
    asyncio.run(get_transaction_for_user(2))
    pt = time.perf_counter() - start
    print("Time taken:", pt * 1000)
