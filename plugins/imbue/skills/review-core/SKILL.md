---
name: review-core
description: Provides review-workflow scaffolding for context, evidence, and output. Use at the start of any detailed review to ensure consistent, comparable findings.
alwaysApply: false
category: review-patterns
tags:
- workflow
- scaffolding
- evidence
- reporting
- analysis
dependencies: []
tools: []
usage_patterns:
- review-preflight
- workflow-scaffolding
- evidence-capture
complexity: intermediate
model_hint: standard
estimated_tokens: 1500
---
# Core Review Workflow

## When To Use
- Use this skill at the beginning of any detailed review workflow (e.g., for architecture, math, or an API).
- It provides a consistent structure for capturing context, logging evidence, and formatting the final report, which makes the findings of different reviews comparable.

## When NOT To Use

- Diff-focused analysis - use diff-analysis

## Activation Patterns
**Trigger Keywords**: review, audit, analysis, assessment, evaluation, inspection
**Contextual Cues**:
- "review this code/design/architecture"
- "conduct an audit of"
- "analyze this for issues"
- "evaluate the quality of"
- "perform an assessment"

**Auto-Load When**: Any review-specific workflow is detected or when analysis methodologies are requested.

## Required TodoWrite Items
1. `review-core:context-established`
2. `review-core:scope-inventoried`
3. `review-core:evidence-captured`
4. `review-core:deliverables-structured`
5. `review-core:findings-verified`
6. `review-core:contingencies-documented`

## Step 1 – Establish Context (`review-core:context-established`)
- Confirm `pwd`, repo, branch, and upstream base (e.g., `git status -sb`, `git rev-parse --abbrev-ref HEAD`).
- Note comparison target (merge base, release tag) so later diffs reference a concrete range.
- Summarize the feature/bug/initiative under review plus stakeholders and deadlines.

## Step 2 – Inventory Scope (`review-core:scope-inventoried`)
- List relevant artifacts for this review: source files, configs, docs, specs, generated assets (OpenAPI, Makefiles, ADRs, notebooks, etc.).
- Record how you enumerated them (commands like `rg --files -g '*.mk'`, `ls docs`, `cargo metadata`).
- Capture assumptions or constraints inherited from the plan/issue so the domain-specific analysis can cite them.

## Step 3 – Capture Evidence (`review-core:evidence-captured`)
- Log every command/output that informs the review (e.g., `git diff --stat`, `make -pn`, `cargo doc`, `web.run` citations). Keep snippets or line numbers for later reference.
- Track open questions or variances found during preflight; if they block progress, record owners/timelines now.

### Record Lessons Learned (decision journal)

If this work involved rework, a failed approach, or a blocker, record it to
`docs/lessons-learned.md` so the insight survives past the session (draft and
confirm):

- If leyline is installed, invoke `Skill(leyline:decision-journal)` and append
  a lesson entry (`what_happened`, `what_didnt_work`, `root_cause`, `action`;
  set `phase` to `review`). Show the draft; append on confirmation.
- Fallback (leyline absent): append to `docs/lessons-learned.md` using the
  in-file ENTRY TEMPLATE; assign the next `LL-NNN` id.

## Step 4 – Structure Deliverables (`review-core:deliverables-structured`)
- Prepare the reporting skeleton shared by all reviews:
  - Summary (baseline, scope, recommendation)
  - Ordered findings (severity, file:line, principle violated, remediation)
  - Follow-up tasks (owner + due date)
  - Evidence appendix (commands, URLs, notebooks)
- validate the domain-specific checklist will populate each section before concluding.

## Step 5 – Verify Findings Are Grounded (`review-core:findings-verified`)

Every finding must be falsifiable: a citation a second pass can
mechanically re-read and confirm. Findings that fail verification do not
ship.

- Use the grounded-finding schema from `Skill(imbue:structured-output)`:
  each finding carries a `Location` (`file:line`) and a verbatim
  `Anchor` snippet copied from that line.
- Write the findings to `.review/findings.json` (one object per finding:
  `id`, `file`, `line`, `anchor`, `severity`, `category`,
  `recommendation`, `evidence_refs`).
- Run the verifier:

  ```bash
  python plugins/imbue/scripts/citation_verifier.py \
    --findings .review/findings.json --repo-root .
  ```

  Exit `0` means every citation resolved; exit `1` lists each finding
  whose path, line, or anchor did not match the source.
- Drop or label `UNVERIFIED` any finding the verifier failed; only
  verified findings enter the report. Attach the verifier output to the
  evidence appendix.
- If the script is unavailable, fall back to re-reading each cited
  `file:line` by hand and confirming the anchor text is present; note the
  manual fallback in the contingency section.

## Step 6 – Contingency Plan (`review-core:contingencies-documented`)
- If a required tool or skill is unavailable (e.g., `web.run`), document the alternative steps that will be taken and any limitations this introduces. This helps reviewers understand any gaps in coverage.
- Note any outstanding approvals or data needed to complete the review.

## Exit Criteria
- All TodoWrite items complete with concrete notes (commands run, files listed, evidence paths).
- Every reported finding carries a `Location` + verbatim `Anchor` and was confirmed by `citation_verifier.py` (or a documented manual re-read); no unverified findings ship.
- `.review/findings.json` exists and the verifier exited `0`, or every failed finding was dropped or labeled `UNVERIFIED`.
- Domain-specific review can now assume consistent context/evidence/deliverable scaffolding and focus on specialized analysis.
- Any rework, failed approach, or blocker uncovered during evidence capture is recorded to `docs/lessons-learned.md` (or the in-file template).
