# API Review

This module shows how a progressive-loading hub can drive an API
review without front-loading every checklist, exemplar, and
language convention at once. It is the loading playbook that
sits behind the `pensive:api-review` skill: when reviewing a
public API, decide which detail modules to load and in what
order, instead of pulling in every possible rule.

## Scope

Use this module when:

- The user asks for an API review, design critique, or
  consistency audit.
- The hub skill needs to choose between language-specific or
  style-specific review modules.
- The session has already loaded a generic review skeleton and
  needs to specialize.

For pure design exploration with no existing surface to audit,
load `api-patterns.md` instead. That module covers slicing API
content; this one covers running the review.

## Three-Phase Loading

API review has three phases, and each phase needs a different
module set. Loading all three at once defeats progressive
loading.

### Phase 1: Surface Inventory

Always load. The reviewer needs to know which symbols are
public before anything else. A small inventory module suffices.

```bash
# Find Python public symbols (no leading underscore)
rg --type py '^(class|def) [A-Za-z]' -l

# Find Rust public items
rg --type rust '^pub (fn|struct|enum|trait) ' -l
```

For larger codebases, generate the inventory once into a
session file and refer to it by path rather than reloading
the rg output every turn.

### Phase 2: Exemplar Comparison

Load on demand. Pick exemplars matching the surface style.
For a Python data API, `pandas` and `polars` are reasonable
references. For an HTTP client, `requests` and `httpx`. The
exemplar list is in a separate module so it can be swapped
without rewriting the review skeleton.

### Phase 3: Consistency Audit

Load when discrepancies between surface and exemplars surface.
The audit module enumerates the rules to check: naming
conventions, error types, return shapes, pagination, idempotency,
auth headers. Most reviews do not exercise every rule, so the
audit module itself can be subdivided.

## Loading Decision Table

| Signal | Load |
|--------|------|
| Python files in surface | `python-api-rules.md` |
| Rust files in surface | `rust-api-rules.md` |
| OpenAPI spec found | `openapi-conformance.md` |
| Mentions of pagination | `pagination-rules.md` |
| Mentions of auth | `auth-rules.md` |
| Versioning question | `versioning-policy.md` |

The signals come from user input, scanned files, and earlier
review turns. Cache the signal set per session so the loader
does not re-scan the working tree on every check.

## Example Loading Trace

A user asks: "Review the public functions in
`plugins/abstract/scripts/skills_auditor.py`."

```text
turn 1: load surface-inventory.md (always)
        run rg for public defs in skills_auditor.py
turn 2: load python-api-rules.md (Python file detected)
turn 3: detect inconsistent return types
        load consistency-audit.md
turn 4: user asks "what about errors?"
        load error-envelopes.md
```

Modules from later turns stay loaded until the session ends or
context pressure forces eviction (see `advanced-patterns.md`).

## Pitfalls

1. **Loading every language module up front**: A Python-only
   review does not need Rust rules. Detect language before
   loading.
2. **Skipping inventory**: Reviews without an explicit surface
   list drift into general code review. Always anchor in the
   inventory phase.
3. **Stale exemplars**: Library APIs evolve. If your exemplar
   module references a function signature that no longer exists
   in the upstream library, the review produces wrong findings.
   Date-stamp exemplar modules.
4. **Re-running rg every turn**: Inventory output is stable
   across the session unless the working tree changes. Cache it.
5. **One mega-rules module**: A 2000-token rule list violates
   the token target in `performance-budgeting.md`. Split by
   language and concern.

## Cross-Reference

See `api-patterns.md` for slicing API spec content and the
parent `SKILL.md` for the hub-and-spoke pattern these review
phases plug into.
