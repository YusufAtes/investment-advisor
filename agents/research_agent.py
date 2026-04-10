"""
Research Agent
==============
Agent with web search (Google Search grounding) capability for gathering
current market data, news, and analysis.
"""

import os
import sys
import time
import re
from google import genai
from google.genai import types
from datetime import datetime
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    GEMINI_API_KEY,
    PROMPTS_DIR,
    RESEARCH_MODEL,
    RESEARCH_TEMPERATURE,
    RESEARCH_MAX_TOKENS,
    RESEARCH_PROMPTS,
    RESEARCH_REPORT_NAMES,
    RESEARCH_REPORTS_DIR,
    VERBOSE,
)
from agents.base_agent import BaseAgent


class ResearchAgent(BaseAgent):
    """
    Research agent with Google Search grounding capability.
    Used for gathering real-time market data, news, and analysis.
    """

    def __init__(self, agent_id: str):
        """
        Initialize the research agent.

        Args:
            agent_id: Agent identifier (e.g., "1A", "2B", "3C")
        """
        if agent_id not in RESEARCH_PROMPTS:
            raise ValueError(f"Invalid research agent ID: {agent_id}. Valid IDs: {list(RESEARCH_PROMPTS.keys())}")

        prompt_file = RESEARCH_PROMPTS[agent_id]

        super().__init__(
            agent_id=f"Research_{agent_id}",
            prompt_file=prompt_file,
            model_name=RESEARCH_MODEL,
            temperature=RESEARCH_TEMPERATURE,
            max_tokens=RESEARCH_MAX_TOKENS,
        )

        self.research_id = agent_id

        if VERBOSE:
            print(f"[{self.agent_id}] Web search grounding enabled.")

    def generate_report(self) -> str:
        """
        Generate a research report using web search.

        Returns:
            Generated report content
        """
        current_date = self.get_current_date()
        timestamp = self.get_timestamp()

        # Build the execution prompt
        user_input = f"""
EXECUTE YOUR RESEARCH TASK NOW.

Instructions:
1. Use web search to gather the MOST CURRENT information available.
2. Focus on data, news, and developments from the past 7 days primarily.
3. CRITICAL SEARCH RULE: You MUST explicitly append the following site constraints to your Google searches to ensure Analyst-grade journalism:
   - For Global/US News append: `site:investing.com OR site:cnbc.com OR site:finance.yahoo.com`
   - For Turkish News append: `site:tr.investing.com OR site:tr.tradingview.com OR site:bloomberght.com`
4. Cite all sources with URLs when possible.
5. Generate your report following the OUTPUT TEMPLATE exactly.
6. Use today's date ({current_date}) for the Report Date in metadata.
7. Use the current timestamp ({timestamp}) for Generation Timestamp.

BEGIN YOUR RESEARCH AND GENERATE THE REPORT:
"""

        full_prompt = self._build_prompt(user_input)
        self._last_input = full_prompt

        if VERBOSE:
            print(f"[{self.agent_id}] Starting research with web search...")

        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Use Google Search grounding tool
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=full_prompt,
                    config=types.GenerateContentConfig(
                        temperature=self.temperature,
                        max_output_tokens=self.max_tokens,
                        tools=[types.Tool(google_search=types.GoogleSearch())],
                    )
                )
                report_content = response.text

                if VERBOSE:
                    print(f"[{self.agent_id}] Research report generated successfully.")

                return report_content

            except Exception as e:
                error_str = str(e)
                
                # Check if it's a rate limit error (429)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    retry_count += 1
                    
                    # Try to extract retry delay from error message
                    delay_match = re.search(r'retry in (\d+\.?\d*)s', error_str)
                    if delay_match:
                        wait_time = float(delay_match.group(1)) + 2  # Add buffer
                    else:
                        wait_time = 15 * retry_count  # Exponential backoff
                    
                    if retry_count < max_retries:
                        print(f"[{self.agent_id}] Rate limited. Waiting {wait_time:.1f}s before retry {retry_count}/{max_retries}...")
                        time.sleep(wait_time)
                        continue
                
                error_msg = f"[{self.agent_id}] Error generating research report: {error_str}"
                print(error_msg)
                raise
        
        raise Exception(f"[{self.agent_id}] Max retries ({max_retries}) exceeded")

    def save_report(self, content: str, output_dir: Optional[str] = None) -> str:
        """
        Save the research report to a file.

        Args:
            content: Report content to save
            output_dir: Directory to save to (defaults to RESEARCH_REPORTS_DIR)

        Returns:
            Path to the saved report file
        """
        if output_dir is None:
            output_dir = RESEARCH_REPORTS_DIR

        # Ensure directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Generate filename
        current_date = self.get_current_date()
        filename_template = RESEARCH_REPORT_NAMES.get(self.research_id)

        if filename_template:
            filename = filename_template.format(date=current_date)
        else:
            filename = f"REPORT_{self.research_id}_{current_date}.txt"

        filepath = os.path.join(output_dir, filename)

        # Save the report
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        if VERBOSE:
            print(f"[{self.agent_id}] Report saved to: {filepath}")

        # Save the model input alongside the output
        input_filename = "INPUT_" + filename
        input_filepath = os.path.join(output_dir, input_filename)
        input_to_save = getattr(self, "_last_input", "")
        if input_to_save:
            with open(input_filepath, "w", encoding="utf-8") as f:
                f.write(input_to_save)
            if VERBOSE:
                print(f"[{self.agent_id}] Input saved to: {input_filepath}")

        return filepath

    def run(self, output_dir: Optional[str] = None) -> tuple[str, str]:
        """
        Execute the full research workflow: generate and save report.

        Args:
            output_dir: Optional output directory override

        Returns:
            Tuple of (report_content, filepath)
        """
        content = self.generate_report()
        filepath = self.save_report(content, output_dir)
        return content, filepath


def run_all_research_agents(output_dir: Optional[str] = None, delay_between_agents: int = 10) -> dict[str, tuple[str, str]]:
    """
    Run all 9 research agents and collect their reports.

    Args:
        output_dir: Optional output directory override
        delay_between_agents: Seconds to wait between agents to avoid rate limits

    Returns:
        Dictionary mapping agent_id to (content, filepath) tuples
    """
    results = {}
    agent_ids = list(RESEARCH_PROMPTS.keys())

    for i, agent_id in enumerate(agent_ids):
        print(f"\n{'='*60}")
        print(f"Running Research Agent: {agent_id}")
        print(f"{'='*60}")

        try:
            agent = ResearchAgent(agent_id)
            content, filepath = agent.run(output_dir)
            results[agent_id] = (content, filepath)
            
            # Add delay between agents (except after the last one)
            if i < len(agent_ids) - 1 and delay_between_agents > 0:
                print(f"[Rate Limit] Waiting {delay_between_agents}s before next agent...")
                time.sleep(delay_between_agents)
                
        except Exception as e:
            print(f"Error running agent {agent_id}: {e}")
            results[agent_id] = (None, None)

    return results


if __name__ == "__main__":
    # Test run a single agent
    agent = ResearchAgent("1A")
    content, filepath = agent.run()
    print(f"\nReport saved to: {filepath}")
