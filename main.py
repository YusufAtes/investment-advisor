"""
Investment Advisor Multi-Agent Orchestrator
============================================
Main entry point for running the complete investment advisory pipeline.

Usage:
    python main.py                                    # Run with defaults
    python main.py --discussion-iterations 5         # Custom discussion iterations
    python main.py --decider-iterations 3            # Custom decider iterations
    python main.py --skip-email                      # Skip email delivery
    python main.py --research-only                   # Only run research agents
    python main.py --discussion-only                 # Only run discussion (requires research)
    python main.py --decider-only                    # Only run decider (requires research + discussion)
"""

import argparse
import sys
import os
from datetime import datetime
from typing import Optional

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    DISCUSSION_ITERATIONS,
    DECIDER_SELF_ITERATIONS,
    VERBOSE,
)
from agents.research_agent import ResearchAgent, run_all_research_agents
from agents.discussion_agent import DiscussionAgent, run_all_discussion_iterations
from agents.decider_agent import DeciderAgent
from utils.file_handler import FileHandler
from utils.email_sender import send_investment_report


def print_banner():
    """Print the application banner."""
    banner = """
================================================================================
                    INVESTMENT ADVISOR MULTI-AGENT SYSTEM                     
                                                                              
  Research Agents (9) -> Discussion Agents (3) -> Decider Agent -> Email Report  
================================================================================
"""
    print(banner)


def print_phase(phase_name: str):
    """Print a phase separator."""
    print(f"\n{'#'*80}")
    print(f"# PHASE: {phase_name}")
    print(f"{'#'*80}\n")


def run_research_phase(file_handler: FileHandler) -> dict[str, str]:
    """
    Run all 9 research agents.

    Args:
        file_handler: FileHandler instance

    Returns:
        Dictionary mapping agent ID to report content
    """
    print_phase("RESEARCH (9 Agents with Web Search)")

    results = run_all_research_agents()

    # Extract content from results
    research_reports = {}
    for agent_id, (content, filepath) in results.items():
        if content:
            research_reports[agent_id] = content
            print(f"[OK] Research Agent {agent_id}: Report generated")
        else:
            print(f"[FAIL] Research Agent {agent_id}: FAILED")

    print(f"\n-> Research phase complete: {len(research_reports)}/9 reports generated")

    return research_reports


def run_discussion_phase(
    research_reports: dict[str, str],
    num_iterations: int,
    file_handler: FileHandler,
) -> dict[str, str]:
    """
    Run all discussion iterations.

    Args:
        research_reports: Dictionary of research report contents
        num_iterations: Number of discussion iterations
        file_handler: FileHandler instance

    Returns:
        Dictionary mapping agent ID to final discussion content
    """
    print_phase(f"DISCUSSION ({num_iterations} Iterations, 3 Agents)")

    all_results = run_all_discussion_iterations(
        research_reports=research_reports,
        num_iterations=num_iterations,
    )

    # Get the final iteration results
    final_iteration = num_iterations
    final_results = all_results.get(final_iteration, {})

    discussion_outputs = {}
    for agent_id, (content, filepath) in final_results.items():
        if content:
            discussion_outputs[agent_id] = content
            print(f"[OK] Discussion Agent {agent_id}: Final output generated")
        else:
            print(f"[FAIL] Discussion Agent {agent_id}: FAILED")

    print(f"\n-> Discussion phase complete: {len(discussion_outputs)}/3 outputs generated")

    return discussion_outputs


def run_decider_phase(
    research_reports: dict[str, str],
    discussion_outputs: dict[str, str],
    self_iterations: int,
    file_handler: FileHandler,
) -> tuple[str, str]:
    """
    Run the decider agent.

    Args:
        research_reports: Dictionary of research report contents
        discussion_outputs: Dictionary of discussion output contents
        self_iterations: Number of self-iteration cycles
        file_handler: FileHandler instance

    Returns:
        Tuple of (decision_content, filepath)
    """
    print_phase(f"DECISION ({self_iterations} Self-Iterations)")

    decider = DeciderAgent(self_iterations=self_iterations)
    content, filepath = decider.run(
        research_reports=research_reports,
        discussion_outputs=discussion_outputs,
    )

    if content:
        print(f"[OK] Decider Agent: Final decision generated")
        print(f"  -> Saved to: {filepath}")
    else:
        print(f"[FAIL] Decider Agent: FAILED")

    return content, filepath


def run_email_phase(
    decision_content: str,
    research_files: Optional[list[str]] = None,
    discussion_files: Optional[list[str]] = None,
    include_attachments: bool = False,
) -> bool:
    """
    Send the final report via email.

    Args:
        decision_content: The final decision content
        research_files: Optional list of research file paths
        discussion_files: Optional list of discussion file paths
        include_attachments: Whether to include attachments

    Returns:
        True if email sent successfully
    """
    print_phase("EMAIL DELIVERY")

    success = send_investment_report(
        decision_content=decision_content,
        research_files=research_files,
        discussion_files=discussion_files,
        include_attachments=include_attachments,
    )

    if success:
        print("[OK] Email sent successfully!")
    else:
        print("[FAIL] Email delivery FAILED")

    return success


def run_full_pipeline(
    discussion_iterations: int = DISCUSSION_ITERATIONS,
    decider_iterations: int = DECIDER_SELF_ITERATIONS,
    skip_email: bool = False,
    include_attachments: bool = False,
) -> bool:
    """
    Run the complete investment advisory pipeline.

    Args:
        discussion_iterations: Number of discussion iterations
        decider_iterations: Number of decider self-iterations
        skip_email: Whether to skip email delivery
        include_attachments: Whether to include report attachments in email

    Returns:
        True if pipeline completed successfully
    """
    print_banner()

    start_time = datetime.now()
    print(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Discussion iterations: {discussion_iterations}")
    print(f"Decider self-iterations: {decider_iterations}")

    # Initialize file handler
    file_handler = FileHandler()
    file_handler.ensure_directories()

    try:
        # Phase 1: Research
        research_reports = run_research_phase(file_handler)

        if len(research_reports) < 9:
            print(f"\n[WARN] Warning: Only {len(research_reports)}/9 research reports generated")

        if not research_reports:
            print("\n[FAIL] Pipeline aborted: No research reports generated")
            return False

        # Phase 2: Discussion
        discussion_outputs = run_discussion_phase(
            research_reports=research_reports,
            num_iterations=discussion_iterations,
            file_handler=file_handler,
        )

        if len(discussion_outputs) < 3:
            print(f"\n[WARN] Warning: Only {len(discussion_outputs)}/3 discussion outputs generated")

        if not discussion_outputs:
            print("\n[FAIL] Pipeline aborted: No discussion outputs generated")
            return False

        # Phase 3: Decision
        decision_content, decision_filepath = run_decider_phase(
            research_reports=research_reports,
            discussion_outputs=discussion_outputs,
            self_iterations=decider_iterations,
            file_handler=file_handler,
        )

        if not decision_content:
            print("\n[FAIL] Pipeline aborted: Decision generation failed")
            return False

        # Phase 4: Email
        if not skip_email:
            email_success = run_email_phase(
                decision_content=decision_content,
                include_attachments=include_attachments,
            )
        else:
            print("\n-> Email delivery skipped (--skip-email flag)")
            email_success = True

        # Summary
        end_time = datetime.now()
        duration = end_time - start_time

        print(f"\n{'='*80}")
        print("PIPELINE COMPLETE")
        print(f"{'='*80}")
        print(f"Duration: {duration}")
        print(f"Research reports: {len(research_reports)}/9")
        print(f"Discussion outputs: {len(discussion_outputs)}/3")
        print(f"Decision: {'Generated' if decision_content else 'Failed'}")
        print(f"Email: {'Sent' if email_success and not skip_email else 'Skipped' if skip_email else 'Failed'}")
        print(f"{'='*80}\n")

        return True

    except KeyboardInterrupt:
        print("\n\n[WARN] Pipeline interrupted by user")
        return False
    except Exception as e:
        print(f"\n[FAIL] Pipeline error: {str(e)}")
        raise


def run_research_only() -> bool:
    """Run only the research phase."""
    print_banner()
    print("MODE: Research Only\n")

    file_handler = FileHandler()
    file_handler.ensure_directories()

    research_reports = run_research_phase(file_handler)
    return len(research_reports) > 0


def run_discussion_only(num_iterations: int = DISCUSSION_ITERATIONS) -> bool:
    """Run only the discussion phase (requires existing research reports)."""
    print_banner()
    print("MODE: Discussion Only\n")

    file_handler = FileHandler()

    # Load existing research reports
    research_reports = file_handler.get_research_reports()

    if not research_reports:
        print("[FAIL] No research reports found. Run research phase first.")
        return False

    print(f"-> Loaded {len(research_reports)} existing research reports")

    discussion_outputs = run_discussion_phase(
        research_reports=research_reports,
        num_iterations=num_iterations,
        file_handler=file_handler,
    )

    return len(discussion_outputs) > 0


def run_decider_only(
    discussion_iteration: int,
    decider_iterations: int = DECIDER_SELF_ITERATIONS,
    skip_email: bool = False,
) -> bool:
    """Run only the decider phase (requires existing research and discussion reports)."""
    print_banner()
    print("MODE: Decider Only\n")

    file_handler = FileHandler()

    # Load existing reports
    research_reports = file_handler.get_research_reports()
    discussion_outputs = file_handler.get_discussion_outputs(discussion_iteration)

    if not research_reports:
        print("[FAIL] No research reports found. Run research phase first.")
        return False

    if not discussion_outputs:
        print(f"[FAIL] No discussion outputs found for iteration {discussion_iteration}.")
        return False

    print(f"-> Loaded {len(research_reports)} research reports")
    print(f"-> Loaded {len(discussion_outputs)} discussion outputs")

    decision_content, decision_filepath = run_decider_phase(
        research_reports=research_reports,
        discussion_outputs=discussion_outputs,
        self_iterations=decider_iterations,
        file_handler=file_handler,
    )

    if decision_content and not skip_email:
        run_email_phase(decision_content)

    return decision_content is not None


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Investment Advisor Multi-Agent System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                                    Run full pipeline with defaults
  python main.py --discussion-iterations 5         Run with 5 discussion iterations
  python main.py --decider-iterations 4            Run with 4 decider self-iterations
  python main.py --skip-email                      Run without sending email
  python main.py --research-only                   Only run research agents
  python main.py --discussion-only                 Only run discussion agents
  python main.py --decider-only --iteration 3     Only run decider (uses iteration 3 discussions)
        """
    )

    # Iteration settings
    parser.add_argument(
        "--discussion-iterations", "-d",
        type=int,
        default=DISCUSSION_ITERATIONS,
        help=f"Number of discussion iterations (default: {DISCUSSION_ITERATIONS})"
    )
    parser.add_argument(
        "--decider-iterations", "-D",
        type=int,
        default=DECIDER_SELF_ITERATIONS,
        help=f"Number of decider self-iterations (default: {DECIDER_SELF_ITERATIONS})"
    )

    # Email settings
    parser.add_argument(
        "--skip-email",
        action="store_true",
        help="Skip email delivery"
    )
    parser.add_argument(
        "--include-attachments",
        action="store_true",
        help="Include report files as email attachments"
    )

    # Mode selection
    parser.add_argument(
        "--research-only",
        action="store_true",
        help="Only run the research phase"
    )
    parser.add_argument(
        "--discussion-only",
        action="store_true",
        help="Only run the discussion phase (requires existing research)"
    )
    parser.add_argument(
        "--decider-only",
        action="store_true",
        help="Only run the decider phase (requires existing research and discussion)"
    )
    parser.add_argument(
        "--iteration", "-i",
        type=int,
        help="Discussion iteration to use for decider-only mode"
    )

    args = parser.parse_args()

    # Validate arguments
    if args.decider_only and args.iteration is None:
        parser.error("--decider-only requires --iteration to specify which discussion iteration to use")

    # Run appropriate mode
    try:
        if args.research_only:
            success = run_research_only()
        elif args.discussion_only:
            success = run_discussion_only(args.discussion_iterations)
        elif args.decider_only:
            success = run_decider_only(
                discussion_iteration=args.iteration,
                decider_iterations=args.decider_iterations,
                skip_email=args.skip_email,
            )
        else:
            success = run_full_pipeline(
                discussion_iterations=args.discussion_iterations,
                decider_iterations=args.decider_iterations,
                skip_email=args.skip_email,
                include_attachments=args.include_attachments,
            )

        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"\n[FAIL] Fatal error: {str(e)}")
        if VERBOSE:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
