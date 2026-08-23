# Skill Triage, August 2026

Inbound-reference counts for all 209 registered skills, with a verdict
per skill. **Nothing in this document has been deleted.** It exists so
the decision is yours and the evidence is in one place.

## How to read it

`Refs` counts mentions of `plugin:skill` anywhere in `plugins/` and
`.claude/`, excluding the skill's own directory. It measures whether
anything routes to a skill, which is a proxy for reachability and not
for worth.

The proxy fails in a specific way worth knowing before acting on it:
**a family of skills reached through a router shows zero references
each.** The nine `archetypes:architecture-paradigm-*` entries at zero
are reachable through `archetypes:architecture-paradigms`, which picks
one and hands off. They are not dead. Check for a router before
deleting anything in a family.

| Verdict | Meaning |
|---------|---------|
| KEEP | 5+ inbound references. Something routes here; removing it breaks callers |
| REVIEW | 1-4 references. Reachable but lightly used. Read it and decide |
| CANDIDATE | 0 references. Nothing routes here. Check for a router, then decide |

## Distribution

| Refs | Skills |
|------|-------:|
| 0 | 21 |
| 1 | 16 |
| 2-4 | 50 |
| 5-14 | 77 |
| 15+ | 45 |

122 of 209 skills have 5 or more inbound references. The graph is
better connected than a 217-skill count suggests, which is an argument
against a large indiscriminate cull.

## What the duplication baseline says

[GitSkills](https://arxiv.org/abs/2608.10906) (MSR '27) mined 3,797,117
`SKILL.md` files from 282,200 public repositories and grouped them into
1,877,981 distinct contents. Slightly over half of every skill file on
public GitHub is a byte-identical copy of another one, because the
format has no registry and spreads by copying folders.

This repository was measured against that baseline:

| Measure | Here | Public GitHub |
|---------|-----:|--------------:|
| Skill markdown files | 759 | 3,797,117 |
| Distinct contents | 759 | 1,877,981 |
| Byte-identical copies | 0% | 50.5% |
| Near-duplicate bodies, frontmatter stripped | 0 groups | not reported |

Zero. That matters for what to do next: the dominant failure mode in
this ecosystem is copied sediment nobody prunes, and it is not the
failure mode here. Whatever is wrong with 209 skills, it is not that
they are each other.

An argument for a large cull has to rest on something else, and the
reference distribution above is the place to look rather than a raw
count.

## Overlap with superpowers

superpowers stays installed. The question is where this repository
restates what it already provides.

Measured two ways, on SKILL.md bodies with frontmatter and code blocks
stripped, comparing word bags by Jaccard similarity:

| Comparison | Pairs above 0.22 | Highest |
|------------|-----------------:|---------|
| This repo against superpowers | 0 | 0.17, `sanctum:test-updates` against `test-driven-development` |
| This repo against itself, across plugins | 1 | 0.25, `leyline:pytest-config` against `parseltongue:python-testing` |

Both results are lower than expected and worth stating plainly: there
is no large body of duplicated skill text here to cut. The repository
already defers to superpowers in 14 skills and 172 references, with
`brainstorming`, `systematic-debugging`, `writing-plans` and
`test-driven-development` the most cited.

The one pair worth looking at internally turned out not to be
redundant. `leyline:pytest-config` is infrastructure configuration and
`parseltongue:python-testing` is testing practice; they already
cross-reference each other and the boundary is stated in both. The
similarity is shared pytest vocabulary.

The single real case was `sanctum:test-updates`, which declared
`superpowers:test-driven-development` as a dependency and shipped a
140-line generic restatement of RED-GREEN-REFACTOR beside it. That
module is now 53 lines and carries only what is local: that generated
tests are supposed to fail, and how to tell a real RED from a broken
test. Everything general defers.

`abstract:methodology-curator` was checked and left alone. Its modules
look like duplicates by filename (`debugging.md`, `testing.md`,
`code-review.md`) but are literature surveys of named methodologies,
Zeller's delta debugging among them, rather than workflows. A survey
of prior art is not a second copy of a procedure.

## Already removed

Deleted in this branch, with all references repaired:

| Asset | Refs | Why |
|-------|-----:|-----|
| `abstract:bulletproof-skill` (command) | 7 | Its stated purpose was hardening skills "against rationalization and bypass behaviors" |
| `shared-modules/enforcement-language.md` | 7 | The tiered intensity ladder, duplicated from `enforcement-patterns.md` |
| `shared-modules/iron-law-interlock.md` | 4 | Ceremonial declarations: "Iron Law Checkpoint: I am about to create [filename]" |
| `shared-modules/anti-rationalization.md` | 21 | Replaced by `skill-selection-judgment.md` |

None of these had zero references, so none met the strict auto-delete
bar. They were removed because their subject matter is the doctrine
`.claude/rules/bounded-autonomy.md` retires, and their references were
mechanical to repair.

## Recommended, not executed

| Asset | Refs | Note |
|-------|-----:|------|
| `shared-modules/iron-law-enforcement.md` | 8 | **Recommendation withdrawn.** A split was proposed here before the file was read closely. It is a reference document carrying substantive TDD content: BDD structure, cargo-cult anti-patterns, coverage and mutation requirements, git-history verification. Its self-check was reframed from a gate into diagnostics and its "Enforcement Levels" heading now says what those levels are, which is the change it actually needed |
| `superpowers:*` (external plugin) | - | You said you have not used it in months. Disabling a plugin is reversible; deleting skills is not. Start there |
| `conserve:action-first-output` | 1 | 297 lines for an output-formatting preference |
| `abstract:friction-detector` | 1 | 220 lines, one caller |
| `sanctum:tutorial-updates` | 1 | 626 lines, one caller. Largest lines-per-reference ratio in the repo |

## The ones worth keeping regardless

The five most-referenced skills carry the repository's actual
conventions rather than general practice:

| Skill | Refs |
|-------|-----:|
| `imbue:proof-of-work` | 197 |
| `scribe:slop-detector` | 115 |
| `sanctum:git-workspace-review` | 66 |
| `imbue:review-core` | 63 |
| `attune:project-init` | 63 |

## Full table

| Skill | Refs | Lines | Verdict |
|-------|-----:|------:|---------|
| `archetypes:architecture-paradigm-cqrs-es` | 0 | 84 | CANDIDATE |
| `archetypes:architecture-paradigm-event-driven` | 0 | 83 | CANDIDATE |
| `archetypes:architecture-paradigm-functional-core` | 0 | 85 | CANDIDATE |
| `archetypes:architecture-paradigm-layered` | 0 | 113 | CANDIDATE |
| `archetypes:architecture-paradigm-microkernel` | 0 | 82 | CANDIDATE |
| `archetypes:architecture-paradigm-pipeline` | 0 | 79 | CANDIDATE |
| `archetypes:architecture-paradigm-serverless` | 0 | 82 | CANDIDATE |
| `archetypes:architecture-paradigm-service-based` | 0 | 82 | CANDIDATE |
| `archetypes:architecture-paradigm-space-based` | 0 | 84 | CANDIDATE |
| `attune:dorodango` | 0 | 142 | CANDIDATE |
| `conserve:agent-expenditure` | 0 | 86 | CANDIDATE |
| `conserve:compression-strategy` | 0 | 180 | CANDIDATE |
| `conserve:context-map` | 0 | 163 | CANDIDATE |
| `conserve:elegant-code` | 0 | 201 | CANDIDATE |
| `conserve:smart-sourcing` | 0 | 174 | CANDIDATE |
| `leyline:deferred-capture` | 0 | 132 | CANDIDATE |
| `leyline:utility` | 0 | 148 | CANDIDATE |
| `memory-palace:digital-garden-cultivator` | 0 | 167 | CANDIDATE |
| `parseltongue:python-async` | 0 | 96 | CANDIDATE |
| `parseltongue:python-packaging` | 0 | 168 | CANDIDATE |
| `sanctum:file-analysis` | 0 | 63 | CANDIDATE |
| `abstract:friction-detector` | 1 | 220 | REVIEW |
| `abstract:methodology-curator` | 1 | 136 | REVIEW |
| `archetypes:architecture-paradigm-client-server` | 1 | 76 | REVIEW |
| `archetypes:architecture-paradigm-microservices` | 1 | 117 | REVIEW |
| `archetypes:architecture-paradigm-modular-monolith` | 1 | 92 | REVIEW |
| `attune:precommit-setup` | 1 | 243 | REVIEW |
| `conserve:action-first-output` | 1 | 297 | REVIEW |
| `conserve:cpu-gpu-performance` | 1 | 119 | REVIEW |
| `gauntlet:gauntlet-curate` | 1 | 128 | REVIEW |
| `imbue:workflow-monitor` | 1 | 256 | REVIEW |
| `memory-palace:memory-palace-architect` | 1 | 157 | REVIEW |
| `memory-palace:palace-index-curator` | 1 | 227 | REVIEW |
| `memory-palace:session-handoff` | 1 | 204 | REVIEW |
| `sanctum:tutorial-updates` | 1 | 626 | REVIEW |
| `scribe:doc-importer` | 1 | 117 | REVIEW |
| `spec-kit:speckit-orchestrator` | 1 | 137 | REVIEW |
| `archetypes:architecture-paradigm-hexagonal` | 2 | 85 | REVIEW |
| `attune:architecture-aware-init` | 2 | 166 | REVIEW |
| `cartograph:code-communities` | 2 | 122 | REVIEW |
| `conjure:codex-delegation` | 2 | 142 | REVIEW |
| `conjure:glm-delegation` | 2 | 161 | REVIEW |
| `conjure:minimax-delegation` | 2 | 168 | REVIEW |
| `conjure:muse-delegation` | 2 | 159 | REVIEW |
| `conjure:opencode-delegation` | 2 | 146 | REVIEW |
| `gauntlet:onboard` | 2 | 53 | REVIEW |
| `imbue:latent-space-engineering` | 2 | 112 | REVIEW |
| `leyline:storage-templates` | 2 | 181 | REVIEW |
| `memory-palace:palace-diagram` | 2 | 125 | REVIEW |
| `phantom:computer-control` | 2 | 179 | REVIEW |
| `sanctum:session-management` | 2 | 236 | REVIEW |
| `scribe:voice-learn` | 2 | 220 | REVIEW |
| `archetypes:architecture-paradigm-domain-driven` | 3 | 231 | REVIEW |
| `attune:workflow-setup` | 3 | 212 | REVIEW |
| `cartograph:class-diagram` | 3 | 126 | REVIEW |
| `cartograph:workflow-diagram` | 3 | 110 | REVIEW |
| `conserve:decisive-action` | 3 | 197 | REVIEW |
| `conserve:mcp-code-execution` | 3 | 250 | REVIEW |
| `gauntlet:graph-search` | 3 | 63 | REVIEW |
| `leyline:progressive-loading` | 3 | 270 | REVIEW |
| `leyline:pytest-config` | 3 | 135 | REVIEW |
| `memory-palace:knowledge-locator` | 3 | 189 | REVIEW |
| `minister:dora-metrics` | 3 | 147 | REVIEW |
| `minister:github-initiative-pulse` | 3 | 75 | REVIEW |
| `sanctum:test-updates` | 3 | 408 | REVIEW |
| `scribe:simplified-technical-english` | 3 | 205 | REVIEW |
| `scribe:style-learner` | 3 | 253 | REVIEW |
| `abstract:shared-patterns` | 4 | 90 | REVIEW |
| `attune:skill-library-mission` | 4 | 161 | REVIEW |
| `cartograph:architecture-diagram` | 4 | 107 | REVIEW |
| `cartograph:data-flow` | 4 | 105 | REVIEW |
| `conjure:gemini-delegation` | 4 | 118 | REVIEW |
| `conjure:qwen-delegation` | 4 | 156 | REVIEW |
| `gauntlet:challenge` | 4 | 74 | REVIEW |
| `gauntlet:curate` | 4 | 36 | REVIEW |
| `hookify:rule-catalog` | 4 | 224 | REVIEW |
| `imbue:assisted-mastery` | 4 | 172 | REVIEW |
| `imbue:vow-enforcement` | 4 | 289 | REVIEW |
| `leyline:evaluation-framework` | 4 | 195 | REVIEW |
| `leyline:service-registry` | 4 | 190 | REVIEW |
| `leyline:stewardship` | 4 | 149 | REVIEW |
| `minister:release-health-gates` | 4 | 69 | REVIEW |
| `sanctum:workflow-improvement` | 4 | 293 | REVIEW |
| `scribe:session-replay` | 4 | 180 | REVIEW |
| `spec-kit:task-planning` | 4 | 125 | REVIEW |
| `tome:ideate` | 4 | 124 | REVIEW |
| `tome:triz` | 4 | 112 | REVIEW |
| `abstract:metacognitive-self-mod` | 5 | 290 | KEEP |
| `cartograph:call-chain` | 5 | 108 | KEEP |
| `memory-palace:review-chamber` | 5 | 311 | KEEP |
| `memory-palace:session-palace-builder` | 5 | 188 | KEEP |
| `pensive:performance-review` | 5 | 323 | KEEP |
| `sanctum:doc-consolidation` | 5 | 313 | KEEP |
| `sanctum:stack-push` | 5 | 189 | KEEP |
| `scribe:session-to-post` | 5 | 289 | KEEP |
| `scribe:tech-tutorial` | 5 | 178 | KEEP |
| `tome:discourse` | 5 | 56 | KEEP |
| `tome:papers` | 5 | 91 | KEEP |
| `abstract:hook-scope-guide` | 6 | 288 | KEEP |
| `cartograph:dependency-graph` | 6 | 119 | KEEP |
| `conserve:response-compression` | 6 | 244 | KEEP |
| `conserve:token-conservation` | 6 | 105 | KEEP |
| `egregore:uninstall-watchdog` | 6 | 118 | KEEP |
| `gauntlet:graph-build` | 6 | 79 | KEEP |
| `imbue:dependency-verification` | 6 | 149 | KEEP |
| `imbue:graduated-implementation` | 6 | 167 | KEEP |
| `leyline:usage-logging` | 6 | 173 | KEEP |
| `oracle:setup` | 6 | 52 | KEEP |
| `parseltongue:python-testing` | 6 | 95 | KEEP |
| `pensive:api-review` | 6 | 150 | KEEP |
| `sanctum:stack-rebase` | 6 | 242 | KEEP |
| `sanctum:version-updates` | 6 | 115 | KEEP |
| `scribe:voice-generate` | 6 | 188 | KEEP |
| `scribe:voice-review` | 6 | 190 | KEEP |
| `abstract:modular-skills` | 7 | 151 | KEEP |
| `abstract:plugin-review` | 7 | 160 | KEEP |
| `abstract:skill-graph-audit` | 7 | 126 | KEEP |
| `leyline:markdown-formatting` | 7 | 184 | KEEP |
| `leyline:sem-integration` | 7 | 112 | KEEP |
| `parseltongue:python-performance` | 7 | 93 | KEEP |
| `sanctum:commit-messages` | 7 | 143 | KEEP |
| `sanctum:doc-updates` | 7 | 368 | KEEP |
| `scribe:voice-extract` | 7 | 251 | KEEP |
| `tome:export` | 7 | 85 | KEEP |
| `tome:synthesize` | 7 | 52 | KEEP |
| `abstract:rules-eval` | 8 | 120 | KEEP |
| `attune:makefile-generation` | 8 | 172 | KEEP |
| `egregore:install-watchdog` | 8 | 128 | KEEP |
| `gauntlet:extract` | 8 | 62 | KEEP |
| `hookify:writing-rules` | 8 | 287 | KEEP |
| `leyline:loop-optimization` | 8 | 156 | KEEP |
| `memory-palace:memory-clarity-probe` | 8 | 243 | KEEP |
| `pensive:math-review` | 8 | 176 | KEEP |
| `pensive:shell-review` | 8 | 178 | KEEP |
| `sanctum:do-issue` | 8 | 154 | KEEP |
| `spec-kit:spec-writing` | 8 | 113 | KEEP |
| `abstract:subagent-testing` | 9 | 113 | KEEP |
| `sanctum:stack-create` | 9 | 172 | KEEP |
| `sanctum:stack-mode` | 9 | 339 | KEEP |
| `abstract:escalation-governance` | 10 | 284 | KEEP |
| `imbue:catchup` | 10 | 113 | KEEP |
| `leyline:error-patterns` | 10 | 172 | KEEP |
| `leyline:quota-management` | 10 | 148 | KEEP |
| `pensive:blast-radius` | 10 | 150 | KEEP |
| `pensive:harden` | 10 | 323 | KEEP |
| `pensive:makefile-review` | 10 | 197 | KEEP |
| `conserve:bloat-detector` | 11 | 190 | KEEP |
| `pensive:tiered-audit` | 11 | 224 | KEEP |
| `sanctum:update-readme` | 11 | 182 | KEEP |
| `scry:media-composition` | 11 | 312 | KEEP |
| `leyline:content-sanitization` | 12 | 124 | KEEP |
| `leyline:supply-chain-advisory` | 12 | 141 | KEEP |
| `scry:gif-generation` | 12 | 205 | KEEP |
| `conserve:code-quality-principles` | 13 | 319 | KEEP |
| `imbue:diff-analysis` | 13 | 98 | KEEP |
| `imbue:feature-review` | 13 | 401 | KEEP |
| `pensive:test-review` | 13 | 274 | KEEP |
| `tome:code-search` | 13 | 52 | KEEP |
| `archetypes:architecture-paradigms` | 14 | 179 | KEEP |
| `egregore:quality-gate` | 14 | 195 | KEEP |
| `imbue:rigorous-reasoning` | 14 | 214 | KEEP |
| `pensive:architecture-review` | 14 | 295 | KEEP |
| `pensive:unified-review` | 14 | 264 | KEEP |
| `tome:dig` | 14 | 55 | KEEP |
| `attune:project-execution` | 15 | 485 | KEEP |
| `leyline:testing-quality-standards` | 15 | 132 | KEEP |
| `pensive:rust-review` | 15 | 313 | KEEP |
| `leyline:authentication-patterns` | 17 | 187 | KEEP |
| `scry:browser-recording` | 17 | 211 | KEEP |
| `abstract:skill-authoring` | 18 | 203 | KEEP |
| `attune:project-specification` | 18 | 105 | KEEP |
| `leyline:damage-control` | 18 | 175 | KEEP |
| `sanctum:validate-pr` | 18 | 281 | KEEP |
| `attune:war-room-checkpoint` | 19 | 353 | KEEP |
| `imbue:karpathy-principles` | 19 | 260 | KEEP |
| `leyline:document-conversion` | 19 | 174 | KEEP |
| `memory-palace:knowledge-intake` | 19 | 737 | KEEP |
| `pensive:bug-review` | 19 | 230 | KEEP |
| `pensive:safety-critical-patterns` | 19 | 207 | KEEP |
| `attune:project-brainstorming` | 21 | 476 | KEEP |
| `conjure:agent-teams` | 21 | 274 | KEEP |
| `sanctum:pr-prep` | 21 | 215 | KEEP |
| `attune:mission-orchestrator` | 22 | 385 | KEEP |
| `attune:project-planning` | 22 | 124 | KEEP |
| `leyline:additive-bias-defense` | 25 | 142 | KEEP |
| `scry:vhs-recording` | 25 | 110 | KEEP |
| `abstract:skills-eval` | 27 | 168 | KEEP |
| `imbue:justify` | 28 | 421 | KEEP |
| `sanctum:pr-review` | 28 | 663 | KEEP |
| `abstract:hooks-eval` | 29 | 205 | KEEP |
| `leyline:risk-classification` | 29 | 182 | KEEP |
| `conjure:delegation-core` | 30 | 283 | KEEP |
| `egregore:summon` | 30 | 364 | KEEP |
| `leyline:decision-journal` | 31 | 145 | KEEP |
| `scribe:doc-generator` | 31 | 248 | KEEP |
| `conserve:clear-context` | 33 | 403 | KEEP |
| `leyline:git-platform` | 33 | 149 | KEEP |
| `pensive:code-refinement` | 33 | 281 | KEEP |
| `conserve:context-optimization` | 35 | 138 | KEEP |
| `abstract:hook-authoring` | 37 | 737 | KEEP |
| `tome:research` | 52 | 226 | KEEP |
| `imbue:scope-guard` | 57 | 293 | KEEP |
| `imbue:structured-output` | 57 | 138 | KEEP |
| `attune:war-room` | 60 | 514 | KEEP |
| `attune:project-init` | 63 | 177 | KEEP |
| `imbue:review-core` | 63 | 134 | KEEP |
| `sanctum:git-workspace-review` | 66 | 117 | KEEP |
| `scribe:slop-detector` | 115 | 532 | KEEP |
| `imbue:proof-of-work` | 196 | 217 | KEEP |
