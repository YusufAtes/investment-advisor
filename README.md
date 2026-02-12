# Investment Advisor Multi-Agent System

A Python-based multi-agent system that generates periodic (every 72 hours) investment advisory reports using Google Gemini AI. The system features a dynamic portfolio tracker, historical report awareness for consistent long-term advice, and an interactive inference mode for ad-hoc questions.

## System Architecture

```
                          ┌──────────────────────┐
                          │   Portfolio Manager   │
                          │  (manage_portfolio.py)│
                          └──────────┬───────────┘
                                     │ reads portfolio
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              RESEARCH PHASE                                  │
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                         │
│  │ 1A-1C       │  │ 2A-2C       │  │ 3A-3C       │                         │
│  │ Real Estate │  │ Gold/Silver │  │ Stocks/Funds│                         │
│  │ (3 agents)  │  │ (3 agents)  │  │ (3 agents)  │                         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                         │
│         │                │                │                                  │
│         └────────────────┼────────────────┘                                  │
│                          ▼                                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DISCUSSION PHASE (N Iterations)                            │
│                    + Dynamic Portfolio Context                                │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │ Agent 1         │  │ Agent 2         │  │ Agent 3         │             │
│  │ Gold-Favored    │◄─┤ RE-Favored      │◄─┤ Stocks-Favored  │             │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘             │
│           │                    │                    │                        │
│           └────────────────────┼────────────────────┘                        │
│                                ▼                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            DECISION PHASE                                    │
│                    + Dynamic Portfolio Context                                │
│                    + Last 3 Decision Reports                                 │
│                                                                              │
│                    ┌───────────────────────┐                                │
│                    │    Decider Agent      │                                │
│                    │  (Self-Iterating)     │                                │
│                    │  Thinking Model       │                                │
│                    └───────────┬───────────┘                                │
│                                │                                             │
└────────────────────────────────┼────────────────────────────────────────────┘
                                 │
                                 ▼
                         ┌───────────────┐
                         │ Email Report  │
                         │ (Gmail SMTP)  │
                         └───────────────┘
```

## Features

- **9 Research Agents** with Google Search grounding for real-time data
- **3 Discussion Agents** with iterative refinement and dynamic portfolio awareness
- **1 Decider Agent** with self-iteration, historical awareness (last 3 reports), and long-term consistency rules
- **Dynamic Portfolio Management** -- interactive CLI to track assets, buy/sell, with full history
- **Inference Mode** -- ask ad-hoc investment questions against historical reports + live web search
- **Email Delivery** via Gmail SMTP
- **72-Hour Run Cycle** -- configurable scheduled execution
- **Configurable** iteration counts, model parameters, and portfolio settings

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the project root with:

```env
# Google Gemini API Key
# Get your key from: https://aistudio.google.com/apikey
GEMINI_API_KEY=your-gemini-api-key-here

# Gmail SMTP Configuration
# For GMAIL_APP_PASSWORD, you need to:
# 1. Enable 2-Factor Authentication on your Google Account
# 2. Go to https://myaccount.google.com/apppasswords
# 3. Generate an App Password for "Mail"
GMAIL_ADDRESS=your-email@gmail.com
GMAIL_APP_PASSWORD=your-16-character-app-password

# Recipient Email Address
RECIPIENT_EMAIL=recipient@email.com
```

### 3. Set Up Your Portfolio

Before running the pipeline, enter your current portfolio data:

```bash
python manage_portfolio.py
```

This interactive tool lets you:
- Add/remove assets
- Record buy and sell actions
- Update asset prices and exchange rates
- View portfolio history

All discussion and decider agents read the portfolio dynamically from `portfolio/current_portfolio.json`.

### 4. Verify Prompt Files

Ensure all 14 prompt files exist in the `prompts/` directory:

- `1A - Real Estate News Agent.txt`
- `1B - Real Estate Market & Fundamental Agent.txt`
- `1C - Real Estate Social & Sentiment Agent.txt`
- `2A - Gold & Silver News Agent.txt`
- `2B - Gold & Silver Market & Fundamental Agent.txt`
- `2C - Gold & Silver Social & Sentiment Agent.txt`
- `3A - Stocks & Funds News Agent.txt`
- `3B - Stocks & Funds Market & Fundamental Agent.txt`
- `3C - Stocks & Funds Social & Sentiment Agent.txt`
- `Discussion Agent 1.txt`
- `Discussion Agent 2.txt`
- `Discussion Agent 3.txt`
- `Decider Agent.txt`
- `Inference Agent.txt`

## Usage

### Run Full Pipeline

```bash
python main.py
```

### Custom Iterations

```bash
# 5 discussion iterations, 4 decider self-iterations
python main.py --discussion-iterations 5 --decider-iterations 4
```

### Skip Email

```bash
python main.py --skip-email
```

### Run Individual Phases

```bash
# Research only
python main.py --research-only

# Discussion only (requires existing research reports)
python main.py --discussion-only

# Decider only (requires existing research + discussion)
python main.py --decider-only --iteration 3
```

### Portfolio Management

```bash
# Interactive portfolio manager
python manage_portfolio.py

# View current portfolio
python manage_portfolio.py --view

# View change history
python manage_portfolio.py --history
```

### Inference Mode (Interactive Q&A)

```bash
# Start interactive session
python inference.py

# Ask a single question
python inference.py --question "Should I sell my ASELS position?"
```

### Scheduled Execution (72-Hour Cycle)

The system runs every 72 hours via the scheduler script:

```bash
# Windows - double-click or use Task Scheduler
run_daily.bat

# PowerShell directly
powershell -ExecutionPolicy Bypass -File "run_daily.ps1"
```

The scheduler checks `last_run.txt` for the last execution timestamp and skips if fewer than 72 hours have passed.

## Portfolio System

The portfolio is stored as structured JSON and dynamically injected into all discussion and decider agent prompts at runtime.

### Portfolio Structure

```
portfolio/
├── current_portfolio.json    # Current portfolio state
├── changes_log.json          # Log of all buy/sell actions
└── history/                  # Archived snapshots before each change
    ├── portfolio_2026-02-10_143000.json
    └── portfolio_2026-02-12_091500.json
```

### Portfolio JSON Format

Each asset in `current_portfolio.json` contains:

| Field | Description |
|-------|-------------|
| `name` | Asset name (e.g., "HLAL Fund") |
| `category` | Asset class: `stocks_funds`, `real_estate`, `gold_silver`, `cash` |
| `pieces` | Number of units held |
| `price_per_piece_tl` | Current price per unit in TRY |
| `total_tl` | Total value in TRY (auto-calculated) |
| `total_usd` | Total value in USD (auto-calculated) |
| `percentage` | Percentage of total portfolio (auto-calculated) |

Top-level fields include `total_portfolio_tl`, `total_portfolio_usd`, `exchange_rate_usd_try`, and `date`.

## Configuration

Edit `config.py` to customize:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `RESEARCH_MODEL` | `gemini-2.0-flash` | Model for research agents |
| `DISCUSSION_MODEL` | `gemini-2.5-pro` | Model for discussion agents |
| `DECIDER_MODEL` | `gemini-2.5-pro` | Model for decider agent |
| `INFERENCE_MODEL` | `gemini-2.5-pro` | Model for inference agent |
| `DISCUSSION_ITERATIONS` | `3` | Number of discussion rounds |
| `DECIDER_SELF_ITERATIONS` | `3` | Number of decider self-reflection cycles |
| `PAST_REPORTS_COUNT` | `3` | Number of past reports fed to decider for consistency |

## Output Structure

```
reports/
├── research/               # 9 research reports per cycle
│   ├── REPORT_1A_News_2026-02-12.txt
│   ├── REPORT_1B_Fundamental_2026-02-12.txt
│   └── ...
├── discussion/             # Discussion outputs by iteration
│   ├── iteration_1/
│   ├── iteration_2/
│   └── iteration_3/
└── final/                  # Final decision reports
    ├── FINAL_Decision_2026-02-09.txt
    ├── FINAL_Decision_2026-02-12.txt
    └── ...                 # Last 3 are fed back to decider
```

## Decider Report Format

The final advisory report contains the following sections:

1. **Market Overview** -- concise environment summary
2. **Key Suggestions** -- prioritized actionable recommendations (1-5 items)
3. **Market Expectations** -- short-term (1-3 months) and medium-term (6-12 months) outlook
4. **Candidate New Investments** -- (conditional) only present when new assets are suggested
5. **Risk Alerts** -- high and medium risk warnings with recommended actions

The decider is designed for long-term wealth building consistency. It references its past 3 reports and avoids flip-flopping advice without clear justification.

## Models Used

| Agent Type | Model | Features |
|------------|-------|----------|
| Research (9) | `gemini-2.0-flash` | Web search grounding |
| Discussion (3) | `gemini-2.5-pro` | Strong reasoning, portfolio-aware |
| Decider (1) | `gemini-2.5-pro` | Self-iterating, history-aware |
| Inference (1) | `gemini-2.5-pro` | Web search + historical context |

## Troubleshooting

### API Key Issues
- Ensure your Gemini API key is valid
- Check you have sufficient quota

### Email Issues
- Verify 2FA is enabled on your Google account
- Ensure you're using an App Password, not your regular password
- Check the App Password is exactly 16 characters (no spaces)

### Missing Reports
- Run phases in order: research -> discussion -> decider
- Check the `reports/` directory for generated files

### Portfolio Not Loading
- Ensure `portfolio/current_portfolio.json` exists and is valid JSON
- Run `python manage_portfolio.py --view` to verify

## License

This project is for personal use.

## Disclaimer

This system generates investment-related information for educational purposes only. It does not constitute financial advice. Always consult with qualified financial professionals before making investment decisions.
