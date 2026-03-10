---
name: investment-advisor
description: >
  Multi-agent investment advisory system that researches global markets (gold, silver,
  global stocks, Turkish stocks), synthesizes insights through a Mixture of Experts
  discussion, and produces actionable portfolio recommendations via email. Includes a
  portfolio management sub-skill where the AI directly edits the portfolio JSON when the
  user wants to add, remove, buy, sell, or update assets. Use when user says "run
  investment analysis", "analyze my portfolio", "investment advice", "market research",
  "run the pipeline", "check my investments", "ask about investments", "manage portfolio",
  "update prices", "evaluate portfolio performance", "run research agents", "get market
  report", "add to my portfolio", "I bought", "I sold", "update my holdings", "show my
  portfolio", or "remove from portfolio".
metadata:
  author: WealthSkills
  version: 1.0.0
  category: wealth-management
---

# Investment Advisor Multi-Agent System

Multi-agent investment advisory system powered by Google Gemini. Orchestrates 9 research
agents (with web search), 10 discussion agents (Mixture of Experts with randomized
investing styles), and a final decider agent that produces comprehensive investment
recommendations through self-iteration.

## First-Time Setup

Run these steps in order on the very first use. All commands assume the working
directory is the skill's `scripts/` folder.

### 1. Install Dependencies

```bash
cd scripts
pip install -r requirements.txt
```

Requires Python 3.11+. Key dependencies: `google-genai`, `python-dotenv`, `yfinance`,
`tefas`, `pandas`, `matplotlib`.

### 2. Configure API Keys

Copy `.env.example` to `.env` and fill in real values:

```bash
cp .env.example .env
```

Required variables:
- `GEMINI_API_KEY` — from https://aistudio.google.com/apikey
- `GMAIL_ADDRESS` — sender Gmail address (for email delivery)
- `GMAIL_APP_PASSWORD` — 16-char app password from https://myaccount.google.com/apppasswords
- `RECIPIENT_EMAIL` — where to send the final report

### 3. Initialize Portfolio

The AI agent manages the portfolio by directly reading and writing
`scripts/portfolio/current_portfolio.json`. No CLI tool is needed.

Create the directory and write the initial portfolio file:

```bash
mkdir -p scripts/portfolio
```

Then write `scripts/portfolio/current_portfolio.json` with this structure:

```json
{
  "date": "2026-03-10",
  "exchange_rate_usd_try": 38.50,
  "total_portfolio_usd": 0.0,
  "total_portfolio_tl": 0.0,
  "assets": []
}
```

Ask the user what assets they hold, then populate the `assets` array.

## Instructions

### Step 1: Run Full Pipeline

Execute all phases: Research (9 agents) -> Discussion (10 experts) -> Decider
(self-iteration) -> Advisory update -> Price update -> Email delivery.

```bash
cd scripts
python main.py
```

Options:
- `--skip-email` — Skip email delivery
- `--discussion-agents N` — Number of discussion experts (default: 10)
- `--decider-iterations N` — Number of decider self-iterations (default: 3)
- `--include-attachments` — Attach reports to email

### Step 2: Research Only

Run the 9 research agents to gather current market data via web search.

```bash
cd scripts
python main.py --research-only
```

### Step 3: Discussion Only

Run the Mixture of Experts discussion phase using existing research reports from today.

```bash
cd scripts
python main.py --discussion-only
```

### Step 4: Decider Only

Run only the decider agent using existing research and discussion outputs.

```bash
cd scripts
python main.py --decider-only
```

### Step 5: Interactive Q&A (Inference Mode)

Ask investment questions interactively. Uses past final reports and real-time web search.

```bash
cd scripts
python inference.py
python inference.py -n 5                          # Use last 5 reports as context
python inference.py --no-context                   # Web search only
python inference.py -q "Should I buy NVIDIA?"      # Single question mode
```

### Step 6: Portfolio Management (Sub-Skill)

When the user wants to view, add, remove, buy, sell, or update assets in their
portfolio, the AI agent handles it by directly editing the portfolio JSON file.
No CLI tool is needed — read the file, apply the user's changes, write it back.

**Portfolio file**: `scripts/portfolio/current_portfolio.json`

**Full JSON structure:**

```json
{
  "date": "2026-03-10",
  "exchange_rate_usd_try": 38.50,
  "total_portfolio_usd": 15250.00,
  "total_portfolio_tl": 587125.00,
  "assets": [
    {
      "name": "HLAL Fund",
      "category": "global_stocks_funds",
      "pieces": 100.0,
      "price_per_piece_usd": 50.25,
      "total_usd": 5025.00,
      "total_tl": 193462.50,
      "percentage": 32.95
    },
    {
      "name": "Gold (gram)",
      "category": "gold_silver",
      "pieces": 50.0,
      "price_per_piece_usd": 95.00,
      "total_usd": 4750.00,
      "total_tl": 182875.00,
      "percentage": 31.15
    }
  ]
}
```

**Valid categories:** `global_stocks_funds`, `turkish_stocks_funds`, `gold_silver`,
`cash`, `other`.

**Workflow for any portfolio change:**

1. Read `scripts/portfolio/current_portfolio.json`
2. Apply the user's requested change:
   - **Add asset**: Append a new object to the `assets` array
   - **Remove asset**: Delete the object from the `assets` array
   - **Buy**: Increase `pieces`, recalculate weighted average `price_per_piece_usd`
   - **Sell**: Decrease `pieces` (set to 0 if fully sold)
   - **Update price**: Change `price_per_piece_usd`
   - **Update exchange rate**: Change `exchange_rate_usd_try`
3. Recalculate derived fields for every asset:
   - `total_usd` = `pieces` * `price_per_piece_usd`
   - `total_tl` = `total_usd` * `exchange_rate_usd_try`
4. Recalculate portfolio totals:
   - `total_portfolio_usd` = sum of all `total_usd`
   - `total_portfolio_tl` = `total_portfolio_usd` * `exchange_rate_usd_try`
5. Recalculate `percentage` for each asset:
   - `percentage` = (`total_usd` / `total_portfolio_usd`) * 100
6. Update `date` to today
7. Write the file back

**Buy with weighted average price example:**
When buying more of an existing asset, compute the new average price:
```
new_avg = (old_pieces * old_price + new_pieces * new_price) / (old_pieces + new_pieces)
```

**Changes log** (optional): Append entries to `scripts/portfolio/changes_log.json`:
```json
[
  {
    "date": "2026-03-10T14:30:00",
    "asset": "HLAL Fund",
    "action": "buy",
    "pieces": 50.0,
    "price_per_piece_usd": 51.00,
    "total_value_usd": 2550.00,
    "notes": "Added on dip"
  }
]
```

### Step 7: Update Financial Data Pool

Fetch latest financial metrics (P/E, ROE, EBITDA, etc.) for all tracked assets via yfinance.

```bash
cd scripts
python -m utils.update_pool
```

### Step 8: Fetch Latest Prices

Fetch current prices for all portfolio assets and update price history.

```bash
cd scripts
python -m tracking.price_fetcher
```

### Step 9: Update Portfolio Totals

Apply latest prices to both current and advisory portfolios.

```bash
cd scripts
python -m tracking.update_portfolio
```

### Step 10: Evaluate Performance

Compare advisory portfolio vs actual holdings and generate plots.

```bash
cd scripts
python -m tracking.evaluate
```

### Step 11: Execute Advisory Actions

Parse the latest decider report and execute recommended trades on the advisory
(shadow) portfolio.

```bash
cd scripts
python -m tracking.advisory_executor
```

## Architecture

```
Research Agents (9, with Google Search grounding)
  1A/1B/1C: Gold & Silver (News, Fundamentals, Sentiment)
  2A/2B/2C: Global Stocks & Funds (News, Fundamentals, Sentiment)
  3A/3B/3C: Turkish Stocks & Funds (News, Fundamentals, Sentiment)
       |
       v
Discussion Agents (10, Mixture of Experts)
  Each with randomized investing style (Conservative / Balanced / Aggressive)
       |
       v
Decider Agent (3 self-iteration cycles)
  Synthesizes all inputs + historical reports + portfolio context
       |
       v
Output: Final Report -> Email -> Advisory Portfolio Update -> Price Tracking
```

## AI Agent Usage Notes

The AI agent directly manages all portfolio operations by reading and writing JSON
files. No interactive CLI tools are needed.

- **Portfolio management**: Read/write `scripts/portfolio/current_portfolio.json`
  directly. Follow the recalculation workflow in Step 6 for every change.
- **Inference**: Use `-q "question"` flag for single questions.
- **Pipeline**: `python main.py --skip-email` runs fully non-interactively.
- The pipeline will warn but continue if no portfolio exists — research and discussion
  phases still work, but advisory tracking phases will be skipped.
- When the user says "add X to my portfolio", "I bought Y", "sell Z", "update my
  holdings", or similar — use Step 6 (Portfolio Management sub-skill).

## Important Notes

- Uses Google Gemini models (gemini-2.0-flash for research, gemini-2.5-pro for
  discussion/decider/inference). API costs apply.
- Research agents use Google Search grounding for real-time data.
- The advisory portfolio is a shadow portfolio tracking recommendations. No real trades.
- Reports saved in `scripts/reports/` organized by type and date.
- Rate limiting handled with automatic retry and exponential backoff.
- Designed for Turkish and global markets with Shariah/participation compliance screening.
- Configuration (models, temperatures, token limits, iteration counts) adjustable in
  `scripts/config.py`.
