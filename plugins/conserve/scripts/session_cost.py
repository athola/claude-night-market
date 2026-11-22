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
    cusage --json | session_cost.py -
    session_cost.py CURSOR_AGENT_RESULTS.jsonl

Cursor transcripts record no usage, so for Cursor the ledger reads Cursor's
own usage data instead: ``cusage --json`` output (the dashboard usage API)
or the result lines of ``cursor-agent -p --output-format json``. Those carry
the cache split but no write duration, and Cursor's cost includes its Token
Rate, so that report gives token shares rather than price-weighted ones.

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


CURSOR_CATEGORIES = ("input", "cache_write", "cache_read", "output")
_CURSOR_SOURCES = (
    "`cursor-agent -p --output-format json` results, `cusage --json`, or the "
    "Admin API's POST /teams/filtered-usage-events"
)


def _cusage_rows(rows: list[Any]) -> dict[str, Any]:
    by_model: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = str(row.get("model") or "?")
        acc = by_model.setdefault(
            name,
            {"model": name, "requests": 0, "cost_cents": 0.0}
            | dict.fromkeys(CURSOR_CATEGORIES, 0),
        )
        acc["requests"] += int(row.get("requests") or 0)
        acc["cost_cents"] += float(row.get("cost_cents") or 0)
        for key in CURSOR_CATEGORIES:
            acc[key] += int(row.get(key) or 0)
    models = sorted(by_model.values(), key=lambda r: r["cost_cents"], reverse=True)
    return {
        "format": "cusage",
        "requests": sum(r["requests"] for r in models),
        "tokens": {k: sum(r[k] for r in models) for k in CURSOR_CATEGORIES},
        "cost_cents": sum(r["cost_cents"] for r in models),
        "by_model": models,
    }


_AGENT_USAGE_FIELDS = {
    "input": "inputTokens",
    "cache_write": "cacheWriteTokens",
    "cache_read": "cacheReadTokens",
    "output": "outputTokens",
}


def _agent_results(usages: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "format": "cursor-agent",
        "requests": len(usages),
        "tokens": {
            key: sum(int(u.get(field) or 0) for u in usages)
            for key, field in _AGENT_USAGE_FIELDS.items()
        },
        "cost_cents": None,
        "by_model": [],
    }


def summarize_cursor_usage_text(text: str) -> dict[str, Any] | None:
    """Report Cursor usage data, or return None when *text* is neither shape.

    ``cusage --json`` is one object with an ``events`` list of per-model rows.
    ``cursor-agent`` writes one ``{"type": "result", "usage": {...}}`` line per
    run, its ``inputTokens`` already net of cache.
    """
    try:
        whole = json.loads(text)
    except ValueError:
        whole = None
    if isinstance(whole, dict) and isinstance(whole.get("events"), list):
        report = _cusage_rows(whole["events"])
    else:
        usages = []
        for line in text.splitlines():
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            if (
                isinstance(entry, dict)
                and entry.get("type") == "result"
                and isinstance(entry.get("usage"), dict)
                # Claude's stream-json result line has snake_case usage keys.
                and any(f in entry["usage"] for f in _AGENT_USAGE_FIELDS.values())
            ):
                usages.append(entry["usage"])
        if not usages:
            return None
        report = _agent_results(usages)
    total = sum(report["tokens"].values())
    report["token_shares"] = (
        {k: v / total for k, v in report["tokens"].items()} if total else {}
    )
    return report


def render_cursor_usage(report: dict[str, Any]) -> str:
    """Format a Cursor usage report as a short table."""
    labels = {
        "input": "uncached input",
        "cache_write": "cache write",
        "cache_read": "cache read",
        "output": "output",
    }
    count = report["requests"]
    noun = "request" if count == 1 else "requests"
    out = [f"Cursor usage ({report['format']}): {count} {noun}", ""]
    out.append(f"{'category':<16}{'tokens':>16}{'token share':>13}")
    for key in CURSOR_CATEGORIES:
        share = report["token_shares"].get(key, 0.0)
        out.append(f"{labels[key]:<16}{report['tokens'][key]:>16,}{share:>13.1%}")
    out.append("")
    out.append(
        "Shares weigh tokens, not price: Cursor reports no cache-write duration "
        "and its cost includes the Cursor Token Rate."
    )
    if report["cost_cents"] is not None:
        out.append(f"Cost: ${report['cost_cents'] / 100:,.2f}")
    if report["by_model"]:
        out.append("By model:")
        for row in report["by_model"]:
            out.append(
                f"  {row['model'][:30]:<31}{row['requests']:>6} req  "
                f"${row['cost_cents'] / 100:>9,.2f}  "
                f"cache read {row['cache_read']:,}"
            )
    return "\n".join(out)


def render(report: dict[str, Any]) -> str:
    """Format the report as a short table."""
    if report["format"] == "cursor":
        return (
            "This is a Cursor transcript. Cursor records no token usage or tool "
            "results in it. Run this script on Cursor's usage data instead: "
            + _CURSOR_SOURCES
            + "."
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
    parser.add_argument("transcript", help="transcript, Cursor usage file, or -")
    parser.add_argument("--top", type=int, default=5)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.transcript == "-":
            text = sys.stdin.read()
        else:
            text = Path(args.transcript).read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"session_cost: cannot read {args.transcript}: {exc}", file=sys.stderr)
        return 2
    try:
        cursor = summarize_cursor_usage_text(text)
    except (TypeError, ValueError) as exc:
        print(f"session_cost: unreadable Cursor usage field: {exc}", file=sys.stderr)
        return 2
    if cursor is not None:
        print(
            json.dumps(cursor, indent=2) if args.json else render_cursor_usage(cursor)
        )
        return 0
    report = summarize(text.splitlines(), top=args.top)
    print(json.dumps(report, indent=2) if args.json else render(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
