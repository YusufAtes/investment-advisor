"""
Advisory Portfolio Executor
============================
Parses the latest Decider report, extracts recommended actions via LLM,
and executes them on the advisory (shadow) portfolio.

All math is done in Python -- the LLM only extracts intent from text.

Usage:
    python tracking/advisory_executor.py
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime
from glob import glob
from typing import Any, Dict, List, Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google import genai

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORTFOLIO_DIR = os.path.join(BASE_DIR, "portfolio")
ADVISORY_PORTFOLIO = os.path.join(PORTFOLIO_DIR, "advisory_portfolio.json")
CURRENT_PORTFOLIO = os.path.join(PORTFOLIO_DIR, "current_portfolio.json")
TRACKING_DIR = os.path.join(BASE_DIR, "tracking")
PRICE_HISTORY_FILE = os.path.join(TRACKING_DIR, "price_history.txt")
ACTIONS_LOG = os.path.join(TRACKING_DIR, "advisory_actions_log.json")
FINAL_REPORTS_DIR = os.path.join(BASE_DIR, "reports", "final")

# Cached real estate price (Cankaya average, in USD)
# Updated via web search when needed; stored persistently
REAL_ESTATE_CACHE_FILE = os.path.join(TRACKING_DIR, "real_estate_price_cache.json")
DEFAULT_CANKAYA_HOUSE_PRICE_USD = 150000  # Fallback if web lookup fails

# LLM Configuration
LLM_MODEL = "gemini-2.0-flash"

# Valid actions the LLM can output
VALID_ACTIONS = {"BUY", "SELL", "HOLD", "LIQUIDATE"}


def load_advisory_portfolio() -> dict:
    """Load the advisory portfolio. If it doesn't exist, copy from current."""
    if not os.path.exists(ADVISORY_PORTFOLIO):
        if os.path.exists(CURRENT_PORTFOLIO):
            import shutil
            shutil.copy2(CURRENT_PORTFOLIO, ADVISORY_PORTFOLIO)
            print("[AdvisoryExecutor] Created advisory portfolio from current portfolio.")
        else:
            raise FileNotFoundError("Neither advisory nor current portfolio exists.")

    with open(ADVISORY_PORTFOLIO, "r", encoding="utf-8") as f:
        return json.load(f)


def save_advisory_portfolio(portfolio: dict) -> None:
    """Save the advisory portfolio."""
    with open(ADVISORY_PORTFOLIO, "w", encoding="utf-8") as f:
        json.dump(portfolio, f, indent=2, ensure_ascii=False)
    print(f"[OK] Advisory portfolio saved: {ADVISORY_PORTFOLIO}")


def get_latest_final_report() -> tuple[str, str]:
    """
    Get the most recent FINAL_Decision report.

    Returns:
        Tuple of (date_str, report_content)
    """
    pattern = os.path.join(FINAL_REPORTS_DIR, "FINAL_Decision_*.txt")
    files = sorted(glob(pattern))

    if not files:
        raise FileNotFoundError("No final decision reports found.")

    latest = files[-1]
    date_match = re.search(r"(\d{4}-\d{2}-\d{2})", os.path.basename(latest))
    date_str = date_match.group(1) if date_match else "unknown"

    with open(latest, "r", encoding="utf-8") as f:
        content = f.read()

    print(f"[AdvisoryExecutor] Using report: {os.path.basename(latest)}")
    return date_str, content


def read_latest_prices() -> Dict[str, float]:
    """Read the latest prices from price_history.txt."""
    if not os.path.exists(PRICE_HISTORY_FILE):
        return {}

    with open(PRICE_HISTORY_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]

    if len(lines) < 2:
        return {}

    header = lines[0].split("\t")
    last_row = lines[-1].split("\t")

    prices = {}
    for i, col in enumerate(header):
        if col == "Date":
            continue
        try:
            prices[col] = float(last_row[i])
        except (ValueError, IndexError):
            prices[col] = 0.0

    return prices


def get_real_estate_price_usd() -> float:
    """
    Get the cached Cankaya average house price in USD.
    Uses a cached value if available, otherwise returns the default.
    """
    if os.path.exists(REAL_ESTATE_CACHE_FILE):
        with open(REAL_ESTATE_CACHE_FILE, "r", encoding="utf-8") as f:
            cache = json.load(f)
            return cache.get("price_usd", DEFAULT_CANKAYA_HOUSE_PRICE_USD)

    # Save default to cache
    cache = {
        "price_usd": DEFAULT_CANKAYA_HOUSE_PRICE_USD,
        "source": "default estimate",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "note": "Average Cankaya house price in USD. Update manually or via web search.",
    }
    os.makedirs(TRACKING_DIR, exist_ok=True)
    with open(REAL_ESTATE_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

    return DEFAULT_CANKAYA_HOUSE_PRICE_USD


def parse_actions_with_llm(report_content: str, portfolio: dict) -> List[Dict[str, Any]]:
    """
    Use Gemini to parse the KEY SUGGESTIONS section into structured JSON actions.

    Args:
        report_content: Full text of the FINAL_Decision report
        portfolio: Current advisory portfolio dict

    Returns:
        List of action dicts with keys: action, asset, quantity, allocation_pct, source
    """
    from config import GEMINI_API_KEY

    # Build asset list for context
    asset_names = [a["name"] for a in portfolio["assets"]]
    asset_info = []
    for a in portfolio["assets"]:
        asset_info.append(
            f"  - {a['name']} (category: {a['category']}, "
            f"pieces: {a['pieces']}, price_usd: {a['price_per_piece_usd']}, "
            f"total_usd: {a['total_usd']})"
        )
    asset_context = "\n".join(asset_info)

    prompt = f"""You are a structured data extractor. Your task is to parse investment action recommendations from an advisory report and convert them into a JSON array of executable actions.

CRITICAL: You must decompose every recommendation -- including combined/compound ones -- into individual SELL and BUY actions. A "REALLOCATE" recommendation is ALWAYS a SELL followed by one or more BUYs. Never skip the BUY side of a reallocation.

STEP-BY-STEP PROCESS:
1. Read the "KEY SUGGESTIONS" section of the report.
2. For each suggestion, determine the action type:
   - "SELL", "LIQUIDATE", "EXIT", "SELL entire position" -> SELL action
   - "BUY", "INCREASE", "ADD TO" -> BUY action
   - "HOLD", "MAINTAIN", "DEFER", "CONSIDER", "RESEARCH" -> HOLD action
   - "REALLOCATE", "REDEPLOY", "CONVERT", "SHIFT", "MOVE proceeds" -> This is a COMPOUND action. You MUST decompose it into:
     a) SELL action(s) for the source asset(s)
     b) BUY action(s) for the target asset(s), with amount_usd computed from the sell proceeds
3. For compound reallocations, compute the math:
   - First, sum up the total_usd of all assets being sold (use the values from PORTFOLIO ASSETS below).
   - Then split that total according to the percentages or proportions stated in the report.
   - Create a BUY action for each target asset with the computed amount_usd.
   - Example: "Sell KPC ($7142) and HKH ($4180), reallocate 60% to HLAL and 40% to Digital Gold"
     -> SELL KPC ALL, SELL HKH ALL, BUY HLAL $6793.20, BUY Digital Gold $4528.80
4. If a reallocation target is a NEW asset not in the portfolio (e.g., a suggested ETF or REIT from "CANDIDATE NEW INVESTMENTS"), you must still create a BUY action for the closest existing asset that matches the intent:
   - Infrastructure/REIT/Real Estate suggestion -> BUY "HLAL Fund" or "SPUS Fund" (global diversified funds as proxy)
   - Gold/Silver conversion (digital to physical) -> SELL "Digital Gold" + BUY "Physical Gold"
   - If no reasonable proxy exists, put the proceeds into "USD Cash" as a BUY.
5. Every asset in the portfolio must appear in your output as either SELL, BUY, or HOLD.
6. If the report says nothing about an asset, output HOLD for it.

RULES:
- Output ONLY valid JSON. No markdown, no explanations, no code fences.
- Each action must use an asset name EXACTLY as it appears in the portfolio list below.
- For SELL: use "quantity": "ALL" for full liquidation, or "quantity": NUMBER for partial sells.
- For BUY: use "amount_usd" for the dollar amount to invest. Include a "source" field.
- For HOLD: no additional fields needed.
- Only extract actions from the "KEY SUGGESTIONS" section.
- Real estate: ignore unless explicitly actionable (specific BUY/SELL with amount).

PORTFOLIO ASSETS:
{asset_context}

Total Portfolio USD: {portfolio['total_portfolio_usd']}

ADVISORY REPORT:
{report_content}

Output format - a JSON array of objects. EVERY portfolio asset must appear:
[
  {{"action": "SELL", "asset": "EXACT_ASSET_NAME", "quantity": "ALL"}},
  {{"action": "BUY", "asset": "EXACT_ASSET_NAME", "amount_usd": 1234.56, "source": "proceeds from SELL of X"}},
  {{"action": "HOLD", "asset": "EXACT_ASSET_NAME"}},
  ...
]

Output the JSON array now:"""

    client = genai.Client(api_key=GEMINI_API_KEY)

    # Try up to 3 times to get valid JSON
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=LLM_MODEL,
                contents=prompt,
            )

            raw_text = response.text.strip()

            # Strip markdown code fences if present
            if raw_text.startswith("```"):
                raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
                raw_text = re.sub(r"\s*```$", "", raw_text)

            actions = json.loads(raw_text)

            if not isinstance(actions, list):
                raise ValueError("LLM output is not a JSON array.")

            # Validate each action
            valid_actions = []
            for act in actions:
                if not isinstance(act, dict):
                    continue
                if act.get("action") not in VALID_ACTIONS:
                    print(f"  [WARN] Skipping invalid action: {act}")
                    continue
                # Map LIQUIDATE -> SELL ALL
                if act["action"] == "LIQUIDATE":
                    act["action"] = "SELL"
                    act["quantity"] = "ALL"
                # Verify asset name exists
                if act.get("asset") not in asset_names:
                    # Try fuzzy match
                    matched = _fuzzy_match_asset(act.get("asset", ""), asset_names)
                    if matched:
                        print(f"  [INFO] Mapped '{act['asset']}' -> '{matched}'")
                        act["asset"] = matched
                    else:
                        print(f"  [WARN] Unknown asset '{act.get('asset')}', skipping.")
                        continue
                valid_actions.append(act)

            print(f"[AdvisoryExecutor] Parsed {len(valid_actions)} actions (attempt {attempt+1})")
            return valid_actions

        except (json.JSONDecodeError, ValueError) as e:
            print(f"  [WARN] LLM output parse error (attempt {attempt+1}): {e}")
            if attempt < 2:
                print("  Retrying...")
            continue

    print("[ERROR] Failed to parse LLM output after 3 attempts.")
    return []


def _fuzzy_match_asset(name: str, valid_names: List[str]) -> Optional[str]:
    """Try to match a possibly-imprecise asset name to a valid portfolio name."""
    if not name:
        return None
    name_lower = name.lower()
    for vn in valid_names:
        if vn.lower() == name_lower:
            return vn
        # Check if the key part matches (e.g., "HLAL" in "HLAL Fund")
        if name_lower in vn.lower() or vn.lower() in name_lower:
            return vn
    return None


def execute_actions(
    portfolio: dict,
    actions: List[Dict[str, Any]],
    prices: Dict[str, float],
    report_date: str,
) -> tuple[dict, List[Dict[str, Any]]]:
    """
    Execute parsed actions on the advisory portfolio.

    All math is done in Python. The LLM only extracted intent.

    Args:
        portfolio: Advisory portfolio dict
        actions: List of action dicts from LLM
        prices: Latest prices dict
        report_date: Date of the report

    Returns:
        Tuple of (updated_portfolio, executed_actions_log)
    """
    # Name-to-column mapping for looking up latest prices
    from tracking.update_portfolio import ASSET_TO_COLUMN

    exchange_rate = portfolio["exchange_rate_usd_try"]
    executed = []
    cash_pool_usd = 0.0  # Temporary pool for proceeds from sales

    # Find or create a cash asset for leftover proceeds
    cash_asset = None
    for a in portfolio["assets"]:
        if a["name"] == "USD Cash":
            cash_asset = a
            break

    # First pass: execute all SELLs to build cash pool
    for act in actions:
        if act["action"] != "SELL":
            continue

        asset_name = act["asset"]
        asset = _find_asset(portfolio, asset_name)
        if asset is None:
            executed.append({**act, "status": "SKIPPED", "reason": f"Asset '{asset_name}' not found"})
            continue

        # Determine quantity
        quantity = act.get("quantity", "ALL")
        if quantity == "ALL":
            sell_pieces = asset["pieces"]
        else:
            try:
                sell_pieces = float(quantity)
            except (ValueError, TypeError):
                sell_pieces = asset["pieces"]

        # Validate
        if sell_pieces <= 0:
            executed.append({**act, "status": "SKIPPED", "reason": "Nothing to sell (0 pieces)"})
            continue

        if sell_pieces > asset["pieces"]:
            print(f"  [WARN] Sell {sell_pieces} > holdings {asset['pieces']} for {asset_name}. Selling all.")
            sell_pieces = asset["pieces"]

        # Execute sell at current price
        price_usd = asset["price_per_piece_usd"]
        proceeds = round(sell_pieces * price_usd, 2)
        cash_pool_usd += proceeds

        asset["pieces"] = round(asset["pieces"] - sell_pieces, 6)
        if asset["pieces"] < 0.0001:
            asset["pieces"] = 0

        executed.append({
            "date": report_date,
            "action": "SELL",
            "asset": asset_name,
            "pieces": sell_pieces,
            "price_usd": price_usd,
            "proceeds_usd": proceeds,
            "status": "EXECUTED",
        })

        print(f"  SELL {sell_pieces:.4f} x {asset_name} @ ${price_usd:.6f} = ${proceeds:.2f}")

    print(f"\n  Cash pool from sales: ${cash_pool_usd:.2f}")

    # Second pass: execute all BUYs
    for act in actions:
        if act["action"] != "BUY":
            continue

        asset_name = act["asset"]
        asset = _find_asset(portfolio, asset_name)

        # Handle real estate buy
        if asset and asset.get("category") == "real_estate":
            re_price = get_real_estate_price_usd()
            amount_usd = act.get("amount_usd", re_price)
            if amount_usd > cash_pool_usd:
                print(f"  [WARN] Not enough cash (${cash_pool_usd:.2f}) for real estate (${amount_usd:.2f}). Skipping.")
                executed.append({**act, "status": "SKIPPED", "reason": "Insufficient cash"})
                continue

            pieces_to_buy = amount_usd / re_price if re_price > 0 else 0
            asset["pieces"] = round(asset["pieces"] + pieces_to_buy, 6)
            asset["price_per_piece_usd"] = re_price
            cash_pool_usd -= amount_usd

            executed.append({
                "date": report_date,
                "action": "BUY",
                "asset": asset_name,
                "pieces": pieces_to_buy,
                "price_usd": re_price,
                "cost_usd": amount_usd,
                "status": "EXECUTED",
            })
            print(f"  BUY {pieces_to_buy:.6f} x {asset_name} @ ${re_price:.2f} = ${amount_usd:.2f}")
            continue

        if asset is None:
            executed.append({**act, "status": "SKIPPED", "reason": f"Asset '{asset_name}' not found"})
            continue

        # Determine buy amount
        amount_usd = act.get("amount_usd", 0)
        if amount_usd <= 0:
            # If no explicit amount, skip
            executed.append({**act, "status": "SKIPPED", "reason": "No amount_usd specified"})
            continue

        if amount_usd > cash_pool_usd:
            print(f"  [WARN] Requested ${amount_usd:.2f} but only ${cash_pool_usd:.2f} available for {asset_name}. Using available.")
            amount_usd = cash_pool_usd

        if amount_usd <= 0:
            executed.append({**act, "status": "SKIPPED", "reason": "No cash available"})
            continue

        # Get current price
        price_usd = asset["price_per_piece_usd"]
        if price_usd <= 0:
            # Try from price history
            col = ASSET_TO_COLUMN.get(asset_name, "")
            price_usd = prices.get(col, 0)
            if price_usd <= 0:
                executed.append({**act, "status": "SKIPPED", "reason": "No valid price available"})
                continue
            asset["price_per_piece_usd"] = price_usd

        pieces_to_buy = round(amount_usd / price_usd, 6)
        cost = round(pieces_to_buy * price_usd, 2)

        asset["pieces"] = round(asset["pieces"] + pieces_to_buy, 6)
        cash_pool_usd -= cost

        executed.append({
            "date": report_date,
            "action": "BUY",
            "asset": asset_name,
            "pieces": pieces_to_buy,
            "price_usd": price_usd,
            "cost_usd": cost,
            "status": "EXECUTED",
        })

        print(f"  BUY {pieces_to_buy:.4f} x {asset_name} @ ${price_usd:.6f} = ${cost:.2f}")

    # Log HOLD actions
    for act in actions:
        if act["action"] == "HOLD":
            executed.append({
                "date": report_date,
                "action": "HOLD",
                "asset": act["asset"],
                "status": "EXECUTED",
            })

    # Put remaining cash into USD Cash
    if cash_pool_usd > 0.01 and cash_asset is not None:
        cash_asset["pieces"] = round(cash_asset.get("pieces", 0) + cash_pool_usd, 2)
        cash_asset["price_per_piece_usd"] = 1.0  # 1 USD = 1 USD
        print(f"\n  Remaining cash ${cash_pool_usd:.2f} added to USD Cash")
    elif cash_pool_usd > 0.01:
        print(f"\n  [WARN] ${cash_pool_usd:.2f} remaining but no USD Cash asset found")

    # Recalculate portfolio
    exchange_rate = portfolio["exchange_rate_usd_try"]
    for asset in portfolio["assets"]:
        asset["total_usd"] = round(asset["pieces"] * asset["price_per_piece_usd"], 2)
        asset["total_tl"] = round(asset["total_usd"] * exchange_rate, 2)

    total_usd = sum(a["total_usd"] for a in portfolio["assets"])
    portfolio["total_portfolio_usd"] = round(total_usd, 2)
    portfolio["total_portfolio_tl"] = round(total_usd * exchange_rate, 2)

    for asset in portfolio["assets"]:
        if total_usd > 0:
            asset["percentage"] = round((asset["total_usd"] / total_usd) * 100, 2)
        else:
            asset["percentage"] = 0.0

    portfolio["date"] = datetime.now().strftime("%Y-%m-%d")

    return portfolio, executed


def _find_asset(portfolio: dict, name: str) -> Optional[dict]:
    """Find an asset by name in the portfolio."""
    for a in portfolio["assets"]:
        if a["name"] == name:
            return a
    return None


def log_actions(executed: List[Dict[str, Any]]) -> None:
    """Append executed actions to the advisory actions log."""
    existing = []
    if os.path.exists(ACTIONS_LOG):
        with open(ACTIONS_LOG, "r", encoding="utf-8") as f:
            existing = json.load(f)

    existing.extend(executed)

    with open(ACTIONS_LOG, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)

    print(f"[OK] Logged {len(executed)} actions to {ACTIONS_LOG}")


def main():
    """Main entry point: parse report, execute actions on advisory portfolio."""
    print("=" * 60)
    print("  ADVISORY PORTFOLIO EXECUTOR")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 1. Load advisory portfolio
    portfolio = load_advisory_portfolio()
    print(f"  Advisory portfolio total: ${portfolio['total_portfolio_usd']:,.2f} USD")

    # 2. Get latest report
    report_date, report_content = get_latest_final_report()

    # 3. Read latest prices
    prices = read_latest_prices()

    # 4. Parse actions via LLM
    print(f"\n--- Parsing actions from report ---")
    actions = parse_actions_with_llm(report_content, portfolio)

    if not actions:
        print("[INFO] No actionable items found. Advisory portfolio unchanged.")
        return

    print(f"\n--- Parsed actions ---")
    for i, act in enumerate(actions, 1):
        print(f"  {i}. {act['action']} {act.get('asset', 'N/A')} "
              f"{act.get('quantity', act.get('amount_usd', ''))}")

    # 5. Execute actions
    print(f"\n--- Executing actions ---")
    portfolio, executed = execute_actions(portfolio, actions, prices, report_date)

    # 6. Save portfolio
    save_advisory_portfolio(portfolio)

    # 7. Log actions
    log_actions(executed)

    # Summary
    sell_count = sum(1 for e in executed if e.get("action") == "SELL" and e.get("status") == "EXECUTED")
    buy_count = sum(1 for e in executed if e.get("action") == "BUY" and e.get("status") == "EXECUTED")
    skip_count = sum(1 for e in executed if e.get("status") == "SKIPPED")

    print(f"\n{'='*60}")
    print(f"  EXECUTION SUMMARY")
    print(f"  Sells executed: {sell_count}")
    print(f"  Buys executed:  {buy_count}")
    print(f"  Skipped:        {skip_count}")
    print(f"  New total: ${portfolio['total_portfolio_usd']:,.2f} USD")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
