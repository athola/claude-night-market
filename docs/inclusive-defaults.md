# Inclusive Defaults Policy

**Status:** project policy as of 1.9.3
**Audit:** [#445](https://github.com/athola/claude-night-market/issues/445)

## The principle

Defaults are a form of accessibility. Most users never read
flags they don't already know about, so opt-in features
functionally don't exist for them. We default features ON
and expose `--no-X` (or equivalent) for opt-out.

The 1.9.x cycle established the pattern. This doc codifies
it as ongoing project policy and lists the TRUE-exception
surfaces where opt-in must stay.

## The rule

When adding a new feature flag, ask three questions in
order:

1. **Does this feature affect the user's workflow when on
   by default?** If yes, would a typical user want it?
   - If they would: default ON, expose `--no-X`
   - If they would not: rethink the feature; defaults are
     not the place to hide opinions
2. **Does the feature have a side effect outside Claude
   Code's process?** (writes to GitHub, hits external
   APIs, installs OS-level state, etc.)
   - If yes: see TRUE-exception checklist below
3. **Is the feature heavy (time, tokens, install)?**
   - If yes: see TRUE-exception checklist below

If the answer to #1 is "users want it" and #2 and #3 are
both "no": flip to default ON.

## The TRUE-exception checklist

A feature may stay opt-in only if at least one of the
following is true. Any other reason ("users might be
surprised", "what if they don't want it", "we should be
conservative") is not sufficient.

### 1. Heavy install footprint

The feature requires non-trivial install work that should
not happen on plugin install alone. Examples:

- Provisioning a separate Python venv
- Downloading a model file (>10MB)
- Starting a background daemon

**Current examples:**

- `oracle:setup` — provisions Python 3.11+ venv, installs
  onnxruntime (~50MB), starts background HTTP daemon

### 2. Irreversible or hard-to-reverse state

The feature triggers an action whose effect persists
outside the session and is not trivial to undo. Examples:

- Merging a PR (revert PR is messy and visible in
  history)
- Force-pushing
- Deleting branches or files
- Modifying CI/CD pipelines

**Current examples:**

- Egregore `pipeline.auto_merge` — merges PRs without
  human review; the entry point (`/egregore:summon`) is
  already opt-in, so auto-merge gates the no-human-loop
  transition specifically

### 3. No reasonable default value exists

The feature requires user-supplied configuration that
cannot be predicted (URLs, API keys, file paths).
Flipping the default is impossible, not just unwise.

**Current examples:**

- Egregore Tier 2 webhooks (Slack/Discord/ntfy.sh) — no
  reasonable default URL
- Conjure delegation (Gemini/Qwen CLIs) — requires
  external CLI authentication

### 4. OS-level or cross-process state changes

The feature installs persistent OS state that survives
beyond the Claude Code session. Examples:

- launchd plist or systemd unit files
- Cron entries
- Cross-process screenshots or input synthesis

**Current examples:**

- `egregore:install-watchdog` — installs OS-level
  launchd plist or systemd unit
- `phantom:control-desktop` — Computer Use API takes
  screenshots and synthesizes keyboard/mouse input

### 5. User-project config that overrides intent

The feature applies project-level rules that would
override what the user set up. Auto-applying defaults
here erases user intent.

**Current examples:**

- `/spec-kit:speckit-constitution` — auto-applying every
  marketplace constitution would override user project
  rules

### 6. Per-rule consent for hooks that block

When a feature consists of many sub-features that each
can interrupt commands, consent should be per-sub-feature,
not per-feature.

**Current examples:**

- Hookify rules — each rule is an individual hook;
  bundling all of them ON would block legitimate
  commands. The `safe-defaults` bundle (1.9.3) bundles
  only `action: warn` rules.

### 7. Full-codebase scans or expensive analysis

When a feature processes the whole codebase, opt-in is
appropriate to control compute. Default to a smaller
tier; require explicit escalation.

**Current examples:**

- `pensive:tiered-audit` Tier 3 — full-codebase scan;
  Tier 1 (git history) is the inclusive default,
  Tier 3 requires explicit user approval
- `.claude/rules/plan-before-large-dispatch.md` — 4+
  parallel agents requires plan mode

### 8. Block-mode enforcement of soft constraints

When a feature can warn or block, defaulting to block
interrupts legitimate workflows. Shadow/warn mode IS the
inclusive default; block mode is the opt-in.

**Current examples:**

- Imbue vow hooks — `VOW_SHADOW_MODE=1` (warn) is the
  inclusive default; set `VOW_SHADOW_MODE=0` to block

### 9. Frontmatter-controlled prescriptive modes

When a skill has advisory and prescriptive variants, the
inclusive default is advisory (no setup); prescriptive
mode requires per-skill consent via frontmatter.

**Current examples:**

- `leyline:utility` advisory mode (default) vs
  prescriptive mode (frontmatter-controlled)

## How to apply this when adding a feature

When adding a flag to a command, skill, or hook, work
through this short checklist:

1. Pick the flag name in the form `--feature-name`
2. Default the flag to ON (`enabled: true`,
   `default=True`, etc.)
3. Provide an opt-out path:
   - For commands: `--no-feature-name`
   - For env vars: `FEATURE_NAME=0`
   - For configs: `feature_name: false`
4. Document the default-ON status in the command/skill/
   hook doc, with the opt-out flag listed prominently
5. Add a CHANGELOG entry under "Changed" naming the new
   default
6. If the feature falls into a TRUE-exception category,
   document which one in the feature's doc

## When in doubt

If a feature feels like it might be a TRUE exception but
doesn't cleanly fit one of the nine categories, it
probably belongs in default-ON territory. The categories
exist to capture genuinely unsafe defaults, not to
provide cover for "I'm not sure".

The branch name `inclusive-default-1.9.3` reflects the
guiding principle: defaults are accessibility. Flags the
user has to discover are not really there.

## Audit history

The 1.9.3 audit ran the FLIP / KEEP / DOC classifier across
all 23 plugins on the `inclusive-default-1.9.3` branch
(see #445). Outcomes are captured by category:

- **DOC entries** folded into per-plugin READMEs and
  command docs as part of the 1.9.3 release commits.
- **FLIP entries** that shipped: hookify `safe-defaults`
  rule bundle (default-ON warn-only set); spec-kit TDD
  task generation under reconsideration for a future
  release.
- **KEEP entries** are codified in the nine TRUE-exception
  categories above. Each remains opt-in by design.

## References

- [Audit checklist (#445)](https://github.com/athola/claude-night-market/issues/445)
- 1.9.2 CHANGELOG — first wave of inclusive flips
  (`--no-insights`, `--no-agent-teams`, etc.)
- 1.9.3 CHANGELOG — `safe-defaults` bundle and policy
  doc itself
