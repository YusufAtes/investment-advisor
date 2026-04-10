#!/usr/bin/env python3
"""
Promising Stock Finder
======================
Interactive research agent that discovers investment candidates matching
a user's thesis, enriched with fundamental data and compliance screening.

Usage:
  python promising_stock_finder.py search --thesis "AI semiconductor companies"
  python promising_stock_finder.py candidates
  python promising_stock_finder.py detail --ticker NVDA
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from config import GEMINI_API_KEY
from skills.schemas import CandidateStock, HalalStatus, IsraelExposure, Confidence
from skills.memory_store import append_event, load_all, CANDIDATE_STOCKS_FILE

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Research via Gemini
# ---------------------------------------------------------------------------

def search_stocks_by_thesis(thesis: str) -> list[CandidateStock]:
    """
    Use Gemini with Google Search grounding to find stocks matching a thesis.

    Args:
        thesis: Investment thesis or theme description.

    Returns:
        List of CandidateStock objects.
    """
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""You are a financial research analyst. The user has an investment thesis:

"{thesis}"

Your task:
1. Search for 5-10 stocks/ETFs that match this thesis.
2. For each, provide:
   - Ticker symbol and full name
   - Exchange (e.g., NYSE, NASDAQ, BIST)
   - Why it fits the thesis (evidence)
   - Key risks (2-3 bullet points)
   - Upcoming catalysts
   - Basic valuation metrics (P/E, Market Cap, 52-week range) if available
   - Shariah/Halal compliance status (COMPLIANT, NON_COMPLIANT, or UNKNOWN)
   - Israel exposure status (NONE, DIRECT, INDIRECT, or UNKNOWN)

CRITICAL RULES:
- Prioritize Shariah-compliant options.
- Flag any Israel exposure clearly.
- Only include stocks you have reasonable confidence in.
- Be specific about why each stock fits the thesis.

Return your response as a JSON array of objects with these fields:
ticker, name, exchange, thesis, evidence (array of strings), risks (array),
catalysts (array), valuation_snapshot (object with pe, market_cap, range_52w),
halal_status (COMPLIANT/NON_COMPLIANT/UNKNOWN),
israel_exposure (NONE/DIRECT/INDIRECT/UNKNOWN),
confidence (HIGH/MEDIUM/LOW)

Return ONLY the JSON array, no other text.
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=4096,
                tools=[types.Tool(google_search=types.GoogleSearch())],
            ),
        )

        # Parse response
        text = response.text.strip()
        # Strip markdown fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.strip()

        raw_list = json.loads(text)
        candidates = []
        for item in raw_list:
            try:
                candidate = CandidateStock(
                    ticker=item.get("ticker", ""),
                    name=item.get("name", ""),
                    exchange=item.get("exchange", ""),
                    thesis=thesis,
                    evidence=item.get("evidence", []),
                    risks=item.get("risks", []),
                    catalysts=item.get("catalysts", []),
                    valuation_snapshot=item.get("valuation_snapshot", {}),
                    halal_status=HalalStatus(item.get("halal_status", "UNKNOWN")),
                    israel_exposure=IsraelExposure(item.get("israel_exposure", "UNKNOWN")),
                    confidence=Confidence(item.get("confidence", "MEDIUM")),
                )
                candidates.append(candidate)
            except Exception as e:
                logger.warning("Failed to parse candidate: %s", e)
                continue

        return candidates

    except Exception as e:
        logger.error("Stock search failed: %s", e)
        print(f"  [ERROR] Search failed: {e}")
        return []


def enrich_with_yfinance(candidate: CandidateStock) -> CandidateStock:
    """Enrich a candidate stock with yfinance fundamental data."""
    try:
        import yfinance as yf
        ticker = yf.Ticker(candidate.ticker)
        info = ticker.info or {}

        candidate.valuation_snapshot.update({
            "pe_trailing": info.get("trailingPE"),
            "pe_forward": info.get("forwardPE"),
            "market_cap": info.get("marketCap"),
            "roe": info.get("returnOnEquity"),
            "revenue_growth": info.get("revenueGrowth"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
            "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
        })
    except Exception as e:
        logger.warning("yfinance enrichment failed for %s: %s", candidate.ticker, e)
    return candidate


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def save_candidates(candidates: list[CandidateStock]) -> None:
    """Save candidates to memory."""
    for c in candidates:
        append_event(CANDIDATE_STOCKS_FILE, c.model_dump())
    print(f"  Saved {len(candidates)} candidate(s) to memory")


def load_saved_candidates() -> list[dict]:
    """Load all saved candidates."""
    return load_all(CANDIDATE_STOCKS_FILE)


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

def display_candidates(candidates: list) -> None:
    """Pretty-print candidate stocks."""
    if not candidates:
        print("  No candidates found.")
        return

    for i, c in enumerate(candidates, 1):
        if isinstance(c, CandidateStock):
            d = c.model_dump()
        else:
            d = c

        halal = d.get("halal_status", "UNKNOWN")
        israel = d.get("israel_exposure", "UNKNOWN")
        halal_icon = "✓" if halal == "COMPLIANT" else ("✗" if halal == "NON_COMPLIANT" else "?")
        israel_icon = "✓" if israel == "NONE" else ("✗" if israel in ("DIRECT", "INDIRECT") else "?")

        print(f"\n  [{i}] {d.get('ticker', '?')} — {d.get('name', 'N/A')}")
        print(f"      Exchange: {d.get('exchange', '?')} | Confidence: {d.get('confidence', '?')}")
        print(f"      Halal: {halal_icon} {halal} | Israel: {israel_icon} {israel}")
        if d.get("evidence"):
            print(f"      Evidence:")
            for ev in d["evidence"][:3]:
                print(f"        • {ev}")
        if d.get("risks"):
            print(f"      Risks:")
            for r in d["risks"][:3]:
                print(f"        • {r}")
        if d.get("catalysts"):
            print(f"      Catalysts:")
            for cat in d["catalysts"][:2]:
                print(f"        • {cat}")
        vs = d.get("valuation_snapshot", {})
        if vs:
            parts = []
            if vs.get("pe_trailing"):
                parts.append(f"P/E: {vs['pe_trailing']:.1f}")
            if vs.get("market_cap"):
                cap = vs["market_cap"]
                if cap > 1e12:
                    parts.append(f"MCap: ${cap/1e12:.1f}T")
                elif cap > 1e9:
                    parts.append(f"MCap: ${cap/1e9:.1f}B")
                else:
                    parts.append(f"MCap: ${cap/1e6:.0f}M")
            if parts:
                print(f"      Valuation: {' | '.join(parts)}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Promising Stock Finder")
    sub = parser.add_subparsers(dest="command")

    p_search = sub.add_parser("search", help="Search for stocks by thesis")
    p_search.add_argument("--thesis", required=True, help="Investment thesis or theme")
    p_search.add_argument("--enrich", action="store_true", help="Enrich with yfinance data")

    sub.add_parser("candidates", help="Show saved candidates")

    p_detail = sub.add_parser("detail", help="Get yfinance details for a ticker")
    p_detail.add_argument("--ticker", required=True)

    args = parser.parse_args()

    if args.command == "search":
        print(f"\n--- Searching for: {args.thesis} ---")
        candidates = search_stocks_by_thesis(args.thesis)

        if args.enrich:
            print("  Enriching with yfinance data...")
            candidates = [enrich_with_yfinance(c) for c in candidates]

        display_candidates(candidates)
        if candidates:
            save_candidates(candidates)

    elif args.command == "candidates":
        saved = load_saved_candidates()
        print(f"\n--- Saved Candidates ({len(saved)}) ---")
        display_candidates(saved)

    elif args.command == "detail":
        print(f"\n--- Details for {args.ticker} ---")
        c = CandidateStock(ticker=args.ticker)
        c = enrich_with_yfinance(c)
        display_candidates([c])

    else:
        parser.print_help()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
