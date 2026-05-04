# Log Analysis Patterns

This module covers progressive-loading for skills that read,
parse, and summarize log files. The selection question is which
parsing modules to load based on log format (JSON, syslog,
custom plain text), volume (kilobytes vs gigabytes), and goal
(error triage, performance review, audit trail).

## When This Module Applies

Load this module when the task involves:

- Reading application or system log files.
- Filtering log streams for errors, warnings, or specific
  events.
- Producing a digest of what happened during a window.
- Correlating events across multiple log sources.

For prose documents, load `document-analysis-patterns.md`. For
git history, load `git-catchup-patterns.md`. This module is for
machine-generated event streams.

## Format Detection First

Log format dictates the parser. Misclassifying a syslog file as
JSON wastes the first parse attempt and produces garbage.

```python
from pathlib import Path

def detect_format(log_path: Path, sample_lines: int = 20) -> str:
    with log_path.open("r", encoding="utf-8", errors="replace") as fp:
        lines = [next(fp, "") for _ in range(sample_lines)]
    sample = "\n".join(line for line in lines if line)
    if sample.lstrip().startswith("{"):
        return "json"
    if " kernel:" in sample or " systemd[" in sample:
        return "syslog"
    if sample.startswith("[") and "INFO" in sample[:200]:
        return "bracketed"
    return "plain"
```

Read only a small sample. A 5GB log file should never be opened
in full just to detect the format.

## Loading Map

| Format | Parser Module | Token Estimate |
|--------|---------------|----------------|
| JSON lines | `json-log-parser.md` | 400 |
| Syslog | `syslog-parser.md` | 500 |
| Bracketed (`[LEVEL] msg`) | `bracketed-parser.md` | 300 |
| Plain text | `plain-text-parser.md` | 500 |
| Mixed (multi-line stack traces) | `multiline-parser.md` | 600 |

The plain-text parser is the largest because it must handle
arbitrary formats with regex heuristics. JSON is smaller because
the structure is self-describing.

## Volume-Based Loading

Log volume splits into three bands that drive different
techniques.

| Band | Size | Strategy Module |
|------|------|-----------------|
| Small | <10 MB | `full-load.md` (read everything) |
| Medium | 10 MB to 1 GB | `streaming.md` (line-at-a-time) |
| Large | >1 GB | `sampled.md` (head, tail, time windows) |

The strategy module loads after the format module, so the
parser knows whether to expect a fully loaded file or a stream.

## Streaming Pattern

Medium-volume logs need line-by-line streaming to keep memory
bounded.

```python
import json
from pathlib import Path
from typing import Iterator

def iter_json_logs(path: Path) -> Iterator[dict]:
    with path.open("r", encoding="utf-8", errors="replace") as fp:
        for line in fp:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue  # Skip malformed lines, do not abort
```

Skipping malformed lines is intentional. Logs often contain
partial writes at the tail when the file is rotated mid-read.

## Sampling Pattern for Large Files

For multi-gigabyte logs, full reads are infeasible. The sampled
module documents three slices that cover most analysis needs.

```bash
# First 1000 lines (startup events)
head -n 1000 /var/log/app.log

# Last 1000 lines (recent events)
tail -n 1000 /var/log/app.log

# Time window via grep on timestamp prefix
grep '^2026-05-03T1[0-2]' /var/log/app.log | head -n 5000
```

For complex queries on large logs, the right answer is often
to ingest into a real log store (`grep`, `rg`, `awk`, or a SIEM)
rather than parse in-process.

## Pitfalls

1. **Loading entire log files**: A 5 GB log file blows the
   process memory and the context budget. Always classify
   volume first.
2. **Aborting on malformed lines**: Logs are streaming data.
   Partial writes at the tail are normal. Skip and continue.
3. **One regex for all plain-text**: Plain-text logs vary by
   application. Use per-application parsers, not a single
   universal regex.
4. **Ignoring multi-line entries**: Stack traces and SQL
   queries span multiple lines. Single-line parsers split them
   incorrectly. Detect and load the multi-line parser when
   needed.
5. **Treating timestamps as strings only**: Sorting logs by
   string timestamp works for ISO-8601 but breaks for syslog
   format `Mon DD HH:MM:SS`. Parse to a datetime when ordering
   matters.

## Cross-Reference

See `document-analysis-patterns.md` for prose documents and
the parent `SKILL.md` for how log modules plug into the
hub-and-spoke pattern.
