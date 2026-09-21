import asyncio
import time

import aiosqlite
from sqlalchemy import text

from database import async_session_maker

DB_PATH = "./mydb.db"


async def get_transaction_for_user(user_id: int):
    sql = """
        SELECT 
            ticker,
            SUM(shares) AS shares,
            SUM(shares * price_per_share) AS cost_basis,
            CASE 
                WHEN SUM(shares) = 0 THEN 0 
                ELSE SUM(shares * price_per_share) / SUM(shares) 
            END AS price_per_share
        FROM transactions
        WHERE user_id = ?
        GROUP BY ticker;
    """

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(sql, (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return rows


if __name__ == "__main__":
    start = time.perf_counter()
    asyncio.run(get_transaction_for_user(2))
    pt = time.perf_counter() - start
    print("Time taken:", pt * 1000)
