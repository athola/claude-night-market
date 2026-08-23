# Skill Triage, August 2026

What was measured about all 209 registered skills, and what those
measurements turned out to be worth. **Nothing in this document has
been deleted on the strength of these numbers**, and the first section
says why that would be a mistake.

Three things were measured. Duplication, which came back clean and is
trustworthy. Overlap with superpowers, which came back small and is
trustworthy. Inbound references, which came back twice with different
answers and is not.

## The reference count does not work, and here is the evidence

The first version of this document ranked skills by inbound reference
count and reported 21 with zero references, marking them CANDIDATE for
deletion. That number was wrong, and so is its replacement. Both are
kept here because the way they fail is the useful part.

**Measure one, qualified references.** Count occurrences of
`plugin:skill` outside the skill's own directory. Result: 21 skills at
zero.

It undercounts. The `archetypes:architecture-paradigms` router names
all fourteen paradigm skills by bare name, not qualified name, so nine
of them scored zero while being demonstrably reachable. Verified
directly: the router file mentions 14 distinct `architecture-paradigm-*`
names and 14 such skills exist.

**Measure two, bare word-boundary names.** Count the skill's directory
name as a whole word anywhere outside its own directory. Result: zero
skills at zero references.

It overcounts, badly, and in a way that is obvious once seen:

| Skill | Bare-name "references" |
|-------|-----------------------:|
| `tome:papers` | 10,571 |
| `tome:research` | 5,315 |
| `gauntlet:extract` | 4,818 |
| `memory-palace:knowledge-intake` | 3,386 |

Those are not references. They are the words "papers", "research" and
"extract" appearing in English prose across the repository.

**What this means.** Reference counting is trustworthy only where the
skill's name is distinctive enough not to collide with ordinary
language. `attune:dorodango` at 4 and `conjure:codex-delegation` at 3
are believable. Anything named after a common noun is unmeasurable
this way, and that is most of the skills worth arguing about.

The measurement that would settle it does not exist. As GitSkills puts
it, a model "selects them probabilistically at run time, and no
compiler or type checker verifies the selection". Reachability in a
skill graph is not a static property, and no amount of grep recovers
it. What would settle it is runtime selection telemetry: which skills
were actually loaded, for which prompts, over a month of real work.

**So this document no longer carries a verdict column.** The full table
below is retained as reference-count data with the caveats above, not
as a recommendation. Deleting a skill on the strength of these numbers
would be acting on a measurement that has now been wrong twice.

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
| `sanctum:tutorial-updates` | 1 | 626 lines. Worth a read on size alone, but "one caller" was the qualified count and should not be trusted on its own |

## The ones the numbers agree about

These five have distinctive names, so the collision problem above does
not reach them, and both measures rank them high. They carry this
repository's own conventions rather than general practice, which is
the property that actually justifies a skill:

| Skill | Refs |
|-------|-----:|
| `imbue:proof-of-work` | 197 |
| `scribe:slop-detector` | 115 |
| `sanctum:git-workspace-review` | 66 |
| `imbue:review-core` | 63 |
| `attune:project-init` | 63 |

## Full table

| Skill | Refs | Lines |
|-------|-----:|------:|
| `archetypes:architecture-paradigm-cqrs-es` | 0 | 84 |
| `archetypes:architecture-paradigm-event-driven` | 0 | 83 |
| `archetypes:architecture-paradigm-functional-core` | 0 | 85 |
| `archetypes:architecture-paradigm-layered` | 0 | 113 |
| `archetypes:architecture-paradigm-microkernel` | 0 | 82 |
| `archetypes:architecture-paradigm-pipeline` | 0 | 79 |
| `archetypes:architecture-paradigm-serverless` | 0 | 82 |
| `archetypes:architecture-paradigm-service-based` | 0 | 82 |
| `archetypes:architecture-paradigm-space-based` | 0 | 84 |
| `attune:dorodango` | 0 | 142 |
| `conserve:agent-expenditure` | 0 | 86 |
| `conserve:compression-strategy` | 0 | 180 |
| `conserve:context-map` | 0 | 163 |
| `conserve:elegant-code` | 0 | 201 |
| `conserve:smart-sourcing` | 0 | 174 |
| `leyline:deferred-capture` | 0 | 132 |
| `leyline:utility` | 0 | 148 |
| `memory-palace:digital-garden-cultivator` | 0 | 167 |
| `parseltongue:python-async` | 0 | 96 |
| `parseltongue:python-packaging` | 0 | 168 |
| `sanctum:file-analysis` | 0 | 63 |
| `abstract:friction-detector` | 1 | 220 |
| `abstract:methodology-curator` | 1 | 136 |
| `archetypes:architecture-paradigm-client-server` | 1 | 76 |
| `archetypes:architecture-paradigm-microservices` | 1 | 117 |
| `archetypes:architecture-paradigm-modular-monolith` | 1 | 92 |
| `attune:precommit-setup` | 1 | 243 |
| `conserve:action-first-output` | 1 | 297 |
| `conserve:cpu-gpu-performance` | 1 | 119 |
| `gauntlet:gauntlet-curate` | 1 | 128 |
| `imbue:workflow-monitor` | 1 | 256 |
| `memory-palace:memory-palace-architect` | 1 | 157 |
| `memory-palace:palace-index-curator` | 1 | 227 |
| `memory-palace:session-handoff` | 1 | 204 |
| `sanctum:tutorial-updates` | 1 | 626 |
| `scribe:doc-importer` | 1 | 117 |
| `spec-kit:speckit-orchestrator` | 1 | 137 |
| `archetypes:architecture-paradigm-hexagonal` | 2 | 85 |
| `attune:architecture-aware-init` | 2 | 166 |
| `cartograph:code-communities` | 2 | 122 |
| `conjure:codex-delegation` | 2 | 142 |
| `conjure:glm-delegation` | 2 | 161 |
| `conjure:minimax-delegation` | 2 | 168 |
| `conjure:muse-delegation` | 2 | 159 |
| `conjure:opencode-delegation` | 2 | 146 |
| `gauntlet:onboard` | 2 | 53 |
| `imbue:latent-space-engineering` | 2 | 112 |
| `leyline:storage-templates` | 2 | 181 |
| `memory-palace:palace-diagram` | 2 | 125 |
| `phantom:computer-control` | 2 | 179 |
| `sanctum:session-management` | 2 | 236 |
| `scribe:voice-learn` | 2 | 220 |
| `archetypes:architecture-paradigm-domain-driven` | 3 | 231 |
| `attune:workflow-setup` | 3 | 212 |
| `cartograph:class-diagram` | 3 | 126 |
| `cartograph:workflow-diagram` | 3 | 110 |
| `conserve:decisive-action` | 3 | 197 |
| `conserve:mcp-code-execution` | 3 | 250 |
| `gauntlet:graph-search` | 3 | 63 |
| `leyline:progressive-loading` | 3 | 270 |
| `leyline:pytest-config` | 3 | 135 |
| `memory-palace:knowledge-locator` | 3 | 189 |
| `minister:dora-metrics` | 3 | 147 |
| `minister:github-initiative-pulse` | 3 | 75 |
| `sanctum:test-updates` | 3 | 408 |
| `scribe:simplified-technical-english` | 3 | 205 |
| `scribe:style-learner` | 3 | 253 |
| `abstract:shared-patterns` | 4 | 90 |
| `attune:skill-library-mission` | 4 | 161 |
| `cartograph:architecture-diagram` | 4 | 107 |
| `cartograph:data-flow` | 4 | 105 |
| `conjure:gemini-delegation` | 4 | 118 |
| `conjure:qwen-delegation` | 4 | 156 |
| `gauntlet:challenge` | 4 | 74 |
| `gauntlet:curate` | 4 | 36 |
| `hookify:rule-catalog` | 4 | 224 |
| `imbue:assisted-mastery` | 4 | 172 |
| `imbue:vow-enforcement` | 4 | 289 |
| `leyline:evaluation-framework` | 4 | 195 |
| `leyline:service-registry` | 4 | 190 |
| `leyline:stewardship` | 4 | 149 |
| `minister:release-health-gates` | 4 | 69 |
| `sanctum:workflow-improvement` | 4 | 293 |
| `scribe:session-replay` | 4 | 180 |
| `spec-kit:task-planning` | 4 | 125 |
| `tome:ideate` | 4 | 124 |
| `tome:triz` | 4 | 112 |
| `abstract:metacognitive-self-mod` | 5 | 290 |
| `cartograph:call-chain` | 5 | 108 |
| `memory-palace:review-chamber` | 5 | 311 |
| `memory-palace:session-palace-builder` | 5 | 188 |
| `pensive:performance-review` | 5 | 323 |
| `sanctum:doc-consolidation` | 5 | 313 |
| `sanctum:stack-push` | 5 | 189 |
| `scribe:session-to-post` | 5 | 289 |
| `scribe:tech-tutorial` | 5 | 178 |
| `tome:discourse` | 5 | 56 |
| `tome:papers` | 5 | 91 |
| `abstract:hook-scope-guide` | 6 | 288 |
| `cartograph:dependency-graph` | 6 | 119 |
| `conserve:response-compression` | 6 | 244 |
| `conserve:token-conservation` | 6 | 105 |
| `egregore:uninstall-watchdog` | 6 | 118 |
| `gauntlet:graph-build` | 6 | 79 |
| `imbue:dependency-verification` | 6 | 149 |
| `imbue:graduated-implementation` | 6 | 167 |
| `leyline:usage-logging` | 6 | 173 |
| `oracle:setup` | 6 | 52 |
| `parseltongue:python-testing` | 6 | 95 |
| `pensive:api-review` | 6 | 150 |
| `sanctum:stack-rebase` | 6 | 242 |
| `sanctum:version-updates` | 6 | 115 |
| `scribe:voice-generate` | 6 | 188 |
| `scribe:voice-review` | 6 | 190 |
| `abstract:modular-skills` | 7 | 151 |
| `abstract:plugin-review` | 7 | 160 |
| `abstract:skill-graph-audit` | 7 | 126 |
| `leyline:markdown-formatting` | 7 | 184 |
| `leyline:sem-integration` | 7 | 112 |
| `parseltongue:python-performance` | 7 | 93 |
| `sanctum:commit-messages` | 7 | 143 |
| `sanctum:doc-updates` | 7 | 368 |
| `scribe:voice-extract` | 7 | 251 |
| `tome:export` | 7 | 85 |
| `tome:synthesize` | 7 | 52 |
| `abstract:rules-eval` | 8 | 120 |
| `attune:makefile-generation` | 8 | 172 |
| `egregore:install-watchdog` | 8 | 128 |
| `gauntlet:extract` | 8 | 62 |
| `hookify:writing-rules` | 8 | 287 |
| `leyline:loop-optimization` | 8 | 156 |
| `memory-palace:memory-clarity-probe` | 8 | 243 |
| `pensive:math-review` | 8 | 176 |
| `pensive:shell-review` | 8 | 178 |
| `sanctum:do-issue` | 8 | 154 |
| `spec-kit:spec-writing` | 8 | 113 |
| `abstract:subagent-testing` | 9 | 113 |
| `sanctum:stack-create` | 9 | 172 |
| `sanctum:stack-mode` | 9 | 339 |
| `abstract:escalation-governance` | 10 | 284 |
| `imbue:catchup` | 10 | 113 |
| `leyline:error-patterns` | 10 | 172 |
| `leyline:quota-management` | 10 | 148 |
| `pensive:blast-radius` | 10 | 150 |
| `pensive:harden` | 10 | 323 |
| `pensive:makefile-review` | 10 | 197 |
| `conserve:bloat-detector` | 11 | 190 |
| `pensive:tiered-audit` | 11 | 224 |
| `sanctum:update-readme` | 11 | 182 |
| `scry:media-composition` | 11 | 312 |
| `leyline:content-sanitization` | 12 | 124 |
| `leyline:supply-chain-advisory` | 12 | 141 |
| `scry:gif-generation` | 12 | 205 |
| `conserve:code-quality-principles` | 13 | 319 |
| `imbue:diff-analysis` | 13 | 98 |
| `imbue:feature-review` | 13 | 401 |
| `pensive:test-review` | 13 | 274 |
| `tome:code-search` | 13 | 52 |
| `archetypes:architecture-paradigms` | 14 | 179 |
| `egregore:quality-gate` | 14 | 195 |
| `imbue:rigorous-reasoning` | 14 | 214 |
| `pensive:architecture-review` | 14 | 295 |
| `pensive:unified-review` | 14 | 264 |
| `tome:dig` | 14 | 55 |
| `attune:project-execution` | 15 | 485 |
| `leyline:testing-quality-standards` | 15 | 132 |
| `pensive:rust-review` | 15 | 313 |
| `leyline:authentication-patterns` | 17 | 187 |
| `scry:browser-recording` | 17 | 211 |
| `abstract:skill-authoring` | 18 | 203 |
| `attune:project-specification` | 18 | 105 |
| `leyline:damage-control` | 18 | 175 |
| `sanctum:validate-pr` | 18 | 281 |
| `attune:war-room-checkpoint` | 19 | 353 |
| `imbue:karpathy-principles` | 19 | 260 |
| `leyline:document-conversion` | 19 | 174 |
| `memory-palace:knowledge-intake` | 19 | 737 |
| `pensive:bug-review` | 19 | 230 |
| `pensive:safety-critical-patterns` | 19 | 207 |
| `attune:project-brainstorming` | 21 | 476 |
| `conjure:agent-teams` | 21 | 274 |
| `sanctum:pr-prep` | 21 | 215 |
| `attune:mission-orchestrator` | 22 | 385 |
| `attune:project-planning` | 22 | 124 |
| `leyline:additive-bias-defense` | 25 | 142 |
| `scry:vhs-recording` | 25 | 110 |
| `abstract:skills-eval` | 27 | 168 |
| `imbue:justify` | 28 | 421 |
| `sanctum:pr-review` | 28 | 663 |
| `abstract:hooks-eval` | 29 | 205 |
| `leyline:risk-classification` | 29 | 182 |
| `conjure:delegation-core` | 30 | 283 |
| `egregore:summon` | 30 | 364 |
| `leyline:decision-journal` | 31 | 145 |
| `scribe:doc-generator` | 31 | 248 |
| `conserve:clear-context` | 33 | 403 |
| `leyline:git-platform` | 33 | 149 |
| `pensive:code-refinement` | 33 | 281 |
| `conserve:context-optimization` | 35 | 138 |
| `abstract:hook-authoring` | 37 | 737 |
| `tome:research` | 52 | 226 |
| `imbue:scope-guard` | 57 | 293 |
| `imbue:structured-output` | 57 | 138 |
| `attune:war-room` | 60 | 514 |
| `attune:project-init` | 63 | 177 |
| `imbue:review-core` | 63 | 134 |
| `sanctum:git-workspace-review` | 66 | 117 |
| `scribe:slop-detector` | 115 | 532 |
| `imbue:proof-of-work` | 196 | 217 |
