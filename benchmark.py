import asyncio
import csv
import os
import statistics
import time
from datetime import datetime

from get_data import get_transaction_for_user


async def benchmark_and_log(
    user_id: int,
    runs: int = 100,
    warmup: int = 5,
    label: str = "Baseline",
    filepath: str = "benchmark_results.csv",
):
    # 1. Warm-up runs
    for _ in range(warmup):
        await get_transaction_for_user(user_id)

    durations_ms = []

    # 2. Timed runs
    for _ in range(runs):
        start = time.perf_counter()
        await get_transaction_for_user(user_id)
        elapsed = (time.perf_counter() - start) * 1000
        durations_ms.append(elapsed)

    # 3. Compute stats
    durations_ms.sort()
    avg_time = statistics.mean(durations_ms)
    min_time = min(durations_ms)
    max_time = max(durations_ms)
    median_time = statistics.median(durations_ms)

    p99_index = max(0, int(len(durations_ms) * 0.99) - 1)
    p99_time = durations_ms[p99_index]

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 4. Append to CSV file
    file_exists = os.path.exists(filepath)

    with open(filepath, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Write header if creating the file for the first time
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

        # Write benchmark row
        writer.writerow(
            [
                timestamp,
                label,
                runs,
                f"{min_time:.3f}",
                f"{median_time:.3f}",
                f"{avg_time:.3f}",
                f"{p99_time:.3f}",
                f"{max_time:.3f}",
            ]
        )

    # Print summary to console as well
    print(f"\n--- Benchmark Logged [{label}] ---")
    print(
        f"Min: {min_time:.3f}ms | Median: {median_time:.3f}ms | Avg: {avg_time:.3f}ms | P99: {p99_time:.3f}ms | Max: {max_time:.3f}ms"
    )
    print(f"Results appended to '{filepath}'")


if __name__ == "__main__":
    asyncio.run(
        benchmark_and_log(user_id=2, runs=100, warmup=5, label="Baseline yfinance")
    )
