"""
Discussion Agent
================
Agent that synthesizes research reports and iteratively refines perspectives
based on other discussion agents' outputs.
"""

import os
import sys
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
    DISCUSSION_PROMPTS,
    DISCUSSION_REPORT_NAMES,
    DISCUSSION_REPORTS_DIR,
    VERBOSE,
)
from agents.base_agent import BaseAgent
from utils.portfolio_loader import format_portfolio_for_prompt


class DiscussionAgent(BaseAgent):
    """
    Discussion agent that synthesizes research reports and iteratively
    refines perspectives based on feedback from other discussion agents.
    """

    # Mapping of agent IDs to their perspective names
    PERSPECTIVES = {
        "gold_silver": "Gold & Silver–Favored",
        "real_estate": "Real Estate–Favored",
        "stocks_funds": "Stocks & Funds–Favored",
    }

    def __init__(self, agent_id: str):
        """
        Initialize the discussion agent.

        Args:
            agent_id: Agent identifier (e.g., "gold_silver", "real_estate", "stocks_funds")
        """
        if agent_id not in DISCUSSION_PROMPTS:
            raise ValueError(
                f"Invalid discussion agent ID: {agent_id}. "
                f"Valid IDs: {list(DISCUSSION_PROMPTS.keys())}"
            )

        prompt_file = DISCUSSION_PROMPTS[agent_id]

        super().__init__(
            agent_id=f"Discussion_{agent_id}",
            prompt_file=prompt_file,
            model_name=DISCUSSION_MODEL,
            temperature=DISCUSSION_TEMPERATURE,
            max_tokens=DISCUSSION_MAX_TOKENS,
        )

        self.discussion_id = agent_id
        self.perspective = self.PERSPECTIVES[agent_id]

        # Inject dynamic portfolio into the system prompt
        try:
            portfolio_text = format_portfolio_for_prompt()
            self.system_prompt = self.system_prompt.replace("{PORTFOLIO}", portfolio_text)
            if VERBOSE:
                print(f"[{self.agent_id}] Portfolio injected into system prompt.")
        except FileNotFoundError:
            if VERBOSE:
                print(f"[{self.agent_id}] WARNING: Portfolio file not found. Using prompt without portfolio data.")

        if VERBOSE:
            print(f"[{self.agent_id}] Model configured: {self.model_name}")

    def generate_discussion(
        self,
        research_reports: dict[str, str],
        iteration: int,
        previous_discussions: Optional[dict[str, str]] = None,
    ) -> str:
        """
        Generate a discussion output based on research reports and optional
        previous discussion outputs.

        Args:
            research_reports: Dictionary mapping report ID to content
            iteration: Current iteration number (1-based)
            previous_discussions: Optional dict of previous discussion outputs

        Returns:
            Generated discussion content
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
            input_sections.append(f"\n--- {report_id} ---\n")
            input_sections.append(content)
            input_sections.append("\n")

        # Add previous discussions if iteration > 1
        if iteration > 1 and previous_discussions:
            input_sections.append("\n" + "=" * 60)
            input_sections.append("PREVIOUS DISCUSSION OUTPUTS (ITERATION {})".format(iteration - 1))
            input_sections.append("=" * 60)

            for disc_id, content in previous_discussions.items():
                if disc_id != self.discussion_id:  # Don't include own previous output
                    input_sections.append(f"\n--- {disc_id} Perspective ---\n")
                    input_sections.append(content)
                    input_sections.append("\n")

        # Build execution prompt
        execution_prompt = f"""
{self.system_prompt}

────────────────────────────────
EXECUTION CONTEXT
────────────────────────────────
- Current Date: {current_date}
- Timestamp: {timestamp}
- Iteration: {iteration}
- Your Perspective: {self.perspective}

────────────────────────────────
INPUT DATA
────────────────────────────────
{"".join(input_sections)}

────────────────────────────────
TASK
────────────────────────────────
Based on the above inputs, generate your discussion output.
- This is iteration {iteration}.
- {"Use ONLY the research reports." if iteration == 1 else "Integrate the previous discussion outputs to refine and align your perspective."}
- Follow the OUTPUT STRUCTURE exactly.
- Set Iteration to: {iteration}
- Set Generation Timestamp to: {timestamp}

GENERATE YOUR DISCUSSION OUTPUT NOW:
"""

        if VERBOSE:
            print(f"[{self.agent_id}] Generating discussion (iteration {iteration})...")

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=execution_prompt,
                config=types.GenerateContentConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                )
            )
            discussion_content = response.text

            if VERBOSE:
                print(f"[{self.agent_id}] Discussion generated successfully.")

            return discussion_content

        except Exception as e:
            error_msg = f"[{self.agent_id}] Error generating discussion: {str(e)}"
            print(error_msg)
            raise

    def save_discussion(
        self,
        content: str,
        iteration: int,
        output_dir: Optional[str] = None,
    ) -> str:
        """
        Save the discussion output to a file.

        Args:
            content: Discussion content to save
            iteration: Current iteration number
            output_dir: Directory to save to

        Returns:
            Path to the saved discussion file
        """
        if output_dir is None:
            output_dir = os.path.join(DISCUSSION_REPORTS_DIR, f"iteration_{iteration}")

        # Ensure directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Generate filename
        current_date = self.get_current_date()
        filename_template = DISCUSSION_REPORT_NAMES.get(self.discussion_id)

        if filename_template:
            filename = filename_template.format(iteration=iteration, date=current_date)
        else:
            filename = f"DISCUSSION_{self.discussion_id}_Iter{iteration}_{current_date}.txt"

        filepath = os.path.join(output_dir, filename)

        # Save the discussion
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        if VERBOSE:
            print(f"[{self.agent_id}] Discussion saved to: {filepath}")

        return filepath

    def run(
        self,
        research_reports: dict[str, str],
        iteration: int,
        previous_discussions: Optional[dict[str, str]] = None,
        output_dir: Optional[str] = None,
    ) -> tuple[str, str]:
        """
        Execute the full discussion workflow: generate and save.

        Args:
            research_reports: Dictionary mapping report ID to content
            iteration: Current iteration number
            previous_discussions: Optional dict of previous discussion outputs
            output_dir: Optional output directory override

        Returns:
            Tuple of (discussion_content, filepath)
        """
        content = self.generate_discussion(
            research_reports=research_reports,
            iteration=iteration,
            previous_discussions=previous_discussions,
        )
        filepath = self.save_discussion(content, iteration, output_dir)
        return content, filepath


def run_discussion_iteration(
    research_reports: dict[str, str],
    iteration: int,
    previous_discussions: Optional[dict[str, str]] = None,
    output_dir: Optional[str] = None,
) -> dict[str, tuple[str, str]]:
    """
    Run all 3 discussion agents for a single iteration.

    Args:
        research_reports: Dictionary mapping report ID to content
        iteration: Current iteration number
        previous_discussions: Optional dict of previous discussion outputs
        output_dir: Optional output directory override

    Returns:
        Dictionary mapping agent_id to (content, filepath) tuples
    """
    results = {}

    for agent_id in DISCUSSION_PROMPTS.keys():
        print(f"\n{'-'*40}")
        print(f"Running Discussion Agent: {agent_id} (Iteration {iteration})")
        print(f"{'-'*40}")

        try:
            agent = DiscussionAgent(agent_id)
            content, filepath = agent.run(
                research_reports=research_reports,
                iteration=iteration,
                previous_discussions=previous_discussions,
                output_dir=output_dir,
            )
            results[agent_id] = (content, filepath)
        except Exception as e:
            print(f"Error running discussion agent {agent_id}: {e}")
            results[agent_id] = (None, None)

    return results


def run_all_discussion_iterations(
    research_reports: dict[str, str],
    num_iterations: int,
    base_output_dir: Optional[str] = None,
) -> dict[int, dict[str, tuple[str, str]]]:
    """
    Run all discussion iterations.

    Args:
        research_reports: Dictionary mapping report ID to content
        num_iterations: Number of iterations to run
        base_output_dir: Optional base output directory

    Returns:
        Dictionary mapping iteration number to results dict
    """
    all_results = {}
    previous_discussions = None

    for iteration in range(1, num_iterations + 1):
        print(f"\n{'='*60}")
        print(f"DISCUSSION ITERATION {iteration} of {num_iterations}")
        print(f"{'='*60}")

        # Set output directory for this iteration
        if base_output_dir:
            output_dir = os.path.join(base_output_dir, f"iteration_{iteration}")
        else:
            output_dir = None

        # Run this iteration
        results = run_discussion_iteration(
            research_reports=research_reports,
            iteration=iteration,
            previous_discussions=previous_discussions,
            output_dir=output_dir,
        )

        all_results[iteration] = results

        # Extract content for next iteration
        previous_discussions = {
            agent_id: content
            for agent_id, (content, _) in results.items()
            if content is not None
        }

    return all_results


if __name__ == "__main__":
    # Test with mock data
    mock_reports = {
        "1A": "Mock Real Estate News Report",
        "1B": "Mock Real Estate Fundamental Report",
        "1C": "Mock Real Estate Sentiment Report",
        "2A": "Mock Gold News Report",
        "2B": "Mock Gold Fundamental Report",
        "2C": "Mock Gold Sentiment Report",
        "3A": "Mock Stocks News Report",
        "3B": "Mock Stocks Fundamental Report",
        "3C": "Mock Stocks Sentiment Report",
    }

    agent = DiscussionAgent("gold_silver")
    content, filepath = agent.run(mock_reports, iteration=1)
    print(f"\nDiscussion saved to: {filepath}")
