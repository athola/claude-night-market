# Log Debugging Hygiene

When pasting logs into a Claude Code session, filter at the
source before you reach for compression. On the committed
`intake_queue.jsonl` fixture in this repo, `tail -n 100` saves
95.6% of bytes; the best lossless compressor we measured saves
70.3%. Filter wins by 25 percentage points and stays forensically
useful because output remains a literal subset of the log.

This module formalizes a three-tier workflow so that compression
is the last lever pulled, not the first.

## When to Use

Reach for this module when any of the following apply:

- About to paste more than 100 log lines into a session.
- A previous paste pushed context above 50% utilization.
- A debugging trace, CI failure, or hook log is the source of
  the bloat (not chat history or code).
- A teammate or skill recommended "compression" before any
  filtering was tried.

Skip this module if the paste is already under 2000 tokens or
if the entire log is needed verbatim for a regression report.

## Required TodoWrite Items

1. `log-debug:tier-1-filtered`
2. `log-debug:tier-2-minimized`
3. `log-debug:token-measured`

## Tier 1: Filter at Source (90-99% byte reduction)

Filtering keeps the lines you actually need and discards
the rest. This step delivers the largest savings and
requires no new tooling.

| Scenario | Command | Why |
|----------|---------|-----|
| Last N lines | `tail -n 100 file.log` | Most recent state |
| First N lines | `head -n 50 file.log` | Startup or init |
| Pattern matches | `rg -n "ERROR\|FAIL" file.log` | Targeted lines |
| Context around match | `rg -B 5 -A 10 "panic" file.log` | Surrounding rows |
| JSON field filter | `jq -c 'select(.level=="error")' f.jsonl` | Structured data |
| Time window | `awk '/14:23:00/,/14:24:00/' file.log` | Slice by stamp |
| Last N unique | `sort -u file.log \| tail -n 30` | Dedup then trim |

Benchmark on this repo's `plugins/memory-palace/data/intake_queue.jsonl`
(1.05 MB, 1333 lines):

| Command | Output bytes | Reduction |
|---------|--------------|-----------|
| `tail -n 100` | 47 KB | 95.6% |
| `jq -c 'select(.tool_name)' \| tail -n 20` | 14 KB | 99.1% |
| logs-tokenizer (compress all) | 491 KB | 70.3% |

Filter beats compression by 25-29 percentage points on this
fixture and by ~99x in absolute reduction when `jq` can
specify the relevant rows. The
`tests/test_log_debugging_hygiene.py::test_filter_first_claim_is_reproducible`
test guards this property.

## Tier 2: Minimize Structurally (50-95% reduction)

When you cannot filter to specific lines, switch your tool to
its most compact output mode. Many tools have a flag for this.

| Tool | Verbose form | Compact form |
|------|--------------|--------------|
| `git log` | `git log` (full) | `git log --oneline -20` |
| `git diff` | `git diff` | `git diff --stat` |
| `pytest` | `pytest -v` | `pytest --tb=short -x` |
| `cargo build` | full output | `2>&1 \| rg "^(error\|warning)" \| head -50` |
| `jq` | pretty | `jq -c` (single-line) |
| `npm install` | full | `--silent` |
| Hook trace | full JSONL | `jq -c '{ts,event}'` projection |

Pair tier 2 with `head -n N` or `tail -n N` to bound the
output even after compaction.

## Tier 3: Compress as Fallback (60-80% reduction)

Use compression only when:

- You genuinely need every line (anomaly detection across a
  full trace, performance debugging where every timing
  matters, race condition analysis).
- Tier 1 and tier 2 cannot isolate the relevant subset.
- The compressed payload still fits within budget.

### External tools (not bundled)

The conserve plugin does not bundle a compressor. Use one
of these if tier 1 and 2 are insufficient:

| Tool | License | Form | Notes |
|------|---------|------|-------|
| [drain3](https://github.com/logpai/Drain3) | MIT | Python lib | Template-mining, stale (2022) but stable |
| [logs-tokenizer](https://github.com/sergeivaskov/logs-tokenizer) | MIT | Rust binary | Lossless macro substitution, desktop tray app |
| [LLMLingua](https://github.com/microsoft/LLMLingua) | MIT | Python lib | Token-pruning, lossy but well-cited |

### Honest framing

Compression saves tokens. It does not improve LLM accuracy on
log debugging tasks. The literature evidence:

- LLMLingua family (Jiang et al., EMNLP 2023, ACL 2024)
  preserves accuracy at 4-20x compression on QA. The
  +17-21% accuracy gain reported by LongLLMLingua is on
  multi-document QA, not log debugging.
- LogFiT and LogLLM (Guan et al., arXiv 2411.08561, 2024)
  argue the opposite direction for logs: preprocessing can
  hurt via cascading parser errors.
- Empirical Study on Prompt Compression (OpenReview 2024)
  shows compression can introduce ASH (Altered Semantic
  Hallucinations) and ILH (Information Loss Hallucinations).
- CompressionAttack (arXiv 2510.22963, 2025) identifies
  prompt compression as a new adversarial attack surface.

If you ship a compression claim, it must say "saves tokens,
preserves accuracy" and cite which compressor produced the
numbers.

## Token vs Byte Reduction

Byte savings overstate token savings by roughly 10 percentage
points because compressed payloads use unusual character
combinations (tag soup like `&1u:!E!`) that the BPE
tokenizer was not trained on.

Measure tokens with `tiktoken` (GPT-4 tokenizer, used as
a proxy for Claude tokenization):

```bash
uv run --quiet --with tiktoken python3 -c "
import tiktoken, sys
enc = tiktoken.get_encoding('cl100k_base')
print(len(enc.encode(open(sys.argv[1]).read())))
" file.log
```

Measured deltas on the same intake_queue.jsonl fixture:

| Sample | Bytes saved | Tokens saved |
|--------|-------------|--------------|
| intake.jsonl full (1.65 MB) | 70.3% | 61.9% |
| intake-500.jsonl (238 KB) | 87.6% | 77.1% |
| intake-200.jsonl (95 KB) | 87.3% | 76.7% |
| git-log-500 (54 KB, diverse) | 34.1% | 19.8% |

The diverse-content row matters most: on logs that lack heavy
repetition (git commits, varied error messages, prose), the
compressor delivers under 20% token savings while still
imposing the legend overhead and tag-soup readability cost.

## Anti-Patterns

Avoid these patterns when handling logs:

- Pasting `pytest -v` output without `--tb=short -x`. The
  per-test verbose lines are almost always discardable.
- Quoting byte savings without measuring tokens. The two
  are not equivalent.
- Adding a compression dependency "in case we need it." Per
  `.claude/rules/shared-utility-consumer-rule.md`, scaffolding
  needs 2+ documented consumers within 30 days.
- Using compression on already-filtered logs. Diminishing
  returns: filter already removed the highest-ratio repeats.
- Repeating the claim "LLMs work better on compressed logs"
  without evidence. Literature does not support it for log
  debugging (see "Honest framing" above).

## Exit Criteria

- [ ] At least one tier 1 command was tried before any paste.
- [ ] Pasted content size was measured in tokens (not bytes)
      using `tiktoken` or equivalent.
- [ ] If a compressor was invoked, the savings claim cites
      tokens, names the tool, and links to its license.
- [ ] No new compression dependency was added unless 2+
      concrete consumers are documented per
      `.claude/rules/shared-utility-consumer-rule.md`.
- [ ] `tests/test_log_debugging_hygiene.py` passes, including
      the reproducible filter-first benchmark.

## References

- `.claude/rules/bounded-discovery.md`: discovery read budgets.
- `.claude/rules/slop-scan-for-docs.md`: evidence-backed claims.
- `.claude/rules/shared-utility-consumer-rule.md`: utility
  scaffolding requires consumers.
- `Skill(conserve:token-conservation)`: session-level token
  budget tracking.
- `Skill(conserve:context-optimization)`: MECW principles.
