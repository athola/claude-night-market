---
name: filter-log
description: Suggest tier-1 filter commands for a log file before any compression or paste. Anchors on the log-debugging-hygiene module.
usage: /conserve:filter-log <file> [--apply] [--tokens] [--lines N]
---

# Filter Log Command

Pick the smallest slice of a log that still answers the question
you brought to it. Filter beats compression: on the committed
`intake_queue.jsonl` fixture, `tail -n 100` saves 95.6 percent
of bytes while logs-tokenizer saves 70.3 percent. The asymmetry
is reproducible and the
`tests/test_log_debugging_hygiene.py::test_filter_first_claim_is_reproducible`
test guards it.

This command routes the user to the tier-1 filters documented
in `skills/compression-strategy/modules/log-debugging-hygiene.md`
and stops there. Tier 3 (compression) is intentionally not the
default path.

## Usage

```bash
/conserve:filter-log path/to/file.log
/conserve:filter-log path/to/file.log --lines 50
/conserve:filter-log path/to/file.log --apply --tokens
/conserve:filter-log path/to/file.jsonl --apply
```

## Arguments

| Arg | Required | Meaning |
|-----|----------|---------|
| `<file>` | yes | Path to the log file (`.log`, `.jsonl`, `.txt`, stdout dump). |
| `--apply` | no | Run the recommended filter and print the result. Default: print the command only. |
| `--tokens` | no | Measure pre- and post-filter token counts with `tiktoken` (cl100k_base proxy). |
| `--lines N` | no | Override the default line budget. Default: 100 for `tail`, 50 for `head`. |

## What This Command Does

When invoked, follow this routine. Do not skip steps.

### Step 1: Inspect the file

Run these probes (read-only, fast):

```bash
wc -l "$FILE"          # total lines
wc -c "$FILE"          # total bytes
file "$FILE"           # type detection
head -n 3 "$FILE"      # first few lines for format
tail -n 3 "$FILE"      # last few lines for recency
```

Use the output to classify the log into one of four shapes:

- **JSONL** (each line parses as JSON) -> `jq` route
- **Timestamped plaintext** (lines start with ISO timestamp
  or `[level]`) -> `rg` or `awk` route
- **Stack trace or panic** -> `rg -B 5 -A 20` route
- **Unstructured** -> `tail` or `head` route as fallback

### Step 2: Recommend the tier-1 filter

Use the decision table from the module. Default lines come from
`--lines` if set, else 100 for tail, 50 for head, 20 for
`rg -A`. Substitute the file path and any pattern the user
mentioned in their prompt.

| Shape and intent | Suggested command |
|------------------|-------------------|
| JSONL, filter by field | `jq -c 'select(.level=="error")' "$FILE" \| tail -n 30` |
| JSONL, projection | `jq -c '{ts,event,msg}' "$FILE" \| tail -n 50` |
| Most recent state | `tail -n 100 "$FILE"` |
| Startup or init flow | `head -n 50 "$FILE"` |
| Errors only | `rg -n "ERROR\|FAIL\|panic" "$FILE"` |
| Context around match | `rg -B 5 -A 20 "panic" "$FILE"` |
| Time window | `awk '/14:23:00/,/14:24:00/' "$FILE"` |
| Last N unique lines | `sort -u "$FILE" \| tail -n 30` |

Print the recommendation as a code block the user can copy.
If `--apply` is set, run the command and show its stdout.

### Step 3: Report savings if `--tokens` is set

After applying, measure the delta:

```bash
uv run --quiet --with tiktoken python3 -c "
import tiktoken, sys
enc = tiktoken.get_encoding('cl100k_base')
print(len(enc.encode(open(sys.argv[1]).read())))
" "$FILE"
```

Repeat against the filtered output. Report bytes and tokens
saved as percentages. Be honest: byte savings overstate token
savings by roughly 10 percentage points (per the module's
"Token vs Byte Reduction" section).

### Step 4: Refer onward if filtering is insufficient

If the user truly needs every line (anomaly detection across a
full trace, race-condition analysis, performance debugging),
point them at tier 2 (compact output flags) and tier 3
(external compressors like logs-tokenizer, drain3, LLMLingua)
from the module. Do not auto-invoke compression.

## Anti-Patterns

Avoid the following:

- Suggesting compression as the first step. Tier 1 wins on
  every measured case in the module's benchmark.
- Quoting only byte savings. Report tokens when `--tokens` is
  set, and note the 10-percentage-point typical gap.
- Inventing a filter pattern the user did not mention. If no
  pattern is obvious, default to `tail -n <lines>`.
- Recommending `cat "$FILE"`. That is the failure mode this
  command exists to prevent.

## Exit Criteria

- [ ] Step 1 probes were run and the file was classified into
      one of the four shapes.
- [ ] The recommended filter is a literal subset of the source
      log when `--apply` runs (no paraphrase, no reordering).
- [ ] When `--tokens` is set, the report cites tokens before
      and after using `tiktoken` (not just bytes).
- [ ] No tier 3 compressor was invoked from this command path.
- [ ] The user has a copy-pasteable command for their next run.

## References

- The `log-debugging-hygiene` module under
  `plugins/conserve/skills/compression-strategy/modules/` for
  the full three-tier workflow and benchmarks.
- `plugins/conserve/tests/test_log_debugging_hygiene.py` for
  the reproducible filter-first claim.
- `.claude/rules/bounded-discovery.md` for the discovery budget
  this command stays within.
