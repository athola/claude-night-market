# Memory Palace Curation Workflow Touchpoint

This note explains how the Memory Palace cache interceptor collaborates with the knowledge-intake skill.

## Intake flag payload

- The hook now builds an `IntakeFlagPayload` dataclass (`memory_palace/curation/models.py`) every time a research query runs.
- It tracks three signals:
  - `should_flag_for_intake`: whether the query should be queued for ingestion.
  - `novelty_score`: heuristic derived from cache overlap and marginal-value redundancy levels.
  - `domain_alignment`: matches against `domains_of_interest` in `hooks/shared/config.py`.
- Duplicate entry IDs (cache hits with ≥0.9 score) are recorded so intake systems can de-duplicate without re-searching the corpus.

## Hook decision + telemetry linkage

- The hook attaches the serialized payload under `hookSpecificOutput.intakeFlagPayload`.
- Additional context includes a `[Memory Palace Intake]` line summarizing novelty, domain alignment, duplicates, and whether the flag is set. This makes intake reasoning visible to the runtime transcript.
- Telemetry rows (`data/telemetry/memory-palace.csv`) now include `novelty_score`, `aligned_domains`, `intake_delta_reasoning`, and a pipe-delimited `duplicate_entry_ids` column so knowledge-intake can short-circuit redundant ingest attempts without re-querying the cache.

## Knowledge-intake handoff

1. When `should_flag_for_intake=True`, the hook persists the intake payload directly to `data/intake_queue.jsonl`. This bypasses hook chain isolation (PreToolUse cannot pass data to PostToolUse).
2. Knowledge-intake processes the queue asynchronously, using the payload's duplicate list and delta reasoning to auto-merge, request operator review, or drop the sample.
3. When a query aligns with configured domains but lacked cache matches, intake can short-circuit to existing domain-specific templates rather than running the entire marginal value filter.
4. When duplicates are detected, intake is skipped (flag stays off) but telemetry still records the reasoning so curators know overlap caused the suppression.

This shared schema keeps curation signals consistent between the hook and the knowledge-intake skill while remaining lightweight enough to run on every intercepted query.

## Dual-output prompt workflow

- `knowledge-intake/scripts/intake_cli.py` now accepts `--dual-output` plus an optional `--prompt-pack` flag.
  - When enabled, the CLI continues to emit the palace entry and developer doc, **and** hydrates a prompt artifact under `docs/prompts/<prompt-pack>.md`.
  - The default pack is `marginal-value-dual`, sourced from `skills/knowledge-intake/prompts/marginal_value_dual.md`; pass another slug to pilot new templates.
- Each prompt file is populated with the candidate metadata, integration decision, and raw intake content so downstream operators (or automated follow-ups) can reuse the curated delta immediately.
- Example run:

  ```bash
  uv run python plugins/memory-palace/skills/knowledge-intake/scripts/intake_cli.py \
    --candidate /tmp/candidate.json \
    --dual-output \
    --prompt-pack marginal-value-dual \
    --auto-accept
  ```

- Capture the generated prompt slug in the curation log row (`prompt:marginal-value-dual`) so audits can trace which operator instructions shipped with a given intake decision.
