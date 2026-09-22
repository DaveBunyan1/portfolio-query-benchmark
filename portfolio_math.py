def calculate_portfolio_metrics(rows, prices):
    portfolio_positions = []
    for row in rows:
        shares = float(row.shares)
        cost_basis = float(row.cost_basis)
        avg_price = float(row.price_per_share)
        current_price = prices.get(row.ticker, 0.0)

        current_value = shares * current_price
        unrealized_pnl = current_value - cost_basis

        portfolio_positions.append(
            {
                "ticker": row.ticker,
                "shares": round(shares, 2),
                "cost_basis": round(cost_basis, 2),
                "avg_price_per_share": round(avg_price, 2),
                "current_price": round(current_price, 2),
                "current_value": round(current_value, 2),
                "unrealized_pnl": round(unrealized_pnl, 2),
            }
        )

    total_portfolio_value = sum(p["current_value"] for p in portfolio_positions)

    for position in portfolio_positions:
        position["weight"] = (
            round(position["current_value"] / total_portfolio_value, 4)
            if total_portfolio_value > 0
            else 0.0
        )

    return portfolio_positions
