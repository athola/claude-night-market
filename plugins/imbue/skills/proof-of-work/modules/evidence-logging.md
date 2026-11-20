# Evidence Logging

Foundation for all evidence-based review workflows. Provides structured evidence capture, audit trails, and reproducibility for analyses.

## When To Use
- During any review or analysis workflow to capture reproducible evidence.
- When findings must be traceable to specific commands, outputs, or sources.
- Before finalizing recommendations that stakeholders will act upon.

## Activation Patterns
**Trigger Keywords**: evidence, proof, trace, audit, reproducible, citation, source, verify
**Contextual Cues**:
- "show your work" or "provide evidence"
- "how can I verify this" or "reproduce these findings"
- "cite your sources" or "where did this come from"
- "create an audit trail"
- "document the steps taken"

## Step 1: Initialize Log
- Create evidence structure with timestamp and context:
  - Session ID or review identifier.
  - Repository, branch, and commit hash.
  - Analyst identity and review scope.
- Establish naming convention for evidence references (e.g., `[E1]`, `[E2]`).

## Step 2: Capture Commands
- Log every command that produces evidence:
  ```
  [E1] Command: git diff --stat HEAD~5..HEAD
       Output: 15 files changed, 234 insertions(+), 89 deletions(-)
       Timestamp: 2024-01-15T10:30:00Z
  ```
- Include full command with arguments (no aliases).
- Capture relevant output snippets, not entire dumps.
- Note working directory and environment if relevant.

## Step 3: Record Citations
- Log external sources consulted:
  ```
  [C1] Source: https://doc.rust-lang.org/nomicon/
       Section: "Working with Unsafe"
       Relevance: Validates unsafe block justification
  ```
- Include web searches performed and key results.
- Reference documentation versions (API docs, RFCs, specs).
- Note any AI-assisted analysis with model/prompt context.

## Step 4: Index Artifacts
- Catalog generated artifacts:
  - Screenshots, diagrams, or visualizations.
  - Exported reports or coverage summaries.
  - Saved query results or API responses.
- Provide file paths or inline content for small artifacts.
- Note artifact retention policy (ephemeral vs. archived).

## Evidence Reference Format
Use consistent format in findings:
```
Finding: Memory leak in connection pool [E3, C2]
- Evidence [E3]: valgrind output showing 4KB unreleased
- Citation [C2]: PostgreSQL docs on connection lifecycle
```

## What Evidence Can Prove

A capped result proves only what it shows. Output cut by `head`,
`head_limit`, a result-count limit, or a "truncated" notice supports
no claim of absence, a complete list, a ranking, or a total. The
missing rows may change the answer. Mark the cap in the
evidence entry (`[E4] ... (capped at 20 rows)`) and either rerun
uncapped or state the claim as "at least".

An empty result is not zero. It means the query matched nothing, and
that equals absence only when the query covers the space: right path,
right pattern, right filters, no error swallowed. Show the coverage
(for example a control query that finds a known item) before
claiming none exist.

Keep four states apart in a claim, because readers act on them
differently:

- observed: a command output you can cite
- inferred: derived from observations, with the reasoning stated
- recommended: a suggested action, not yet taken
- executed: an action taken, with the command that took it

A command that exited 0 shows it ran. It does not show the question
was answered. Tie each claim to the output that answers it.

## Exit Criteria
- All findings traceable to specific evidence references.
- Downstream reports can cite evidence without re-running commands.
