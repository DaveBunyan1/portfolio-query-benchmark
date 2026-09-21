import asyncio
import time

from database import async_session_maker
from repository import PortfolioRepository

DB_PATH = "./mydb.db"


async def get_transaction_for_user(user_id: int):
    async with async_session_maker() as session:
        repo = PortfolioRepository(session)

        rows = await repo.get_user_portfolio(user_id)
        for row in rows:
            print(f"{row.ticker}: {row.shares} {row.cost_basis} {row.price_per_share}")


if __name__ == "__main__":
    start = time.perf_counter()
    asyncio.run(get_transaction_for_user(2))
    pt = time.perf_counter() - start
    print("Time taken:", pt * 1000)
