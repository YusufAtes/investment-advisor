"""
File Handler Utility
====================
Handles reading and writing report files for the Investment Advisor system.
"""

import os
import re
import sys
import glob
from datetime import datetime
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    REPORTS_DIR,
    RESEARCH_REPORTS_DIR,
    DISCUSSION_REPORTS_DIR,
    FINAL_REPORTS_DIR,
    PORTFOLIO_DIR,
    PORTFOLIO_HISTORY_DIR,
    RESEARCH_REPORT_NAMES,
    RESEARCH_REPORT_NAMES,
    DECIDER_REPORT_NAME,
    VERBOSE,
)


class FileHandler:
    """
    Handles all file operations for the Investment Advisor system.
    """

    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialize the file handler.

        Args:
            base_dir: Base reports directory (defaults to config)
        """
        self.base_dir = base_dir or REPORTS_DIR
        self.research_dir = RESEARCH_REPORTS_DIR
        self.discussion_dir = DISCUSSION_REPORTS_DIR
        self.final_dir = FINAL_REPORTS_DIR

    def ensure_directories(self) -> None:
        """Create all necessary directories if they don't exist."""
        dirs = [
            self.base_dir,
            self.research_dir,
            self.discussion_dir,
            self.final_dir,
            PORTFOLIO_DIR,
            PORTFOLIO_HISTORY_DIR,
        ]

        for directory in dirs:
            os.makedirs(directory, exist_ok=True)

        if VERBOSE:
            print(f"[FileHandler] Directories initialized at: {self.base_dir}")

    def read_file(self, filepath: str) -> Optional[str]:
        """
        Read content from a file.

        Args:
            filepath: Path to the file

        Returns:
            File content or None if file doesn't exist
        """
        if not os.path.exists(filepath):
            if VERBOSE:
                print(f"[FileHandler] File not found: {filepath}")
            return None

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            if VERBOSE:
                print(f"[FileHandler] Read file: {filepath}")

            return content

        except Exception as e:
            print(f"[FileHandler] Error reading file {filepath}: {e}")
            return None

    def write_file(self, filepath: str, content: str) -> bool:
        """
        Write content to a file.

        Args:
            filepath: Path to the file
            content: Content to write

        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            directory = os.path.dirname(filepath)
            if directory:
                os.makedirs(directory, exist_ok=True)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

            if VERBOSE:
                print(f"[FileHandler] Wrote file: {filepath}")

            return True

        except Exception as e:
            print(f"[FileHandler] Error writing file {filepath}: {e}")
            return False

    def get_research_reports(
        self,
        date: Optional[str] = None,
        directory: Optional[str] = None,
    ) -> dict[str, str]:
        """
        Load all research reports for a given date.

        Args:
            date: Date in YYYY-MM-DD format (defaults to today)
            directory: Directory to load from (defaults to research_dir)

        Returns:
            Dictionary mapping report ID to content
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        if directory is None:
            directory = self.research_dir

        reports = {}

        for report_id, filename_template in RESEARCH_REPORT_NAMES.items():
            filename = filename_template.format(date=date)
            filepath = os.path.join(directory, filename)

            content = self.read_file(filepath)
            if content:
                reports[report_id] = content
            else:
                if VERBOSE:
                    print(f"[FileHandler] Missing research report: {report_id}")

        return reports

    def get_discussion_outputs(
        self,
        iteration: int,
        date: Optional[str] = None,
        directory: Optional[str] = None,
    ) -> dict[str, str]:
        """
        Load discussion outputs for a specific iteration.

        Args:
            iteration: Iteration number
            date: Date in YYYY-MM-DD format (defaults to today)
            directory: Base directory (defaults to discussion_dir)

        Returns:
            Dictionary mapping discussion ID to content
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        if directory is None:
            directory = self.discussion_dir

        iteration_dir = os.path.join(directory, f"iteration_{iteration}")
        outputs = {}

        pattern = os.path.join(iteration_dir, f"DISCUSSION_*_{date}.txt")
        files = glob.glob(pattern)

        for filepath in files:
            # Extract agent ID from filename
            basename = os.path.basename(filepath)
            # Format is usually DISCUSSION_{agent_id}_{date}.txt
            disc_id = basename.replace("DISCUSSION_", "").replace(f"_{date}.txt", "")
            
            content = self.read_file(filepath)
            if content:
                outputs[disc_id] = content
            else:
                if VERBOSE:
                    print(f"[FileHandler] Warning: Could not read discussion output {filepath}")

        return outputs

    def get_final_decision(
        self,
        date: Optional[str] = None,
        directory: Optional[str] = None,
    ) -> Optional[str]:
        """
        Load the final decision report for a given date.

        Args:
            date: Date in YYYY-MM-DD format (defaults to today)
            directory: Directory to load from (defaults to final_dir)

        Returns:
            Decision content or None if not found
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        if directory is None:
            directory = self.final_dir

        filename = DECIDER_REPORT_NAME.format(date=date)
        filepath = os.path.join(directory, filename)

        return self.read_file(filepath)

    def get_recent_final_reports(
        self,
        n: int = 3,
        exclude_today: bool = True,
        directory: Optional[str] = None,
    ) -> list[tuple[str, str]]:
        """
        Load the N most recent final decision reports, sorted by date descending.

        Args:
            n: Number of recent reports to retrieve
            exclude_today: Whether to exclude today's report
            directory: Directory to scan (defaults to final_dir)

        Returns:
            List of (date_string, content) tuples, most recent first
        """
        if directory is None:
            directory = self.final_dir

        if not os.path.exists(directory):
            return []

        # Find all FINAL_Decision_*.txt files
        pattern = os.path.join(directory, "FINAL_Decision_*.txt")
        files = glob.glob(pattern)

        # Extract dates from filenames and pair with paths
        date_file_pairs = []
        date_regex = re.compile(r"FINAL_Decision_(\d{4}-\d{2}-\d{2})\.txt$")

        today = datetime.now().strftime("%Y-%m-%d")

        for filepath in files:
            basename = os.path.basename(filepath)
            match = date_regex.match(basename)
            if match:
                file_date = match.group(1)
                if exclude_today and file_date == today:
                    continue
                date_file_pairs.append((file_date, filepath))

        # Sort by date descending (most recent first)
        date_file_pairs.sort(key=lambda x: x[0], reverse=True)

        # Take top N
        results = []
        for file_date, filepath in date_file_pairs[:n]:
            content = self.read_file(filepath)
            if content:
                results.append((file_date, content))

        if VERBOSE:
            print(f"[FileHandler] Loaded {len(results)} recent final reports (requested {n})")

        return results

    def list_reports(
        self,
        report_type: str = "all",
        date: Optional[str] = None,
    ) -> list[str]:
        """
        List all report files of a given type.

        Args:
            report_type: "research", "discussion", "final", or "all"
            date: Optional date filter in YYYY-MM-DD format

        Returns:
            List of file paths
        """
        files = []

        if report_type in ["research", "all"]:
            pattern = os.path.join(self.research_dir, "*.txt")
            files.extend(glob.glob(pattern))

        if report_type in ["discussion", "all"]:
            pattern = os.path.join(self.discussion_dir, "**", "*.txt")
            files.extend(glob.glob(pattern, recursive=True))

        if report_type in ["final", "all"]:
            pattern = os.path.join(self.final_dir, "*.txt")
            files.extend(glob.glob(pattern))

        # Filter by date if specified
        if date:
            files = [f for f in files if date in os.path.basename(f)]

        return sorted(files)

    def cleanup_old_reports(self, days_to_keep: int = 30) -> int:
        """
        Remove reports older than specified days.

        Args:
            days_to_keep: Number of days of reports to keep

        Returns:
            Number of files deleted
        """
        import time

        cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
        deleted_count = 0

        for filepath in self.list_reports("all"):
            if os.path.getmtime(filepath) < cutoff_time:
                try:
                    os.remove(filepath)
                    deleted_count += 1
                    if VERBOSE:
                        print(f"[FileHandler] Deleted old report: {filepath}")
                except Exception as e:
                    print(f"[FileHandler] Error deleting {filepath}: {e}")

        return deleted_count

    def get_all_report_files(
        self,
        date: Optional[str] = None,
    ) -> dict[str, list[str]]:
        """
        Get all report file paths organized by type.

        Args:
            date: Optional date filter

        Returns:
            Dictionary with keys 'research', 'discussion', 'final'
        """
        return {
            "research": self.list_reports("research", date),
            "discussion": self.list_reports("discussion", date),
            "final": self.list_reports("final", date),
        }


def load_all_inputs_for_decider(
    date: Optional[str] = None,
    final_iteration: Optional[int] = None,
) -> tuple[dict[str, str], dict[str, str]]:
    """
    Convenience function to load all inputs needed by the Decider Agent.

    Args:
        date: Date in YYYY-MM-DD format (defaults to today)
        final_iteration: The final discussion iteration number

    Returns:
        Tuple of (research_reports, discussion_outputs)
    """
    handler = FileHandler()

    research_reports = handler.get_research_reports(date)

    if final_iteration:
        discussion_outputs = handler.get_discussion_outputs(final_iteration, date)
    else:
        discussion_outputs = {}

    return research_reports, discussion_outputs


if __name__ == "__main__":
    # Test file handler
    handler = FileHandler()
    handler.ensure_directories()

    # List existing reports
    all_files = handler.get_all_report_files()
    print("\nExisting reports:")
    for report_type, files in all_files.items():
        print(f"\n{report_type.upper()}:")
        for f in files:
            print(f"  - {f}")
