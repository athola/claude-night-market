# Observability Hook Audit: Copy-Pasteable Resolution Pattern

**Status**: Phase 1 (audit) complete; per-hook PRs tracked
**Source**: Issue #460, Discussion #447

## Pattern definition

When an observability hook surfaces actionable drift, emit the
exact shell command that resolves it. Listing paths or describing
the resolution in prose forces the next agent to compose the
command, adding latency, error surface, and one more reason to
ignore the warning.

### Reference implementation

``plugins/sanctum/hooks/brainstorm_session_warn.py`` (locked by
``test_warning_includes_batch_rm_command``) emits:

````
- `.superpowers/brainstorm/abc`
- `.superpowers/brainstorm/def`

To remove all listed sessions in one go, run:

```
rm -rf .superpowers/brainstorm/abc .superpowers/brainstorm/def
```
````

Uses ``shlex.quote`` per path so session ids with spaces or
shell metacharacters are handled safely.

## Hook classification

Each observability hook falls into one of three categories.

### Apply pattern: **binary-actionable**

Hook surfaces drift with a clear resolve-or-keep choice.

| Hook | Status | Notes |
|------|--------|-------|
| ``sanctum/hooks/brainstorm_session_warn.py`` | DONE | Reference implementation |

After examining the rest of the candidate set, the audit found
no other hook that emits a multi-item drift warning to the user
with a single resolve-or-keep decision. The pattern is narrow.
Future binary-actionable hooks adopt it from authorship.

### Skip pattern: **observe-only**

Hook records a signal for retrospective analysis; no immediate
action expected.

| Hook | Reason |
|------|--------|
| ``abstract/hooks/skill_execution_logger.py`` | Logs to JSON for daily aggregation; no action expected per invocation. |
| ``abstract/hooks/aggregate_learnings_daily.py`` | Daily batch run; output is a report, not a prompt. |
| ``abstract/hooks/post_learnings_stop.py`` | Writes session summary; no per-hook action. |

### Skip pattern: **needs-triage**

Resolution requires per-item triage (review N items, classify
each, choose disposition). A single resolve-all command would
hide the per-item judgment the hook surfaced.

| Hook | Reason |
|------|--------|
| ``leyline/hooks/fetch-recent-discussions.sh`` | Lists discussions; users decide which to read/skip. |
| ``conserve/hooks/context_warning.py`` | Suggests one of several actions (clear, compact, summarize) based on context state. |
| ``leyline/hooks/supply_chain_check.py`` | Lists dependency advisories; resolution depends on each one. |

## Per-hook follow-up PRs

For binary-actionable hooks listed above as TODO, each gets one
small PR that adds:

1. The fenced cleanup block emitted from the hook output
2. ``shlex.quote`` per path to handle metacharacters
3. A contract test mirroring
   ``test_warning_includes_batch_rm_command``
4. A counter-example test confirming needs-triage hooks did NOT
   adopt the pattern (regression guard)

## Counter-examples

The pattern actively harms when:

- Resolution requires inspection of each item (lists of
  discussions, dependencies, lint warnings).
- Resolution is destructive and the user has not yet decided
  whether to keep.
- The list contains paths the user explicitly chose to keep
  (would imply the hook should not surface them at all).

## Acceptance criteria

- [x] Audit list of observability hooks with classification
  (this document)
- [ ] For each binary-actionable hook missing the pattern: a
  small PR adds the cleanup block with ``shlex.quote`` and a
  contract test
- [x] Counter-examples documented (this document)

## References

- Issue #460 (origin)
- Discussion #447 (Learning from ``/sanctum:fix-workflow``
  retrospective on PR #417)
- Reference implementation:
  ``plugins/sanctum/hooks/brainstorm_session_warn.py``
- Reference test:
  ``plugins/sanctum/tests/test_brainstorm_session_warn.py::test_warning_includes_batch_rm_command``
