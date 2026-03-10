"""
Investment Advisor - Interactive Inference Mode
================================================
Run this script to ask investment questions interactively.
The agent will use the last N final reports and real-time web search.

Usage:
    python inference.py                    # Uses last 3 final reports (default)
    python inference.py -n 5               # Uses last 5 final reports
    python inference.py --no-context       # Web search only, no reports
"""

import argparse
import sys
import os
import glob
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import VERBOSE
from utils.file_handler import FileHandler
from agents.inference_agent import InferenceAgent, run_interactive_session


def load_final_reports(n: int = 3) -> list:
    """
    Load the last N final reports for context.
    
    Args:
        n: Number of most recent final reports to load (default 3)
        
    Returns:
        List of tuples: [(date, content), ...] sorted newest first
    """
    handler = FileHandler()
    
    print(f"\n[Loading] Looking for the last {n} final reports...")
    
    # Get all final report files
    final_files = handler.list_reports("final")
    
    if not final_files:
        print("[Loading] No final reports found!")
        print("[Tip] Run 'python main.py' first to generate reports.")
        return []
    
    # Sort by filename (which contains date) in descending order (newest first)
    final_files = sorted(final_files, reverse=True)
    
    # Take only the last N files
    files_to_load = final_files[:n]
    
    final_reports = []
    for filepath in files_to_load:
        content = handler.read_file(filepath)
        if content:
            # Extract date from filename (e.g., FINAL_DECISION_2026-01-15.txt)
            filename = os.path.basename(filepath)
            # Try to extract date from filename
            date_str = filename.replace("FINAL_DECISION_", "").replace(".txt", "")
            final_reports.append((date_str, content))
    
    if final_reports:
        print(f"[Loading] Loaded {len(final_reports)} final report(s)")
        for date_str, _ in final_reports:
            print(f"  - {date_str}")
    else:
        print("[Loading] Could not load any final reports")
    
    return final_reports


def main():
    """Main entry point for interactive inference mode."""
    parser = argparse.ArgumentParser(
        description="Interactive Investment Advisor - Ask questions about investments"
    )
    parser.add_argument(
        "-n", "--num-reports",
        type=int,
        default=3,
        help="Number of recent final reports to use as context (default: 3)"
    )
    parser.add_argument(
        "--no-context",
        action="store_true",
        help="Run without loading reports (web search only)"
    )
    parser.add_argument(
        "--question",
        "-q",
        type=str,
        default=None,
        help="Single question mode (non-interactive)"
    )
    
    args = parser.parse_args()
    
    print("\n" + "=" * 70)
    print("    INVESTMENT ADVISOR - INFERENCE MODE")
    print("=" * 70)
    
    # Load context unless --no-context is specified
    if args.no_context:
        print("\n[Mode] Running without pre-loaded context (web search only)")
        final_reports = []
    else:
        final_reports = load_final_reports(args.num_reports)
    
    # Single question mode
    if args.question:
        print("\n[Mode] Single question mode")
        print(f"\n[Question] {args.question}")
        print("\n" + "-" * 70)
        print("Analyzing... (this may take a moment)")
        print("-" * 70 + "\n")
        
        agent = InferenceAgent()
        try:
            response = agent.answer_question(
                question=args.question,
                final_reports=final_reports,
            )
            print(response)
        except Exception as e:
            print(f"\nError: {e}")
            sys.exit(1)
    else:
        # Interactive mode
        run_interactive_session(
            final_reports=final_reports,
        )


if __name__ == "__main__":
    main()

