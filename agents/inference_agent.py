"""
Inference Agent
===============
Interactive advisory agent that answers user investment questions
using research reports, discussion outputs, and real-time web search.
"""

import os
import sys
import time
from google import genai
from google.genai import types
from datetime import datetime
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    GEMINI_API_KEY,
    PROMPTS_DIR,
    INFERENCE_MODEL,
    INFERENCE_TEMPERATURE,
    INFERENCE_MAX_TOKENS,
    INFERENCE_PROMPT,
    VERBOSE,
)
from agents.base_agent import BaseAgent
from utils.portfolio_loader import format_portfolio_for_prompt


class InferenceAgent(BaseAgent):
    """
    Interactive inference agent that answers investment questions
    using all available context and real-time web search.
    """

    def __init__(self):
        """Initialize the inference agent with web search capability."""
        super().__init__(
            agent_id="Inference",
            prompt_file=INFERENCE_PROMPT,
            model_name=INFERENCE_MODEL,
            temperature=INFERENCE_TEMPERATURE,
            max_tokens=INFERENCE_MAX_TOKENS,
        )
        
        # Enable web search tool
        self.search_tool = types.Tool(
            google_search=types.GoogleSearch()
        )
        
        if VERBOSE:
            print(f"[{self.agent_id}] Initialized with model: {self.model_name}")
            print(f"[{self.agent_id}] Web search enabled")

    def _build_context(
        self,
        final_reports: list,
    ) -> str:
        """
        Build the complete context from portfolio and final reports.
        
        Args:
            final_reports: List of tuples [(date, content), ...] sorted newest first
            
        Returns:
            Formatted context string
        """
        sections = []
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        sections.append("=" * 80)
        sections.append(f"INVESTMENT ADVISOR CONTEXT - {current_date}")
        sections.append("=" * 80)
        
        # Current Portfolio Section
        try:
            portfolio_text = format_portfolio_for_prompt()
            sections.append("\n" + "=" * 80)
            sections.append("SECTION A: CURRENT PORTFOLIO")
            sections.append("=" * 80)
            sections.append("\nThis is the user's current investment portfolio:")
            sections.append(portfolio_text)
        except FileNotFoundError:
            sections.append("\n[Portfolio data not available]")
        
        # Final Reports Section
        if final_reports:
            sections.append("\n" + "=" * 80)
            sections.append(f"SECTION B: PAST DECISION REPORTS ({len(final_reports)} most recent)")
            sections.append("=" * 80)
            sections.append("\nThese are the most recent synthesized recommendations (newest first):")
            
            for i, (report_date, content) in enumerate(final_reports, 1):
                sections.append("\n" + "-" * 80)
                sections.append(f"REPORT {i} - Date: {report_date}")
                sections.append("-" * 80)
                sections.append(content)
        else:
            sections.append("\n[No historical reports available - using web search only]")
        
        return "\n".join(sections)

    def answer_question(
        self,
        question: str,
        final_reports: Optional[list] = None,
        max_retries: int = 3,
    ) -> str:
        """
        Answer an investment question using final reports context and web search.
        
        Args:
            question: The user's investment question
            final_reports: List of tuples [(date, content), ...] sorted newest first
            max_retries: Maximum retry attempts for API errors
            
        Returns:
            The agent's response
        """
        # Build context
        context = self._build_context(
            final_reports=final_reports or [],
        )
        
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M:%S")
        
        # Build the full prompt
        full_prompt = f"""
{self.system_prompt}

================================================================================
CURRENT DATE & TIME: {current_date} {current_time}
================================================================================

{context}

================================================================================
USER'S QUESTION
================================================================================

{question}

================================================================================
INSTRUCTIONS
================================================================================

1. First, review the user's CURRENT PORTFOLIO to understand their holdings and allocation
2. Analyze the past decision reports for relevant recommendations and trends
3. Use web search to get CURRENT prices, news, and market data
4. Cross-reference the portfolio, reports, and real-time information
5. Think deeply about the user's specific situation and portfolio context
6. Provide a comprehensive, evidence-based response following the format in your prompt

Remember: The user is relying on you for informed guidance. Be thorough but clear.

BEGIN YOUR ANALYSIS:
"""
        
        if VERBOSE:
            print(f"\n[{self.agent_id}] Processing question...")
            print(f"[{self.agent_id}] Context size: {len(context)} characters")
            print(f"[{self.agent_id}] Searching web and analyzing...")
        
        # Generate response with retry logic
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=full_prompt,
                    config=types.GenerateContentConfig(
                        temperature=self.temperature,
                        max_output_tokens=self.max_tokens,
                        tools=[self.search_tool],
                    )
                )
                
                if VERBOSE:
                    print(f"[{self.agent_id}] Response generated successfully")
                
                return response.text
                
            except Exception as e:
                error_str = str(e)
                
                # Handle rate limiting
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    wait_time = (attempt + 1) * 30
                    print(f"[{self.agent_id}] Rate limited. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                
                # Other errors
                if attempt < max_retries - 1:
                    print(f"[{self.agent_id}] Error: {error_str}. Retrying...")
                    time.sleep(5)
                    continue
                else:
                    raise Exception(f"Failed after {max_retries} attempts: {error_str}")
        
        return "Unable to generate response. Please try again."


def run_interactive_session(
    final_reports: Optional[list] = None,
):
    """
    Run an interactive Q&A session with the inference agent.
    
    Args:
        final_reports: List of tuples [(date, content), ...] sorted newest first
    """
    print("\n" + "=" * 70)
    print("    INVESTMENT ADVISOR - INTERACTIVE Q&A SESSION")
    print("=" * 70)
    print("\nWelcome! I'm your AI Investment Advisor.")
    
    if final_reports:
        print(f"I have access to {len(final_reports)} recent final report(s) and web search.")
    else:
        print("I'm using web search only (no reports loaded).")
    
    print("\nYou can ask me questions like:")
    print("  - Should I sell my AAPL stock? I need money urgently.")
    print("  - People say NVIDIA is great, should I buy it?")
    print("  - Should I invest in gold or real estate right now?")
    print("  - Is it a good time to buy Bitcoin?")
    print("\nType 'quit' or 'exit' to end the session.")
    print("=" * 70)
    
    agent = InferenceAgent()
    
    while True:
        print("\n")
        try:
            question = input("Your Question: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nSession ended.")
            break
        
        if not question:
            print("Please enter a question.")
            continue
        
        if question.lower() in ['quit', 'exit', 'q']:
            print("\nThank you for using the Investment Advisor. Goodbye!")
            break
        
        print("\n" + "-" * 70)
        print("Analyzing your question... (this may take a moment)")
        print("-" * 70 + "\n")
        
        try:
            response = agent.answer_question(
                question=question,
                final_reports=final_reports,
            )
            print(response)
        except Exception as e:
            print(f"\nError: {e}")
            print("Please try again with a different question.")


if __name__ == "__main__":
    # Test with no context
    run_interactive_session()

