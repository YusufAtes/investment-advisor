---
name: investment-advisor
description: >
  Multi-agent investment advisory system that researches global markets (gold, silver,
  global stocks, Turkish stocks), synthesizes insights through a Mixture of Experts
  discussion, and produces actionable portfolio recommendations via email. Supports full
  pipeline, partial runs (research-only, discussion-only, decider-only), interactive Q&A
  inference mode, and portfolio management. Use when user says "run investment analysis",
  "analyze my portfolio", "investment advice", "market research", "run the pipeline",
  "check my investments", "ask about investments", "manage portfolio", "update prices",
  "evaluate portfolio performance", "run research agents", or "get market report".
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

## Prerequisites

### API Keys

A `.env` file must exist in `scripts/` with the following variables (copy `.env.example`):

```
GEMINI_API_KEY=<your-gemini-api-key>
GMAIL_ADDRESS=<your-gmail>
GMAIL_APP_PASSWORD=<your-app-password>
RECIPIENT_EMAIL=<recipient-email>
```

### Python Dependencies

```bash
cd scripts
pip install -r requirements.txt
```

Requires Python 3.11+. Key dependencies: `google-genai`, `python-dotenv`, `yfinance`,
`tefas`, `pandas`, `matplotlib`.

### Portfolio Setup

A portfolio JSON file must exist at `scripts/portfolio/current_portfolio.json`.
Use the portfolio manager (Step 6) to create and maintain it.

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

### Step 6: Portfolio Management

Interactive CLI for managing portfolio assets (buy, sell, add, remove, update prices).

```bash
cd scripts
python manage_portfolio.py                # Interactive mode
python manage_portfolio.py --view         # Display current portfolio
python manage_portfolio.py --history      # View change history
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
