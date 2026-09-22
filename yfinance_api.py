from datetime import UTC, datetime, timedelta

import yfinance as yf  # type: ignore


def get_ticker_data(
    tickers: list[str], start_date: str | None = None, end_date: str | None = None
):
    if start_date is None:
        start_date = (datetime.now(tz=UTC) - timedelta(days=1)).strftime("%Y-%m-%d")

    return yf.download(
        tickers, start=start_date, end=end_date, auto_adjust=True, progress=False
    )
