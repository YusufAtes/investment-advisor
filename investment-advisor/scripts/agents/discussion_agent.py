"""
Discussion Agent
================
Agent that synthesizes research reports and yfinance financial data
into distinct portfolio stances using a Mixture of Experts approach.
"""

import os
import sys
import json
import random
from google import genai
from google.genai import types
from datetime import datetime
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    GEMINI_API_KEY,
    PROMPTS_DIR,
    DISCUSSION_MODEL,
    DISCUSSION_TEMPERATURE,
    DISCUSSION_MAX_TOKENS,
    DISCUSSION_PROMPT_TEMPLATE,
    DISCUSSION_REPORT_NAMES,
    DISCUSSION_REPORTS_DIR,
    DISCUSSION_AGENT_COUNT,
    VERBOSE,
)
from agents.base_agent import BaseAgent
from utils.portfolio_loader import format_portfolio_for_prompt


def generate_random_investing_style() -> dict:
    """Generates a random json investing style."""
    aggression = random.uniform(0.1, 0.9)
    if aggression < 0.3:
        risk_appetite = "Conservative"
        holding_period = "Long-term (3+ years)"
        outline = "A highly risk-averse approach focused on capital preservation and steady dividend income over long-term market cycles. Prefers gold, cash, and very stable blue-chip companies."
    elif aggression < 0.7:
        risk_appetite = "Balanced / Moderate"
        holding_period = "Medium to Long-term (1-3 years)"
        outline = "A balanced approach aiming for steady growth while managing downside risk. Accepts moderate volatility for quality value stocks and diversified funds."
    else:
        risk_appetite = "Aggressive"
        holding_period = "Short to Medium-term (6 months - 2 years)"
        outline = "A growth-oriented approach seeking maximum capital appreciation. Willing to accept high volatility and concentrate positions in high-conviction growth stocks or momentum sectors."

    return {
        "Outline": outline,
        "Details": {
            "Risk Appetite": risk_appetite,
            "Holding Period": holding_period,
            "Strategy Consistency": str(round(random.uniform(0.7, 0.95), 2)),
            "Rationality": str(round(random.uniform(0.7, 0.95), 2)),
            "Aggression Level": str(round(aggression, 2))
        }
    }


class DiscussionAgent(BaseAgent):
    """
    Discussion agent that synthesizes data into a defined investing style stance.
    """

    def __init__(self, agent_index: int):
        """
        Initialize the discussion agent.
        Args:
            agent_index: Index of the agent (e.g., 1, 2, 3)
        """
        self.agent_index = agent_index
        agent_id = f"Agent_{agent_index}"

        super().__init__(
            agent_id=f"Discussion_{agent_id}",
            prompt_file=DISCUSSION_PROMPT_TEMPLATE,
            model_name=DISCUSSION_MODEL,
            temperature=DISCUSSION_TEMPERATURE,
            max_tokens=DISCUSSION_MAX_TOKENS,
        )

        self.discussion_id = agent_id
        
        # Inject dynamic portfolio
        try:
            portfolio_text = format_portfolio_for_prompt()
            self.system_prompt = self.system_prompt.replace("{PORTFOLIO}", portfolio_text)
        except Exception:
            pass

        # Generate and inject random investing style
        self.investing_style = generate_random_investing_style()
        style_json = json.dumps(self.investing_style, indent=2)
        self.system_prompt = self.system_prompt.replace("{INVESTING_STYLE}", style_json)

        if VERBOSE:
            print(f"[{self.agent_id}] Initialized with Aggression Level: {self.investing_style['Details']['Aggression Level']}")

    def generate_discussion(
        self,
        research_reports: dict[str, str],
        financial_pool_data: str,
    ) -> str:
        """
        Generate a discussion output based on inputs.
        """
        current_date = self.get_current_date()
        timestamp = self.get_timestamp()

        # Build the input context
        input_sections = []

        # Add research reports
        input_sections.append("=" * 60)
        input_sections.append("RESEARCH REPORTS")
        input_sections.append("=" * 60)

        for report_id, content in research_reports.items():
            input_sections.append(f"\\n--- {report_id} ---\\n")
            input_sections.append(content)
            input_sections.append("\\n")

        # Add financial pool data
        input_sections.append("\\n" + "=" * 60)
        input_sections.append("YFINANCE FINANCIAL DATA POOL")
        input_sections.append("=" * 60)
        input_sections.append("\\n" + financial_pool_data + "\\n")

        execution_prompt = f"""
{self.system_prompt}

────────────────────────────────
EXECUTION CONTEXT
────────────────────────────────
- Current Date: {current_date}
- Timestamp: {timestamp}

────────────────────────────────
INPUT DATA
────────────────────────────────
{"".join(input_sections)}

────────────────────────────────
TASK
────────────────────────────────
Based ONLY on the inputs and your assigned investing style, generate your discussion output.
- Follow the OUTPUT STRUCTURE exactly.
- Set Generation Timestamp to: {timestamp}

GENERATE YOUR DISCUSSION OUTPUT NOW:
"""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=execution_prompt,
                config=types.GenerateContentConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                )
            )
            return response.text
        except Exception as e:
            print(f"[{self.agent_id}] Error generating discussion: {e}")
            raise

    def save_discussion(self, content: str, output_dir: Optional[str] = None) -> str:
        if output_dir is None:
            # We don't use iteration subfolders anymore
            output_dir = DISCUSSION_REPORTS_DIR

        os.makedirs(output_dir, exist_ok=True)
        current_date = self.get_current_date()
        
        # Use config naming or fallback
        filename_template = DISCUSSION_REPORT_NAMES.get("{agent_id}", "DISCUSSION_{agent_id}_{date}.txt")
        filename = filename_template.format(agent_id=self.discussion_id, date=current_date)
        
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return filepath


def run_all_discussion_agents(
    research_reports: dict[str, str],
    financial_pool_data: str,
    num_agents: int = DISCUSSION_AGENT_COUNT,
    base_output_dir: Optional[str] = None,
) -> dict[str, tuple[str, str]]:
    """
    Run N discussion agents (Mixture of Experts) in parallel loops.
    """
    all_results = {}
    output_dir = base_output_dir or DISCUSSION_REPORTS_DIR

    print(f"\\n{'='*60}")
    print(f"DISCUSSION PHASE ({num_agents} Mixture of Experts Agents)")
    print(f"{'='*60}")

    for i in range(1, num_agents + 1):
        print(f"\\n{'-'*40}")
        print(f"Running Discussion Agent {i}")
        print(f"{'-'*40}")

        try:
            agent = DiscussionAgent(i)
            content = agent.generate_discussion(research_reports, financial_pool_data)
            filepath = agent.save_discussion(content, output_dir)
            all_results[agent.discussion_id] = (content, filepath)
        except Exception as e:
            print(f"Error running discussion agent {i}: {e}")
            all_results[f"Agent_{i}"] = (None, None)

    # Note: Returning dict with '1' key for backward compatibility in main.py if needed, 
    # but we can adjust main.py to read appropriately.
    return {1: all_results}
