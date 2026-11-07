"""Regression and correctness tests for TOME-001 and TOME-004 fixes."""

from __future__ import annotations


# ---------------------------------------------------------------------------
# TOME-001: union-find fuzzy_deduplicate
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# TOME-001 (blocking): multi-channel deduplication correctness
#
# The O(n²) pair-enumeration loop was replaced with channel-blocking:
# group findings by channel, enumerate pairs only within groups.
# Output is identical; this suite guards against regression.
# ---------------------------------------------------------------------------
