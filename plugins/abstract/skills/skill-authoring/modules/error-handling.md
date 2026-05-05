# Error Handling in Skills

Skills run in environments that fail in many ways: tools missing,
commands timing out, partial subagent results, network errors,
permission denials. This module covers how the SKILL.md should
direct Claude when failures occur. The goal is a skill that
fails loudly and recoverably rather than one that drifts into
hallucinated success.

## Three failure surfaces

A skill must handle errors at three layers. Conflating them
produces skills that catch the wrong thing or paper over real
problems.

| Layer | Example failure | Skill response |
|-------|-----------------|----------------|
| Tool | `gh` returns exit 1 | Surface the stderr verbatim, stop |
| Dependency | Required Python module missing | Print install command, stop |
| Logic | Subagent returned partial result | Detect partial, retry or escalate |

## Tool failures

The most common failure. A shell command exits non-zero, an MCP
tool returns an error payload, a script raises. Claude tends to
narrate around the error ("I'll try a different approach") and
proceeds without the data the next step needs.

### Pattern: surface, stop, ask

In SKILL.md, write the rule explicitly:

```markdown
## Tool Failures

When a tool returns a non-zero exit or an error payload:

1. Print the exit code and stderr verbatim (no paraphrasing).
2. Stop the workflow. Do not attempt the next step.
3. Tell the user what failed and what input would let you
   recover. Wait for the user to respond.

Do not "try a different approach" silently. Do not retry the
same command with different arguments unless the error message
explicitly suggests an argument fix.
```

This blocks the most expensive rationalization: Claude deciding
that a failure is "minor" and continuing into a state where the
next failure is much more expensive to diagnose.

### Pattern: classify before reacting

For skills that handle a class of tool failures (e.g., git
operations), include a classification table:

```markdown
## Git Failure Classes

| Error pattern | Class | Action |
|---------------|-------|--------|
| `nothing to commit` | benign | Report, continue |
| `merge conflict` | user-input | Stop, ask user to resolve |
| `permission denied` | auth | Stop, see authentication.md |
| `repository not found` | config | Stop, ask for correct remote |
```

Without classification, every error becomes a stop, which is
safe but noisy. With classification, the skill stops only when
human input is required.

## Missing dependencies

Skills that ship scripts often assume `uv`, `python3.11+`,
`ripgrep`, or specific MCP servers are installed. When a
dependency is missing, the failure surface is:

1. Script invocation fails with `command not found` or
   `ModuleNotFoundError`.
2. Claude reads the error and tries to install the dependency.
3. Install fails for an unrelated reason (no sudo, wrong python).
4. Two failures stacked, neither diagnosed.

### Pattern: declare and verify

Declare dependencies in the skill frontmatter or an opening
section, and have the skill verify them before any work:

```markdown
## Dependencies

This skill requires:
- `python3` 3.11 or later (`python3 --version`)
- `ripgrep` (`rg --version`)
- `gh` (`gh --version`)

Run the verification step first. If any check fails, stop and
print the install command for the user's platform. Do not
attempt to install dependencies on the user's behalf.
```

The "do not attempt to install" line is critical. Auto-install
chains hide the actual problem (wrong PATH, missing sudo, wrong
package manager) behind a more confusing failure.

### Pattern: graceful degradation when optional

Some dependencies are optional. State which features require
which dependency, and fall back cleanly:

```markdown
## Optional Dependencies

- `sem` (semantic diff): if missing, the skill skips semantic
  analysis and falls back to plain `git diff`. Print a notice
  ("sem not installed, using git diff") rather than continuing
  silently.
```

The notice matters. Silent fallback degrades skill output
quality without telling the user why.

## Partial failures

The hardest class. A subagent dispatched to do five things
returns three with results, one with a stub, and one with a
plausible-sounding fabrication. Or a parallel review returns
six findings out of an expected ten.

### Pattern: explicit completion contract

Skills that dispatch subagents should require an explicit
completion signal:

```markdown
## Subagent Completion Contract

Every dispatched subagent must end its output with one of:

- `STATUS: COMPLETE` (all assigned work done with evidence)
- `STATUS: PARTIAL <reason>` (some work blocked, reason given)
- `STATUS: FAILED <reason>` (work not attempted, reason given)

If a subagent returns without one of these markers, treat the
result as `STATUS: UNKNOWN`. Do not merge unknown results into
the final output. Re-dispatch or escalate to the user.
```

The marker forces the subagent to commit to a state. Without
it, partial output looks identical to complete output.

### Pattern: count and verify

For dispatches with known cardinality (six findings, ten
files), verify the count before treating the result as
complete:

```markdown
## Result Verification

After parallel dispatch, count the returned items:

- Expected: 10 file analyses
- Received: count the items in each response

If received < expected, list the missing items by name and
re-dispatch only those. Do not produce a final summary from a
short result.
```

This catches the failure mode where a subagent returns a
summary like "I analyzed all the files" with five entries.

## Anti-patterns

These patterns look like error handling but degrade behavior.

### Catch-all rescue

```markdown
## Error Recovery

If anything fails, try the alternative approach in
modules/<fallback-name>.md.
```

This trains Claude to swallow errors. Every failure becomes a
detour into the fallback module, hiding the original problem.
Specify which error classes route to which fallback.

### Helpful retries

```markdown
## Retry Policy

If a tool fails, retry up to 3 times before reporting.
```

For idempotent reads (a `gh api` GET), one retry is reasonable.
For state-changing operations (commits, pushes, file writes),
silent retries cause duplicate work or corrupt state. Default
to no retry. Add retries only for specific commands with
documented idempotence.

### Best-effort completion

```markdown
## Partial Results

If some steps fail, continue with the steps that succeeded and
report the failures at the end.
```

This produces output that looks complete but is missing the
parts the user actually needed. Stop on the first failure
unless the skill explicitly handles partial results with a
known recovery path.

### Error paraphrase

```markdown
When a command fails, summarize the error in plain language for
the user.
```

Paraphrased errors lose the diagnostic strings (line numbers,
exit codes, error class names) the user needs to debug. Print
the raw error first, then add context if needed.

## Verification

Add baseline tests for each failure surface:

```
Tool failure: run the skill against a repo where `gh auth status`
returns exit 1. Expected: skill stops, surfaces the error.
Failure: skill paraphrases the error or proceeds.

Missing dependency: rename `rg` out of PATH and run the skill.
Expected: skill stops at the dependency check, prints install
command. Failure: skill silently uses `grep` or hallucinates rg
output.

Partial result: dispatch a subagent that returns three of five
findings. Expected: skill reports incomplete and re-dispatches
or escalates. Failure: skill produces a summary as if all five
were received.
```

Cross-reference: see `Skill(leyline:error-patterns)` for the
shared error classification taxonomy reused across plugins, and
`Skill(superpowers:systematic-debugging)` for the diagnosis
methodology applied to skill failures.
