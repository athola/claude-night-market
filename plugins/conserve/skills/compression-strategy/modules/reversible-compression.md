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

It then surfaces a digest (first and last 20 lines, total line and byte
counts) and the exact retrieval command. Fetch the original later with:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/context_retrieve.py ccr-<hash> \
  [--grep PATTERN] [--head N] [--tail N] [--lines A:B]
```

The handle is content-addressed, so identical outputs map to one file
(natural dedup), and the archive survives `/clear` and continuation-agent
handoffs.

### Worked example

A 67 KB log dump (2,401 lines) is archived to `ccr-e722db719ab6.txt`. The
model sees a ~2 KB digest. Later, one command pulls back only the line that
matters:

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

- `opencode-dynamic-context-pruning`: the closest open-source analog, with
  reversible `decompress`/`recompress` by id inside an agent loop.
- RECOMP (arXiv 2310.04408) and ICAE (arXiv 2307.06945): academic grounding
  for recoverable compression (originals stay reconstructable from a store).

## Evidence

Benchmark numbers above are sourced to the Headroom README
(`github.com/chopratejas/headroom`) and the research synthesis in
`docs/research/headroom-context-compression.md`, which carries the full
citation set (LLMLingua, LongLLMLingua, RECOMP, ICAE, the boundary-condition
papers, and the practitioner caveats).
