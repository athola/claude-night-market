---
name: cache-aligned-prefixes
description: |
  Order context so provider KV caches hit: stable content first, volatile
  content last. The prefix-stabilization idea behind Headroom's CacheAligner,
  with the cost caveats that make it advisory rather than automatic.
category: conservation
---

# Cache-Aligned Prefixes

Providers cache the key-value tensors for a request prefix and reuse them
when the next request shares that exact prefix, skipping the prefill
recompute. The cache is keyed by a byte-stable prefix: one changed token
near the top voids everything after it. Ordering context so the stable part
comes first is what Headroom's CacheAligner does, and it is a real
provider-side mechanism (vLLM automatic prefix caching, Anthropic prompt
caching).

This module is advisory. Claude Code already caches automatically, so the
guidance below matters most when you author agents or call a provider API
directly.

## The rule

Put content in order of how often it changes, most stable first:

1. System prompt, tool and skill definitions (stable across a session).
2. Pinned files and reference material (stable across a task).
3. Conversation and tool results (grows, but append-only).
4. Volatile tokens last: timestamps, live counters, random ids, anything
   that changes every request.

A volatile token near the top is the common, expensive mistake. A current
timestamp injected into the system prompt busts the cache on every single
request.

## Do and do not

Do:

- Keep a long, stable system prompt and reuse it verbatim across requests.
- Append new turns rather than rewriting earlier ones.
- Move per-request data (the user's current question, the clock) to the end.

Do not:

- Interpolate timestamps, request ids, or random values into the prefix.
- Reorder or reword tool definitions between requests in a session.
- Assume caching is free (see the cost caveats next).

## Caveats that make this advisory

- **Cache writes cost more than normal tokens.** Anthropic prices cache
  writes at 1.25x (5-minute) or 2x (1-hour) and reads at 0.1x. On a prefix
  that is never reused, caching is a net loss. It pays off only with stable,
  repeated prefixes.
- **The window is short.** The default time-to-live is about five minutes,
  refreshed on each hit. Workflows with long gaps between requests fall out
  of the window and pay the write cost again.
- **Verify the cache is actually hitting.** A silent cache miss in a layered
  API stack produced a $38k bill in one reported incident. Instrument
  cache-read versus cache-write token counts; do not assume.
- **It is redundant where the harness already caches.** Inside Claude Code,
  this is mostly handled for you. Reach for explicit alignment when you
  control the request payload.

## Evidence

Provider mechanics and cost figures: Anthropic prompt caching docs and vLLM
automatic prefix caching. The cache-stability failure mode is evaluated in
"Don't Break the Cache" (arXiv 2601.06007). Full citations and the
practitioner reports (the 1.25x write cost, the five-minute window, the
billing incident) are in `docs/research/headroom-context-compression.md`.
