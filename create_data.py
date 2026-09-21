import asyncio
import random
from datetime import datetime, timedelta, timezone

from faker import Faker

from database import async_session_maker, create_all_tables
from models import Transaction, User

fake = Faker()

# Sample tickers for realistic stock data
TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "BRK.B"]


async def seed_bulk_data(num_users: int = 10, avg_tx_per_user: int = 1000):
    async with async_session_maker() as session:
        async with session.begin():
            print(f"Generating {num_users} users...")

            users = []
            for i in range(num_users):
                # Generate user with associated random transactions
                num_transactions = avg_tx_per_user

                transactions = [
                    Transaction(
                        ticker=random.choice(TICKERS),
                        shares=round(random.uniform(1.0, 100.0), 2),
                        price_per_share=round(random.uniform(10.0, 1000.0), 2),
                        transaction_at=datetime.now(timezone.utc)
                        - timedelta(days=random.randint(0, 365)),
                    )
                    for _ in range(num_transactions)
                ]

                user = User(
                    username=fake.unique.user_name(),
                    transactions=transactions,
                )
                users.append(user)
                print(f"Transactions for user {i + 1} complete.")

            # Stage all users and nested transactions at once
            session.add_all(users)

        print(f"Successfully seeded {num_users} users and their transactions!")


if __name__ == "__main__":
    asyncio.run(create_all_tables())
    asyncio.run(seed_bulk_data(num_users=2, avg_tx_per_user=100000))
