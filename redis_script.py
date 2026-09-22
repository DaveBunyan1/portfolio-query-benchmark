import asyncio

import redis.asyncio as aioredis


async def test_redis_connection():
    # Connect to local Redis on default port 6379
    redis = aioredis.Redis(host="localhost", port=6379, db=0)

    try:
        # Test basic SET / GET
        await redis.set("price:AAPL", "238.98", ex=60)  # TTL of 60 seconds
        val = await redis.get("price:AAPL")

        print(f"Redis Connection Successful!")
        print(f"Retrieved key 'price:AAPL' -> {val.decode('utf-8')}")
    finally:
        await redis.close()


if __name__ == "__main__":
    asyncio.run(test_redis_connection())
