---
module: stub-and-deferral
category: detection
dependencies: [Grep, Read]
estimated_tokens: 500
---

# Stub & Deferral Detection

**Every stub marker is a defect awaiting a production
incident. Either resolve, file a tracked issue, or delete
the surrounding code.**

This module covers the surface markers AI uses to signal
"I did not actually finish this." They are conceptually
simple: pattern-matched comments and constructs: but
they accumulate fast in AI-generated codebases because
the agent commits its incomplete drafts.

## The rule

Every match in this module must resolve to one of:

1. **Resolved**: the work is done, the marker is deleted.
2. **Tracked**: a linked issue/ticket replaces the bare
   marker (`// TODO(#1234): ...`).
3. **Deleted**: the surrounding code path is removed
   because the work is no longer needed.

Bare stub markers in production code are debt. The
*existence* of the marker is the bug.

## Patterns

### Class 1: Standard stub comments

```
// TODO
// TODO:
// FIXME
// FIXME:
// XXX
// HACK
// NOTE: temporary
// TBD
// To be done
// To be implemented
// Implement later
// Coming soon
```

Detection:

```bash
rg -n '^\s*(//|#|--)\s*(TODO|FIXME|XXX|HACK|TBD)\b' --type-add 'src:*.{py,rs,ts,js,go,rb}' --type src
```

### Class 2: Hedging comments (deferral language)

These are softer than TODO but signal the same thing:
"this is not final."

```
// for now,
// for the moment,
// this should work
// this should work in most cases
// works for now
// good enough for now
// placeholder
// dummy data
// dummy value
// stub
// mock implementation
// fake data
// quick and dirty
// hack
// kludge
// workaround
// work around (without "for X" specifier)
// not sure if this is right
// might need to revisit
// revisit later
```

The diagnostic phrase is "for now": every "for now"
needs to either become "permanent" or be deleted.

### Class 3: Stub constructs in code

Language-specific constructs that the runtime treats as
explicit "not implemented":

```python
# Python
raise NotImplementedError
raise NotImplementedError("...")
pass  # in a body that should do something
def foo(): ...  # body is just `...`
```

```rust
// Rust
todo!()
todo!("...")
unimplemented!()
unimplemented!("...")
panic!("not implemented")
panic!("TODO")
```

```typescript
// TypeScript / JavaScript
throw new Error("not implemented");
throw new Error("TODO");
return null as any;  // placeholder cast
```

These in any code path reachable from a public API are
defects with high blast radius. Detect by:

```bash
rg -n 'todo!\(|unimplemented!\(|NotImplementedError|throw new Error\("(?:TODO|not implemented)' .
```

### Class 4: Magic constants flagged as arbitrary

```rust
let limit = 100;        // arbitrary
let timeout = 5000;     // tune later
let max_retries = 3;    // why 3?
const BUFFER: usize = 4096;  // seems reasonable
```

Comments that admit the constant was guessed are stubs.
Either:
- Determine the right value (benchmark, requirement, spec).
- Make the constant configurable.
- Delete the comment if the value really is arbitrary
  (and accept that it can be revisited any time).

## Hedging in prose

The same "for now" / "should work" pattern shows up in
markdown documentation, commit messages, and PR
descriptions. Flag these with the same severity:

```
"this should work in most cases"
"for now, we recommend"
"this is a temporary workaround"
"this is a placeholder until"
"this approach may not scale"
"may need to revisit"
"good enough for now"
"works in our environment"
```

Each one tells the reader the documented behavior is
provisional. Either:
- Make it not provisional (commit to the design).
- Document the actual constraint ("works for inputs
  under 1MB; for larger inputs use the streaming API").
- Delete the section.

## Output format

```
[FINDING N]
file:        src/auth.rs
line:        142
category:    stub-and-deferral/bare-todo
severity:    medium
confidence:  high
evidence:    >    // TODO: handle expired tokens
rationale:   Bare TODO with no tracked issue, in a code
             path that handles authentication. Current
             behavior on expired tokens: silent success:
fix:         Either:
             1. Implement the expired-token branch and
                delete the TODO.
             2. Open issue, change to `// TODO(#NNNN):
                handle expired tokens`.
             3. Add an explicit early return + 401 if
                the design is "fail closed".
```

## Configuration: allowed bare TODOs

Some teams allow bare TODOs in non-production paths
(experiments, examples, local scripts). Configure path
exclusions in the slop-detector config:

```yaml
stub-and-deferral:
  allow_bare_todo:
    - "examples/**"
    - "scratch/**"
    - "tests/fixtures/**"
  require_tracked_issue:
    - "src/**"
    - "lib/**"
```

The default is strict: every TODO in `src/` requires a
tracked issue link.

## Special cases

- `unreachable!()` is *not* a stub if the surrounding
  code makes the unreachability provable. Treat it as
  asserting an invariant, not deferring work.
- A `// TODO:` with a name attached (`// TODO(alice):`)
  is conventionally a deferred assignment, not a stub.
  Whether you accept this depends on team convention.
- Generated code (build.rs output, prost/tonic, codegen
  templates) should be excluded from this scan: it
  legitimately contains placeholder patterns.

## Integration

Runs as part of the cleanup workflow Pass 2 (hallucination
& stubs sweep). The "tracked-issue" check should run in
CI, not just locally: a bare TODO that compiles is a
bare TODO that ships.
