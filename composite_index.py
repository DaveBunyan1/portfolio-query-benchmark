import asyncio

from sqlalchemy import text

from database import engine


async def create_index():
    sql = text(
        """
        CREATE INDEX IF NOT EXISTS idx_transactions_user_ticker 
        ON transactions (user_id, ticker, shares, price_per_share);
    """
    )
    async with engine.begin() as conn:
        await conn.execute(sql)
    print("Index created successfully!")


if __name__ == "__main__":
    asyncio.run(create_index())
