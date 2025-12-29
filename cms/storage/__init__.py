"""
Storage module for persistent memory management.
Supports SQLite backend (built into Python, no external database needed).
"""

from cms.storage.sqlite import SQLiteStorage

__all__ = ['SQLiteStorage']
