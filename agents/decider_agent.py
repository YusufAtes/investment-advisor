"""
Decider Agent
=============
Final decision-making agent that synthesizes all research and discussion outputs
into actionable investment guidance using self-iteration for refinement.
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
    DECIDER_MODEL,
    DECIDER_TEMPERATURE,
    DECIDER_MAX_TOKENS,
    DECIDER_PROMPT,
    DECIDER_REPORT_NAME,
    DECIDER_SELF_ITERATIONS,
    FINAL_REPORTS_DIR,
    PAST_REPORTS_COUNT,
    VERBOSE,
)
from agents.base_agent import BaseAgent
from utils.file_handler import FileHandler
from utils.portfolio_loader import format_portfolio_for_prompt


class DeciderAgent(BaseAgent):
    """
    Final decision-making agent that uses self-iteration to produce
    refined, actionable investment guidance.
    """

    def __init__(self, self_iterations: Optional[int] = None):
        """
        Initialize the decider agent.

        Args:
            self_iterations: Number of self-iteration cycles (defaults to config value)
        """
        super().__init__(
            agent_id="Decider",
            prompt_file=DECIDER_PROMPT,
            model_name=DECIDER_MODEL,
            temperature=DECIDER_TEMPERATURE,
            max_tokens=DECIDER_MAX_TOKENS,
        )

        self.self_iterations = self_iterations or DECIDER_SELF_ITERATIONS

        # Inject dynamic portfolio into the system prompt
        try:
            portfolio_text = format_portfolio_for_prompt()
            self.system_prompt = self.system_prompt.replace("{PORTFOLIO}", portfolio_text)
            if VERBOSE:
                print(f"[{self.agent_id}] Portfolio injected into system prompt.")
        except FileNotFoundError:
            if VERBOSE:
                print(f"[{self.agent_id}] WARNING: Portfolio file not found. Using prompt without portfolio data.")

        # Inject User Profile
        try:
            user_profile = FileHandler().load_user_profile()
            self.system_prompt = self.system_prompt.replace("{USER_PROFILE}", user_profile)
            if VERBOSE:
                print(f"[{self.agent_id}] User profile injected into system prompt.")
        except Exception as e:
            if VERBOSE:
                print(f"[{self.agent_id}] WARNING: Could not inject user profile: {e}")

        # Load past decision reports for historical awareness
        self.past_reports = self._load_past_reports(PAST_REPORTS_COUNT)

        if VERBOSE:
            print(f"[{self.agent_id}] Thinking model configured: {self.model_name}")
            print(f"[{self.agent_id}] Loaded {len(self.past_reports)} past decision reports.")

    def _load_past_reports(self, n: int = 3) -> list[tuple[str, str]]:
        """
        Load the last N final decision reports for historical awareness.

        Args:
            n: Number of past reports to load

        Returns:
            List of (date, content) tuples, most recent first
        """
        try:
            file_handler = FileHandler()
            return file_handler.get_recent_final_reports(n=n, exclude_today=True)
        except Exception as e:
            if VERBOSE:
                print(f"[{self.agent_id}] Warning: Could not load past reports: {e}")
            return []

    def _build_input_context(
        self,
        discussion_outputs: dict[str, str],
        financial_pool_data: str,
    ) -> str:
        """
        Build the complete input context from discussion outputs and pool data.

        Args:
            discussion_outputs: Dictionary mapping discussion ID to content
            financial_pool_data: String containing the YFinance data pool

        Returns:
            Formatted input context string
        """
        sections = []

        # Financial Pool Section
        sections.append("=" * 80)
        sections.append("SECTION A: YFINANCE FINANCIAL DATA POOL")
        sections.append("=" * 80)
        sections.append("\n" + financial_pool_data + "\n")

        # Discussion Outputs Section
        num_discussions = len(discussion_outputs)
        sections.append("\n" + "=" * 80)
        sections.append(f"SECTION B: DISCUSSION AGENT OUTPUTS ({num_discussions} EXPERTS)")
        sections.append("=" * 80)

        for disc_id, content in discussion_outputs.items():
            sections.append(f"\n### Expert Perspective: {disc_id} ###\n")
            sections.append(content)

        # Past Decision Reports Section
        if self.past_reports:
            sections.append("\n" + "=" * 80)
            sections.append(f"SECTION C: YOUR PAST DECISION REPORTS ({len(self.past_reports)} REPORTS)")
            sections.append("These are YOUR previous outputs. Use them for consistency and to avoid repetition.")
            sections.append("=" * 80)

            for report_date, report_content in self.past_reports:
                sections.append(f"\n### Past Report: {report_date} ###\n")
                sections.append(report_content)
        else:
            sections.append("\n" + "=" * 80)
            sections.append("SECTION C: YOUR PAST DECISION REPORTS")
            sections.append("No previous decision reports available. This appears to be your first report.")
            sections.append("=" * 80)

        return "\n".join(sections)

    def _generate_iteration(
        self,
        input_context: str,
        iteration_num: int,
        previous_output: Optional[str] = None,
    ) -> str:
        """
        Generate a single self-iteration output.

        Args:
            input_context: The complete input context
            iteration_num: Current iteration number (1-based)
            previous_output: Output from previous iteration (if any)

        Returns:
            Generated output for this iteration
        """
        current_date = self.get_current_date()
        timestamp = self.get_timestamp()

        if iteration_num == 1:
            # First iteration: Initial synthesis
            iteration_prompt = f"""
{self.system_prompt}

────────────────────────────────
SELF-ITERATION: {iteration_num} of {self.self_iterations} (INITIAL SYNTHESIS)
────────────────────────────────

CURRENT DATE: {current_date}
TIMESTAMP: {timestamp}

{input_context}

────────────────────────────────
TASK: INITIAL SYNTHESIS
────────────────────────────────

This is your FIRST iteration. Your task:
1. Read ALL inputs thoroughly (research reports, discussions, AND your past decision reports)
2. Identify key themes, agreements, and conflicts
3. Compare with your past recommendations — what has changed? What still holds?
4. Generate your INITIAL recommendations following the OUTPUT TEMPLATE

Note: You will have {self.self_iterations - 1} more iteration(s) to refine this output.

GENERATE YOUR INITIAL SYNTHESIS NOW:
"""
        elif iteration_num == self.self_iterations:
            # Final iteration: Final refinement
            iteration_prompt = f"""
{self.system_prompt}

────────────────────────────────
SELF-ITERATION: {iteration_num} of {self.self_iterations} (FINAL REFINEMENT)
────────────────────────────────

CURRENT DATE: {current_date}
TIMESTAMP: {timestamp}

YOUR PREVIOUS OUTPUT:
{previous_output}

────────────────────────────────
TASK: FINAL REFINEMENT
────────────────────────────────

This is your FINAL iteration. Your task:
1. Review your previous output critically
2. Integrate any remaining improvements
3. Ensure the output is clear, actionable, and complete
4. Verify all sections of the OUTPUT TEMPLATE are filled
5. Confirm long-term consistency with your past decision reports
6. Add your self-iteration notes at the end

Set "Self-Iterations Completed" to: {self.self_iterations}

GENERATE YOUR FINAL OUTPUT NOW:
"""
        else:
            # Middle iteration: Critical review
            iteration_prompt = f"""
{self.system_prompt}

────────────────────────────────
SELF-ITERATION: {iteration_num} of {self.self_iterations} (CRITICAL REVIEW)
────────────────────────────────

CURRENT DATE: {current_date}
TIMESTAMP: {timestamp}

YOUR PREVIOUS OUTPUT:
{previous_output}

ORIGINAL INPUT CONTEXT:
{input_context}

────────────────────────────────
TASK: CRITICAL REVIEW
────────────────────────────────

This is iteration {iteration_num}. Your task:
1. Challenge your previous recommendations
2. Look for blind spots or biases
3. Ensure all asset classes are fairly represented
4. Check if any important information was missed
5. Verify consistency with your past decision reports — are you flip-flopping without justification?
6. Refine and improve your output

GENERATE YOUR REFINED OUTPUT NOW:
"""

        if VERBOSE:
            print(f"[{self.agent_id}] Running self-iteration {iteration_num}/{self.self_iterations}...")

        # Store each iteration's input for later saving
        if not hasattr(self, "_iteration_inputs"):
            self._iteration_inputs = []
        self._iteration_inputs.append((iteration_num, iteration_prompt))

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=iteration_prompt,
                config=types.GenerateContentConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                )
            )
            return response.text

        except Exception as e:
            error_msg = f"[{self.agent_id}] Error in iteration {iteration_num}: {str(e)}"
            print(error_msg)
            raise

    def generate_decision(
        self,
        discussion_outputs: dict[str, str],
        financial_pool_data: str,
    ) -> str:
        # Reset iteration inputs for this run
        self._iteration_inputs = []
        """
        Generate the final investment decision through self-iteration.

        Args:
            discussion_outputs: Dictionary mapping discussion ID to content
            financial_pool_data: YFinance metrics.

        Returns:
            Final decision output
        """
        if VERBOSE:
            print(f"\n[{self.agent_id}] Starting decision process with {self.self_iterations} self-iterations...")

        input_context = self._build_input_context(discussion_outputs, financial_pool_data)

        # Run self-iterations
        current_output = None

        for iteration in range(1, self.self_iterations + 1):
            current_output = self._generate_iteration(
                input_context=input_context,
                iteration_num=iteration,
                previous_output=current_output,
            )

            if VERBOSE:
                print(f"[{self.agent_id}] Completed self-iteration {iteration}/{self.self_iterations}")

        if VERBOSE:
            print(f"[{self.agent_id}] Decision generation complete.")

        return current_output

    def save_decision(
        self,
        content: str,
        output_dir: Optional[str] = None,
    ) -> str:
        """
        Save the final decision to a file.

        Args:
            content: Decision content to save
            output_dir: Directory to save to

        Returns:
            Path to the saved decision file
        """
        if output_dir is None:
            output_dir = FINAL_REPORTS_DIR

        # Ensure directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Generate filename
        current_date = self.get_current_date()
        filename = DECIDER_REPORT_NAME.format(date=current_date)
        filepath = os.path.join(output_dir, filename)

        # Save the decision
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        if VERBOSE:
            print(f"[{self.agent_id}] Decision saved to: {filepath}")

        # Save all iteration inputs alongside the output
        iteration_inputs = getattr(self, "_iteration_inputs", [])
        if iteration_inputs:
            input_filename = "INPUT_" + filename
            input_filepath = os.path.join(output_dir, input_filename)
            with open(input_filepath, "w", encoding="utf-8") as f:
                for iteration_num, iteration_prompt in iteration_inputs:
                    f.write(f"{'=' * 80}\n")
                    f.write(f"ITERATION {iteration_num} OF {self.self_iterations} — INPUT PROMPT\n")
                    f.write(f"{'=' * 80}\n\n")
                    f.write(iteration_prompt)
                    f.write(f"\n\n")
            if VERBOSE:
                print(f"[{self.agent_id}] Iteration inputs saved to: {input_filepath}")

        return filepath

    def run(
        self,
        discussion_outputs: dict[str, str],
        financial_pool_data: str,
        output_dir: Optional[str] = None,
    ) -> tuple[str, str]:
        """
        Execute the full decision workflow: generate and save.

        Args:
            discussion_outputs: Dictionary mapping discussion ID to content
            financial_pool_data: String of YFinance financial data
            output_dir: Optional output directory override

        Returns:
            Tuple of (decision_content, filepath)
        """
        content = self.generate_decision(discussion_outputs, financial_pool_data)
        filepath = self.save_decision(content, output_dir)
        return content, filepath


if __name__ == "__main__":
    # Test with mock data
    mock_research = {
        "1A": "Mock Real Estate News",
        "1B": "Mock Real Estate Fundamental",
        "1C": "Mock Real Estate Sentiment",
        "2A": "Mock Gold News",
        "2B": "Mock Gold Fundamental",
        "2C": "Mock Gold Sentiment",
        "3A": "Mock Stocks News",
        "3B": "Mock Stocks Fundamental",
        "3C": "Mock Stocks Sentiment",
    }

    mock_discussions = {
        "gold_silver": "Mock Gold Discussion",
        "real_estate": "Mock Real Estate Discussion",
        "stocks_funds": "Mock Stocks Discussion",
    }

    agent = DeciderAgent(self_iterations=2)
    content, filepath = agent.run(mock_research, mock_discussions)
    print(f"\nDecision saved to: {filepath}")
