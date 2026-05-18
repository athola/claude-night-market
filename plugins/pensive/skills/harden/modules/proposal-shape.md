# Proposal Shape

Every proposed remediation in a hardening report follows this
schema. The schema is not optional: a finding without a complete
proposal cannot be applied (the user can still choose to file or
defer it).

## Required fields

| Field | Purpose |
|-------|---------|
| `id` | Stable identifier across runs (e.g., `H7`, `PY03`) |
| `severity` | CRITICAL / HIGH / MEDIUM / LOW / ADVISORY |
| `citation` | Primary CWE plus NIST SSDF practice (mandatory) |
| `file` | Single file the proposal touches (multi-file proposals split into siblings) |
| `lines` | Affected line range, e.g., `42-58` |
| `detection_signal` | What pattern the scanner saw (in safe-to-quote form) |
| `proposal` | One-paragraph description of the fix |
| `diff` | Concrete diff or config snippet, not "consider doing X" |
| `blast_radius` | low / medium / high — see below |
| `reversal_plan` | Exact command to revert and the conditions to reapply |
| `expected_test` | Test path that should pass after the change |

## Severity to default disposition

| Severity | Default disposition |
|----------|---------------------|
| CRITICAL | apply or file immediately; never advisory |
| HIGH | propose for apply with prompt |
| MEDIUM | propose for apply only when `--auto-apply medium` |
| LOW | file as issue by default |
| ADVISORY | report only; never proposed |

CRITICAL findings always prompt even under `--auto-apply`.

## Blast radius scale

The proposal queries `Skill(pensive:blast-radius)` for the
change-impact graph and reports one of:

| Tier | Definition |
|------|------------|
| **low** | Single file; no public API change; no signature change; no behavior visible to callers |
| **medium** | Multiple files OR public API addition (new param with default, new method) OR test-only behavior change |
| **high** | Public API breaking change OR cross-plugin coupling OR config schema change |

High-blast-radius proposals require explicit approval even
under `--auto-apply`. The skill warns when the radius rises
above the user's current `--auto-apply` ceiling.

## Reversal plan template

```
Reversal:
  command: git revert <sha> --no-edit
  retry condition: <when it would be safe to reapply>
  evidence file: reviews/harden-<date>.md (this report)
```

For config changes that cannot be reverted by `git revert`
alone (e.g., a CI permission change that runs only on push):

```
Reversal:
  command: git revert <sha> --no-edit
  follow-up: re-trigger the workflow on master to confirm the
             permissions are restored
  evidence file: reviews/harden-<date>.md
```

## Expected-passing test

Each proposal cites a test that should pass after the change:

- If a test already exists, name it: `tests/unit/x.py::test_y`.
- If a test must be added, the proposal includes the test code in
  the same diff block. The test must fail against the
  pre-proposal code (RED) and pass after (GREEN).

A proposal without an expected test is downgraded to ADVISORY.
This is the harden equivalent of `Skill(imbue:proof-of-work)`'s
Iron Law.

## Approval options (per finding)

When the approval gate fires, the user gets:

1. **apply** — apply the diff, commit, run gates, advance.
2. **file** — create a GitHub issue with the proposal body and
   close out the finding.
3. **defer** — log to `.harden/backlog.md` for future runs to
   surface again.
4. **reject** — record a rejection with optional rationale; the
   finding will not surface again unless code changes invalidate
   the rejection.

The auto-apply ceiling determines which severities skip the gate
entirely:

```bash
/harden --auto-apply low      # apply LOW automatically
/harden --auto-apply medium   # apply LOW + MEDIUM automatically
/harden --auto-apply high     # apply LOW + MEDIUM + HIGH automatically
```

CRITICAL is never auto-applied.

## Worked example

```yaml
id: PY01
severity: HIGH
citation: "CWE-502 (Deserialization of Untrusted Data), NIST SSDF PW.7"
file: src/api/loader.py
lines: 42-44
detection_signal: |
  Module imports the Python stdlib unsafe-deserialization helper
  and calls its loads() helper on bytes that originate from the
  request body (data flows from request.body through validate()
  into loader.loads()).
proposal: |
  Replace the unsafe loader call with json.loads. The payload
  shape is JSON-compatible per the API spec (verified by reading
  the OpenAPI schema for /v1/upload). This eliminates the
  arbitrary-code-execution attack path while preserving the
  positive-path behavior.
diff: |
  --- a/src/api/loader.py
  +++ b/src/api/loader.py
  @@ -42,3 +42,5 @@
  -from <stdlib-unsafe-loader> import loads
  +import json
  -    obj = loads(payload)
  +    obj = json.loads(payload)
blast_radius: low
reversal_plan:
  command: "git revert <sha> --no-edit"
  retry_condition: "do not retry; the previous form was unsafe by design"
  evidence_file: "reviews/harden-2026-05-10.md"
expected_test: tests/unit/api/test_loader.py::test_round_trip_json
```

## Multi-file proposals

When a hardening fix needs touches across multiple files (e.g.,
adding a `Tier` `Literal` requires updates in classifiers, the
DORAMetrics dataclass, and the tests), split into sibling
proposals (PY01a, PY01b, PY01c) with a shared `parent_id`. The
approval gate applies them as one unit, but each is its own
commit so reverts stay surgical.

## What a proposal must NOT do

- Modify generated code, vendored code, or `node_modules`.
- Touch the changelog except to add a `### Security` bullet.
- Bump dependency versions beyond the minimum required for the
  fix (a separate proposal per dep upgrade).
- Introduce a new dependency without an `imbue:proof-of-work`
  evidence trail showing the dep was vetted.
- Disable existing tests or assertions to make the fix easier.
