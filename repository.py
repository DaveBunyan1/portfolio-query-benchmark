from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class PortfolioRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_user_portfolio(self, user_id: int):
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

        result = await self._session.execute(sql, {"user_id": user_id})

        return result.all()
