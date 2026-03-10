"""
Base Agent Class
================
Provides the foundation for all Gemini-powered agents in the system.
"""

import os
from google import genai
from google.genai import types
from datetime import datetime
from typing import Optional
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    GEMINI_API_KEY,
    PROMPTS_DIR,
    VERBOSE,
)


class BaseAgent:
    """
    Base class for all agents in the investment advisory system.
    Provides common functionality for Gemini API interaction.
    """

    def __init__(
        self,
        agent_id: str,
        prompt_file: str,
        model_name: str,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ):
        """
        Initialize the base agent.

        Args:
            agent_id: Unique identifier for this agent
            prompt_file: Name of the prompt file (.txt)
            model_name: Gemini model to use
            temperature: Generation temperature
            max_tokens: Maximum output tokens
        """
        self.agent_id = agent_id
        self.prompt_file = prompt_file
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = None
        self.client = None

        # Initialize Gemini client
        self.client = genai.Client(api_key=GEMINI_API_KEY)

        # Load the system prompt
        self._load_prompt()

    def _load_prompt(self) -> None:
        """Load the system prompt from the prompt file."""
        prompt_path = os.path.join(PROMPTS_DIR, self.prompt_file)

        if not os.path.exists(prompt_path):
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

        with open(prompt_path, "r", encoding="utf-8") as f:
            self.system_prompt = f.read()

        if VERBOSE:
            print(f"[{self.agent_id}] Loaded prompt from: {self.prompt_file}")

    def _build_prompt(self, user_input: str) -> str:
        """
        Build the full prompt combining system prompt and user input.

        Args:
            user_input: The user's input or context

        Returns:
            Combined prompt string
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_date = datetime.now().strftime("%Y-%m-%d")

        return f"""{self.system_prompt}

────────────────────────────────
CURRENT EXECUTION CONTEXT
- Date: {current_date}
- Timestamp: {timestamp}
────────────────────────────────

{user_input}"""

    def generate(self, user_input: str) -> str:
        """
        Generate a response from the agent.

        Args:
            user_input: The input/context for generation

        Returns:
            Generated response text
        """
        full_prompt = self._build_prompt(user_input)

        if VERBOSE:
            print(f"[{self.agent_id}] Generating response...")

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                )
            )
            result = response.text

            if VERBOSE:
                print(f"[{self.agent_id}] Response generated successfully.")

            return result

        except Exception as e:
            error_msg = f"[{self.agent_id}] Error generating response: {str(e)}"
            print(error_msg)
            raise

    def get_current_date(self) -> str:
        """Get current date in YYYY-MM-DD format."""
        return datetime.now().strftime("%Y-%m-%d")

    def get_timestamp(self) -> str:
        """Get current timestamp in YYYY-MM-DD HH:MM:SS format."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.agent_id}, model={self.model_name})"
