# Review Protocol

Run only after ALL skills exist. Authoring agents work in isolation
and cannot see each other's contradictions; the review phase is
where the library becomes one coherent artifact.

## Reviewers

Three parallel reviewers over the complete set, then one fixer.
Keep concurrency at three or fewer unless the dispatch was planned
and approved (see the repo's dispatch rules if it has them).

| Lens | Checks | Blocking when |
|------|--------|---------------|
| FACTUAL | Re-verify flags, paths, commands, and citations against the repo; run each skill's provenance one-liners. | A wrong command, nonexistent path, or invented claim would send an engineer down a wrong path. |
| DOCTRINE | Contradictions with the project's own rules or between skills; overstated claims; missing gating on anything that changes behavior. | Guidance routes around change control or two skills disagree on the same fact. |
| USABILITY | Trigger quality of descriptions; duplication (one home per fact, cross-references elsewhere); self-containedness; scannability. | A description would never fire, or a fact's only home is a private path. |

## Severity Ladder

- `blocking`: would send an engineer down a wrong path. Must be
  fixed before the mission reports done.
- `important`: misleading, drifted, or overstated. Fixed by the
  fixer in the same pass.
- `minor`: cosmetic. Recorded, not necessarily fixed.

## Reviewer Output Contract

```yaml
output_contract:
  required_sections: [summary, findings]
  finding_fields: [file, claim, evidence, severity, fix]
  min_evidence: command run plus output excerpt per finding
  strictness: strict
```

## Fixer

One agent, sequential, after all reviewers return:

- Applies blocking and important findings only.
- Re-verifies each finding before editing (re-run its evidence
  command); skips with a recorded reason if it does not reproduce.
- Same write fence as authoring: edits only inside
  `.claude/skills/`, no mutating git commands.
- Preserves each skill's voice, frontmatter validity, and the
  repo's markdown formatting rules.

## Why the Barrier Is Correct Here

The fixer needs ALL findings at once: duplicates across lenses must
be merged before editing, and a zero-finding review should skip the
fixer entirely. This is one of the few places a full barrier between
stages beats a pipeline.

## Final Report

The mission ends with a report to the user containing:

- [ ] The skill inventory with one-line descriptions
- [ ] What was verified by spot-check, with evidence references
- [ ] What remains uncertain, labeled open or candidate
