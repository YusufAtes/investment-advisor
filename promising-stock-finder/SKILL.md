---
name: promising-stock-finder
description: >
  Finds promising stocks based on an investment thesis or theme. Uses web research,
  yfinance fundamentals, and halal/Israel compliance screening. Returns a shortlist
  with evidence, risks, catalysts, and valuation. Use when user says "find stocks",
  "stock ideas", "investment thesis", "screen stocks", "promising investments",
  "research a sector", "halal stocks", or "what stocks should I look at".
metadata:
  author: WealthSkills
  version: 1.0.0
  category: wealth-management
---

# Promising Stock Finder

Interactive research agent that discovers investment candidates matching a user's
thesis or theme, enriched with fundamental data and compliance screening.

## Instructions

### Step 1: Search by Thesis
```bash
python scripts/promising_stock_finder.py search --thesis "AI semiconductor companies with strong margins"
python scripts/promising_stock_finder.py search --thesis "Turkish energy sector plays"
python scripts/promising_stock_finder.py search --thesis "Halal ETFs with low expense ratios"
```

### Step 2: View Saved Candidates
```bash
python scripts/promising_stock_finder.py candidates
```

### Step 3: Get Details on a Specific Ticker
```bash
python scripts/promising_stock_finder.py detail --ticker NVDA
```

## Output Format
For each candidate, the tool returns:
- **Ticker & Name**: Stock identifier and company name
- **Evidence**: Why this stock fits the thesis
- **Risks**: Key risk factors
- **Catalysts**: Upcoming events or trends that could drive price
- **Valuation Snapshot**: P/E, ROE, EBITDA, 52-week range (from yfinance)
- **Halal Status**: COMPLIANT / NON_COMPLIANT / UNKNOWN
- **Israel Exposure**: NONE / DIRECT / INDIRECT / UNKNOWN

## Examples

**Example 1: Sector research**
User says: "Find me halal tech stocks with good fundamentals"
Actions:
1. Run: `python scripts/promising_stock_finder.py search --thesis "halal technology stocks with strong fundamentals and no Israel exposure"`
2. Present the shortlist with compliance status highlighted

**Example 2: Check saved candidates**
User says: "What stock ideas do we have saved?"
Actions:
1. Run: `python scripts/promising_stock_finder.py candidates`

## Important Notes
- Candidates are saved to `memory/candidate_stocks.jsonl` for the Weekly Advisor
- Compliance status marked UNKNOWN should be verified before trading
- Requires Gemini API key for web research
