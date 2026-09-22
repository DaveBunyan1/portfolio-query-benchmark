import asyncio
import time

from get_prices_with_redis import get_redis_client, get_transaction_for_user_cached


async def run_redis_benchmark(user_id: int, runs: int = 100):
    redis_client = await get_redis_client()

    try:
        # --- TEST 1: Cold Cache (Force Cache Miss) ---
        await redis_client.flushdb()  # Clear cache

        t0 = time.perf_counter()
        await get_transaction_for_user_cached(user_id, redis_client)
        cold_latency_ms = (time.perf_counter() - t0) * 1000
        print(f"Cold Cache Latency: {cold_latency_ms:.2f} ms")

        # --- TEST 2: Hot Cache (100% Hit Rate) ---
        # Run warmup iteration
        await get_transaction_for_user_cached(user_id, redis_client)

        latencies = []
        for _ in range(runs):
            t0 = time.perf_counter()
            await get_transaction_for_user_cached(user_id, redis_client)
            latencies.append((time.perf_counter() - t0) * 1000)

        # Output results for CSV logging
        avg_lat = sum(latencies) / len(latencies)
        min_lat = min(latencies)
        max_lat = max(latencies)
        latencies.sort()
        median_lat = latencies[len(latencies) // 2]
        p99_lat = latencies[int(len(latencies) * 0.99)]

        print("\n--- Hot Cache Results (Redis MGET) ---")
        print(f"Runs: {runs}")
        print(f"Min: {min_lat:.3f} ms | Median: {median_lat:.3f} ms")
        print(f"Max: {max_lat:.3f} ms")
        print(f"Avg: {avg_lat:.3f} ms | P99: {p99_lat:.3f} ms")

    finally:
        await redis_client.aclose()


if __name__ == "__main__":
    asyncio.run(run_redis_benchmark(user_id=2, runs=100))
