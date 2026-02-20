"""
Price Fetcher
=============
Fetches current prices for all portfolio assets via yfinance and tefas,
converts everything to USD, and appends a row to price_history.txt.

Usage:
    python tracking/price_fetcher.py
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import yfinance as yf
import tefas

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Constants
TROY_OUNCE_GRAMS = 31.1035
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRACKING_DIR = os.path.join(BASE_DIR, "tracking")
PRICE_HISTORY_FILE = os.path.join(TRACKING_DIR, "price_history.txt")

# Column order for price_history.txt
COLUMNS = [
    "Date", "HLAL", "SPUS", "KPC", "HKH", "RBH",
    "THYAO", "LKMNH", "BIMAS", "ASML", "SPTE",
    "GOLD_GRAM", "SILVER_GRAM", "USDTRY",
]

# yfinance symbol mapping
YF_SYMBOLS = {
    "HLAL": "HLAL",           # USD native
    "SPUS": "SPUS",           # USD native
    "SPTE": "SPTE",           # USD native
    "ASML": "ASML",           # USD native
    "THYAO": "THYAO.IS",      # TRY native
    "LKMNH": "LKMNH.IS",     # TRY native
    "BIMAS": "BIMAS.IS",     # TRY native
}

# Assets that return prices in TRY and need USD conversion
TRY_NATIVE_YF = {"THYAO", "LKMNH", "BIMAS"}

# TEFAS funds (all TRY native)
TEFAS_FUNDS = ["KPC", "HKH", "RBH"]


def _now_iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def yf_last_price(symbol: str) -> float:
    """
    Fetch latest price from yfinance.
    Tries fast_info first, then falls back to .info.
    """
    t = yf.Ticker(symbol)
    price: Optional[float] = None

    # Preferred: fast_info
    try:
        fi = t.fast_info
        if fi:
            p = fi.get("lastPrice") or fi.get("last_price") or fi.get("last")
            if p is not None:
                price = float(p)
    except Exception:
        pass

    # Fallback: .info
    if price is None:
        info = t.info
        p = info.get("regularMarketPrice") or info.get("previousClose")
        if p is None:
            raise ValueError(f"Could not get price for {symbol} from yfinance.")
        price = float(p)

    return price


def tefas_latest_price(fon_kodu: str) -> float:
    """
    Fetch latest TEFAS fund unit price.
    Returns the most recent price in TRY.
    """
    df = tefas.get_data(fon_kodu, verbose=False)

    # Find the correct column
    if fon_kodu in df.columns:
        col = fon_kodu
    else:
        cols = {c.upper(): c for c in df.columns}
        if fon_kodu.upper() in cols:
            col = cols[fon_kodu.upper()]
        else:
            raise ValueError(f"TEFAS dataframe has no column for {fon_kodu}. Columns: {list(df.columns)}")

    return float(df[col].iloc[-1])


def fetch_all_prices() -> Dict[str, float]:
    """
    Fetch all asset prices and return them in USD.
    Returns a dict mapping column name -> USD price.
    """
    prices: Dict[str, float] = {}

    # 1. Fetch USD/TRY rate first (we need it for conversions)
    print("[PriceFetcher] Fetching USD/TRY exchange rate...")
    usdtry = yf_last_price("USDTRY=X")
    prices["USDTRY"] = round(usdtry, 4)
    print(f"  USDTRY = {usdtry:.4f}")

    # 2. Fetch yfinance assets
    for name, symbol in YF_SYMBOLS.items():
        try:
            print(f"[PriceFetcher] Fetching {name} ({symbol})...")
            raw_price = yf_last_price(symbol)

            if name in TRY_NATIVE_YF:
                # Convert TRY to USD
                usd_price = round(raw_price / usdtry, 6)
                print(f"  {name} = {raw_price:.2f} TRY -> {usd_price:.6f} USD")
            else:
                usd_price = round(raw_price, 6)
                print(f"  {name} = {usd_price:.6f} USD")

            prices[name] = usd_price

        except Exception as e:
            print(f"  [ERROR] Failed to fetch {name}: {e}")
            prices[name] = 0.0

    # 3. Fetch TEFAS funds (TRY native, convert to USD)
    for fund in TEFAS_FUNDS:
        try:
            print(f"[PriceFetcher] Fetching {fund} (TEFAS)...")
            try_price = tefas_latest_price(fund)
            usd_price = round(try_price / usdtry, 6)
            print(f"  {fund} = {try_price:.4f} TRY -> {usd_price:.6f} USD")
            prices[fund] = usd_price

        except Exception as e:
            print(f"  [ERROR] Failed to fetch {fund}: {e}")
            prices[fund] = 0.0

    # 4. Fetch Gold and Silver (USD/oz -> USD/gram)
    try:
        print("[PriceFetcher] Fetching Gold (GC=F)...")
        gold_oz_usd = yf_last_price("GC=F")
        gold_gram_usd = round(gold_oz_usd / TROY_OUNCE_GRAMS, 6)
        print(f"  Gold = {gold_oz_usd:.2f} USD/oz -> {gold_gram_usd:.6f} USD/gram")
        prices["GOLD_GRAM"] = gold_gram_usd
    except Exception as e:
        print(f"  [ERROR] Failed to fetch Gold: {e}")
        prices["GOLD_GRAM"] = 0.0

    try:
        print("[PriceFetcher] Fetching Silver (SI=F)...")
        silver_oz_usd = yf_last_price("SI=F")
        silver_gram_usd = round(silver_oz_usd / TROY_OUNCE_GRAMS, 6)
        print(f"  Silver = {silver_oz_usd:.2f} USD/oz -> {silver_gram_usd:.6f} USD/gram")
        prices["SILVER_GRAM"] = silver_gram_usd
    except Exception as e:
        print(f"  [ERROR] Failed to fetch Silver: {e}")
        prices["SILVER_GRAM"] = 0.0

    return prices


def append_to_price_history(prices: Dict[str, float]) -> str:
    """
    Append a row to price_history.txt (or create the file with header).
    If today's date already exists, overwrite that row.

    Returns the file path.
    """
    os.makedirs(TRACKING_DIR, exist_ok=True)

    today = datetime.now().strftime("%d.%m.%Y")

    # Build the row values in column order
    row_values = [today]
    for col in COLUMNS[1:]:  # skip "Date"
        val = prices.get(col, 0.0)
        row_values.append(f"{val:.6f}")

    new_row = "\t".join(row_values)

    if os.path.exists(PRICE_HISTORY_FILE):
        # Read existing file
        with open(PRICE_HISTORY_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Check if header exists
        if not lines or not lines[0].startswith("Date"):
            header = "\t".join(COLUMNS)
            lines.insert(0, header + "\n")

        # Check if today's row already exists, and overwrite it
        updated = False
        for i, line in enumerate(lines):
            if line.startswith(today + "\t"):
                lines[i] = new_row + "\n"
                updated = True
                break

        if not updated:
            lines.append(new_row + "\n")

        with open(PRICE_HISTORY_FILE, "w", encoding="utf-8") as f:
            f.writelines(lines)
    else:
        # Create new file with header
        header = "\t".join(COLUMNS)
        with open(PRICE_HISTORY_FILE, "w", encoding="utf-8") as f:
            f.write(header + "\n")
            f.write(new_row + "\n")

    print(f"\n[OK] Price history updated: {PRICE_HISTORY_FILE}")
    return PRICE_HISTORY_FILE


def main():
    """Fetch all prices and save to price_history.txt."""
    print("=" * 60)
    print("  PRICE FETCHER")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    prices = fetch_all_prices()

    print(f"\n--- Summary ---")
    for col in COLUMNS[1:]:
        val = prices.get(col, 0.0)
        unit = "TRY/USD" if col == "USDTRY" else "USD/gram" if "GRAM" in col else "USD"
        print(f"  {col:<14} = {val:.6f} {unit}")

    append_to_price_history(prices)

    # Also save latest prices as JSON for other scripts
    latest_path = os.path.join(TRACKING_DIR, "latest_prices.json")
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "timestamp": _now_iso_utc(),
            "prices": prices,
        }, f, indent=2, ensure_ascii=False)
    print(f"[OK] Latest prices saved: {latest_path}")


if __name__ == "__main__":
    main()
