"""
Portfolio Manager CLI
=====================
Interactive command-line tool for managing your investment portfolio.
Supports buying/selling assets, adding new assets, and viewing portfolio state.

Usage:
    python manage_portfolio.py                # Interactive mode
    python manage_portfolio.py --view         # View current portfolio
    python manage_portfolio.py --history      # View change history
"""

import json
import os
import shutil
import sys
from datetime import datetime
from typing import Optional

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Portfolio file paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PORTFOLIO_DIR = os.path.join(BASE_DIR, "portfolio")
PORTFOLIO_FILE = os.path.join(PORTFOLIO_DIR, "current_portfolio.json")
PORTFOLIO_HISTORY_DIR = os.path.join(PORTFOLIO_DIR, "history")
PORTFOLIO_CHANGES_LOG = os.path.join(PORTFOLIO_DIR, "changes_log.json")


def load_portfolio() -> dict:
    """Load the current portfolio from JSON file."""
    if not os.path.exists(PORTFOLIO_FILE):
        print("[ERROR] Portfolio file not found. Please create portfolio/current_portfolio.json first.")
        sys.exit(1)

    with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_portfolio(portfolio: dict) -> None:
    """Save the portfolio to JSON file."""
    os.makedirs(PORTFOLIO_DIR, exist_ok=True)
    with open(PORTFOLIO_FILE, "w", encoding="utf-8") as f:
        json.dump(portfolio, f, indent=2, ensure_ascii=False)
    print(f"\n[OK] Portfolio saved to: {PORTFOLIO_FILE}")


def archive_portfolio(portfolio: dict) -> str:
    """Archive the current portfolio to history before making changes."""
    os.makedirs(PORTFOLIO_HISTORY_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    archive_filename = f"portfolio_{timestamp}.json"
    archive_path = os.path.join(PORTFOLIO_HISTORY_DIR, archive_filename)

    with open(archive_path, "w", encoding="utf-8") as f:
        json.dump(portfolio, f, indent=2, ensure_ascii=False)

    print(f"[OK] Previous portfolio archived to: {archive_path}")
    return archive_path


def log_change(asset_name: str, action: str, pieces: float, price_per_piece_tl: float, notes: str = "") -> None:
    """Append a change entry to the changes log."""
    changes = []
    if os.path.exists(PORTFOLIO_CHANGES_LOG):
        with open(PORTFOLIO_CHANGES_LOG, "r", encoding="utf-8") as f:
            changes = json.load(f)

    change_entry = {
        "date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "asset": asset_name,
        "action": action,
        "pieces": pieces,
        "price_per_piece_tl": price_per_piece_tl,
        "total_value_tl": round(pieces * price_per_piece_tl, 2),
        "notes": notes,
    }

    changes.append(change_entry)

    with open(PORTFOLIO_CHANGES_LOG, "w", encoding="utf-8") as f:
        json.dump(changes, f, indent=2, ensure_ascii=False)

    print(f"[OK] Change logged: {action.upper()} {pieces} x {asset_name} @ {price_per_piece_tl:.2f} TL")


def recalculate_portfolio(portfolio: dict) -> dict:
    """Recalculate all derived fields (total_tl, total_usd, percentages)."""
    exchange_rate = portfolio["exchange_rate_usd_try"]

    # Recalculate each asset
    for asset in portfolio["assets"]:
        asset["total_tl"] = round(asset["pieces"] * asset["price_per_piece_tl"], 2)
        if exchange_rate > 0:
            asset["total_usd"] = round(asset["total_tl"] / exchange_rate, 2)
        else:
            asset["total_usd"] = 0.0

    # Recalculate totals
    total_tl = sum(asset["total_tl"] for asset in portfolio["assets"])
    portfolio["total_portfolio_tl"] = round(total_tl, 2)

    if exchange_rate > 0:
        portfolio["total_portfolio_usd"] = round(total_tl / exchange_rate, 2)
    else:
        portfolio["total_portfolio_usd"] = 0.0

    # Recalculate percentages
    for asset in portfolio["assets"]:
        if total_tl > 0:
            asset["percentage"] = round((asset["total_tl"] / total_tl) * 100, 2)
        else:
            asset["percentage"] = 0.0

    # Update date
    portfolio["date"] = datetime.now().strftime("%Y-%m-%d")

    return portfolio


def display_portfolio(portfolio: dict) -> None:
    """Display the portfolio in a formatted table."""
    print("\n" + "=" * 100)
    print(f"  CURRENT PORTFOLIO (as of {portfolio['date']})")
    print(f"  Exchange Rate: 1 USD = {portfolio['exchange_rate_usd_try']:.2f} TRY")
    print("=" * 100)

    # Header
    header = f"{'#':<4} {'Asset':<28} {'Pieces':>8} {'Price/Pc (TL)':>14} {'Total (TL)':>14} {'Total (USD)':>12} {'%':>7}"
    print(header)
    print("-" * 100)

    # Assets
    for i, asset in enumerate(portfolio["assets"], 1):
        row = (
            f"{i:<4} "
            f"{asset['name']:<28} "
            f"{asset['pieces']:>8.2f} "
            f"{asset['price_per_piece_tl']:>14,.2f} "
            f"{asset['total_tl']:>14,.2f} "
            f"{asset['total_usd']:>12,.2f} "
            f"{asset['percentage']:>6.2f}%"
        )
        print(row)

    # Totals
    print("-" * 100)
    total_row = (
        f"{'':4} "
        f"{'TOTAL':<28} "
        f"{'':>8} "
        f"{'':>14} "
        f"{portfolio['total_portfolio_tl']:>14,.2f} "
        f"{portfolio['total_portfolio_usd']:>12,.2f} "
        f"{'100.00%':>7}"
    )
    print(total_row)
    print("=" * 100)


def display_changes_history() -> None:
    """Display the changes log."""
    if not os.path.exists(PORTFOLIO_CHANGES_LOG):
        print("\n[INFO] No changes recorded yet.")
        return

    with open(PORTFOLIO_CHANGES_LOG, "r", encoding="utf-8") as f:
        changes = json.load(f)

    if not changes:
        print("\n[INFO] No changes recorded yet.")
        return

    print("\n" + "=" * 90)
    print("  PORTFOLIO CHANGE HISTORY")
    print("=" * 90)

    header = f"{'Date':<22} {'Action':<6} {'Asset':<28} {'Pieces':>8} {'Price/Pc':>12} {'Total (TL)':>12}"
    print(header)
    print("-" * 90)

    for change in changes:
        row = (
            f"{change['date']:<22} "
            f"{change['action'].upper():<6} "
            f"{change['asset']:<28} "
            f"{change['pieces']:>8.2f} "
            f"{change['price_per_piece_tl']:>12,.2f} "
            f"{change['total_value_tl']:>12,.2f}"
        )
        print(row)
        if change.get("notes"):
            print(f"  Note: {change['notes']}")

    print("=" * 90)


def get_input(prompt: str, default: Optional[str] = None) -> str:
    """Get user input with optional default value."""
    if default:
        user_input = input(f"{prompt} [{default}]: ").strip()
        return user_input if user_input else default
    return input(f"{prompt}: ").strip()


def get_float_input(prompt: str, default: Optional[float] = None) -> float:
    """Get a float value from user input."""
    while True:
        try:
            if default is not None:
                raw = input(f"{prompt} [{default}]: ").strip()
                if not raw:
                    return default
                return float(raw)
            else:
                return float(input(f"{prompt}: ").strip())
        except ValueError:
            print("  [!] Please enter a valid number.")


def get_int_choice(prompt: str, min_val: int, max_val: int) -> int:
    """Get an integer choice within a range."""
    while True:
        try:
            choice = int(input(f"{prompt}: ").strip())
            if min_val <= choice <= max_val:
                return choice
            print(f"  [!] Please enter a number between {min_val} and {max_val}.")
        except ValueError:
            print("  [!] Please enter a valid number.")


def action_buy_sell(portfolio: dict) -> dict:
    """Handle a buy or sell action on an existing asset."""
    print("\n--- SELECT ASSET ---")
    for i, asset in enumerate(portfolio["assets"], 1):
        print(f"  {i}. {asset['name']} (currently {asset['pieces']:.2f} pieces)")

    asset_idx = get_int_choice("Select asset number", 1, len(portfolio["assets"])) - 1
    selected_asset = portfolio["assets"][asset_idx]

    print(f"\nSelected: {selected_asset['name']}")
    print(f"Current pieces: {selected_asset['pieces']:.2f}")
    print(f"Current price/piece: {selected_asset['price_per_piece_tl']:,.2f} TL")

    # Buy or Sell
    print("\n  1. BUY (add more)")
    print("  2. SELL (reduce)")
    action_choice = get_int_choice("Select action", 1, 2)
    action = "buy" if action_choice == 1 else "sell"

    # How many pieces
    pieces = get_float_input(f"How many pieces to {action}?")

    if action == "sell" and pieces > selected_asset["pieces"]:
        print(f"  [!] You only have {selected_asset['pieces']:.2f} pieces. Selling all.")
        pieces = selected_asset["pieces"]

    # Price per piece
    price_per_piece = get_float_input(
        "Price per piece (TL)?",
        default=selected_asset["price_per_piece_tl"] if selected_asset["price_per_piece_tl"] > 0 else None,
    )

    # Update exchange rate
    exchange_rate = get_float_input(
        "Current USD/TRY exchange rate?",
        default=portfolio["exchange_rate_usd_try"],
    )
    portfolio["exchange_rate_usd_try"] = exchange_rate

    # Apply change
    if action == "buy":
        # Weighted average price if already holding
        if selected_asset["pieces"] > 0 and selected_asset["price_per_piece_tl"] > 0:
            total_old_value = selected_asset["pieces"] * selected_asset["price_per_piece_tl"]
            total_new_value = pieces * price_per_piece
            new_total_pieces = selected_asset["pieces"] + pieces
            selected_asset["price_per_piece_tl"] = round((total_old_value + total_new_value) / new_total_pieces, 2)
        else:
            selected_asset["price_per_piece_tl"] = price_per_piece
        selected_asset["pieces"] = round(selected_asset["pieces"] + pieces, 4)
    else:
        selected_asset["pieces"] = round(selected_asset["pieces"] - pieces, 4)
        if selected_asset["pieces"] <= 0:
            selected_asset["pieces"] = 0
            # Keep price for reference, user can remove asset separately

        # Update price to current market price on sell
        selected_asset["price_per_piece_tl"] = price_per_piece

    # Optional notes
    notes = get_input("Any notes? (press Enter to skip)", default="")

    # Log the change
    log_change(selected_asset["name"], action, pieces, price_per_piece, notes)

    # Recalculate
    portfolio = recalculate_portfolio(portfolio)

    return portfolio


def action_add_asset(portfolio: dict) -> dict:
    """Add a new asset to the portfolio."""
    print("\n--- ADD NEW ASSET ---")

    name = get_input("Asset name (e.g., 'THYAO Stock (BIST100)')")

    # Check duplicate
    existing_names = [a["name"].lower() for a in portfolio["assets"]]
    if name.lower() in existing_names:
        print(f"  [!] Asset '{name}' already exists. Use buy/sell to modify it.")
        return portfolio

    # Category
    print("\nCategory:")
    print("  1. stocks_funds")
    print("  2. real_estate")
    print("  3. gold_silver")
    print("  4. cash")
    cat_choice = get_int_choice("Select category", 1, 4)
    categories = {1: "stocks_funds", 2: "real_estate", 3: "gold_silver", 4: "cash"}
    category = categories[cat_choice]

    pieces = get_float_input("Number of pieces?")
    price_per_piece = get_float_input("Price per piece (TL)?")

    # Update exchange rate
    exchange_rate = get_float_input(
        "Current USD/TRY exchange rate?",
        default=portfolio["exchange_rate_usd_try"],
    )
    portfolio["exchange_rate_usd_try"] = exchange_rate

    new_asset = {
        "name": name,
        "category": category,
        "pieces": pieces,
        "price_per_piece_tl": price_per_piece,
        "total_tl": 0.0,
        "total_usd": 0.0,
        "percentage": 0.0,
    }

    portfolio["assets"].append(new_asset)

    # Log the change
    notes = get_input("Any notes? (press Enter to skip)", default="")
    log_change(name, "buy", pieces, price_per_piece, notes)

    # Recalculate
    portfolio = recalculate_portfolio(portfolio)

    print(f"\n[OK] Added '{name}' to portfolio.")
    return portfolio


def action_remove_asset(portfolio: dict) -> dict:
    """Remove an asset from the portfolio entirely."""
    print("\n--- REMOVE ASSET ---")

    zero_assets = [a for a in portfolio["assets"] if a["pieces"] <= 0]
    if not zero_assets:
        print("\n  No assets with 0 pieces. Sell the asset first before removing it.")
        return portfolio

    print("\nAssets with 0 pieces (eligible for removal):")
    for i, asset in enumerate(zero_assets, 1):
        print(f"  {i}. {asset['name']}")

    choice = get_int_choice("Select asset to remove (0 to cancel)", 0, len(zero_assets))
    if choice == 0:
        return portfolio

    asset_to_remove = zero_assets[choice - 1]
    portfolio["assets"] = [a for a in portfolio["assets"] if a["name"] != asset_to_remove["name"]]

    portfolio = recalculate_portfolio(portfolio)
    print(f"\n[OK] Removed '{asset_to_remove['name']}' from portfolio.")
    return portfolio


def action_update_prices(portfolio: dict) -> dict:
    """Update the price per piece for all or selected assets."""
    print("\n--- UPDATE ASSET PRICES ---")
    print("  1. Update all prices")
    print("  2. Update a single asset price")

    choice = get_int_choice("Select option", 1, 2)

    # Update exchange rate first
    exchange_rate = get_float_input(
        "Current USD/TRY exchange rate?",
        default=portfolio["exchange_rate_usd_try"],
    )
    portfolio["exchange_rate_usd_try"] = exchange_rate

    if choice == 1:
        print("\nEnter current price per piece for each asset (press Enter to keep current):\n")
        for asset in portfolio["assets"]:
            new_price = get_float_input(
                f"  {asset['name']} (current: {asset['price_per_piece_tl']:,.2f} TL)",
                default=asset["price_per_piece_tl"],
            )
            asset["price_per_piece_tl"] = new_price
    else:
        for i, asset in enumerate(portfolio["assets"], 1):
            print(f"  {i}. {asset['name']} ({asset['price_per_piece_tl']:,.2f} TL)")
        asset_idx = get_int_choice("Select asset", 1, len(portfolio["assets"])) - 1
        selected = portfolio["assets"][asset_idx]
        new_price = get_float_input(
            f"New price for {selected['name']} (TL)?",
            default=selected["price_per_piece_tl"],
        )
        selected["price_per_piece_tl"] = new_price

    portfolio = recalculate_portfolio(portfolio)
    print("\n[OK] Prices updated and portfolio recalculated.")
    return portfolio


def interactive_menu() -> None:
    """Main interactive menu loop."""
    portfolio = load_portfolio()

    print("\n" + "=" * 60)
    print("  INVESTMENT PORTFOLIO MANAGER")
    print("=" * 60)

    while True:
        display_portfolio(portfolio)

        print("\n  ACTIONS:")
        print("  1. Buy / Sell an existing asset")
        print("  2. Add a new asset")
        print("  3. Remove an asset (0 pieces only)")
        print("  4. Update asset prices")
        print("  5. View change history")
        print("  6. Save and exit")
        print("  7. Exit without saving")

        choice = get_int_choice("\nSelect action", 1, 7)

        if choice == 1:
            archive_portfolio(portfolio)
            portfolio = action_buy_sell(portfolio)
        elif choice == 2:
            archive_portfolio(portfolio)
            portfolio = action_add_asset(portfolio)
        elif choice == 3:
            portfolio = action_remove_asset(portfolio)
        elif choice == 4:
            archive_portfolio(portfolio)
            portfolio = action_update_prices(portfolio)
        elif choice == 5:
            display_changes_history()
        elif choice == 6:
            save_portfolio(portfolio)
            print("\n[OK] Portfolio saved. Goodbye!")
            break
        elif choice == 7:
            confirm = get_input("Are you sure? Unsaved changes will be lost (y/n)", default="n")
            if confirm.lower() == "y":
                print("\n[OK] Exited without saving.")
                break


def main():
    """Entry point with argument parsing."""
    import argparse

    parser = argparse.ArgumentParser(description="Investment Portfolio Manager")
    parser.add_argument("--view", action="store_true", help="View current portfolio")
    parser.add_argument("--history", action="store_true", help="View change history")
    args = parser.parse_args()

    if args.view:
        portfolio = load_portfolio()
        portfolio = recalculate_portfolio(portfolio)
        display_portfolio(portfolio)
    elif args.history:
        display_changes_history()
    else:
        interactive_menu()


if __name__ == "__main__":
    main()
