#!/usr/bin/env python3
"""
Logic Discovery & Valuation CLI
===============================
Standalone tool to test a user's investment hypothesis. 
It evaluates the reasoning using web search, then identifies potential beneficiaries and losers, strictly respecting user compliance constraints.
"""

import argparse
import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import GEMINI_API_KEY
from utils.file_handler import FileHandler

def evaluate_logic_and_find_assets(hypothesis: str):
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # Load constraints from user profile
    try:
        user_profile = FileHandler().load_user_profile() or "No user profile found."
    except Exception:
        user_profile = "No user profile found."

    prompt = f"""You are a top-tier financial analyst. A user has presented the following investment hypothesis:
"{hypothesis}"

Your task is split into two parts:

PART 1: EVALUATE THE HYPOTHESIS
Use web search to check the validity of this logic. Is it fundamentally sound, flawed, or overly speculative?
Are regulatory changes actually happening? Is the macroeconomic premise correct?

PART 2: IDENTIFY WINNERS & LOSERS
Based on the premise (if it holds any merit), identify 3-5 specific assets/stocks that will experience POSITIVE effects, and 2-3 that will experience NEGATIVE effects.

CRITICAL USER CONSTRAINTS:
{user_profile}

- You MUST filter and label all recommendations according to the user's Halal and No-Israel constraints. If an asset clearly violates these, DO NOT suggest it as a BUY. 
- You MUST explicitly state the Halal/Israel exposure status for every POSITIVE asset mentioned.

Respond in JSON format with the following structure:
{{
  "evaluation": {{
    "soundness": "SOUND | FLAWED | SPECULATIVE",
    "analysis": "2-3 paragraphs analyzing the premise",
    "key_risks": ["risk 1", "risk 2"]
  }},
  "beneficiaries": [
    {{
      "ticker": "...",
      "name": "...",
      "reason": "...",
      "halal_status": "COMPLIANT | NON_COMPLIANT | UNKNOWN",
      "israel_exposure": "NONE | DIRECT | INDIRECT | UNKNOWN"
    }}
  ],
  "losers": [
    {{
      "ticker": "...",
      "name": "...",
      "reason": "..."
    }}
  ]
}}

Return ONLY valid JSON format without markdown blocks. Keep it analytical and objective.
"""

    print(f"\n[1/2] Searching web and evaluating hypothesis: '{hypothesis}'...")
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro", # Use the reasoning model
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=4096,
                tools=[types.Tool(google_search=types.GoogleSearch())],
            ),
        )

        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            print("[ERROR] Failed to parse agent output as JSON. Raw output:")
            print(text)
            return
        
        # Display output
        eval_data = data.get("evaluation", {})
        print("\n" + "="*80)
        print(f"HYPOTHESIS EVALUATION: {eval_data.get('soundness', 'UNKNOWN')}")
        print("="*80)
        print(eval_data.get("analysis", ""))
        
        print("\nKEY RISKS TO THIS PREMISE:")
        for r in eval_data.get("key_risks", []):
            print(f"  - {r}")
            
        print("\n" + "="*80)
        print("POTENTIAL BENEFICIARIES (POSITIVE EFFECT)")
        print("="*80)
        for b in data.get("beneficiaries", []):
            print(f"\n[+] {b.get('ticker', 'N/A')} - {b.get('name', 'N/A')}")
            print(f"    Reason: {b.get('reason', '')}")
            print(f"    Compliance: Halal: {b.get('halal_status', '')} | Israel Exposure: {b.get('israel_exposure', '')}")
            
        print("\n" + "="*80)
        print("POTENTIAL LOSERS (NEGATIVE EFFECT)")
        print("="*80)
        for L in data.get("losers", []):
            print(f"\n[-] {L.get('ticker', 'N/A')} - {L.get('name', 'N/A')}")
            print(f"    Reason: {L.get('reason', '')}")
            
        print("\n" + "="*80)
        
    except Exception as e:
        print(f"\n[ERROR] Failed to evaluate logic: {e}")

def main():
    parser = argparse.ArgumentParser(description="Logic Discovery & Valuation Tool")
    parser.add_argument("--hypothesis", "--logic", type=str, required=True, help="Full sentence hypothesis to test")
    
    args = parser.parse_args()
    evaluate_logic_and_find_assets(args.hypothesis)

if __name__ == "__main__":
    main()
