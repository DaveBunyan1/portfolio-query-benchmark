# High-Performance Portfolio Aggregation Engine

A low-latency financial portfolio aggregation service built with Python, FastAPI, SQLAlchemy (Async), Redis, and Domain-Driven Design (DDD) principles.

The engine calculates real-time user portfolio holdings, market values, unrealized profit/loss (PnL), and asset weights with a targeted sub-20ms SLA.

---

## Key Performance Benchmarks

Optimizations transitioned the query pipeline from an initial **~49ms** (unindexed DB) and **~276ms** (uncached external network API) down to a **~13ms average latency**.

| Benchmark Stage                | Runs    | Min (ms)   | Median (ms) | Avg (ms)   | P99 (ms)   | Speedup vs Network |
| :----------------------------- | :------ | :--------- | :---------- | :--------- | :--------- | :----------------- |
| **Direct `yfinance` Baseline** | 100     | 225.520    | 261.334     | 276.565    | 625.816    | 1.0x (Baseline)    |
| **Redis Cold Cache (Miss)**    | 1       | 578.130    | 578.130     | 578.130    | 578.130    | 0.48x              |
| **Redis Hot Cache (`MGET`)**   | **100** | **12.225** | **12.919**  | **13.031** | **16.687** | **~21.2x**         |

---

## Architectural Highlights

- **Composite Covering Index:** SQL aggregation latency optimized using a composite index on `transactions(user_id, ticker, shares, price_per_share)`.
- **Read-Through Caching Pattern:** Batch price retrieval using Redis `MGET` pipelines with fallback fetching to prevent network thread lock.
- **Pure Math Engine:** In-memory PnL and weight calculation logic isolated into pure, zero-I/O helper functions for instant unit testing.

---

## Tech Stack

- **Framework:** FastAPI / Python 3.11+
- **Database:** SQLite / PostgreSQL with SQLAlchemy (Async Engine)
- **Caching Layer:** Async Redis (`redis.asyncio`)
- **Type Checking & Testing:** Mypy, Pytest

---

## Quickstart

### 1. Start Redis Service

```bash
docker run -d --name quant-redis -p 6379:6379 redis:alpine
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Benchmark Suite

```bash
python benchmark_results.py
```
