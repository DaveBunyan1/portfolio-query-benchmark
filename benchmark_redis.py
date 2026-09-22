import asyncio
import csv
import os
import time
from datetime import datetime

from get_prices_with_redis import get_redis_client, get_transaction_for_user_cached


def append_to_csv(
    file_path: str,
    label: str,
    runs: int,
    min_ms: float,
    median_ms: float,
    avg_ms: float,
    p99_ms: float,
    max_ms: float,
):
    """Appends benchmark metrics directly to the tracking CSV file."""
    file_exists = os.path.exists(file_path)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(file_path, mode="a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)

        # Write header if starting a new file
        if not file_exists:
            writer.writerow(
                [
                    "Timestamp",
                    "Label",
                    "Runs",
                    "Min (ms)",
                    "Median (ms)",
                    "Avg (ms)",
                    "P99 (ms)",
                    "Max (ms)",
                ]
            )

        writer.writerow(
            [
                timestamp,
                label,
                runs,
                f"{min_ms:.3f}",
                f"{median_ms:.3f}",
                f"{avg_ms:.3f}",
                f"{p99_ms:.3f}",
                f"{max_ms:.3f}",
            ]
        )


async def run_redis_benchmark(
    user_id: int, runs: int = 100, csv_path: str = "benchmark_results.csv"
):
    redis_client = await get_redis_client()

    try:
        # --- TEST 1: Cold Cache (Force Cache Miss) ---
        await redis_client.flushdb()  # Clear cache

        t0 = time.perf_counter()
        await get_transaction_for_user_cached(user_id, redis_client)
        cold_latency_ms = (time.perf_counter() - t0) * 1000

        print(f"Cold Cache Latency: {cold_latency_ms:.2f} ms")

        # Log Cold Cache single-run record
        append_to_csv(
            file_path=csv_path,
            label="Redis Cold Cache (Miss)",
            runs=1,
            min_ms=cold_latency_ms,
            median_ms=cold_latency_ms,
            avg_ms=cold_latency_ms,
            p99_ms=cold_latency_ms,
            max_ms=cold_latency_ms,
        )

        # --- TEST 2: Hot Cache (100% Hit Rate) ---
        # Run warmup iteration
        await get_transaction_for_user_cached(user_id, redis_client)

        latencies = []
        for _ in range(runs):
            t0 = time.perf_counter()
            await get_transaction_for_user_cached(user_id, redis_client)
            latencies.append((time.perf_counter() - t0) * 1000)

        # Output results for logging
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

        # Log Hot Cache aggregated record
        append_to_csv(
            file_path=csv_path,
            label="Redis Hot Cache (MGET)",
            runs=runs,
            min_ms=min_lat,
            median_ms=median_lat,
            avg_ms=avg_lat,
            p99_ms=p99_lat,
            max_ms=max_lat,
        )
        print(f"\n[+] Results successfully appended to {csv_path}")

    finally:
        await redis_client.aclose()


if __name__ == "__main__":
    asyncio.run(run_redis_benchmark(user_id=2, runs=100))
