import asyncio
import time

from sqlalchemy import text

from database import async_session_maker


async def get_transaction_for_user(user_id: int):
    sql = text(
        """
        SELECT 
            ticker,
            SUM(shares) AS shares,
            SUM(shares * price_per_share) AS cost_basis,
            CASE 
                WHEN SUM(shares) = 0 THEN 0 
                ELSE SUM(shares * price_per_share) / SUM(shares) 
            END AS price_per_share
        FROM transactions
        WHERE user_id = :user_id
        GROUP BY ticker;
    """
    )

    async with async_session_maker() as session:
        result = await session.execute(sql, {"user_id": user_id})
        rows = result.all()

        for row in rows:
            print(f"{row.ticker}: {row.shares} {row.cost_basis} {row.price_per_share}")


if __name__ == "__main__":
    start = time.perf_counter()
    asyncio.run(get_transaction_for_user(2))
    pt = time.perf_counter() - start
    print("Time taken:", pt * 1000)
