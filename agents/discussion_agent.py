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
            
        # Inject User Profile
        try:
            from utils.file_handler import FileHandler
            user_profile = FileHandler().load_user_profile()
            self.system_prompt = self.system_prompt.replace("{USER_PROFILE}", user_profile)
        except Exception as e:
            if VERBOSE:
                print(f"[{self.agent_id}] WARNING: Could not inject user profile: {e}")

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

        # Add financial pool data (Sampled 30% for this agent)
        from utils.data_formatter import truncate_and_sample_financial_pool
        sampled_pool_data = truncate_and_sample_financial_pool(financial_pool_data, sample_ratio=0.3)
        
        input_sections.append("\\n" + "=" * 60)
        input_sections.append("YFINANCE FINANCIAL DATA POOL (RANDOM SAMPLE)")
        input_sections.append("=" * 60)
        input_sections.append("\\n" + sampled_pool_data + "\\n")

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
- VERY IMPORTANT: At the very beginning of your output, explicitly state your assigned Risk Appetite, Holding Period, and Aggression Level so the Decider Agent knows your exact stance.

GENERATE YOUR DISCUSSION OUTPUT NOW:
"""

        provider = "gemini"
        from config import OPENAI_API_KEY, ANTHROPIC_API_KEY
        if self.agent_index % 3 == 0 and OPENAI_API_KEY:
            provider = "openai"
        elif self.agent_index % 3 == 2 and ANTHROPIC_API_KEY:
            provider = "anthropic"

        if VERBOSE:
            print(f"[{self.agent_id}] Routing request to provider: {provider.upper()}")

        try:
            if provider == "openai":
                return self._call_openai(execution_prompt)
            elif provider == "anthropic":
                return self._call_anthropic(execution_prompt)
            else:
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

    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API using urllib."""
        import urllib.request
        import json
        from config import OPENAI_API_KEY
        
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        data = {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers)
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"]

    def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic API using urllib."""
        import urllib.request
        import json
        from config import ANTHROPIC_API_KEY
        
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        data = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers)
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result["content"][0]["text"]

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

        # Save the model input alongside the output
        input_filename = "INPUT_" + filename
        input_filepath = os.path.join(output_dir, input_filename)
        input_to_save = getattr(self, "_last_input", "")
        if input_to_save:
            with open(input_filepath, "w", encoding="utf-8") as f:
                f.write(input_to_save)

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
