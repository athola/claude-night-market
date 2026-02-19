# GitHub Discussions as Agent Collective Memory - Specification v0.1.0

**Author**: Claude (from project brief)
**Date**: 2026-02-19
**Status**: Draft

## Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1.0 | 2026-02-19 | Claude | Initial draft from brainstorm |

## Overview

**Purpose**: Bridge the gap between local agent decision-making and persistent, searchable collective memory by integrating GitHub Discussions as a shared knowledge blackboard across sessions.

**Scope**:
- IN: GraphQL wrapper utilities, discussion category/template setup, war room publishing, session-start retrieval, knowledge promotion, minister playbook fixes, scope-guard discussion linking
- OUT: Real-time monitoring, cross-repo federation, GitLab/Bitbucket parity, embedding-based semantic search, agent-to-agent messaging

**Stakeholders**:
- Agent sessions (primary consumer — retrieves prior decisions at session start)
- Human contributors (secondary — reads decisions, reviews promoted knowledge)
- Plugin maintainers (tertiary — integrates discussion support into existing workflows)

## Functional Requirements

### FR-001: GraphQL Discussion Wrapper Module (leyline)

**Description**: A shared `discussions` skill module in the leyline plugin that provides reusable `gh api graphql` command templates for all Discussion CRUD operations. This module extends the existing `command-mapping.md` to include Discussion operations alongside issues, PRs, and CI/CD.

**Acceptance Criteria**:
- [ ] Given the leyline plugin, when a skill references `dependencies: [leyline:git-platform]`, then Discussion operation templates are available in the command mapping
- [ ] Given a GitHub repository, when calling the "list categories" template, then all Discussion categories and their node IDs are returned
- [ ] Given a category slug and body text, when calling the "create discussion" template, then a new Discussion is created and its `number`, `id`, and `url` are returned
- [ ] Given a discussion node ID and comment body, when calling the "add comment" template, then a threaded comment is added
- [ ] Given a comment node ID, when calling the "mark as answer" template, then the comment is marked as the accepted answer
- [ ] Given a search query string, when calling the "search discussions" template, then matching discussions are returned with `number`, `title`, `url`, and `category`
- [ ] Given a discussion number, when calling the "get discussion" template, then the full discussion body, comments, labels, and answer status are returned
- [ ] Given a non-GitHub platform (GitLab, Bitbucket), when Discussion operations are attempted, then a clear "not supported on this platform" message is returned (graceful degradation)

**Priority**: High
**Dependencies**: None (foundation for all other FRs)
**Estimated Effort**: M

---

### FR-002: Discussion Category and Template Setup

**Description**: Create custom Discussion categories on the repository and structured YAML form templates in `.github/DISCUSSION_TEMPLATE/` that enforce machine-readable structured input for agent-created discussions.

**Acceptance Criteria**:
- [ ] Given the repository, when viewing Discussions, then at least 4 custom categories exist: Decisions, Deliberations, Learnings, Knowledge
- [ ] Given the "Decisions" category, when creating a new discussion via the web UI or API, then a structured form is presented with fields: Status (dropdown), Context (textarea), Decision (textarea), Consequences (textarea), Reversibility Score (input), Related PRs/Issues (input)
- [ ] Given the "Deliberations" category, when creating a discussion, then a form is presented with fields: Problem Statement (textarea), Stakeholders (input), Options Considered (textarea), Current Status (dropdown: in-progress/resolved)
- [ ] Given the "Learnings" category, when creating a discussion, then a form is presented with fields: Category (dropdown: pattern/anti-pattern/debugging/performance), Summary (textarea), Evidence (textarea), Applicable To (input)
- [ ] Given the "Knowledge" category (Q&A format), when creating a discussion, then a form is presented with fields: Topic (input), Maturity (dropdown: seedling/growing/evergreen), Source (input), Content (textarea)
- [ ] Given the `.github/DISCUSSION_TEMPLATE/` directory, when listing files, then one YAML file exists per custom category following GitHub's discussion category forms syntax

**Priority**: High
**Dependencies**: None (can be done in parallel with FR-001)
**Estimated Effort**: S

---

### FR-003: War Room Decision Publishing (attune)

**Description**: After a war room deliberation completes its Supreme Commander synthesis (Phase 7), the agent publishes the decision to the "Decisions" Discussion category. The existing strategeion local storage continues as-is; the Discussion is an additional publication channel.

**Acceptance Criteria**:
- [ ] Given a completed war room session, when the Supreme Commander synthesis is finalized, then the agent prompts the user: "Publish this decision to GitHub Discussions? [Y/n]"
- [ ] Given user approval, when publishing, then a Discussion is created in the "Decisions" category with title `[War Room] <topic>`, body containing: Context, Decision, Consequences, Reversibility Score, Alternatives Considered, Expert Panel composition
- [ ] Given the created Discussion, when viewing it, then it has labels matching the war room mode (`war-room`, `type-1a`, `full-council`, etc.) and topic-relevant labels
- [ ] Given the created Discussion, when viewing comments, then the deliberation phases are posted as threaded comments (Intelligence → Assessment → COAs → Red Team → Synthesis)
- [ ] Given the synthesis comment, when viewing, then it is marked as the "answer" on the Discussion
- [ ] Given a published Discussion, when the local strategeion file is saved, then it contains a `discussion_url` field linking to the published Discussion
- [ ] Given user denial ("n"), when the prompt is answered, then no Discussion is created and the local-only workflow continues unchanged

**Priority**: High
**Dependencies**: FR-001, FR-002
**Estimated Effort**: L

---

### FR-004: Session-Start Discussion Retrieval

**Description**: At session start, a lightweight query fetches recent and relevant Discussions and injects a brief summary into the session context. This enables "cross-session learning" — the agent knows what was decided before.

**Acceptance Criteria**:
- [ ] Given a new session starting on a GitHub repository, when the SessionStart hook runs, then the 5 most recent "Decisions" discussions are queried via GraphQL
- [ ] Given query results, when formatting for injection, then each discussion is summarized as: `#<number> <title> (<date>) — <first 100 chars of body>` (max ~500 tokens total)
- [ ] Given the formatted summary, when injected into session context, then the agent can reference prior decisions without the user explicitly asking
- [ ] Given a repository with 0 discussions, when the hook runs, then no error occurs and no summary is injected (graceful empty state)
- [ ] Given a repository without Discussions enabled, when the hook runs, then the hook exits silently without error
- [ ] Given the hook, when measuring performance, then it completes within 3 seconds (the GraphQL query must be fast and bounded)
- [ ] Given a non-GitHub platform, when the hook runs, then it skips the discussion query entirely

**Priority**: High
**Dependencies**: FR-001
**Estimated Effort**: M

---

### FR-005: Knowledge Promotion to Discussions (memory-palace)

**Description**: The knowledge-librarian agent gains a "promote to Discussion" action that publishes evergreen knowledge-corpus entries to the "Knowledge" Discussion category (Q&A format). The local corpus entry gains a `discussion_url` field for cross-referencing.

**Acceptance Criteria**:
- [ ] Given a knowledge-corpus entry at "evergreen" maturity, when the knowledge-librarian reviews it, then a "Promote to Discussion" option is presented
- [ ] Given user approval to promote, when publishing, then a Discussion is created in the "Knowledge" category with the entry's title, content, source URL, and tags as labels
- [ ] Given a promoted Discussion, when the original corpus entry is viewed, then it contains a `discussion_url` field linking to the Discussion
- [ ] Given a knowledge-corpus entry at "seedling" or "growing" maturity, when the librarian reviews it, then the "Promote to Discussion" option is NOT presented
- [ ] Given a knowledge-corpus entry that has already been promoted (has `discussion_url`), when the librarian reviews it, then the option shows "Update Discussion" instead of "Promote"
- [ ] Given an "Update Discussion" action, when executed, then the existing Discussion body is updated via the `updateDiscussion` mutation rather than creating a duplicate

**Priority**: Medium
**Dependencies**: FR-001, FR-002
**Estimated Effort**: M

---

### FR-006: Scope-Guard Discussion Linking (imbue)

**Description**: When scope-guard defers a feature (worthiness < 1.0), it already MANDATORILY creates a GitHub issue. This FR adds an optional linked Discussion in the "Deliberations" category that preserves the full reasoning context, alternatives considered, and scoring rationale — richer than what fits in an issue body.

**Acceptance Criteria**:
- [ ] Given a scope-guard deferral, when the GitHub issue is created, then the agent asks: "Also create a Discussion with full reasoning context? [Y/n]"
- [ ] Given user approval, when the Discussion is created, then it is in the "Deliberations" category with title `[Scope Guard] <feature name>`, body containing the full scoring breakdown, alternatives considered, and context
- [ ] Given the created Discussion, when viewing the linked GitHub issue, then the issue body contains a link to the Discussion: `Full reasoning: <discussion_url>`
- [ ] Given the created Discussion, when viewing, then it has labels: `scope-guard`, `deferred`, and the branch name
- [ ] Given user denial, when the prompt is answered, then only the issue is created (existing behavior preserved)

**Priority**: Medium
**Dependencies**: FR-001, FR-002
**Estimated Effort**: S

---

### FR-007: Fix Minister Playbook Discussion References

**Description**: Replace the 3 non-functional `gh discussion` CLI commands in minister's `github-program-rituals.md` with working `gh api graphql` equivalents that reference the leyline command-mapping templates.

**Acceptance Criteria**:
- [ ] Given `github-program-rituals.md`, when reading the Wednesday Risk Radar section, then the `gh discussion create` command is replaced with a working `gh api graphql` mutation that creates a Discussion in a specified category
- [ ] Given `github-program-rituals.md`, when reading the Monthly Executive Packet section, then the `gh discussion comment` command is replaced with a working `gh api graphql` mutation that adds a comment to an existing Discussion
- [ ] Given `release-train-health.md`, when reading quality gate checks, then any `gh discussion list` commands are replaced with working `gh api graphql` queries
- [ ] Given the updated playbooks, when an agent follows the documented workflow, then all Discussion commands execute successfully

**Priority**: Medium
**Dependencies**: FR-001
**Estimated Effort**: S

---

### FR-008: Discussion-Aware Prior Decision Check

**Description**: When the agent is about to make an architectural decision (detected via war-room-checkpoint or scope-guard invocation), it first searches existing Discussions for prior decisions in the same area. This prevents repeating deliberations already completed.

**Acceptance Criteria**:
- [ ] Given a war-room session starting, when the topic is provided, then the agent searches Discussions for `category:Decisions <topic keywords>` before beginning deliberation
- [ ] Given search results that match, when 1+ relevant prior decisions are found, then the agent presents them: "Found prior decisions on this topic: #<number> <title>. Review before proceeding?"
- [ ] Given the user reviews a prior decision, when they confirm it still applies, then the war room is skipped with a note referencing the existing Discussion
- [ ] Given the user reviews a prior decision, when they decide it's outdated, then the war room proceeds and the new decision's Discussion references the prior one as superseded
- [ ] Given no matching discussions, when the search completes, then the war room proceeds normally without delay

**Priority**: Low
**Dependencies**: FR-001, FR-003, FR-004
**Estimated Effort**: M

## Non-Functional Requirements

### NFR-001: Performance

- SessionStart discussion retrieval hook MUST complete within 3 seconds
- GraphQL queries MUST be bounded (max 10 results per query, no pagination loops)
- Discussion creation/commenting MUST not block the agent's primary workflow (fire-and-confirm pattern)
- Total token overhead from injected discussion context MUST be < 600 tokens per session

### NFR-002: Reliability

- All GraphQL operations MUST handle network failures gracefully (log warning, continue without discussion data)
- Missing Discussion categories MUST NOT cause hook failures (skip with warning)
- Rate limiting from GitHub API MUST be detected and handled (back off, warn user)
- If `gh` CLI is not authenticated, discussion operations MUST skip with a clear message

### NFR-003: Security

- No secrets or credentials are stored in Discussion bodies
- Discussion publishing ALWAYS requires user confirmation (no auto-publish)
- The agent MUST NOT create Discussions in repositories the user doesn't own or maintain
- War room anonymized expert identities (Merkle-DAG) are preserved in Discussion comments (no unmasking without user consent)

### NFR-004: Maintainability

- All GraphQL query templates MUST be in a single, readable location (leyline command-mapping module)
- Each plugin's Discussion integration MUST be self-contained (no cross-plugin imports for discussion logic)
- Python hook scripts MUST be compatible with Python 3.9.6 (no union types, no `datetime.UTC`, no `slots=True`)
- GraphQL queries MUST use parameterized variables (no string interpolation of user input into queries)

### NFR-005: Token Conservation

- SessionStart hook injects a maximum of 600 tokens of discussion context
- Discussion bodies published by the agent MUST be concise (max 2000 words for decision summaries)
- Knowledge promotion MUST NOT duplicate the full corpus entry — link back to the local file for details

## Technical Constraints

**GitHub API**:
- `gh` CLI v2.86.0+ required (for `gh api graphql`)
- GitHub GraphQL Discussions API (no REST equivalent)
- Repository must have Discussions enabled (Settings → Features → Discussions)
- GraphQL filtering limited to `categoryId` + `answered`; label-based filtering requires `search(type: DISCUSSION)`

**Python Compatibility**:
- System Python 3.9.6 — all hooks must work without 3.10+ features
- `from __future__ import annotations` for type hint syntax
- `datetime.timezone.utc` instead of `datetime.UTC`
- No `@dataclass(slots=True)`

**Plugin Architecture**:
- leyline provides shared GraphQL templates (new `discussions` section in command-mapping)
- Each consuming plugin (attune, minister, memory-palace, imbue) adds its own integration code
- No new hooks unless justified; prefer extending existing skills and post-deliberation workflows

**File Locations**:
- `plugins/leyline/skills/git-platform/modules/command-mapping.md` — new Discussion Operations section
- `.github/DISCUSSION_TEMPLATE/*.yml` — structured form templates
- `plugins/attune/skills/war-room/modules/discussion-publishing.md` — war room integration module
- `plugins/memory-palace/skills/knowledge-intake/modules/discussion-promotion.md` — promotion module
- `plugins/imbue/skills/scope-guard/modules/github-integration.md` — extend existing file
- `plugins/minister/docs/playbooks/github-program-rituals.md` — fix existing file

## Out of Scope

- **Real-time discussion monitoring** — No webhooks or polling during sessions
- **Cross-repository federation** — Only current repo's discussions
- **GitLab/Bitbucket discussion parity** — GitHub-only; leyline stub for future extension
- **Embedding-based semantic search** — Keyword/label search via GraphQL only
- **Discussion-based agent-to-agent messaging** — Discussions are human-readable knowledge
- **Automatic discussion creation without user consent** — All publishing requires confirmation
- **Discussion moderation or deletion** — Read and create only; no automated cleanup
- **Custom GitHub labels for discussions** — Use existing label infrastructure from minister

## Dependencies

**External**:
- GitHub GraphQL API (Discussions mutations and queries)
- `gh` CLI v2.86.0+ (for `gh api graphql` command)
- Repository Discussions feature enabled

**Internal (plugins)**:
- `leyline:git-platform` — foundation for all Discussion templates
- `attune:war-room` — decision publishing source
- `memory-palace:knowledge-intake` — knowledge promotion source
- `imbue:scope-guard` — deferral linking source
- `minister:github-initiative-pulse` — playbook fix target

## Acceptance Testing Strategy

### Unit Testing
- GraphQL query templates validated against GitHub's schema (mock responses)
- Category ID resolution tested with mock `gh api graphql` output
- Python 3.9 compatibility verified via `python3.9 -c "import ..."` checks

### Integration Testing
- End-to-end: Create a Discussion via the wrapper → verify it appears via GraphQL query
- End-to-end: Search for a Discussion by category + keyword → verify result format
- SessionStart hook tested with 0 discussions, 5 discussions, and API error scenarios

### Manual Verification
- War room session → publish → verify Discussion content and threading
- Knowledge promotion → verify Discussion appears in "Knowledge" category with correct form
- Minister playbook → follow updated commands → verify Discussion creation/commenting works

## Success Criteria

Project is successful when:
- [ ] All High priority FRs (FR-001 through FR-004) implemented and tested
- [ ] SessionStart hook completes in < 3 seconds with discussion context injected
- [ ] At least 3 Discussions published via agent workflows (1 war room, 1 knowledge, 1 scope-guard)
- [ ] Minister playbook commands execute without error
- [ ] No regressions in existing plugin functionality (war room still saves to strategeion, scope-guard still creates issues)
- [ ] Python 3.9.6 compatibility verified for all new hook code

## Glossary

| Term | Definition |
|------|-----------|
| **Discussion** | A GitHub Discussions thread — a forum-like post with threaded comments, categories, labels, and an optional "answer" |
| **Category** | A grouping for Discussions (e.g., "Decisions", "Knowledge") with a specific format (open, Q&A, announcement) |
| **Node ID** | GitHub's GraphQL global identifier for objects (e.g., `D_kwDOABC123`) — required for mutations |
| **Strategeion** | The war room's local file-based decision archive at `~/.claude/memory-palace/strategeion/` |
| **Knowledge-corpus** | Memory-palace's local knowledge store at `plugins/memory-palace/docs/knowledge-corpus/` |
| **Evergreen** | The highest maturity level in the digital garden lifecycle (seedling → growing → evergreen) |
| **Reversibility Score (RS)** | War room's 0-1 metric for how reversible a decision is; higher = less reversible |

## References

- [GitHub Discussions GraphQL API](https://docs.github.com/en/graphql/guides/using-the-graphql-api-for-discussions)
- [Discussion Category Forms Syntax](https://docs.github.com/en/discussions/managing-discussions-for-your-community/syntax-for-discussion-category-forms)
- [Memory in the Age of AI Agents (arXiv:2512.13564)](https://arxiv.org/abs/2512.13564)
- [Agent Blackboard Pattern](https://github.com/claudioed/agent-blackboard)
- [ADR with AI Coding Assistants](https://blog.thestateofme.com/2025/07/10/using-architecture-decision-records-adrs-with-ai-coding-assistants/)
- Project Brief: `docs/project-brief.md`
