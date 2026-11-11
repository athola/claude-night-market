# ADR-0029: Trust-Based Delivery Keeps PRs as the Human Gate

**Date**: 2026-11-11
**Status**: Accepted
**Deciders**: Claude Night Market maintainers

## Context

A small product team published how it ships. Everyone pushes to main,
with machine review before the push and human review after it. Anyone
can start a release, which announces itself in Slack and waits 15
minutes, and anyone can pause it inside that window. Platform clients
ship features independently, and review after the fact finds where
they diverge. The team says every part of it rests on reciprocity:
you fix your own mess, someone fixes it if you do not, and you do the
same for them.

The maintainer wanted these plugins to support that way of working,
and kept one part out. Pull requests stay as the human review of code
entering main. The rest is adapted around them.

A `tome:research` pass checked the mechanisms this depends on.

- GitHub's own wait timer is not the countdown. It runs 1 to 43,200
  minutes, administrators can bypass it by default, and on the Free,
  Pro and Team plans it exists only for public repositories
  ([GitHub docs](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)).
  Nothing in it lets anyone pause.
- Ship/Show/Ask ([Wilsenach](https://www.martinfowler.com/articles/ship-show-ask.html))
  is the published form of "open a PR when you are outside your lane".
  With every change going through a PR, the useful half here is who
  reviews it.
- No commit in this repository carries a `Fixes:` trailer, so a ledger
  of who fixes whose work would measure nothing yet.

## Decision

1. **Machine review before the PR, humans in it.** `sanctum:pr-prep`'s
   self-review runs a machine review of the diff before the PR opens.
2. **Outside your lane, name a reviewer who is in it.**
   `plugins/sanctum/scripts/review_routing.py` reads the diff and the
   history of each directory it touches. Where the author has no
   recent commits and others do, it suggests the people who do, by
   name. CODEOWNERS rules take precedence, because GitHub already
   requests those reviewers.
3. **A release countdown anyone can pause and nobody can skip.**
   `plugins/herald/scripts/release_countdown.py` announces the release,
   waits, and checks for an open issue carrying a pause label. It has
   no skip flag. A failed announcement or a failed pause lookup stops
   the release, because a window nobody saw gives nobody a chance.
   This repository's publish workflow runs it only when the
   `RELEASE_COUNTDOWN_MINUTES` repository variable is set.
4. **Divergence found after the fact.** pensive's `parity-sweep`
   workflow inventories features per platform root and reports each
   mismatch with file evidence.

## Consequences

- Who may pause is who may label issues, which is triage access or
  higher. An issue template that applied the label itself would let
  anyone pause a public repository's release, so none does.
- A paused run triggered by a tag leaves the tag pushed. Re-running the
  workflow starts a new countdown.
- Reviewer suggestions come from commit history, so a directory with no
  history gets none, and a new contributor is outside every lane.
- The parity sweep reports. It changes nothing and does not decide
  which platform is right.
