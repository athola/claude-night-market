#!/usr/bin/env python3
"""Show where a Claude Code session's spend went, from its transcript.

Compressing tool output is usually aimed at the wrong number. A billed-run
study of Claude Code found token reduction and cost reduction correlated at
r = 0.15, because prompt-cache writes and reads dominate input cost (arXiv
2607.12161). This ledger reports the split, in base-input units so no price
list goes stale, and the re-read cost of each tool result: a result stays in
the cached prefix and is read again by every later request until a
compaction drops it.

Usage:
    session_cost.py TRANSCRIPT.jsonl [--top N] [--json]

The newest transcript for a project is the newest file in
``~/.claude/projects/<project-slug>/``. Subagents write their own
transcripts under ``<session-id>/subagents/``. Run the ledger on each one to
include their spend.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

# Relative to base input, from platform.claude.com/docs/en/about-claude/pricing
# (2026-11-20). Writes and output are the same multiple on every model.
WRITE_5M_RATE = 1.25
WRITE_1H_RATE = 2.0
OUTPUT_RATE = 5.0
# Cache reads are 0.1x except on these models.
_CACHE_READ_RATES = (
    ("claude-fable-5-2", 0.025),
    ("claude-mythos-5-2", 0.025),
    ("claude-fable-5-1", 0.025),
    ("claude-mythos-5-1", 0.025),
    ("claude-opus-5-5", 0.05),
    ("claude-sonnet-5-5", 0.05),
)
DEFAULT_CACHE_READ_RATE = 0.1
CHARS_PER_TOKEN = 4
CATEGORIES = ("input", "cache_write_5m", "cache_write_1h", "cache_read", "output")
_LABELS = {
    "input": "uncached input",
    "cache_write_5m": "cache write 5m",
    "cache_write_1h": "cache write 1h",
    "cache_read": "cache read",
    "output": "output",
}


def cache_read_rate(model: str) -> float:
    """Return the cache-read multiple for *model*."""
    for prefix, rate in _CACHE_READ_RATES:
        if model.startswith(prefix):
            return rate
    return DEFAULT_CACHE_READ_RATE


def _result_chars(content: object) -> int:
    if isinstance(content, str):
        return len(content)
    if isinstance(content, list):
        return sum(
            len(block.get("text") or "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    return 0


def _usage_tokens(usage: dict[str, Any]) -> dict[str, int]:
    split = usage.get("cache_creation")
    if isinstance(split, dict):
        write_5m = split.get("ephemeral_5m_input_tokens") or 0
        write_1h = split.get("ephemeral_1h_input_tokens") or 0
    else:
        write_5m = usage.get("cache_creation_input_tokens") or 0
        write_1h = 0
    return {
        "input": usage.get("input_tokens") or 0,
        "cache_write_5m": write_5m,
        "cache_write_1h": write_1h,
        "cache_read": usage.get("cache_read_input_tokens") or 0,
        "output": usage.get("output_tokens") or 0,
    }


class _Ledger:
    """Accumulate usage per request and the re-reads of each tool result."""

    def __init__(self) -> None:
        self.usage_by_id: dict[str, tuple[str, dict[str, int]]] = {}
        self.tool_names: dict[str, str] = {}
        self.results: list[dict[str, Any]] = []
        self.resident: list[dict[str, Any]] = []
        # Cursor rows carry "role" and no "type", and no usage at all.
        self.cursor_rows = 0

    def assistant(self, message: dict[str, Any]) -> None:
        content = message.get("content")
        for block in content if isinstance(content, list) else []:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                self.tool_names[block.get("id", "")] = block.get("name", "?")
        msg_id = message.get("id")
        usage = message.get("usage")
        if not msg_id or not isinstance(usage, dict):
            return
        model = message.get("model") or ""
        if msg_id not in self.usage_by_id:
            # A new request sends every resident result again: the first send
            # writes it to the cache and each later one reads it back.
            rate = cache_read_rate(model)
            for row in self.resident:
                if row["sends"] > 0:
                    row["rereads"] += 1
                    row["reread_units"] += row["tokens"] * rate
                row["sends"] += 1
        self.usage_by_id[msg_id] = (model, _usage_tokens(usage))

    def user(self, message: dict[str, Any]) -> None:
        content = message.get("content")
        for block in content if isinstance(content, list) else []:
            if isinstance(block, dict) and block.get("type") == "tool_result":
                row = {
                    "tool": self.tool_names.get(block.get("tool_use_id", ""), "?"),
                    "tokens": _result_chars(block.get("content")) // CHARS_PER_TOKEN,
                    "sends": 0,
                    "rereads": 0,
                    "reread_units": 0.0,
                }
                self.results.append(row)
                self.resident.append(row)

    def compacted(self) -> None:
        self.resident = []

    def report(self, top: int, skipped: int) -> dict[str, Any]:
        tokens = dict.fromkeys(CATEGORIES, 0)
        units = dict.fromkeys(CATEGORIES, 0.0)
        for model, counts in self.usage_by_id.values():
            for key in CATEGORIES:
                tokens[key] += counts[key]
            units["input"] += counts["input"]
            units["cache_write_5m"] += counts["cache_write_5m"] * WRITE_5M_RATE
            units["cache_write_1h"] += counts["cache_write_1h"] * WRITE_1H_RATE
            units["cache_read"] += counts["cache_read"] * cache_read_rate(model)
            units["output"] += counts["output"] * OUTPUT_RATE
        total = sum(units.values())
        ranked = sorted(self.results, key=lambda row: row["reread_units"], reverse=True)
        cursor = self.cursor_rows > 0 and not self.usage_by_id
        return {
            "format": "cursor" if cursor else "claude",
            "requests": len(self.usage_by_id),
            "skipped_lines": skipped,
            "tokens": tokens,
            "units": units,
            "shares": {key: units[key] / total for key in CATEGORIES} if total else {},
            "tool_results": {
                "count": len(self.results),
                "tokens": sum(row["tokens"] for row in self.results),
                "reread_units": sum(row["reread_units"] for row in self.results),
            },
            "top_tool_results": [
                {key: row[key] for key in ("tool", "tokens", "rereads", "reread_units")}
                for row in ranked[:top]
            ],
        }


def summarize(lines: Iterable[str], top: int = 5) -> dict[str, Any]:
    """Build the spend report from transcript lines."""
    ledger = _Ledger()
    skipped = 0
    for line in lines:
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except ValueError:
            entry = None
        if not isinstance(entry, dict):
            skipped += 1
            continue
        kind = entry.get("type")
        message = entry.get("message")
        if kind is None and "role" in entry:
            ledger.cursor_rows += 1
        if kind == "system" and entry.get("subtype") == "compact_boundary":
            ledger.compacted()
        elif kind == "assistant" and isinstance(message, dict):
            ledger.assistant(message)
        elif kind == "user" and isinstance(message, dict):
            ledger.user(message)
    return ledger.report(top, skipped)


def render(report: dict[str, Any]) -> str:
    """Format the report as a short table."""
    if report["format"] == "cursor":
        return (
            "This is a Cursor transcript. Cursor records no token usage or tool "
            "results in it. Per-request usage is in the Cursor dashboard."
        )
    total = sum(report["units"].values())
    out = [f"Requests: {report['requests']}", ""]
    out.append(f"{'category':<16}{'tokens':>14}{'input units':>14}{'share':>8}")
    for key in CATEGORIES:
        share = report["shares"].get(key, 0.0)
        out.append(
            f"{_LABELS[key]:<16}{report['tokens'][key]:>14,}"
            f"{report['units'][key]:>14,.0f}{share:>8.1%}"
        )
    tools = report["tool_results"]
    reread_share = tools["reread_units"] / total if total else 0.0
    out += [
        "",
        f"Tool results: {tools['count']}, about {tools['tokens']:,} tokens. "
        f"Cache reads spent re-reading tool results: {tools['reread_units']:,.0f} "
        f"units, {reread_share:.1%} of the session.",
    ]
    if report["top_tool_results"]:
        out.append("Costliest to keep in context:")
        for row in report["top_tool_results"]:
            out.append(
                f"  {row['tool']:<12}{row['tokens']:>9,} tokens, "
                f"re-read {row['rereads']} times, {row['reread_units']:,.0f} units"
            )
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    """Print the spend report for one transcript."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("transcript", type=Path)
    parser.add_argument("--top", type=int, default=5)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        with args.transcript.open(encoding="utf-8", errors="replace") as handle:
            report = summarize(handle, top=args.top)
    except OSError as exc:
        print(f"session_cost: cannot read {args.transcript}: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2) if args.json else render(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
