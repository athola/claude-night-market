# Research Protocol

Step 2 of the sweep. Runs only when drift detection exited `1`.

The detector proves what changed locally. It cannot say what a release
actually did. This step establishes that, and every claim it produces
must carry a source before the sweep acts on it.

## Mandatory sources

Two sources are required for every run. A findings set missing either
one is incomplete, and the sweep does not proceed on it.

| Source | What it settles |
|--------|-----------------|
| Release notes | What shipped, what broke, what was deprecated |
| Model card | Context window, training cutoff, tier positioning, intended use |

For a harness release, the release notes are the changelog for the
version in `harness.version`. For a model release, the model card is
the authoritative statement of the model's shape, and the release notes
say how the harness exposes it.

Read both before forming any conclusion. The release notes say what
changed. The model card says what the thing now is. A sweep driven by
only one of them updates syntax without updating judgment, which is how
a repo ends up pinning a new model to the tier the old one occupied.

Additional channels are optional and add context, never authority:
community discourse, migration guides, and the harness binary's own
help output.

## Channel selection

Check for the tome plugin on disk rather than assuming it:

```bash
test -d plugins/tome && echo "tome available" || echo "fall back to web"
```

### When tome is installed

```
Skill(tome:research)
```

Build the query from the drift report, not from memory. A harness
version bump asks a different question than a model release.

| Drift class | Query shape |
|-------------|-------------|
| `harness` | "Claude Code <old> to <new> changelog, breaking changes, new hook events" |
| `vocabulary` | "<model name> release notes model card tier positioning" |
| `unknown_tier` | "<tier> model card context window intended use" |

Tome dispatches parallel channel agents and returns ranked findings
with sources. Point it at release notes and model cards explicitly, or
the discourse channels will dominate the ranking.

### When tome is absent

Fall back to `WebSearch` and `WebFetch` directly. The fallback must
still cover both mandatory sources:

1. `WebSearch` for the release notes and the model card by name.
2. `WebFetch` each authoritative URL and read it rather than trusting
   the search snippet.
3. Record the URL beside each claim.

The fallback is narrower than tome, not weaker. It reaches the same two
required sources by a shorter path.

## Evidence bar

Every finding carries a source URL. Claims without one are dropped,
per the repo evidence bar. This matters more here than in most
research because the output drives edits across 24 plugins, and a
hallucinated capability becomes a hallucinated pin.

Two failure modes to watch for specifically:

- **Assumed continuity.** A new model in a family does not inherit the
  previous model's context window, pricing, or tier fit. Read the card.
- **Assumed symmetry.** A harness release that adds a field does not
  necessarily keep the old one working. Read the notes.

## Output

Produce a findings table the sweep can consume directly:

| Finding | Source | Asset classes implicated | Confidence |
|---------|--------|--------------------------|------------|

`Asset classes implicated` uses the vocabulary in
`modules/asset-sweep.md`. A finding that implicates nothing is still
recorded, because "this changed and touches none of our assets" is a
useful result and stops the next run re-researching it.
