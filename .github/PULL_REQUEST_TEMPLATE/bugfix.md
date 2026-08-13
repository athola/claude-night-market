<!--
Title: name the wrong behavior and the correction.
"Reject empty resume bodies with 422 instead of 500".
-->

| | |
|---|---|
| **Who** | <!-- who hit this bug --> |
| **Where** | <!-- internal: module + file count. External: any status code, payload, or contract that changes, or `none` --> |
| **When** | <!-- `on merge`, or the release that carries the fix --> |

## Why

<!-- The failure, and what it cost. Link the issue. What did callers
see, and what did they do about it? -->

## What and how

<!-- The fix. If the guard sits at a trust boundary rather than deeper
in the call path, say so: that is a design decision a reviewer will
otherwise ask about. -->

## Test plan

<!-- Reproduce, fix, verify. Step 1 must fail on the parent commit. -->

1. Reproduce on `main`: <!-- command -->
   Expected before the fix: <!-- the bug -->
2. `make test`: <!-- N/N passing, M new regression cases -->
3. Verify on this branch: <!-- same command as step 1 -->
   Expected now: <!-- correct behavior -->

## Checklist

- [ ] A test fails on the parent commit and passes here
- [ ] Root cause fixed, not the symptom
- [ ] Docs updated if the behavior was documented
