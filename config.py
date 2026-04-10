"""
Investment Advisor System Configuration
======================================
All configurable parameters for the multi-agent investment advisory system.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# =============================================================================
# API CONFIGURATION
# =============================================================================

# Google Gemini API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your-gemini-api-key")

# Multi-LLM Support Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# =============================================================================
# EMAIL CONFIGURATION
# =============================================================================

# Gmail SMTP settings
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS", "your-email@gmail.com")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "your-app-password")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", "recipient@email.com")

# SMTP Server settings
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# =============================================================================
# MODEL CONFIGURATION
# =============================================================================

# Research agents - web search enabled, fast model for data gathering
# 2.0-flash is sufficient for factual retrieval with web search
RESEARCH_MODEL = "gemini-2.0-flash"

# Discussion agents - need strong reasoning for analysis
# 2.5-pro is the most capable currently available model
DISCUSSION_MODEL = "gemini-2.5-pro"

# Decider agent - most complex task, needs best reasoning
# 2.5-pro for synthesizing 12 inputs and making final decisions
DECIDER_MODEL = "gemini-2.5-pro"

# Inference agent - interactive Q&A with web search
# 2.5-pro for deep thinking and evidence-based responses
INFERENCE_MODEL = "gemini-2.5-pro"

# =============================================================================
# ITERATION SETTINGS
# =============================================================================

# Number of discussion iterations (3-5 recommended)
DISCUSSION_ITERATIONS = 3

# Number of self-iteration cycles for the decider agent
DECIDER_SELF_ITERATIONS = 3

# Number of past final reports to feed into the decider for historical awareness
PAST_REPORTS_COUNT = 3

# =============================================================================
# PATH CONFIGURATION
# =============================================================================

# Base directory (where this config file is located)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Prompts directory (where .txt prompt files are stored)
PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")

# Reports output directory
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
RESEARCH_REPORTS_DIR = os.path.join(REPORTS_DIR, "research")
DISCUSSION_REPORTS_DIR = os.path.join(REPORTS_DIR, "discussion")
FINAL_REPORTS_DIR = os.path.join(REPORTS_DIR, "final")

# Portfolio directory
PORTFOLIO_DIR = os.path.join(BASE_DIR, "portfolio")
PORTFOLIO_FILE = os.path.join(PORTFOLIO_DIR, "current_portfolio.json")
ADVISORY_PORTFOLIO_FILE = os.path.join(PORTFOLIO_DIR, "advisory_portfolio.json")
PORTFOLIO_HISTORY_DIR = os.path.join(PORTFOLIO_DIR, "history")
PORTFOLIO_CHANGES_LOG = os.path.join(PORTFOLIO_DIR, "changes_log.json")

# Tracking directory (price history, evaluation, plots)
TRACKING_DIR = os.path.join(BASE_DIR, "tracking")
PRICE_HISTORY_FILE = os.path.join(TRACKING_DIR, "price_history.txt")
EVALUATION_LOG = os.path.join(TRACKING_DIR, "evaluation_log.csv")
ADVISORY_ACTIONS_LOG = os.path.join(TRACKING_DIR, "advisory_actions_log.json")
PLOTS_DIR = os.path.join(TRACKING_DIR, "plots")

# =============================================================================
# AGENT PROMPT FILES
# =============================================================================

# =============================================================================
# AGENT PROMPT FILES
# =============================================================================

# Research agent prompts (9 agents)
RESEARCH_PROMPTS = {
    "1A": "1A - Gold & Silver News Agent.txt",
    "1B": "1B - Gold & Silver Market & Fundamental Agent.txt",
    "1C": "1C - Gold & Silver Social & Sentiment Agent.txt",
    "2A": "2A - Global Stocks & Funds News Agent.txt",
    "2B": "2B - Global Stocks & Funds Market & Fundamental Agent.txt",
    "2C": "2C - Global Stocks & Funds Social & Sentiment Agent.txt",
    "3A": "3A - Turkish Stocks & Funds News Agent.txt",
    "3B": "3B - Turkish Stocks & Funds Market & Fundamental Agent.txt",
    "3C": "3C - Turkish Stocks & Funds Social & Sentiment Agent.txt",
}

# Discussion agent prompts (Template used dynamically)
DISCUSSION_PROMPT_TEMPLATE = "Discussion Agent Template.txt"
# Number of dynamically generated mixture of experts (user wants 10 default)
DISCUSSION_AGENT_COUNT = 10

# Decider agent prompt
DECIDER_PROMPT = "Decider Agent.txt"

# Inference agent prompt
INFERENCE_PROMPT = "Inference Agent.txt"

# =============================================================================
# REPORT FILE NAMING
# =============================================================================

# Research report filename patterns
RESEARCH_REPORT_NAMES = {
    "1A": "REPORT_1A_Metals_News_{date}.txt",
    "1B": "REPORT_1B_Metals_Fundamentals_{date}.txt",
    "1C": "REPORT_1C_Metals_Sentiment_{date}.txt",
    "2A": "REPORT_2A_GlobalStocksFunds_News_{date}.txt",
    "2B": "REPORT_2B_GlobalStocksFunds_Fundamental_{date}.txt",
    "2C": "REPORT_2C_GlobalStocksFunds_Sentiment_{date}.txt",
    "3A": "REPORT_3A_TurkishStocksFunds_News_{date}.txt",
    "3B": "REPORT_3B_TurkishStocksFunds_Fundamental_{date}.txt",
    "3C": "REPORT_3C_TurkishStocksFunds_Sentiment_{date}.txt",
}

# Discussion report filename patterns
DISCUSSION_REPORT_NAMES = {
    "{agent_id}": "DISCUSSION_{agent_id}_{date}.txt",
}

# Final decider report filename pattern
DECIDER_REPORT_NAME = "FINAL_Decision_{date}.txt"

# =============================================================================
# GENERATION SETTINGS
# =============================================================================

# Temperature settings for different agent types
RESEARCH_TEMPERATURE = 0.7
DISCUSSION_TEMPERATURE = 0.7
DECIDER_TEMPERATURE = 0.5
INFERENCE_TEMPERATURE = 0.6  # Balanced for thoughtful responses

# Maximum output tokens
RESEARCH_MAX_TOKENS = 8192
DISCUSSION_MAX_TOKENS = 4096
DECIDER_MAX_TOKENS = 8192
INFERENCE_MAX_TOKENS = 16384  # Larger for detailed responses

# =============================================================================
# LOGGING
# =============================================================================

# Enable verbose logging
VERBOSE = True

# Log file path
LOG_FILE = os.path.join(BASE_DIR, "investment_advisor.log")
