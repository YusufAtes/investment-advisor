# Investment Advisor Multi-Agent System

A Python-based multi-agent system that generates daily investment advisory reports using Google Gemini AI.

## System Architecture

```
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
│                           DISCUSSION PHASE                                   │
│                          (N Iterations)                                      │
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
- **3 Discussion Agents** with iterative refinement
- **1 Decider Agent** with self-iteration for final synthesis
- **Email Delivery** via Gmail SMTP
- **Configurable** iteration counts and model parameters
- **CLI Interface** with multiple run modes

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

### 3. Verify Prompt Files

Ensure all 13 prompt files are present:
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

### Include Attachments in Email

```bash
python main.py --include-attachments
```

## Configuration

Edit `config.py` to customize:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `RESEARCH_MODEL` | `gemini-2.0-flash` | Model for research agents |
| `DISCUSSION_MODEL` | `gemini-2.0-flash` | Model for discussion agents |
| `DECIDER_MODEL` | `gemini-2.0-flash-thinking-exp` | Model for decider agent |
| `DISCUSSION_ITERATIONS` | `3` | Number of discussion rounds |
| `DECIDER_SELF_ITERATIONS` | `3` | Number of decider self-reflection cycles |

## Output Structure

```
reports/
├── research/           # 9 research reports
│   ├── REPORT_1A_News_2026-01-13.txt
│   ├── REPORT_1B_Fundamental_2026-01-13.txt
│   └── ...
├── discussion/         # Discussion outputs by iteration
│   ├── iteration_1/
│   ├── iteration_2/
│   └── iteration_3/
└── final/              # Final decision report
    └── FINAL_Decision_2026-01-13.txt
```

## Models Used

| Agent Type | Model | Features |
|------------|-------|----------|
| Research | `gemini-2.0-flash` | Web search grounding |
| Discussion | `gemini-2.0-flash` | Fast, efficient |
| Decider | `gemini-2.0-flash-thinking-exp` | Advanced reasoning |

## Troubleshooting

### API Key Issues
- Ensure your Gemini API key is valid
- Check you have sufficient quota

### Email Issues
- Verify 2FA is enabled on your Google account
- Ensure you're using an App Password, not your regular password
- Check the App Password is exactly 16 characters (no spaces)

### Missing Reports
- Run phases in order: research → discussion → decider
- Check the `reports/` directory for generated files

## License

This project is for personal use.

## Disclaimer

This system generates investment-related information for educational purposes only. It does not constitute financial advice. Always consult with qualified financial professionals before making investment decisions.
