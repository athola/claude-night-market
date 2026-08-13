<!--
Title: name what breaks.
"Replace generate_pdf() with Resume.to_pdf()".

The External half of the Where row and the Migration guide are not
optional in this template.
-->

| | |
|---|---|
| **Who** | <!-- every consumer that has to change, and who owns them --> |
| **Where** | <!-- internal: module + file count. External: REQUIRED. Name every API, wire format, CLI contract, or schema that breaks --> |
| **When** | <!-- landing date, deprecation window, and the release that removes the old path --> |

## Why

<!-- Why the break is worth its cost to consumers. A break needs a
reason a downstream owner would accept. -->

## What and how

<!-- The change, and the compatibility strategy: shim, dual-write,
versioned endpoint, or hard cut. Say which and why. -->

## Migration guide

**Before:**

```
<!-- old call -->
```

**After:**

```
<!-- new call -->
```

<!-- Any automated migration path (codemod, script), or state that
migration is manual. -->

## Test plan

1. `make test`: <!-- N/N passing -->
2. Old path still works through the shim: <!-- command -->
   Expected: <!-- result, plus the deprecation warning -->
3. New path: <!-- command --> Expected: <!-- result -->
4. Downstream check: <!-- how a consumer was verified, or which
   consumer owner signed off -->

## Checklist

- [ ] Every breaking consumer named in the Where row
- [ ] Migration guide shows a working before and after
- [ ] Deprecation window stated in the When row
- [ ] CHANGELOG entry under a breaking-change heading
- [ ] Downstream owners notified
