# MMPO True Belief Entropy: the logprob access path (blocked)

**Status:** Blocked. Low priority. Tracking issue #553.

True Belief Entropy, the quantitative clarity signal from MMPO
(arXiv:2605.30159, Liu et al. 2026, Eq. 5), cannot be implemented in
night-market today because it needs token-level log-probabilities
from the generating model, and no surface in the stack exposes them.
This note records why, what would unblock it, and what we ship
instead. It is a decision record, not a work item: do not implement
the entropy signal until one of the three paths below exists.

## What the signal needs

MMPO Eq. 5 computes belief entropy over the model's predictive
distribution at each generated token. That requires the per-token
log-probabilities (or the full logit vector) of the model that
produced the summary. A qualitative re-reading of the text cannot
recover this number: it is a property of the generation, not of the
output string.

## Why night-market cannot provide it

| Surface | logprob access | Why not |
|---------|----------------|---------|
| Claude Code skills | None | Skills see text in and text out; model internals are not exposed to the harness. |
| `conjure` CLI delegation | None | Gemini and Qwen CLI delegation return completions, not token logprobs. |
| `oracle` daemon | None | Loads linear YAML models (weights + intercept) and serves point predictions over localhost HTTP. No generative model, so no token distribution. |

Verified at HEAD: `plugins/oracle/src/oracle/daemon.py` loads
`*.yaml` weight/intercept models; `plugins/conjure` exposes no
`logprob` flag.

## Three paths that would unblock it

1. **ONNX sidecar (oracle Phase 2).** The oracle daemon is already
   slated to grow `onnxruntime` inference (see `oracle:setup`). A
   local generative model served through ONNX with logit output
   would let the probe read token distributions directly. Highest
   alignment with existing plans; largest build.
2. **OpenAI-compatible local endpoint.** A `llama.cpp` server or
   Ollama run with a logprobs flag exposes per-token log-probs over
   an OpenAI-shaped HTTP API. The probe could call it for the entropy
   number while Claude continues to produce the summary text. Lowest
   build; adds an external runtime dependency the user must stand up.
3. **`claude-api` skill extension.** If Anthropic adds a logprob
   endpoint, the `claude-api` skill could request log-probs for the
   summary tokens. Zero local infrastructure; entirely gated on an
   upstream capability that does not exist yet.

## What we ship instead

Until a path lands, the dual-probe clarity check is qualitative. It
asks two anchor questions (progress and gap) and scores the answers
for specificity:

- `memory-palace:memory-clarity-probe` runs the dual probe.
- `conserve:context-optimization` module `belief-clarity.md` gates
  pre-compression and continuation handoffs on it.
- `memory-palace:knowledge-intake` and `session-palace-builder` gate
  storage and session checkpoints on it.

The qualitative gate catches drift and omission. Its known blind spot
is confident-but-wrong state: a summary that answers both probes
crisply yet inaccurately scores as clear. The entropy signal would
narrow that gap by flagging high-uncertainty generations the text
alone hides. Pair the qualitative gate with `imbue:proof-of-work`
task-state verification for high-stakes handoffs in the meantime.

## References

- arXiv:2605.30159, MMPO, Eq. 5 (True Belief Entropy) and Section 2.2.
- Issue #553 (this tracking record), #549 (the qualitative probe).
- `plugins/memory-palace/skills/memory-clarity-probe/SKILL.md`.
- `plugins/conserve/skills/context-optimization/modules/belief-clarity.md`.
