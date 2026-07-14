---
name: dependency-verification
description: Verifies a package exists before install, defending against hallucination and slopsquatting. Use when adding, recommending, or installing a package.
alwaysApply: false
category: workflow-methodology
tags:
- dependencies
- supply-chain
- hallucination
- slopsquatting
- verification
dependencies: []
tools: []
usage_patterns:
- pre-install-verification
- supply-chain-defense
- dependency-review
complexity: basic
model_hint: standard
estimated_tokens: 1400
modules:
- modules/registry-checks.md
role: library
---

> A package name the model produced is a claim, not a fact. The
> registry is the fact. Verify before you install.

# Dependency Verification

## Overview

Code-generating language models recommend packages that do not
exist at a measured rate of 5.2% (commercial models) to 21.7%
(open models) across 576,000 samples (Spracklen et al. 2024,
arXiv 2406.10279). Worse, 58% of hallucinated names recur across
reruns, so an attacker can predict them, register the empty name,
and ship malware. This is "slopsquatting." A proof-of-concept
package (`huggingface-cli`) drew over 30,000 downloads after being
registered against a commonly hallucinated name. Package
hallucination is also inversely correlated with coding-benchmark
score, so a better model does not make this go away.

The defense is cheap: confirm the name exists in its registry
before installing or recommending it. This skill defines that
check and is enforced by the `guard_package_hallucination.py`
PreToolUse hook.

## When To Use

Apply before any of these:

- Running `pip install`, `uv add`, `npm install`, `pnpm add`,
  `yarn add`, `cargo add`, `poetry add`, or `pdm add`.
- Writing a dependency into `pyproject.toml`, `requirements.txt`,
  `package.json`, or `Cargo.toml`.
- Recommending a package to the user in prose.

## When NOT To Use

- Bumping versions of packages already known to exist (use
  `sanctum:version-updates`)
- Auditing a dependency's supply chain (use
  `leyline:supply-chain-advisory`)

## The Two Signals

A package fails verification on either signal:

1. **Nonexistent**: the name is absent from its registry. This is
   a likely hallucination. Do not install it. Search for the
   correct name or confirm the package was renamed or removed.
2. **Typosquat / slopsquat**: the name is one or two edits from a
   popular package (for example `reqeusts` versus `requests`).
   This is either a typo or a deliberate impersonation. Confirm
   the exact name you intend before proceeding.

A name that is unknown to the bundled popular-package set but
present in the registry passes. A name that cannot be checked
because the registry is unreachable is reported as `unverified`,
never blocked: the guard does not fail closed on a network error.

## A Confidence Signal, Not a Gate

Registry existence is the pass/fail check. Real-world usage is a
separate, softer signal that builds confidence on top of it. Once a
package clears the two signals above, cross-checking that it is
actually used by other projects raises your confidence that the name
is the established one rather than a freshly-registered impostor that
happens to exist.

Useful confidence signals, none of them blocking:

- GitHub dependents or code search hits for the exact package name
  (an established package is imported across many repositories).
- Repository stars, recent commit activity, and release cadence on
  the package's source.
- Download counts and publish history on the registry (a popular
  name registered yesterday is a red flag; a modest name with years
  of releases is reassuring).

Treat low usage as a prompt to look closer, never as a reason to
reject on its own. New, niche, internal, and private packages are
legitimately low-usage, so a missing GitHub footprint must not block
an install the registry already confirmed. Use this signal to build
confidence and to disambiguate between two similarly-named packages,
not to gate.

## Verification Procedure

1. Extract the exact package names the command or manifest edit
   would fetch (strip version specifiers and flags).
2. For each name, confirm existence in the registry. See
   [registry-checks.md](modules/registry-checks.md) for the
   per-ecosystem endpoints and the offline-degradation rule.
3. For any name close to a popular package, restate the intended
   name and confirm it is the one you meant.
4. Capture the verification as evidence (the registry URL and the
   HTTP status) when the install lands in a PR, per
   `imbue:proof-of-work`.

## Relationship to the Guard Hook

The `guard_package_hallucination.py` hook runs this check
automatically on every Bash install command. Shadow mode (warn
only) is the default; set `VOW_SHADOW_MODE=0` to block
typosquat and nonexistent installs. Disable the network lookup
with `IMBUE_PKG_REGISTRY_CHECK=0` to rely on the offline
typosquat signal alone. The hook is a backstop, not a substitute:
verify deliberately when you add a dependency rather than waiting
for the gate.

## Related Skills

- `imbue:proof-of-work`: capture the registry check as evidence.
- `leyline:supply-chain-advisory`: broader dependency supply-chain
  auditing (lockfile drift, artifact integrity, bad versions).

## Exit Criteria

- [ ] Every package in the install command or manifest edit is
      confirmed present in its registry, or the install is
      abandoned.
- [ ] Any name within two edits of a popular package is restated
      and confirmed before install.
- [ ] A name that could not be verified online is reported as
      unverified and not silently installed.
- [ ] For PR-bound installs, the registry check is captured as
      proof-of-work evidence.
