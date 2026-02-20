"""
Portfolio Evaluation Script
============================
Logs daily portfolio values to CSV and generates comparison plots.

Plots:
  5.1 - Current vs Advisory total return over time (USD)
  5.2 - Each asset price over time (USD)
  5.3 - Current portfolio total + individual asset values over time (USD)

Usage:
    python tracking/evaluate.py
"""

from __future__ import annotations

import csv
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for script usage
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORTFOLIO_DIR = os.path.join(BASE_DIR, "portfolio")
TRACKING_DIR = os.path.join(BASE_DIR, "tracking")
PLOTS_DIR = os.path.join(TRACKING_DIR, "plots")

CURRENT_PORTFOLIO = os.path.join(PORTFOLIO_DIR, "current_portfolio.json")
ADVISORY_PORTFOLIO = os.path.join(PORTFOLIO_DIR, "advisory_portfolio.json")
PRICE_HISTORY_FILE = os.path.join(TRACKING_DIR, "price_history.txt")
EVALUATION_LOG = os.path.join(TRACKING_DIR, "evaluation_log.csv")

# Asset column names (must match price_history.txt header)
ASSET_COLUMNS = [
    "HLAL", "SPUS", "KPC", "HKH", "RBH",
    "THYAO", "LKMNH", "BIMAS", "ASML", "SPTE",
    "GOLD_GRAM", "SILVER_GRAM",
]


def load_portfolio(path: str) -> Optional[dict]:
    """Load a portfolio JSON file."""
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_asset_totals(portfolio: dict) -> Dict[str, float]:
    """Get total_usd for each asset, keyed by a short name."""
    # Map portfolio asset names to short column names
    name_map = {
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
        "Physical Gold": "PHYS_GOLD",
        "USD Cash": "USD_CASH",
        "EUR Cash": "EUR_CASH",
    }

    totals = {}
    for asset in portfolio["assets"]:
        short = name_map.get(asset["name"], asset["name"])
        totals[short] = asset.get("total_usd", 0.0)

    return totals


def log_daily_values() -> None:
    """
    Append today's portfolio values to evaluation_log.csv.
    If today's date already exists, overwrite that row.
    """
    os.makedirs(TRACKING_DIR, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")

    # Load portfolios
    current = load_portfolio(CURRENT_PORTFOLIO)
    advisory = load_portfolio(ADVISORY_PORTFOLIO)

    if current is None:
        print("[WARN] Current portfolio not found. Skipping log.")
        return

    current_total = current.get("total_portfolio_usd", 0.0)
    advisory_total = advisory.get("total_portfolio_usd", 0.0) if advisory else 0.0
    usdtry = current.get("exchange_rate_usd_try", 0.0)

    # Get individual asset totals from both portfolios
    current_assets = get_asset_totals(current)
    advisory_assets = get_asset_totals(advisory) if advisory else {}

    # Build header and row
    asset_cols_current = [f"cur_{col}" for col in ASSET_COLUMNS]
    asset_cols_advisory = [f"adv_{col}" for col in ASSET_COLUMNS]

    header = ["date", "current_total_usd", "advisory_total_usd"] + \
             asset_cols_current + asset_cols_advisory + ["USDTRY"]

    row = [
        today,
        current_total,
        advisory_total,
    ]
    # Current asset values
    for col in ASSET_COLUMNS:
        row.append(current_assets.get(col, 0.0))
    # Advisory asset values
    for col in ASSET_COLUMNS:
        row.append(advisory_assets.get(col, 0.0))
    row.append(usdtry)

    # Read existing CSV
    existing_rows = []
    if os.path.exists(EVALUATION_LOG):
        with open(EVALUATION_LOG, "r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            existing_header = next(reader, None)
            for r in reader:
                existing_rows.append(r)

    # Check if today already exists, overwrite if so
    updated = False
    for i, r in enumerate(existing_rows):
        if r and r[0] == today:
            existing_rows[i] = [str(v) for v in row]
            updated = True
            break

    if not updated:
        existing_rows.append([str(v) for v in row])

    # Write CSV
    with open(EVALUATION_LOG, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(existing_rows)

    print(f"[OK] Evaluation log updated: {EVALUATION_LOG}")
    print(f"  Current: ${current_total:,.2f} | Advisory: ${advisory_total:,.2f} | USDTRY: {usdtry:.4f}")


def generate_plots() -> None:
    """Generate all three evaluation plots."""
    os.makedirs(PLOTS_DIR, exist_ok=True)

    if not os.path.exists(EVALUATION_LOG):
        print("[WARN] No evaluation log found. Skipping plots.")
        return

    # Read evaluation log
    df = pd.read_csv(EVALUATION_LOG, parse_dates=["date"])

    if len(df) < 2:
        print("[INFO] Not enough data points for meaningful plots (need at least 2).")
        return

    # Plot styling
    plt.style.use("seaborn-v0_8-whitegrid")

    # =========================================================================
    # Plot 5.1: Current vs Advisory Total Return
    # =========================================================================
    fig, ax = plt.subplots(figsize=(12, 6))

    ax.plot(df["date"], df["current_total_usd"], "b-o", label="Current Portfolio", linewidth=2, markersize=4)
    ax.plot(df["date"], df["advisory_total_usd"], "r-s", label="Advisory Portfolio", linewidth=2, markersize=4)

    ax.set_title("Current vs Advisory Portfolio Total Value (USD)", fontsize=14, fontweight="bold")
    ax.set_xlabel("Date")
    ax.set_ylabel("Total Value (USD)")
    ax.legend(fontsize=11)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    fig.autofmt_xdate()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    path1 = os.path.join(PLOTS_DIR, "total_return_comparison.png")
    fig.savefig(path1, dpi=150)
    plt.close(fig)
    print(f"[OK] Plot saved: {path1}")

    # =========================================================================
    # Plot 5.2: Each Asset Price Over Time
    # =========================================================================
    if os.path.exists(PRICE_HISTORY_FILE):
        price_df = pd.read_csv(PRICE_HISTORY_FILE, sep="\t")

        # Parse dates
        price_df["Date"] = pd.to_datetime(price_df["Date"], format="%d.%m.%Y")

        fig, ax = plt.subplots(figsize=(14, 7))

        colors = plt.cm.tab20.colors
        price_cols = [c for c in price_df.columns if c not in ("Date", "USDTRY")]

        for i, col in enumerate(price_cols):
            if col in price_df.columns:
                ax.plot(price_df["Date"], price_df[col], "-o",
                        label=col, linewidth=1.5, markersize=3,
                        color=colors[i % len(colors)])

        ax.set_title("Asset Prices Over Time (USD)", fontsize=14, fontweight="bold")
        ax.set_xlabel("Date")
        ax.set_ylabel("Price (USD)")
        ax.legend(fontsize=9, ncol=3, loc="upper left")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        fig.autofmt_xdate()
        ax.grid(True, alpha=0.3)

        # Use log scale if prices differ by orders of magnitude
        min_price = price_df[price_cols].min().min()
        max_price = price_df[price_cols].max().max()
        if max_price > 0 and min_price > 0 and (max_price / min_price) > 100:
            ax.set_yscale("log")
            ax.set_ylabel("Price (USD, log scale)")

        plt.tight_layout()
        path2 = os.path.join(PLOTS_DIR, "asset_prices.png")
        fig.savefig(path2, dpi=150)
        plt.close(fig)
        print(f"[OK] Plot saved: {path2}")
    else:
        print("[WARN] No price history file found. Skipping asset prices plot.")

    # =========================================================================
    # Plot 5.3: Current Portfolio Total + Individual Asset Values
    # =========================================================================
    fig, ax = plt.subplots(figsize=(14, 7))

    # Total portfolio - bold line
    ax.plot(df["date"], df["current_total_usd"], "k-", label="TOTAL PORTFOLIO",
            linewidth=3, alpha=0.8)

    # Individual assets - thinner lines
    colors = plt.cm.tab20.colors
    cur_cols = [c for c in df.columns if c.startswith("cur_")]

    for i, col in enumerate(cur_cols):
        label = col.replace("cur_", "")
        ax.plot(df["date"], df[col], "-", label=label,
                linewidth=1.2, alpha=0.7,
                color=colors[i % len(colors)])

    ax.set_title("Current Portfolio: Total + Individual Assets (USD)", fontsize=14, fontweight="bold")
    ax.set_xlabel("Date")
    ax.set_ylabel("Value (USD)")
    ax.legend(fontsize=8, ncol=3, loc="upper left")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    fig.autofmt_xdate()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    path3 = os.path.join(PLOTS_DIR, "portfolio_with_assets.png")
    fig.savefig(path3, dpi=150)
    plt.close(fig)
    print(f"[OK] Plot saved: {path3}")


def main():
    """Log daily values and generate plots."""
    print("=" * 60)
    print("  PORTFOLIO EVALUATION")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Step 1: Log daily values
    print("\n--- Logging daily values ---")
    log_daily_values()

    # Step 2: Generate plots
    print("\n--- Generating plots ---")
    generate_plots()

    print(f"\n{'='*60}")
    print("  EVALUATION COMPLETE")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
