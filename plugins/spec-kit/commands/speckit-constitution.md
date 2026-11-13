---
description: Create/update the project constitution from principle inputs and bump its version
argument-hint: "Principle or constraint to add"
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Scope Guard

This command updates the project constitution and nothing else. The other
speckit commands read `.specify/memory/constitution.md` when they run, so
an amendment reaches them without this command editing them.

- Classify every part of the user input as either constitution content or
  a separate, non-governance intent.
- If the input includes feature implementation, code generation,
  refactoring, building, or deployment requests, you **MUST NOT** execute
  them. Extract them as deferred intents instead.
- You **MUST NOT** create, modify, or delete application source files,
  tests, deployment files, or other artifacts unrelated to the constitution.
- If it is unclear whether an instruction is constitution content, ask
  before making changes.
- After the update, add a `Next Actions` section listing each deferred
  intent and the speckit command that fits it, such as `/speckit-specify`,
  without invoking it. Omit the section when there are none.

## Outline

You are updating the project constitution at `.specify/memory/constitution.md`. This file is a TEMPLATE containing placeholder tokens in square brackets (e.g. `[PROJECT_NAME]`, `[PRINCIPLE_1_NAME]`). Your job is to (a) collect/derive concrete values, and (b) fill the template precisely.

Follow this execution flow:

1. Load the existing constitution template at `.specify/memory/constitution.md`.
   - Identify every placeholder token of the form `[ALL_CAPS_IDENTIFIER]`.
   **IMPORTANT**: The user might require less or more principles than the ones used in the template. If a number is specified, respect that - follow the general template. You will update the doc accordingly.

2. Collect/derive values for placeholders:
   - If user input (conversation) supplies a value, use it.
   - Otherwise infer from existing repo context (README, docs, prior constitution versions if embedded).
   - For governance dates: `RATIFICATION_DATE` is the original adoption date (if unknown ask or mark TODO), `LAST_AMENDED_DATE` is today if changes are made, otherwise keep previous.
   - `CONSTITUTION_VERSION` must increment according to semantic versioning rules:
     - MAJOR: Backward incompatible governance/principle removals or redefinitions.
     - MINOR: New principle/section added or materially expanded guidance.
     - PATCH: Clarifications, wording, typo fixes, non-semantic refinements.
   - If version bump type ambiguous, propose reasoning before finalizing.

3. Draft the updated constitution content:
   - Replace every placeholder with concrete text (no bracketed tokens left except intentionally retained template slots that the project has chosen not to define yet: explicitly justify any left).
   - Preserve heading hierarchy and comments can be removed once replaced unless they still add clarifying guidance.
   - validate each Principle section: succinct name line, paragraph (or bullet list) capturing non‑negotiable rules, explicit rationale if not obvious.
   - validate Governance section lists amendment procedure, versioning policy, and compliance review expectations.

### Record the Tradeoff (decision journal)

When this step settles a decision with real alternatives, record it to
`docs/tradeoffs.md` while the reasoning is live (draft and confirm):

- If leyline is installed, invoke `Skill(leyline:decision-journal)` and append
  a tradeoff entry (the decision, the options weighed, and what was
  sacrificed, with `phase` set to `plan`). Show the draft and append
  on confirmation.
- Fallback (leyline absent): append to `docs/tradeoffs.md` using the in-file
  ENTRY TEMPLATE, and assign the next `TR-NNN` id.

4. Produce a Sync Impact Report as an HTML comment at the top of the constitution file. It is scratch material for a person reviewing the amendment, not governance content, and is removed before the amended constitution file is committed:
   - Version change: old → new
   - List of modified principles (old title → new title if renamed)
   - Added sections
   - Removed sections
   - Follow-up TODOs if any placeholders intentionally deferred.

5. Validation before final output:
   - No remaining unexplained bracket tokens.
   - Version line matches report.
   - Dates ISO format YYYY-MM-DD.
   - Principles are declarative, testable, and free of vague language ("should" → replace with MUST/SHOULD rationale where appropriate).

6. Write the completed constitution back to `.specify/memory/constitution.md` (overwrite).

7. Output a final summary to the user with:
   - New version and bump rationale.
   - Any TODO placeholders or deferred items needing manual follow-up.
   - A `Next Actions` section for any deferred non-governance intents.
   - Suggested commit message (e.g., `docs: amend constitution to vX.Y.Z (principle additions + governance update)`).

Formatting & Style Requirements:

- Use Markdown headings exactly as in the template (do not demote/promote levels).
- Wrap long rationale lines to keep readability (<100 chars ideally) but do not hard enforce with awkward breaks.
- Keep a single blank line between sections.
- Avoid trailing whitespace.

If the user supplies partial updates (e.g., only one principle revision), still perform validation and version decision steps.

If critical info missing (e.g., ratification date truly unknown), insert `TODO(<FIELD_NAME>): explanation` and include in the Sync Impact Report under deferred items.

Write only `.specify/memory/constitution.md`. Do not create or modify template files.
