---
name: deferred-capture
description: Defines the contract for deferred-item capture across plugins. Use when building or validating a plugin's deferred-capture wrapper or adding source labels.
alwaysApply: false
model_hint: standard
---
# Deferred Capture Contract

## When To Use

- Building a new plugin deferred-capture wrapper
- Validating an existing wrapper against the contract
- Adding new source labels or template fields

## When NOT To Use

- Capturing a deferred item at runtime (use the plugin
  wrapper directly, e.g. `plugins/<plugin>/scripts/deferred_capture.py`)
- Creating GitHub issues manually

Specification that all plugin deferred-capture wrappers implement.
Not a runtime dependency, just a convention.

## CLI Interface

Required arguments:

- `--title` (str): Concise description. Becomes issue title
  after `[Deferred]` prefix
- `--source` (str): Origin skill. One of: war-room, brainstorm,
  scope-guard, feature-review, review, regression, egregore
- `--context` (str): Why raised and why deferred

Optional arguments:

- `--labels` (str): Comma-separated additional labels beyond
  `deferred` and source
- `--session-id` (str): Session ID. Canonical source:
  `session_id` from the hook payload stdin
  (`jq -r '.session_id'`), fallback: UTC timestamp
  `YYYYMMDD-HHMMSS`
- `--artifact-path` (str): Absolute path or `$HOME`-based
  path to source artifact
- `--captured-by` (str): `explicit` (default) or `safety-net`
- `--dry-run` (flag): Print JSON output without creating issue

## Issue Template

Title: `[Deferred] <title>`

Labels: `deferred` and `<source>`

Body:

    ## Deferred Item

    **Source:** <source> (session <session-id>)
    **Captured:** <YYYY-MM-DD>
    **Branch:** <current git branch>
    **Captured by:** <explicit|safety-net>

    ### Context

    <context argument verbatim>

    ### Original Artifact

    <artifact-path if provided, otherwise "N/A">

    ### Next Steps

    - [ ] Evaluate feasibility in a future cycle
    - [ ] Link to related work if applicable

## Label Taxonomy

| Label | Color | Purpose |
|-------|-------|---------|
| `deferred` | `#7B61FF` | Universal query handle |
| `war-room` | `#B60205` | Source: war-room deliberation |
| `brainstorm` | `#1D76DB` | Source: brainstorming session |
| `scope-guard` | `#FBCA04` | Source: scope-guard deferral |
| `feature-review` | `#F9A825` | Source: feature-review |
| `review` | `#0E8A16` | Source: code/PR review |
| `regression` | `#D73A4A` | Source: skill regression |
| `egregore` | `#5319E7` | Source: autonomous agent |

## Duplicate Detection

Search: `gh issue list --search "<title> in:title"
--state open --json number,title`

Compare: exact title match after stripping `[Deferred]`
prefix and normalizing to lowercase.

Only open issues are checked. Re-filing a closed deferred
item is intentional.

## Output (JSON to stdout)

Created: `{"status": "created", "issue_url": "...", "number": 42}`
Duplicate: `{"status": "duplicate", "existing_url": "...", "number": 17}`
Error: `{"status": "error", "message": "..."}`

## Compliance Test

Any wrapper can verify conformance with:

    python3 scripts/deferred_capture.py \
      --title "Test: compliance check" \
      --source test \
      --context "Automated compliance verification" \
      --dry-run

Must output valid JSON with a `status` field.

## Exit Criteria

- [ ] Compliance test passes: `deferred_capture.py --dry-run` outputs
  valid JSON with a `status` field (`created`, `duplicate`, or
  `error`) for any conformant wrapper
- [ ] Created issues have title prefixed `[Deferred]`, carry both
  the `deferred` label and the source label, and body matches the
  required template (Source, Captured, Branch, Captured by,
  Context, Original Artifact, Next Steps)
- [ ] Duplicate detection runs before creation: `gh issue list
  --search "<title> in:title"` called and exact match (after
  stripping prefix and lowercasing) suppresses the new issue
- [ ] JSON written to stdout on every invocation; `{"status":
  "created", "issue_url": "...", "number": N}` on success,
  `{"status": "duplicate", ...}` on duplicate, `{"status":
  "error", "message": "..."}` on failure
