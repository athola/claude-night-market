<!--
Title: imperative, naming the capability.
"Add symmetric to_pdf and read_yaml I/O methods".
-->

| | |
|---|---|
| **Who** | <!-- audience for the capability; out-of-band reviewer if any --> |
| **Where** | <!-- internal: module and file count. External: new or changed public surface, or `none` --> |
| **When** | <!-- `on merge`, or the flag and the date it is fully rolled out --> |

## Why

<!-- The problem this capability solves and why it matters now. Link
the issue or design discussion. -->

## What and how

<!-- What the feature does. Then the design decision: the approach
taken, the alternative rejected, and why. This section is the one that
saves a review round trip. -->

## Test plan

<!-- Numbered steps, each with an expected result. Manual steps are
required for any user-facing or CLI-facing path. -->

1. `make test`: <!-- N/N passing, M new cases -->
2. `make lint`: <!-- clean -->
3. Manual: <!-- command --> Expected: <!-- observable result -->

## Checklist

- [ ] Tests fail if the feature is reverted
- [ ] Docs updated (README, guides, capabilities reference)
- [ ] No new public surface beyond what the Why justifies
