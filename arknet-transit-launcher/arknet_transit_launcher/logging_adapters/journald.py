"""Minimal journald adapter: try to import systemd.journal, otherwise no-op.
This module provides `get_handler()` which returns a logging.Handler if available.
"""
import logging

try:
    from systemd import journal
    HAS_JOURNAL = True
except Exception:
    HAS_JOURNAL = False


def get_handler():
    if not HAS_JOURNAL:
        return None
    # Use systemd.journal.JournalHandler if available
    try:
        handler = journal.JournalHandler()
        handler.setLevel(logging.INFO)
        return handler
    except Exception:
        return None
