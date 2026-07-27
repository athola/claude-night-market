---
name: reversible-compression
description: |
  Archive a large tool output to an external cache, keep only a digest and a
  retrievable handle in context, and fetch the original (or a slice) on
  demand. The CCR pattern, ported from chopratejas/headroom.
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

It then surfaces a digest (first and last 20 lines, total line and
character counts) and the exact retrieval command. Fetch the original
later with:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/context_retrieve.py ccr-<hash> \
  [--grep PATTERN] [--head N] [--tail N] [--lines A:B]
```

The handle is content-addressed, so identical outputs map to one file
(natural dedup), and the archive survives `/clear` and continuation-agent
handoffs.

### Worked example (illustrative)

A 67 KB log dump (2,401 lines) is archived to an `ccr-<hash>.txt` handle.
The handle below is illustrative, not a real run; yours is the SHA-256
prefix of the actual output. The model sees a ~2 KB digest. Later, one
command pulls back only the line that matters:

```bash
context_retrieve.py ccr-e722db719ab6 --grep FATAL
# FATAL: database connection refused
```

## Honest constraint: what the hook does not do

A `PostToolUse` hook runs after the tool result is already in context. It
can add a digest, but it cannot redact the result it just saw, so it does
not shrink the current turn. Its value is the durable external cache plus
retrieve-on-demand: a later turn, or a fresh continuation agent after
`/clear`, reads the handle instead of re-running the expensive command.

To save tokens in the current turn you still need the usual moves: `/clear`,
a continuation agent (`Skill(conserve:clear-context)`), or not dumping the
output in the first place. CCR makes those moves cheap to undo.

## When compression pays off, and when it does not

Savings are content-type-dependent. Do not quote a single headline number.
Measured reductions, from Headroom's own benchmarks (see Evidence):

| Workload                     | Before  | After  | Reduction |
|------------------------------|--------:|-------:|----------:|
| Code search (100 results)    | 17,765  | 1,408  | 92%       |
| SRE incident debugging       | 65,694  | 5,118  | 92%       |
| GitHub issue triage          | 54,174  | 14,761 | 73%       |
| Codebase exploration         | 78,502  | 41,254 | 47%       |

Logs and structured tool output compress hard. Dense prose compresses by
roughly nothing (one practitioner report measured -0.3%), and encrypted or
high-entropy data not at all. Archive verbose, repetitive output; leave
prose answers alone.

Two cautions worth stating plainly:

- **Retrieve-on-demand can miss context**, the same failure mode as RAG. If
  the digest hides the span that mattered and nobody expands the handle, the
  model proceeds on partial information. Keep the digest honest (head, tail,
  and counts), and retrieve when a task depends on the body.
- **Do not aggressively compress multi-step reasoning.** At roughly 2x
  compression, math and chained reasoning degrade even when surface
  similarity stays high (arXiv 2605.17932, 2602.15843). Code, extraction,
  and retrieval context tolerate aggressive ratios; arithmetic does not.

## Prior art

| Project | Technique | Numbers |
|---------|-----------|---------|
| [opencode-dynamic-context-pruning](https://github.com/Opencode-DCP/opencode-dynamic-context-pruning) | Reversible: `/dcp decompress <id>` restores originals; tool-call dedup; error purge | ~85% vs ~90% cache hit (small intentional trade) |
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
| RECOMP | 2310.04408 | 6% retained | "minimal loss"; recoverable from source store |
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

Benchmark numbers above are otherwise sourced to the Headroom README
(`github.com/chopratejas/headroom`).
