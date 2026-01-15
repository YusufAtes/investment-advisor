"""
Investment Advisor Utilities Package
====================================
Contains utility functions for email, file handling, and other common operations.
"""

from .email_sender import EmailSender, send_investment_report
from .file_handler import FileHandler

__all__ = [
    "EmailSender",
    "send_investment_report",
    "FileHandler",
]
