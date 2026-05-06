---
module: reporting
category: ux
dependencies: [Read, Bash]
estimated_tokens: 1000
---

# Scan Reporting: Progress and Metrics

Two responsibilities are bundled here because both control what
the slop scanner emits during and after a run:

1. **Progress indicators** while files are being scanned.
2. **Historical metrics** persisted to `.slop-history/` for trend
   detection.

Merged from `progress-indicators.md` + `metrics.md` (P-14) so a
caller loading "how do I report results?" gets one module.

## Part 1: Progress Indicators

### When to Show Progress

Skip progress output entirely for single files or pairs of files. Show progress
when scanning 3 or more files. This avoids noise for the common single-file case.

| File count | Default behavior |
|------------|-----------------|
| 1-2 | No progress output |
| 3+ | Show file count progress |

### Output Modes

Three modes control what gets printed during a scan.

#### Default Mode

Show a counter line for each file as it is processed:

```
[1/49] Scanning plugins/scribe/README.md...
[2/49] Scanning plugins/scribe/SKILL.md...
...
[49/49] Scanning plugins/abstract/README.md...

Scanned 49 files in 3.2s
```

Format for each progress line:

```
[{current}/{total}] Scanning {filepath}...
```

Format for the completion summary:

```
Scanned {total} files in {elapsed:.1f}s
```

#### Quiet Mode (`--quiet`)

Suppress all progress output. Print only the final report. Use this in CI
pipelines and scripts where progress lines would pollute logs.

No per-file lines. No summary line. Only the report.

#### Verbose Mode (`--verbose`)

Print the per-file slop score immediately after each file is processed:

```
[1/49] Scanning plugins/scribe/README.md... score=2.1 (Light)
[2/49] Scanning plugins/scribe/SKILL.md... score=0.4 (Clean)
...

Scanned 49 files in 3.2s
```

Score label mapping:

| Score range | Label |
|-------------|-------|
| 0 - 1.0 | Clean |
| 1.0 - 2.5 | Light |
| 2.5 - 5.0 | Moderate |
| 5.0+ | Heavy |

### Implementation Notes

- Write progress lines to stdout so they can be redirected or captured.
- Compute elapsed time from scan start to the final file completion.
- Round elapsed time to one decimal place.
- Use 1-based indexing in the counter (`[1/49]`, not `[0/49]`).
- If a file cannot be read, print a warning on that line and continue:

```
[7/49] Scanning path/to/file.md... WARNING: could not read file
```

Do not abort the scan on a single unreadable file.

## Part 2: Historical Metrics

Store scan results over time to detect regressions and measure cleanup progress.

### Storage Location

Write scan records to `.slop-history/` at the repo root. Add this directory to `.gitignore`:

```
.slop-history/
```

### File Naming

One JSON file per scan:

```
.slop-history/scan-YYYY-MM-DD-HHMMSS.json
```

Example: `.slop-history/scan-2026-03-01-143022.json`

Generate the timestamp with:

```python
from datetime import datetime
datetime.now().strftime("%Y-%m-%d-%H%M%S")
```

### JSON Schema

```json
{
  "timestamp": "2026-03-01T14:30:22",
  "files_scanned": 12,
  "scores": [
    {"path": "docs/guide.md", "score": 1.4, "word_count": 320}
  ],
  "summary": {
    "avg_score": 1.4,
    "max_score": 3.1,
    "total_markers": 18
  }
}
```

All fields are required. Use `datetime.isoformat()` for the timestamp string.

### Saving Results (`--track`)

When the `--track` flag is present, write a record after every scan:

1. Build the `scores` list from the per-file results.
2. Compute `summary.avg_score` as the mean of all scores (0.0 if no files).
3. Compute `summary.max_score` as the maximum score (0.0 if no files).
4. Count `summary.total_markers` as the sum of all raw marker hits across files.
5. Write the JSON file to `.slop-history/` using the timestamp name.
6. Report the path written: `Saved: .slop-history/scan-YYYY-MM-DD-HHMMSS.json`

### Loading History (`--history`)

When the `--history` flag is present, read all files in `.slop-history/` sorted by
filename (chronological order) and print a trend table:

```
Date                 Files  Avg Score  Delta
2026-02-15-090000       10       1.20      —
2026-02-22-143000       12       1.45  +0.25
2026-03-01-143022       12       1.90  +0.45
```

Column widths: date 20, files 6, avg score 10, delta 8.
Use `—` for the delta on the first row. Prefix positive deltas with `+`.

### Regression Warning

After printing the trend table, check the two most recent records. If
`avg_score` increased by more than 0.5:

```
WARNING: avg score increased by 0.62 since last scan (1.28 -> 1.90)
```

This warning also fires when `--track` saves a new result and the previous
record exists. Compare the new avg against the most recent existing record
before writing.
