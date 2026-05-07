# ADR-0011: Shared Session-Capture Envelope for Friction and Trace Data

**Date**: 2026-05-06
**Status**: Accepted
**Deciders**: Claude Night Market maintainers
**Source**: PR #417 review finding NB6 (issue #422)

## Context

Two skills in the abstract plugin emit per-session JSON payloads that
record signals about Claude's execution behavior:

- ``abstract:friction-detector`` writes "signals" (retry loops,
  re-reads, correction patterns) to
  ``~/.claude/friction/sessions/{date}-{id}.json``
- ``abstract:metacognitive-self-mod`` (via the ``trace-capture``
  module) writes "traces" (tool sequences, decision points,
  outcomes) to ``~/.claude/skills/traces/{trace_id}.json``

The friction-detector SKILL.md states it "Feeds into ...
metacognitive-self-mod," but no shared schema or storage convention
links the two. Today they store side-by-side per-session JSON with
overlapping data shape and disjoint field names. Risk: two
non-interoperable session logs accumulate, duplicating disk usage
and making downstream analysis harder than it needs to be.

PR #417 review finding NB6 surfaced three resolutions:

1. **Shared schema, separate files.** Define a common envelope and
   have both skills emit JSONL into one file per session.
2. **Producer/consumer split.** friction-detector becomes the
   producer (raw signals); metacognitive-self-mod becomes the
   consumer (structured analysis). Single storage path.
3. **Merge.** Consolidate into one skill with two output modes.

## Decision

Adopt **Option 1: Shared envelope, separate files**.

Both skills retain their existing storage paths but wrap their
payload in a common envelope shape so downstream readers (LEARNINGS
aggregation, skill-improver hypothesis lookup, future analytics) can
consume them uniformly.

### Envelope schema (v1)

```json
{
  "schema_version": "session-capture/1",
  "session_id": "{date}-{hash}",
  "timestamp": "2026-05-06T10:30:00Z",
  "source": "friction-detector | trace-capture",
  "payload": { ... source-specific shape ... }
}
```

Fields:

- ``schema_version`` (string, required): identifies envelope shape
  for forward compatibility. ``session-capture/1`` for this ADR.
- ``session_id`` (string, required): stable across all envelopes
  emitted in one Claude session. Format ``{YYYY-MM-DD}-{8-char-hash}``.
- ``timestamp`` (RFC 3339 UTC, required): emit time of the envelope
  itself (not the underlying event).
- ``source`` (string, required): producer name. Permitted values
  ``friction-detector`` and ``trace-capture`` for v1; future
  producers extend this enum and bump ``schema_version`` if the
  envelope itself changes.
- ``payload`` (object, required): producer-specific content.
  friction-detector keeps its existing signal shape under
  ``payload``; trace-capture keeps its existing trace shape under
  ``payload``.

### Storage paths

Unchanged. friction-detector continues to write to
``~/.claude/friction/sessions/`` and trace-capture continues to
write to ``~/.claude/skills/traces/``. Aggregators that want a
unified view glob both directories and decode the envelope.

### Migration path

- Both skills emit envelopes for newly captured sessions starting
  from this ADR's release.
- Existing files (pre-envelope) are left untouched. Downstream
  consumers detect a missing ``schema_version`` field and treat
  legacy files as ``session-capture/0`` with the entire file as
  ``payload``.
- A small helper in ``leyline/src/leyline/`` (future work, not
  blocking) wraps emit and decode so producers do not duplicate
  envelope-construction code.

## Consequences

### Positive

- Downstream readers can iterate both directories with one parser.
- ``schema_version`` gives a clean forward-compatibility hatch.
- Disk format remains JSON (one envelope per file), so existing
  shell-based inspection (``jq``, ``cat``) keeps working.
- No migration required for legacy files.

### Negative

- Two more required fields per emitted file (small overhead,
  ~120 bytes).
- Two skills must stay in sync on the envelope contract; mitigated
  by extracting a shared helper later.

### Neutral

- Choosing separate storage paths over a unified path means
  glob-and-merge is the read pattern. Acceptable given current
  read frequency (LEARNINGS daily aggregation, manual analysis).

## Acceptance criteria

- [x] ADR drafted explaining the chosen split (this document)
- [ ] friction-detector SKILL.md references the envelope schema and
  ``schema_version`` field
- [ ] trace-capture module references the envelope schema and
  ``schema_version`` field
- [ ] Migration path documented for existing per-session files
  (this ADR's "Migration path" section)

## Source

- PR #417 review comment NB6:
  <https://github.com/athola/claude-night-market/pull/417#issuecomment-4308484498>
- Issue #422
