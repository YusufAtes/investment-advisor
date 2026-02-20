"""
Portfolio Price Updater
=======================
Reads the latest prices from price_history.txt and updates
both current_portfolio.json and advisory_portfolio.json.

- Updates price_per_piece_usd for all non-real-estate assets.
- Recalculates total_usd, total_tl, percentages, and portfolio totals.
- Does NOT change piece counts (those only change from user actions
  or advisory executor).

Usage:
    python tracking/update_portfolio.py
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from typing import Dict, Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRACKING_DIR = os.path.join(BASE_DIR, "tracking")
PRICE_HISTORY_FILE = os.path.join(TRACKING_DIR, "price_history.txt")
PORTFOLIO_DIR = os.path.join(BASE_DIR, "portfolio")
CURRENT_PORTFOLIO = os.path.join(PORTFOLIO_DIR, "current_portfolio.json")
ADVISORY_PORTFOLIO = os.path.join(PORTFOLIO_DIR, "advisory_portfolio.json")

# Map portfolio asset names to price_history.txt column names
ASSET_TO_COLUMN = {
    "HLAL Fund": "HLAL",
    "SPUS Fund": "SPUS",
    "KPC Fund (BIST100)": "KPC",
    "HKH Fund (BIST100)": "HKH",
    "RBH Fund (BIST100)": "RBH",
    "THYAO Stock (BIST100)": "THYAO",
    "LKMNH Stock (BIST100)": "LKMNH",
    "BIMAS Stock (BIST100)": "BIMAS",
    "ASML Stock (S&P)": "ASML",
    "SPTE Fund": "SPTE",
    "Digital Gold": "GOLD_GRAM",
    "Digital Silver": "SILVER_GRAM",
    "Physical Gold": "GOLD_GRAM",  # Same price source, different pieces
}

# Categories excluded from price updates
EXCLUDED_CATEGORIES = {"real_estate", "cash"}


def read_latest_prices() -> tuple[Dict[str, float], float]:
    """
    Read the last row of price_history.txt.

    Returns:
        Tuple of (price_dict mapping column_name -> USD price, usdtry rate)
    """
    if not os.path.exists(PRICE_HISTORY_FILE):
        raise FileNotFoundError(f"Price history file not found: {PRICE_HISTORY_FILE}")

    with open(PRICE_HISTORY_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]

    if len(lines) < 2:
        raise ValueError("Price history file has no data rows.")

    # Parse header
    header = lines[0].split("\t")
    # Parse last data row
    last_row = lines[-1].split("\t")

    if len(last_row) != len(header):
        raise ValueError(
            f"Column count mismatch: header has {len(header)} columns, "
            f"last row has {len(last_row)} columns."
        )

    prices = {}
    for i, col in enumerate(header):
        if col == "Date":
            continue
        try:
            prices[col] = float(last_row[i])
        except (ValueError, IndexError):
            prices[col] = 0.0

    usdtry = prices.get("USDTRY", 0.0)
    if usdtry <= 0:
        raise ValueError("USDTRY rate is zero or missing in price history.")

    date_str = last_row[0]
    print(f"[UpdatePortfolio] Using prices from: {date_str}")
    print(f"[UpdatePortfolio] USDTRY rate: {usdtry:.4f}")

    return prices, usdtry


def update_portfolio_prices(
    portfolio_path: str,
    prices: Dict[str, float],
    usdtry: float,
    label: str = "Portfolio",
) -> dict:
    """
    Update a portfolio JSON file with latest prices.

    Args:
        portfolio_path: Path to the portfolio JSON file
        prices: Dict mapping column name to USD price
        usdtry: USD/TRY exchange rate
        label: Label for logging

    Returns:
        Updated portfolio dict
    """
    if not os.path.exists(portfolio_path):
        raise FileNotFoundError(f"{label} file not found: {portfolio_path}")

    with open(portfolio_path, "r", encoding="utf-8") as f:
        portfolio = json.load(f)

    # Update exchange rate
    portfolio["exchange_rate_usd_try"] = usdtry

    # Update each asset price
    updated_count = 0
    for asset in portfolio["assets"]:
        name = asset["name"]
        category = asset.get("category", "")

        # Skip excluded categories
        if category in EXCLUDED_CATEGORIES:
            continue

        # Find the matching column
        column = ASSET_TO_COLUMN.get(name)
        if column is None:
            print(f"  [WARN] No price column mapping for '{name}', skipping.")
            continue

        new_price = prices.get(column)
        if new_price is None or new_price <= 0:
            print(f"  [WARN] No valid price for '{name}' (column={column}), skipping.")
            continue

        old_price = asset.get("price_per_piece_usd", 0.0)
        asset["price_per_piece_usd"] = round(new_price, 6)
        updated_count += 1

        if old_price > 0:
            change_pct = ((new_price - old_price) / old_price) * 100
            print(f"  {name}: {old_price:.6f} -> {new_price:.6f} USD ({change_pct:+.2f}%)")
        else:
            print(f"  {name}: 0.0 -> {new_price:.6f} USD (new)")

    # Recalculate totals (USD-first)
    for asset in portfolio["assets"]:
        asset["total_usd"] = round(asset["pieces"] * asset["price_per_piece_usd"], 2)
        asset["total_tl"] = round(asset["total_usd"] * usdtry, 2)

    total_usd = sum(asset["total_usd"] for asset in portfolio["assets"])
    portfolio["total_portfolio_usd"] = round(total_usd, 2)
    portfolio["total_portfolio_tl"] = round(total_usd * usdtry, 2)

    for asset in portfolio["assets"]:
        if total_usd > 0:
            asset["percentage"] = round((asset["total_usd"] / total_usd) * 100, 2)
        else:
            asset["percentage"] = 0.0

    # Update date
    portfolio["date"] = datetime.now().strftime("%Y-%m-%d")

    # Save
    with open(portfolio_path, "w", encoding="utf-8") as f:
        json.dump(portfolio, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] {label} updated: {updated_count} assets, total = ${total_usd:,.2f} USD")

    return portfolio


def main():
    """Read latest prices and update both portfolios."""
    print("=" * 60)
    print("  PORTFOLIO PRICE UPDATER")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Read latest prices
    prices, usdtry = read_latest_prices()

    # Update current portfolio
    print(f"\n--- Updating Current Portfolio ---")
    try:
        update_portfolio_prices(CURRENT_PORTFOLIO, prices, usdtry, "Current Portfolio")
    except FileNotFoundError as e:
        print(f"[WARN] {e}")

    # Update advisory portfolio (same prices, different piece counts)
    print(f"\n--- Updating Advisory Portfolio ---")
    try:
        update_portfolio_prices(ADVISORY_PORTFOLIO, prices, usdtry, "Advisory Portfolio")
    except FileNotFoundError as e:
        print(f"[WARN] {e}")

    print(f"\n{'='*60}")
    print("  PRICE UPDATE COMPLETE")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
