---
name: reversible-compression
description: |
  Archive a large tool output to an external cache under a retrievable
  handle, and fetch the original (or a slice) on demand after /clear or a
  handoff. The CCR pattern, after headroomlabs-ai/headroom.
category: conservation
---

# Reversible Compression (CCR)

Large tool outputs are the fastest way to fill a context window: a single
code search or log dump can cost tens of thousands of tokens, most of which
the model never needs. Reversible compression keeps the output recoverable
without keeping it resident.

The pattern, after Headroom's CCR (Cached Compression with Retrieval):

1. When one tool output is large, write the original to an external cache
   keyed by a content hash (the handle).
2. Keep only a compact digest plus that handle in the conversation.
3. Fetch the original, or just the slice you need, on demand by handle.

The original is never lost, so the compression is reversible. The model
reads the digest, and pulls the full text back only when a task actually
needs it.

## What is wired up in this plugin

The `tool_output_summarizer` PostToolUse hook archives any single Bash,
Read, or Grep output at or above `CONSERVE_CCR_THRESHOLD` characters
(default 25,000) to:

```
.claude/context-archive/ccr-<sha256[:12]>.txt
```

It then adds one line: the output's size, the handle, a statement that the
archive is the verbatim output, and the retrieval command. It repeats none
of the output, which is already in context.

A Bash result past Claude Code's inline limit (about 30,000 characters) is
skipped. Claude Code has already saved the whole output to a file and given
the model its path, and the hook sees only the first 30,000 characters, so
its archive would be a truncated copy. Fetch an archived original later
with:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/context_retrieve.py ccr-<hash> \
  [--grep PATTERN] [--head N] [--tail N] [--lines A:B]
```

The handle is content-addressed, so identical outputs map to one file
(natural dedup), and the archive survives `/clear` and continuation-agent
handoffs.

### Worked example (illustrative)

A 67 KB log dump (2,401 lines) is archived to an `ccr-<hash>.txt` handle.
The handle below is illustrative. Yours is the SHA-256
prefix of the actual output. After a `/clear`, one command pulls back only
the line that matters:

```bash
context_retrieve.py ccr-e722db719ab6 --grep FATAL
# FATAL: database connection refused
```

## What the hook does not do, and why

The hook does not replace the result it just saw. Claude Code allows it: a
PostToolUse hook can return `updatedToolOutput` with the tool's output
shape, and the model then sees the replacement. conserve does not, for
three reasons:

- Claude Code already moves a valid Bash result over roughly 30,000
  characters to a file and shows a 2,000-character preview
  ([tools reference](https://code.claude.com/docs/en/tools-reference)).
  The largest results never reach the model whole.
- In 2,908 billed Claude Code runs, the largest compression setup cut
  tool-output tokens 38.4% and raised billed cost 6.8%, and aggressive
  compression lowered successful patches
  ([arXiv 2607.12161](https://arxiv.org/abs/2607.12161)). Compressed
  observations changed the agent's path: more retrieval, testing and turns.
- Placeholder-with-restore helped some models and not others
  ([arXiv 2609.26121](https://arxiv.org/abs/2609.26121)). A gain on one
  model does not transfer to the next.

The archive's value is the durable copy: a later turn, or a continuation
agent after `/clear`, reads the handle instead of re-running the command.
To save tokens in the current turn, use `/clear`, a continuation agent
(`Skill(conserve:clear-context)`), or do not dump the output at all.

## Measure before compressing

Tool output is rarely where a session's money goes. Prompt-cache writes
and reads are. `plugins/conserve/scripts/session_cost.py` reads a
transcript and splits spend into uncached input, cache writes, cache reads
and output, in base-input units, and ranks tool results by what
re-reading them cost:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/session_cost.py \
  ~/.claude/projects/<project-slug>/<session-id>.jsonl [--top N] [--json]
```

On one 472-request session it reported cache reads at 53.6% of spend,
cache writes at 33.3%, output at 13.1%, and re-reading tool results at
5.6%. The first send of each result is a cache write as well, which the
ledger leaves in the cache-write row. It reads one transcript: subagent
transcripts are separate files under `<session-id>/subagents/`.

## When compression pays off, and when it does not

Independent measurements put tool-output compression at a few percent of
a Claude Code bill, and sometimes below zero:

| Source | Setup | Result |
|--------|-------|--------|
| [arXiv 2607.12161](https://arxiv.org/abs/2607.12161) | 2,908 billed runs, 103 tasks | -38.4% tool-output tokens, +6.8% billed cost, token and cost reduction correlated at r = 0.15 |
| [codepointer.dev replay](https://codepointer.dev/p/cutting-llm-token-costs-with-rtk) | 500 sessions, $926 | Headroom 2.8%, RTK 0.5%, caveman 0.4% of spend, quality not measured |
| [headroom#4918](https://github.com/headroomlabs-ai/headroom/issues/4918) | Claude Code, Headroom 0.44.0 | about 1% of input tokens |
| [arXiv 2508.21433](https://arxiv.org/abs/2508.21433) | SWE-agent, SWE-bench Verified | masking old observations roughly halved cost at a similar solve rate; LLM summaries lengthened runs 13-15% |
| [arXiv 2605.28876](https://arxiv.org/abs/2605.28876) | 35 CI failures, 11 log reducers | grep plus tail near-best at about 4.5x fewer tokens than grep alone; weak contexts cost 2-4x more tool calls |

Headroom's own table (21-57% fewer tokens on four agent scenarios) counts
tokens with no model call and no answer check
(`benchmarks/index_proof_table.py`). Logs and repetitive structured output
compress hard. Dense prose compresses by roughly nothing. Filter verbose
logs at the source (`/conserve:filter-log`) and leave prose alone.

Two cautions worth stating plainly:

- **Retrieve-on-demand can miss context**, the same failure mode as RAG.
  After a `/clear` the handle is all that remains, and a model that never
  expands it proceeds on partial information. The note calls the archive
  verbatim because naming the authoritative output recovered 6.3-7.9
  accuracy points for GPT-5.x models that otherwise answered from their own
  notes. Claude Opus and Sonnet 4.6 showed no loss to recover
  ([arXiv 2610.26836](https://arxiv.org/abs/2610.26836)).
- **Do not aggressively compress multi-step reasoning.** At roughly 2x
  compression, math and chained reasoning degrade even when surface
  similarity stays high (arXiv 2605.17932, 2602.15843). Code, extraction,
  and retrieval context tolerate aggressive ratios, but arithmetic does not.

## Prior art

| Project | Technique | Numbers |
|---------|-----------|---------|
| [opencode-dynamic-context-pruning](https://github.com/Opencode-DCP/opencode-dynamic-context-pruning) | Reversible (`/dcp decompress <id>` restores originals), tool-call dedup, error purge | ~85% vs ~90% cache hit (small intentional trade) |
| [microsoft/LLMLingua](https://github.com/microsoft/LLMLingua) | Self-information token pruning via a small LM | up to 20x; 2,365 to 211 tokens (11.2x) |
| [LLMLingua-2](https://arxiv.org/abs/2403.12968) | Distilled keep/drop classifier, task-agnostic | 2x-5x; 3x-6x faster than v1 |
| [Selective_Context](https://github.com/liyucheng09/Selective_Context) | Self-information span pruning | ~2x content, ~40% memory savings |
| [logpare](https://github.com/logpare/logpare) | Drain log templating plus frequency folding | 60-90% on logs |

Only Headroom and opencode-DCP implement true reversibility
(retrieve-on-demand). LLMLingua, Selective Context, and logpare are one-way
lossy, so an over-aggressive ratio is unrecoverable.

## Evidence

Accuracy-preservation results behind the ratios recommended above:

| Paper | arXiv | Compression | Accuracy |
|-------|-------|-------------|----------|
| LLMLingua | 2310.05736 | up to 20x | "little performance loss" (GSM8K, BBH) |
| LongLLMLingua | 2310.06839 | ~4x | +21.4% over uncompressed on NaturalQuestions |
| RECOMP | 2310.04408 | 6% retained | "minimal loss", recoverable from source store |
| ICAE | 2307.06945 | 4x (reversible) | reconstructable memory slots |
| DynamicKV | 2412.14838 | 1.7% KV retained | ~85% of full-cache performance (LongBench) |
| Perplexity Paradox | 2602.15843 | code r>=0.6, math lower | 96% quality at 22% cost |

Two caveats bound every number here. Savings are content-type-dependent:
Headroom's own reported figures are ~90% on logs, ~70% on tool output,
50-70% on database rows, and **-0.3% on dense prose, 0% on encrypted**
([HN 46663757](https://news.ycombinator.com/item?id=46663757)). Never quote
a single headline percentage. And retrieve-on-demand inherits RAG's failure
mode: the model may never expand the handle that mattered
([Lobsters](https://lobste.rs/s/xankns/cutting_llm_token_usage_by_80_using_repl)).

Headroom moved from `github.com/chopratejas/headroom` to
`github.com/headroomlabs-ai/headroom`, which the old address redirects to.
