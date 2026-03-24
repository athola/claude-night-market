"""Tests for context warning hook with three-tier MECW alerts.

This module has been split into focused sub-modules for maintainability:

- test_context_warning_thresholds.py  -- severity thresholds, edge cases,
                                         configurable threshold, emergency
                                         recommendations
- test_context_warning_output.py      -- format_hook_output(), env reading,
                                         main() entry point
- test_context_warning_estimation.py  -- session-file estimation, turn
                                         counting, session discovery,
                                         content counting, path resolution

All tests remain discoverable by pytest via the sub-modules above.
This file is retained for git blame continuity.
"""
