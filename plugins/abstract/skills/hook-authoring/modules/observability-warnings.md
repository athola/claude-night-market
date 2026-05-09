# Observability Warning Patterns

When a hook surfaces actionable drift (state the user can resolve
or keep), emit the **exact shell command** that resolves it.
Listing paths or describing the resolution in prose forces the
next agent to compose the command, adding latency, error surface,
and one more reason to ignore the warning.

## Reference implementation

`plugins/sanctum/hooks/brainstorm_session_warn.py` (locked by
`test_warning_includes_batch_rm_command` in
`plugins/sanctum/tests/test_brainstorm_session_warn.py`) emits:

````
- `.superpowers/brainstorm/abc`
- `.superpowers/brainstorm/def`

To remove all listed sessions in one go, run:

```
rm -rf .superpowers/brainstorm/abc .superpowers/brainstorm/def
```
````

Uses `shlex.quote` per path so session ids with spaces or shell
metacharacters are handled safely.

## Three-category classification

When designing an observability hook, classify it into one of
three categories. Only one of them takes the copy-pasteable
resolution pattern.

### Apply pattern: binary-actionable

Hook surfaces drift with a clear resolve-or-keep choice. The
user inspects the list, decides "yes, clean this up" or "no,
keep it", and a single command resolves the entire batch.

| Hook | Notes |
|------|-------|
| `sanctum/hooks/brainstorm_session_warn.py` | Reference implementation |

The pattern is narrow. After the original audit, no other hook
in the codebase emitted a multi-item drift warning with a single
resolve-or-keep decision. Future binary-actionable hooks should
adopt the pattern from authorship.

### Skip pattern: observe-only

Hook records a signal for retrospective analysis; no immediate
action expected.

| Hook | Reason |
|------|--------|
| `abstract/hooks/skill_execution_logger.py` | Logs to JSON for daily aggregation; no action expected per invocation |
| `abstract/hooks/aggregate_learnings_daily.py` | Daily batch run; output is a report, not a prompt |
| `abstract/hooks/post_learnings_stop.py` | Writes session summary; no per-hook action |

### Skip pattern: needs-triage

Resolution requires per-item triage (review N items, classify
each, choose disposition). A single resolve-all command would
hide the per-item judgment the hook surfaced.

| Hook | Reason |
|------|--------|
| `leyline/hooks/fetch-recent-discussions.sh` | Lists discussions; users decide which to read or skip |
| `conserve/hooks/context_warning.py` | Suggests one of several actions (clear, compact, summarize) based on context state |
| `leyline/hooks/supply_chain_check.py` | Lists dependency advisories; resolution depends on each one |

## Counter-examples (when NOT to apply)

The pattern actively harms when:

- Resolution requires inspection of each item (lists of
  discussions, dependencies, lint warnings)
- Resolution is destructive and the user has not yet decided
  whether to keep
- The list contains paths the user explicitly chose to keep
  (which would imply the hook should not surface them at all)

## Authoring checklist for binary-actionable hooks

When adding a new binary-actionable observability hook:

1. Emit a fenced block listing the items
2. Follow with a single resolve-all command
3. Use `shlex.quote` per path to handle metacharacters
4. Add a contract test mirroring
   `test_warning_includes_batch_rm_command`
5. If the hook is in a category that would normally skip the
   pattern, add a counter-example test confirming the pattern
   was deliberately not adopted (regression guard)

## References

- Issue #460 (origin)
- Discussion #447 (retrospective on PR #417)
- Reference implementation:
  `plugins/sanctum/hooks/brainstorm_session_warn.py`
- Reference test:
  `plugins/sanctum/tests/test_brainstorm_session_warn.py`
