# Authoring Rules

Bake every rule below into every authoring agent's prompt. These are
the non-negotiables that made the first run trustworthy; an agent
that skips one produces a skill that is worse than no skill.

## The Rules

1. **Audience**: a zero-context mid-level engineer or Sonnet-class
   model. Imperative runbook voice; copy-pasteable commands; every
   jargon term defined once; tables and checklists over prose. Each
   skill says when NOT to use it and which sibling to use instead.

2. **Format**: `.claude/skills/<name>/SKILL.md` with YAML
   frontmatter containing `name` and a trigger-rich `description`
   stating exactly when a model should load it.

3. **Ground truth only**: verify every command, flag, path, and
   claim against the repo before stating it. Wrong runbooks are
   worse than none. An unverified claim is a finding for the review
   phase, not a sentence in a skill.

4. **Embed knowledge**: do not reference private or user-specific
   paths as load-bearing sources. The skill must work for a reader
   who has only the repository.

5. **Date-stamp volatile facts**, and end each skill with a
   "Provenance and maintenance" section containing one-line
   re-verification commands for anything that may drift.

6. **No oversell**: unproven things stay labeled open or candidate.
   Nothing may contradict the project's own manifest or rules, and
   no skill may route around the project's change control.

7. **Write fence**: authoring agents write ONLY inside
   `.claude/skills/`. The rest of the repo is read-only. No
   mutating git commands.

## Per-Agent Prompt Template

Dispatch one agent per skill. Each prompt supplies:

```text
You are authoring one skill of a project skill library.

SKILL: <name from taxonomy>
CONTENTS: <the taxonomy row, expanded with Phase 1 findings>
DISCOVERY BRIEF: <the Phase 1 summary and the user's answers to
the five questions>

RULES (non-negotiable): <the seven rules above, verbatim>

Verify every claim against the repo before writing it. Return the
path of the SKILL.md you wrote plus a list of claims you could NOT
verify (these go to the review phase).
```

## Output Contract

Every authoring agent must return, in structure or prose:

- `path`: the SKILL.md written
- `verified_claims`: count of claims checked against the repo
- `unverified_claims`: list of claims stated as open or candidate
- `scripts_shipped`: any executables placed in the skill's
  `scripts/` dir

Agents without this contract get no output validation; treat a
missing contract as a review finding.
