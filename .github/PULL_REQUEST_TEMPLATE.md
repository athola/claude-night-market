<!--
Title: imperative and self-contained, so it still reads correctly in
`git log` a year from now. "Delete the FizzBuzz RPC", not "Fix bug".

Variants for other change types:
  ?template=bugfix.md | ?template=feature.md | ?template=breaking-change.md
Structure and rationale: docs/adr/0021-pr-descriptions-in-two-registers.md
-->

| | |
|---|---|
| **Who** | <!-- audience for this change; name a reviewer only for out-of-band routing --> |
| **Where** | <!-- internal: module and file count. External: consumers, APIs, wire formats, or `none` --> |
| **When** | <!-- `on merge`, or the flag / migration window / full-integration date --> |

## Why

<!-- The motivating problem and why merging now matters. Link the
issue. Ground it in a number, an incident, or a report. -->

## What and how

<!-- What changed, in the reader's terms. Then how, only if there was a
real decision point: name the approach and the alternative you
rejected. Mechanical changes skip the how. -->

## Test plan

<!-- Numbered steps, each with its expected result.

Required when the change has no automated coverage, touches a
user-facing or CLI flow, fixes a bug (reproduce / fix / verify), or
changes an external contract. Otherwise list commands and results. -->

1. `make test`: <!-- N/N passing -->
2. `make lint`: <!-- clean -->

## Checklist

- [ ] Tests fail if the change is reverted
- [ ] Docs updated
- [ ] Breaking changes stated in the Where row
