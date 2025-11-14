"""Logging adapters to forward logs to OS subsystems or fallback to files."""
from . import journald, eventlog, filehandler

__all__ = ["journald", "eventlog", "filehandler"]
