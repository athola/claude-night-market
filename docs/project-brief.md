# GitHub Discussions as Agent Collective Memory - Project Brief

## Problem Statement

The claude-night-market codebase has three sophisticated but **disconnected** systems:

1. **Decision Machinery** (war room, scope-guard, rigorous-reasoning, ADRs) — produces high-quality deliberation artifacts but stores them only in local strategeion files (`~/.claude/memory-palace/strategeion/`) that are invisible to future sessions and other contributors.

2. **Knowledge Management** (memory-palace) — captures session knowledge, PR review insights, and external research through a rich pipeline (intake queue, marginal value filter, digital garden lifecycle), but all knowledge stays in local files under `plugins/memory-palace/docs/knowledge-corpus/`.

3. **GitHub Integration** (minister, sanctum, leyline) — deep support for issues (`gh issue`) and PRs (`gh pr`, GraphQL mutations) but **zero functional Discussion support**. The 3 `gh discussion` references in minister playbooks use a CLI command that doesn't exist. The leyline command-mapping table omits discussions entirely. The repo has 0 discussions and only default categories.

**The result**: Agent sessions are amnesiac about past deliberations. A war room that spent 30 minutes debating an architecture choice produces a local file that no future session will ever find. A scope-guard deferral creates a GitHub issue but loses the reasoning context. Knowledge captured by memory-palace is trapped in the repo's file tree rather than being searchable and linkable on GitHub.

## Who Experiences This Problem

- **Future agent sessions** that repeat decisions already made because they can't find prior deliberations
- **Contributors** who want to understand *why* architectural choices were made but find only code, not reasoning
- **The codebase itself**, which accumulates local decision files that grow stale without review or promotion

## Current Solutions and Their Limitations

| Current Mechanism | What It Does | What It Lacks |
|---|---|---|
| `MEMORY.md` (auto-memory) | Agent writes notes for itself, loaded at session start | 200-line limit, no structure, no searchability, single-author |
| `docs/adr/` | 6 ADRs documenting architecture decisions | Manual creation only, no automated capture from war room |
| `strategeion/` (war palace) | Stores full war room session artifacts | Local files only, not searchable by `gh`, no cross-session retrieval |
| `review-chamber/` | Captures PR review knowledge | Siloed in memory-palace, not visible on GitHub |
| `knowledge-corpus/` | Stores research intake with evaluation scores | Local files, no promotion path to Discussions |
| `minister` playbooks | Reference `gh discussion create/comment/list` | **Commands don't exist** in gh v2.86.0 — entirely non-functional |

## Goals

1. **Make agent decisions searchable and persistent** — War room deliberations, scope-guard evaluations, and architectural decisions should be published to GitHub Discussions where future sessions can query them via GraphQL.

2. **Enable cross-session learning** — When a new session starts work on an area where a prior deliberation exists, it should automatically surface relevant past discussions.

3. **Bridge local knowledge to the public square** — Memory-palace knowledge that reaches "evergreen" maturity should have a promotion path to Discussions, making it visible to all contributors and future agents.

4. **Fix the broken Discussion integration** — Replace the non-functional `gh discussion` CLI references with working `gh api graphql` wrappers, and extend leyline's platform abstraction to cover Discussions.

5. **Structure the Discussions board** — Create custom categories, structured form templates, and labeling conventions that make the Discussions board a machine-readable knowledge base, not just a human forum.

## Success Criteria

- [ ] War room sessions automatically publish their synthesis to a "Decisions" discussion category
- [ ] Scope-guard deferrals create linked Discussions (not just issues) with full reasoning context
- [ ] New agent sessions query past discussions for relevant prior decisions before proposing new ones
- [ ] Knowledge-corpus entries at "evergreen" maturity can be promoted to Discussions
- [ ] The leyline command-mapping table includes Discussion operations (create, search, comment, answer)
- [ ] `.github/DISCUSSION_TEMPLATE/` contains structured forms for ADR, Deliberation, and Learning categories
- [ ] All minister playbook `gh discussion` references work via GraphQL wrappers
- [ ] At least 3 custom Discussion categories exist beyond the defaults

## Constraints

### Technical
- **`gh` CLI v2.86.0 has no native `discussion` subcommand** — all operations must use `gh api graphql` with the GitHub GraphQL Discussions API
- **GraphQL filtering is limited** — can filter by `categoryId` and `answered` status but NOT by label at the `discussions` query level; must use `search(type: DISCUSSION)` for label-based queries
- **System Python is 3.9.6** — any hook scripts must be compatible (no union types, no `datetime.UTC`, etc.)
- **200-line MEMORY.md limit** — can't dump discussion results into auto-memory; need selective injection

### Architectural
- **leyline abstraction** — Discussion support must go through the git-platform skill to maintain cross-platform compatibility (GitLab has similar "Discussions" in MR threads)
- **Plugin boundaries** — Changes span multiple plugins (leyline, minister, sanctum, attune, memory-palace, imbue) and must respect their separation of concerns
- **Existing hook budget** — 20 hooks already registered; adding more should be justified by clear value

### Process
- **Human approval for publishing** — Agent decisions should require user confirmation before posting to public Discussions (similar to how memory-palace requires curator approval for tidying)
- **Token conservation** — Retrieving discussion context at session start must be selective, not exhaustive; fetching all discussions would blow the context window

## Approach Comparison

### Approach 1: Thin GraphQL Wrapper Layer (Bottom-Up)

Build a minimal `discussions.py` utility in leyline that wraps `gh api graphql` for CRUD operations. Each plugin (attune, minister, memory-palace) calls it directly when needed.

**Pros**: Minimal new infrastructure, each plugin owns its publishing logic, easy to implement incrementally
**Cons**: No centralized retrieval strategy, each plugin reinvents search/filter patterns, no automatic surfacing at session start

### Approach 2: Discussion-Aware Memory Palace (Knowledge-Centric)

Extend memory-palace to treat GitHub Discussions as an external storage tier alongside the local knowledge-corpus. The knowledge-librarian agent gains the ability to publish and retrieve from Discussions.

**Pros**: Leverages existing evaluation pipeline (importance scoring, marginal value filter), natural fit with digital garden lifecycle (seedling → growing → evergreen → Discussions), single source of truth for knowledge governance
**Cons**: Couples Discussion access through memory-palace, other plugins need memory-palace as intermediary, may overload memory-palace's scope

### Approach 3: New "Discussions" Plugin (Dedicated Infrastructure)

Create a new plugin (e.g., "agora" or "forum") that owns all Discussion operations: GraphQL wrappers, category management, template enforcement, retrieval, and publishing. Other plugins declare it as a dependency.

**Pros**: Clean separation of concerns, single place for all Discussion logic, can own `.github/DISCUSSION_TEMPLATE/` management, no existing plugin is overloaded
**Cons**: Another plugin to maintain, adds dependency chain, may be overengineered for the scope

### Approach 4: Distributed Hooks + Shared Leyline Module (Hybrid) -- SELECTED

Add a `discussions` module to leyline (alongside existing `git-platform`, `error-patterns`, etc.) that provides the GraphQL wrapper and search utilities. Each plugin uses this module in its own publishing hooks and skills:

- **attune**: War room publishes synthesis to "Decisions" category after deliberation
- **minister**: Playbook commands use working GraphQL wrappers instead of broken `gh discussion` references
- **memory-palace**: Knowledge-librarian gains a "promote to Discussion" action for evergreen content
- **imbue**: Scope-guard creates linked Discussions for deferred features with reasoning
- **sanctum**: Session-start skill queries past discussions for relevant context

Add a lightweight **SessionStart hook** (in leyline or sanctum) that queries recent/relevant discussions and injects a summary into the session context.

**Pros**: Follows existing architectural patterns (leyline as foundation, plugins extend), no new plugin needed, each plugin retains ownership of its publishing logic, shared search/wrapper utilities prevent duplication
**Cons**: Changes span 5+ plugins (but each change is small and well-scoped)

## Rationale for Selection

**Approach 4 (Hybrid)** is selected because:

1. **Follows the existing architecture** — leyline already provides shared infrastructure (git-platform, error-patterns, storage-templates). A `discussions` module fits naturally.
2. **Respects plugin ownership** — attune owns war room publishing, minister owns playbook commands, memory-palace owns knowledge promotion. Each plugin adds its own Discussion-aware behavior.
3. **Avoids overengineering** — No new plugin. No heavy abstraction layer. Just a shared utility module and targeted integrations.
4. **Incremental delivery** — Can be built phase-by-phase: (1) leyline wrapper, (2) category/template setup, (3) war room publishing, (4) session retrieval, (5) knowledge promotion.

## Trade-offs Accepted

- **GraphQL complexity over CLI simplicity**: Since `gh discussion` doesn't exist, we accept the verbosity of `gh api graphql` commands wrapped in helper functions
- **Cross-plugin changes over single-plugin encapsulation**: The distributed approach means touching 5+ plugins, but each change is small and self-contained
- **Selective retrieval over comprehensive loading**: Session-start discussion retrieval will be keyword/label-based rather than loading all discussions, accepting potential misses for token conservation
- **User confirmation for publishing**: Adds friction to the "auto-publish" workflow but prevents accidental public posting of internal deliberations

## Out of Scope

- **Real-time discussion monitoring** — No webhooks or polling for new discussions during a session
- **Cross-repository discussion federation** — Only the current repo's discussions
- **GitLab/Bitbucket discussion parity** — Initial implementation is GitHub-only; leyline abstraction allows future extension
- **Embedding-based semantic search over discussions** — Start with keyword/label search via GraphQL; semantic search is a future enhancement
- **Discussion-based agent-to-agent communication** — Discussions are for human-readable knowledge, not inter-agent messaging

## Research Foundation

### Online Research Findings

- **Agent memory landscape**: All major coding agents (Claude Code, Cursor, Aider, Devin) use file-based convention files loaded at session start. The AGENTS.md standard (Linux Foundation) is emerging for interoperability. Academic research (arXiv:2512.13564) positions memory as "a first-class primitive" for agent intelligence.
- **GitHub Discussions API**: Full GraphQL support for CRUD (createDiscussion, addDiscussionComment, markDiscussionCommentAsAnswer). Category forms via `.github/DISCUSSION_TEMPLATE/`. Search via `search(type: DISCUSSION)`.
- **Blackboard pattern**: Classical AI architecture where multiple specialized agents read/write to a shared knowledge repository. Directly maps to war room → Discussion publishing.
- **ADR automation**: Multi-agent ADR writer pipelines (researcher → writer → validator) demonstrate feasibility of automated decision capture.

### Codebase Findings

- **Memory-palace gap**: 6 skills, 4 agents, 7 hooks — rich local pipeline but no external store integration. Knowledge-librarian can fetch but not publish.
- **War room gap**: Produces strategeion artifacts locally but has no publication mechanism. The conjure war_room_orchestrator.py manages multi-LLM deliberation but outputs only to local files.
- **leyline gap**: Command mapping covers issues, PRs, CI/CD, repo metadata — but zero discussion coverage.
- **minister gap**: 3 broken `gh discussion` references in playbooks; discussion template mentioned but not implemented.

## Next Steps

1. `/attune:specify` — Create detailed specification from this brief
2. `/attune:blueprint` — Plan architecture and implementation phases
3. `/attune:execute` — Implement systematically

## Discussion Category Design (Proposed)

| Category | Slug | Format | Purpose | Labels |
|---|---|---|---|---|
| **Decisions** | `decisions` | Announcement (maintainer-only) | War room outcomes, ADR-style records | `war-room`, `scope-guard`, `adr`, `accepted`, `superseded` |
| **Deliberations** | `deliberations` | Open discussion | Active decision-making threads where agent posts perspectives | `in-progress`, `resolved`, `architecture`, `performance` |
| **Learnings** | `learnings` | Open discussion | Session retrospectives, pattern discoveries, debugging insights | `pattern`, `anti-pattern`, `debugging`, `performance` |
| **Knowledge** | `knowledge` | Q&A (with answers) | Promoted evergreen content from knowledge-corpus | `evergreen`, `growing`, `reference`, `convention` |
| **Announcements** | (default) | Announcement | Release notes, breaking changes | (keep default) |
| **Q&A** | (default) | Q&A | General questions | (keep default) |
