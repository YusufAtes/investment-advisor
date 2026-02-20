"""
Portfolio Loader Utility
========================
Loads the current portfolio from JSON and formats it for injection into agent prompts.
"""

import json
import os
import sys
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_current_portfolio(portfolio_file: Optional[str] = None) -> dict:
    """
    Load the current portfolio from JSON file.

    Args:
        portfolio_file: Path to the portfolio JSON file (defaults to config value)

    Returns:
        Portfolio dictionary
    """
    if portfolio_file is None:
        from config import PORTFOLIO_FILE
        portfolio_file = PORTFOLIO_FILE

    if not os.path.exists(portfolio_file):
        raise FileNotFoundError(f"Portfolio file not found: {portfolio_file}")

    with open(portfolio_file, "r", encoding="utf-8") as f:
        return json.load(f)


def format_portfolio_for_prompt(portfolio: Optional[dict] = None, portfolio_file: Optional[str] = None) -> str:
    """
    Convert the portfolio JSON into a readable text block suitable for injection
    into agent prompts.

    Args:
        portfolio: Portfolio dictionary (if None, loads from file)
        portfolio_file: Path to portfolio file (used if portfolio is None)

    Returns:
        Formatted portfolio text string
    """
    if portfolio is None:
        portfolio = load_current_portfolio(portfolio_file)

    lines = []

    lines.append("=" * 80)
    lines.append(f"CURRENT PORTFOLIO (as of {portfolio['date']})")
    lines.append(f"Exchange Rate: 1 USD = {portfolio['exchange_rate_usd_try']:.2f} TRY")
    lines.append("=" * 80)
    lines.append("")

    # Column headers
    header = (
        f"{'Asset':<30} "
        f"{'Pieces':>8} "
        f"{'Price/Pc(USD)':>15} "
        f"{'Total(USD)':>12} "
        f"{'Total(TL)':>14} "
        f"{'%':>7}"
    )
    lines.append(header)
    lines.append("-" * 92)

    # Group by category for readability
    categories_order = ["stocks_funds", "real_estate", "gold_silver", "cash"]
    category_labels = {
        "stocks_funds": "STOCKS & FUNDS",
        "real_estate": "REAL ESTATE",
        "gold_silver": "GOLD & SILVER",
        "cash": "CASH",
    }

    for category in categories_order:
        category_assets = [a for a in portfolio["assets"] if a.get("category") == category]
        if not category_assets:
            continue

        lines.append(f"\n  [{category_labels.get(category, category.upper())}]")

        for asset in category_assets:
            row = (
                f"  {asset['name']:<28} "
                f"{asset['pieces']:>8.2f} "
                f"{asset['price_per_piece_usd']:>15,.6f} "
                f"{asset['total_usd']:>12,.2f} "
                f"{asset['total_tl']:>14,.2f} "
                f"{asset['percentage']:>6.2f}%"
            )
            lines.append(row)

    # Handle uncategorized assets
    uncategorized = [a for a in portfolio["assets"] if a.get("category") not in categories_order]
    if uncategorized:
        lines.append(f"\n  [OTHER]")
        for asset in uncategorized:
            row = (
                f"  {asset['name']:<28} "
                f"{asset['pieces']:>8.2f} "
                f"{asset['price_per_piece_usd']:>15,.6f} "
                f"{asset['total_usd']:>12,.2f} "
                f"{asset['total_tl']:>14,.2f} "
                f"{asset['percentage']:>6.2f}%"
            )
            lines.append(row)

    # Totals
    lines.append("")
    lines.append("-" * 92)
    total_row = (
        f"  {'TOTAL PORTFOLIO':<28} "
        f"{'':>8} "
        f"{'':>15} "
        f"{portfolio['total_portfolio_usd']:>12,.2f} "
        f"{portfolio['total_portfolio_tl']:>14,.2f} "
        f"{'100.00%':>7}"
    )
    lines.append(total_row)
    lines.append("=" * 92)

    return "\n".join(lines)


def load_changes_log(changes_file: Optional[str] = None) -> list:
    """
    Load the portfolio changes log.

    Args:
        changes_file: Path to the changes log file

    Returns:
        List of change entries
    """
    if changes_file is None:
        from config import PORTFOLIO_CHANGES_LOG
        changes_file = PORTFOLIO_CHANGES_LOG

    if not os.path.exists(changes_file):
        return []

    with open(changes_file, "r", encoding="utf-8") as f:
        return json.load(f)


def format_recent_changes_for_prompt(n: int = 10, changes_file: Optional[str] = None) -> str:
    """
    Format the last N portfolio changes for prompt injection.

    Args:
        n: Number of recent changes to include
        changes_file: Path to the changes log file

    Returns:
        Formatted changes text
    """
    changes = load_changes_log(changes_file)

    if not changes:
        return "No recent portfolio changes recorded."

    recent = changes[-n:]
    lines = ["RECENT PORTFOLIO CHANGES:"]

    for change in recent:
        price = change.get("price_per_piece_usd", change.get("price_per_piece_tl", 0))
        total = change.get("total_value_usd", change.get("total_value_tl", 0))
        line = (
            f"  [{change['date']}] {change['action'].upper()} "
            f"{change['pieces']} x {change['asset']} "
            f"@ {price:,.4f} USD "
            f"(Total: {total:,.2f} USD)"
        )
        lines.append(line)
        if change.get("notes"):
            lines.append(f"    Note: {change['notes']}")

    return "\n".join(lines)


if __name__ == "__main__":
    # Test: display formatted portfolio
    try:
        text = format_portfolio_for_prompt()
        print(text)
        print("\n")
        changes_text = format_recent_changes_for_prompt()
        print(changes_text)
    except FileNotFoundError as e:
        print(f"Error: {e}")
