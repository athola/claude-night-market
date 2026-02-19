# GitHub Discussions Integration - Implementation Plan v1.0

**Author**: Claude (from specification v0.1.0)
**Date**: 2026-02-19
**Status**: Draft
**Specification**: `docs/specification.md`
**Project Brief**: `docs/project-brief.md`

## Architecture Design

### System Overview

Distributed Hooks + Shared Leyline Module architecture. Leyline provides the GraphQL foundation; each plugin owns its publishing/retrieval logic.

```
┌──────────────────────────────────────────────────────────────────┐
│                     GitHub Discussions (Remote)                    │
│  ┌──────────┐ ┌──────────────┐ ┌──────────┐ ┌───────────┐       │
│  │ Decisions │ │ Deliberations│ │ Learnings│ │ Knowledge │       │
│  └────▲─────┘ └──────▲───────┘ └────▲─────┘ └─────▲─────┘       │
└───────┼──────────────┼──────────────┼──────────────┼─────────────┘
        │              │              │              │
        │   GraphQL    │   GraphQL    │              │   GraphQL
        │   Mutations  │   Mutations  │              │   Mutations
        │              │              │              │
┌───────┴──────────────┴──────────────┴──────────────┴─────────────┐
│              leyline:git-platform / command-mapping                │
│              (Discussion Operations — new section)                 │
│    ┌────────────────────────────────────────────────────────┐     │
│    │  Templates: create, comment, answer, search, get, list │     │
│    │  Category resolution: slug → nodeID                     │     │
│    │  Graceful degradation: non-GitHub → skip with warning   │     │
│    └────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────┘
        │              │              │              │
   ┌────┴───┐    ┌─────┴────┐  ┌─────┴────┐  ┌─────┴──────┐
   │ attune │    │  imbue   │  │ minister │  │memory-palace│
   │war-room│    │scope-grd │  │playbooks │  │ knowledge   │
   │ FR-003 │    │  FR-006  │  │  FR-007  │  │   FR-005    │
   └────────┘    └──────────┘  └──────────┘  └────────────┘

                  ┌──────────────────────┐
                  │  SessionStart Hook   │
                  │  (FR-004: retrieval) │
                  └──────────────────────┘
```

### Component Interfaces

#### Leyline Discussion Templates (FR-001)

The command-mapping module gains a new **Discussion Operations** section providing `gh api graphql` command templates. These are reference commands (not executable code) that consuming plugins copy and parameterize.

**Templates provided**:
| Template | GraphQL Operation | Returns |
|----------|-------------------|---------|
| List categories | `repository.discussionCategories` | `slug`, `name`, `id` |
| Create discussion | `createDiscussion` mutation | `number`, `id`, `url` |
| Add comment | `addDiscussionComment` mutation | `id`, `url` |
| Mark as answer | `markDiscussionCommentAsAnswer` mutation | success status |
| Search discussions | `search(type: DISCUSSION)` | `number`, `title`, `url`, `category` |
| Get discussion | `repository.discussion(number:)` | body, comments, labels, answer |

**Non-GitHub graceful degradation**: Each template section includes a note: "GitLab/Bitbucket: Not supported. Operations will be skipped with a warning."

#### Discussion Category Forms (FR-002)

Four YAML form templates in `.github/DISCUSSION_TEMPLATE/`:

| File | Category | Format | Key Fields |
|------|----------|--------|------------|
| `decisions.yml` | Decisions | Announcement | Status, Context, Decision, Consequences, RS, Related |
| `deliberations.yml` | Deliberations | Open | Problem Statement, Stakeholders, Options, Status |
| `learnings.yml` | Learnings | Open | Category, Summary, Evidence, Applicable To |
| `knowledge.yml` | Knowledge | Q&A | Topic, Maturity, Source, Content |

#### Plugin Integration Points

Each plugin adds a self-contained module referencing leyline templates:

| Plugin | New/Modified File | Trigger | Publishes To |
|--------|-------------------|---------|-------------|
| attune | `modules/discussion-publishing.md` (NEW) | Post-Phase 7 synthesis | Decisions |
| memory-palace | `modules/discussion-promotion.md` (NEW) | Knowledge-librarian review | Knowledge |
| imbue | `modules/github-integration.md` (EXTEND) | Scope-guard deferral | Deliberations |
| minister | `playbooks/github-program-rituals.md` (FIX) | Weekly/monthly rituals | Decisions |
| minister | `playbooks/release-train-health.md` (FIX) | Quality gate checks | Support |

### Data Flow

**Publishing flow** (write path):
1. Plugin skill completes its workflow (war room synthesis, knowledge evaluation, scope-guard deferral)
2. Agent prompts user: "Publish to GitHub Discussions? [Y/n]"
3. On approval, agent resolves category nodeID using leyline's "list categories" template
4. Agent calls leyline's "create discussion" template with structured body
5. For threaded content (war room phases), agent calls "add comment" template per phase
6. For Q&A content (knowledge), agent calls "mark as answer" on the canonical answer
7. Local artifact updated with `discussion_url` field for cross-referencing

**Retrieval flow** (read path):
1. SessionStart hook fires
2. Hook detects GitHub platform via `gh auth status`
3. Hook queries 5 most recent Decisions discussions using leyline's "search discussions" template
4. Hook formats results as `#<number> <title> (<date>) — <first 100 chars>`
5. Formatted summary injected into session context (< 600 tokens)

---

## Task Breakdown

### Phase 1: Foundation (No Dependencies)

These tasks can be executed in parallel. They establish the shared infrastructure that all subsequent phases depend on.

---

#### TASK-001: Add Discussion Operations to Leyline Command Mapping

**Description**: Add a new "Discussion Operations" section to `plugins/leyline/skills/git-platform/modules/command-mapping.md` with GraphQL query/mutation templates for all Discussion CRUD operations.

**Type**: Implementation
**Priority**: P0 (Critical Path)
**Estimate**: M
**Dependencies**: None
**Implements**: FR-001

**Target File**: `plugins/leyline/skills/git-platform/modules/command-mapping.md`

**Acceptance Criteria**:
- [ ] New "Discussion Operations" section added after "Repo Metadata" section
- [ ] Table includes: List Categories, Create Discussion, Add Comment, Mark as Answer, Search Discussions, Get Discussion
- [ ] GitHub column has working `gh api graphql` commands with parameterized variables
- [ ] GitLab/Bitbucket columns show "N/A — Discussions not supported on this platform"
- [ ] Category ID resolution example included (slug → nodeID lookup)
- [ ] All GraphQL queries use `-f` variables (no string interpolation of user input)

**Technical Notes**:
- Follow existing table format (Operation | GitHub | GitLab | Bitbucket)
- Add a "Category Resolution" subsection before the operations table showing the `discussionCategories` query pattern
- The `createDiscussion` mutation requires `repositoryId` (not owner/name) and `categoryId` (nodeID) — include the resolution queries
- `search(type: DISCUSSION)` is the only way to filter by label — document this limitation
- Keep templates generic (use `OWNER`, `REPO`, `CATEGORY_ID` placeholders)

---

#### TASK-002: Create Discussion Category Form Templates

**Description**: Create four YAML form templates in `.github/DISCUSSION_TEMPLATE/` that enforce structured input for agent-created discussions. Also document the four custom categories that must be created on the repository.

**Type**: Implementation
**Priority**: P0 (Critical Path)
**Estimate**: S
**Dependencies**: None
**Implements**: FR-002

**Target Files**:
- `.github/DISCUSSION_TEMPLATE/decisions.yml`
- `.github/DISCUSSION_TEMPLATE/deliberations.yml`
- `.github/DISCUSSION_TEMPLATE/learnings.yml`
- `.github/DISCUSSION_TEMPLATE/knowledge.yml`

**Acceptance Criteria**:
- [ ] Four YAML files created following GitHub's discussion category forms syntax
- [ ] `decisions.yml`: Status (dropdown), Context (textarea), Decision (textarea), Consequences (textarea), Reversibility Score (input), Related PRs/Issues (input)
- [ ] `deliberations.yml`: Problem Statement (textarea), Stakeholders (input), Options Considered (textarea), Current Status (dropdown: in-progress/resolved)
- [ ] `learnings.yml`: Category (dropdown: pattern/anti-pattern/debugging/performance), Summary (textarea), Evidence (textarea), Applicable To (input)
- [ ] `knowledge.yml`: Topic (input), Maturity (dropdown: seedling/growing/evergreen), Source (input), Content (textarea)
- [ ] Each template has `labels:` pre-configured with category-appropriate defaults

**Technical Notes**:
- Follow GitHub's YAML form syntax: `body:` array with `type: dropdown`, `type: textarea`, `type: input`
- Each file needs `title:`, `labels:`, and `body:` top-level keys
- The categories themselves (Decisions, Deliberations, Learnings, Knowledge) must be created manually via GitHub Settings → Discussions → Categories — document this in a comment block at the top of each template
- Decisions category should use "Announcement" format (maintainer-only posting)
- Knowledge category should use "Q&A" format (supports answers)

---

### Phase 2: Core Publishing & Retrieval (Depends on Phase 1)

These tasks depend on TASK-001 (leyline templates) and TASK-002 (categories). They implement the primary value: publishing decisions and retrieving them at session start.

---

#### TASK-003: War Room Decision Publishing Module

**Description**: Create a new module `discussion-publishing.md` for the war room skill that publishes completed deliberation syntheses to the "Decisions" Discussion category after Phase 7 (Supreme Commander Synthesis).

**Type**: Implementation
**Priority**: P0 (Critical Path)
**Estimate**: L
**Dependencies**: TASK-001, TASK-002
**Implements**: FR-003

**Target File**: `plugins/attune/skills/war-room/modules/discussion-publishing.md` (NEW)

**Also Modified**:
- `plugins/attune/skills/war-room/SKILL.md` — add module to `modules:` list and add dependency on `leyline:git-platform`

**Acceptance Criteria**:
- [ ] New module created with clear instructions for post-Phase 7 publishing
- [ ] User prompt: "Publish this decision to GitHub Discussions? [Y/n]"
- [ ] On approval: Discussion created in "Decisions" category with title `[War Room] <topic>`
- [ ] Body contains: Context, Decision, Consequences, RS score, Alternatives Considered, Expert Panel composition
- [ ] Labels applied: `war-room`, `type-1a`/`type-1b`/`type-2` (matching mode), topic-relevant labels
- [ ] Deliberation phases posted as threaded comments (Intelligence → Assessment → COAs → Red Team → Synthesis)
- [ ] Synthesis comment marked as answer
- [ ] Local strategeion file updated with `discussion_url` field
- [ ] User denial ("n") preserves existing local-only workflow

**Technical Notes**:
- Reference leyline command-mapping templates for all GraphQL operations
- The publishing flow is: (1) resolve category ID, (2) create discussion, (3) add phase comments, (4) mark answer
- Each phase comment should be concise (reference the strategeion file for full details)
- Include the war room session ID in the discussion body for cross-referencing
- The module should be loaded only after Phase 7 completes (progressive loading)

---

#### TASK-004: Session-Start Discussion Retrieval Hook

**Description**: Create a lightweight SessionStart hook that queries the 5 most recent "Decisions" discussions and injects a brief summary into the session context. This enables cross-session learning.

**Type**: Implementation
**Priority**: P0 (Critical Path)
**Estimate**: M
**Dependencies**: TASK-001
**Implements**: FR-004

**Target File**: New hook script (location TBD — either leyline or sanctum hooks directory)

**Also Modified**:
- Plugin's `hooks/` configuration to register the new SessionStart hook

**Acceptance Criteria**:
- [ ] SessionStart hook queries 5 most recent "Decisions" discussions via GraphQL
- [ ] Each discussion formatted as: `#<number> <title> (<date>) — <first 100 chars of body>`
- [ ] Total injected context < 600 tokens
- [ ] Completes within 3 seconds (bounded GraphQL query, max 10 results)
- [ ] Graceful empty state: 0 discussions → no summary injected, no error
- [ ] Discussions disabled → hook exits silently
- [ ] Non-GitHub platform → hook skips entirely
- [ ] `gh` not authenticated → hook skips with warning
- [ ] Network failure → hook logs warning, continues without discussion data

**Technical Notes**:
- Use `gh api graphql` with a bounded `first: 5` query on `repository.discussions`
- Filter by Decisions category using `categoryId` parameter
- The hook must be fast — single GraphQL query, no pagination, no label filtering
- Python 3.9.6 compatible (no union types, no `datetime.UTC`, no `slots=True`)
- Check `gh auth status` before querying to avoid auth errors
- Consider placing in leyline (it owns git-platform infrastructure) or sanctum (it owns session-start workflows)

---

#### TASK-005: Fix Minister Playbook Discussion Commands

**Description**: Replace all 3 non-functional `gh discussion` CLI commands in minister playbooks with working `gh api graphql` equivalents.

**Type**: Bug Fix
**Priority**: P1 (High)
**Estimate**: S
**Dependencies**: TASK-001
**Implements**: FR-007

**Target Files**:
- `plugins/minister/docs/playbooks/github-program-rituals.md` (2 broken commands)
- `plugins/minister/docs/playbooks/release-train-health.md` (1 broken command)

**Broken Commands**:
1. `github-program-rituals.md:22` — `gh discussion create --title "Weekly Risk Radar" --body-file .claude/minister/risk.md`
2. `github-program-rituals.md:42` — `gh discussion comment EXEC_ID --body-file .claude/minister/executive.md`
3. `release-train-health.md:23` — `gh discussion list --category support`

**Acceptance Criteria**:
- [ ] Wednesday Risk Radar: `gh discussion create` → `gh api graphql` mutation referencing leyline template
- [ ] Monthly Executive Packet: `gh discussion comment` → `gh api graphql` mutation referencing leyline template
- [ ] Quality Signals: `gh discussion list --category support` → `gh api graphql` query referencing leyline template
- [ ] All replaced commands execute successfully against a repo with Discussions enabled
- [ ] Each replaced command includes a comment referencing the leyline command-mapping template it uses

**Technical Notes**:
- The existing `gh issue comment` and `gh issue create` patterns in the playbooks show the established style — mirror that format for the GraphQL replacements
- For the `create` replacement, the body must be read from file and passed as a GraphQL variable — use `$(cat .claude/minister/risk.md)` as the body variable
- For the `list` replacement in release-train-health.md, the table format should note this is a GraphQL query, not a simple CLI command
- Add a brief note after each replacement: "See leyline command-mapping: Discussion Operations for template reference"

---

### Phase 3: Extended Integration (Depends on Phases 1-2)

These tasks extend the Discussion integration to additional plugins. They are Medium priority and can be implemented incrementally.

---

#### TASK-006: Knowledge Promotion to Discussions Module

**Description**: Create a new module `discussion-promotion.md` for the knowledge-intake skill that adds a "Promote to Discussion" action for evergreen knowledge-corpus entries.

**Type**: Implementation
**Priority**: P2 (Medium)
**Estimate**: M
**Dependencies**: TASK-001, TASK-002
**Implements**: FR-005

**Target File**: `plugins/memory-palace/skills/knowledge-intake/modules/discussion-promotion.md` (NEW)

**Also Modified**:
- `plugins/memory-palace/skills/knowledge-intake/SKILL.md` — add module to `modules:` list

**Acceptance Criteria**:
- [ ] "Promote to Discussion" option presented when reviewing evergreen entries
- [ ] NOT presented for seedling or growing entries
- [ ] On approval: Discussion created in "Knowledge" category (Q&A format) with title, content, source URL, tags as labels
- [ ] Local corpus entry updated with `discussion_url` field
- [ ] Already-promoted entries show "Update Discussion" instead of "Promote"
- [ ] "Update Discussion" uses `updateDiscussion` mutation (not duplicate creation)

**Technical Notes**:
- The knowledge-librarian agent's review flow is the trigger point
- The module should check for `discussion_url` field in the corpus entry to determine promote vs. update
- Knowledge content in Discussion should be concise — link back to the local corpus file for full details (NFR-005)
- Max 2000 words in Discussion body

---

#### TASK-007: Scope-Guard Discussion Linking Module

**Description**: Extend the existing `github-integration.md` module in scope-guard to optionally create a linked Discussion in the "Deliberations" category alongside the mandatory GitHub issue.

**Type**: Implementation
**Priority**: P2 (Medium)
**Estimate**: S
**Dependencies**: TASK-001, TASK-002
**Implements**: FR-006

**Target File**: `plugins/imbue/skills/scope-guard/modules/github-integration.md` (EXTEND)

**Acceptance Criteria**:
- [ ] After issue creation, agent asks: "Also create a Discussion with full reasoning context? [Y/n]"
- [ ] On approval: Discussion created in "Deliberations" category with title `[Scope Guard] <feature name>`
- [ ] Discussion body contains: full scoring breakdown, alternatives considered, context
- [ ] Issue body updated with link: `Full reasoning: <discussion_url>`
- [ ] Discussion has labels: `scope-guard`, `deferred`, branch name
- [ ] User denial → only issue created (existing behavior preserved)

**Technical Notes**:
- The existing deferral process (Steps 1-3 in the current file) is preserved unchanged
- Add a new "Step 4: Create Linked Discussion (Optional)" section after Step 3
- Mirror the existing code style — the `gh issue create` heredoc pattern should be adapted for the GraphQL mutation
- The issue body needs to be updated with the discussion link after creation — this requires a second `gh issue edit` or include a placeholder

---

#### TASK-008: Discussion-Aware Prior Decision Check

**Description**: When a war room session starts, automatically search existing Discussions for prior decisions on the same topic to prevent re-deliberation.

**Type**: Implementation
**Priority**: P3 (Low)
**Estimate**: M
**Dependencies**: TASK-001, TASK-003, TASK-004
**Implements**: FR-008

**Target File**: `plugins/attune/skills/war-room/modules/discussion-publishing.md` (EXTEND — add "Prior Decision Check" section)

**Acceptance Criteria**:
- [ ] Before deliberation, agent searches Discussions for `category:Decisions <topic keywords>`
- [ ] Matching prior decisions presented: "Found prior decisions: #<number> <title>. Review before proceeding?"
- [ ] If user confirms prior decision still applies → war room skipped with reference to existing Discussion
- [ ] If user decides it's outdated → war room proceeds, new Discussion references prior as superseded
- [ ] No matches → war room proceeds normally without delay

**Technical Notes**:
- Use the `search(type: DISCUSSION)` query from leyline templates
- Extract topic keywords from the war room invocation argument
- The "superseded" reference should be a link in the new Discussion body: `Supersedes: #<prior_number>`
- This is a pre-deliberation check — runs before Phase 1 (Intelligence Gathering)

---

## Dependency Graph

```
TASK-001 (Leyline Templates)    TASK-002 (Category Forms)
    │                               │
    ├──────────┬───────────┐        │
    │          │           │        │
    ▼          ▼           ▼        │
TASK-004    TASK-005    TASK-003 ◄──┘
(Session    (Minister   (War Room    │
 Hook)       Fix)       Publish)     │
                           │         │
    ┌──────────────────────┤         │
    │                      │         │
    ▼                      ▼         ▼
TASK-008               TASK-006   TASK-007
(Prior Check)          (Knowledge)(Scope-Guard)
```

**Critical path**: TASK-001 → TASK-003 → TASK-008

---

## Development Phases

### Phase 1: Foundation (Sprint 1)

| Task | Name | Estimate | Parallel? |
|------|------|----------|-----------|
| TASK-001 | Leyline Discussion Templates | M | Yes (with TASK-002) |
| TASK-002 | Category Form Templates | S | Yes (with TASK-001) |

**Deliverable**: Shared infrastructure in place. All GraphQL templates documented. Form templates ready for category creation.

**Verification**:
- Templates follow existing command-mapping format
- YAML forms pass GitHub's schema validation
- Category resolution query returns expected format against live repo

---

### Phase 2: Core Publishing & Retrieval (Sprint 2)

| Task | Name | Estimate | Parallel? |
|------|------|----------|-----------|
| TASK-003 | War Room Publishing | L | Yes (with TASK-004, TASK-005) |
| TASK-004 | Session-Start Retrieval | M | Yes (with TASK-003, TASK-005) |
| TASK-005 | Minister Playbook Fixes | S | Yes (with TASK-003, TASK-004) |

**Deliverable**: War room decisions publish to Discussions. New sessions see prior decisions. Minister playbooks work.

**Verification**:
- War room session → publish → Discussion visible on GitHub with correct category, labels, threading
- New session → 5 most recent decisions appear in context
- Minister playbook commands execute without error

---

### Phase 3: Extended Integration (Sprint 3)

| Task | Name | Estimate | Parallel? |
|------|------|----------|-----------|
| TASK-006 | Knowledge Promotion | M | Yes (with TASK-007) |
| TASK-007 | Scope-Guard Linking | S | Yes (with TASK-006) |
| TASK-008 | Prior Decision Check | M | After TASK-003 |

**Deliverable**: Full Discussion integration across all plugins.

**Verification**:
- Evergreen knowledge entry → promote → Discussion in Knowledge category
- Scope-guard deferral → issue + linked Discussion in Deliberations category
- War room start → prior decisions surfaced → option to skip or supersede

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Discussion categories require manual creation | Medium | High | Document clearly in TASK-002; cannot be automated via API |
| GraphQL rate limiting on SessionStart hook | High | Low | Bounded query (max 5 results), single API call |
| `gh` CLI not authenticated in some environments | Medium | Medium | All hooks check `gh auth status` first; skip with warning |
| Discussion body exceeds practical readability | Low | Medium | NFR-005 enforces max 2000 words; link to local files for details |
| Python 3.9.6 compatibility issues in hook | High | Low | No union types, no `datetime.UTC`, no `slots=True`; test with system Python |
| Repo has Discussions disabled | Medium | Low | Hooks detect this and skip silently (FR-004 AC-5) |

---

## Success Metrics

- [ ] All P0 tasks (TASK-001 through TASK-005) completed and tested
- [ ] SessionStart hook completes in < 3 seconds with discussion context injected
- [ ] At least 3 Discussions published via agent workflows (1 war room, 1 knowledge, 1 scope-guard)
- [ ] Minister playbook commands execute without error
- [ ] No regressions in existing plugin functionality
- [ ] Python 3.9.6 compatibility verified for all new hook code
- [ ] Total injected discussion context < 600 tokens per session

---

## File Change Summary

| File | Action | Task | Lines (est.) |
|------|--------|------|-------------|
| `plugins/leyline/skills/git-platform/modules/command-mapping.md` | EXTEND | TASK-001 | +80 |
| `.github/DISCUSSION_TEMPLATE/decisions.yml` | CREATE | TASK-002 | ~40 |
| `.github/DISCUSSION_TEMPLATE/deliberations.yml` | CREATE | TASK-002 | ~35 |
| `.github/DISCUSSION_TEMPLATE/learnings.yml` | CREATE | TASK-002 | ~35 |
| `.github/DISCUSSION_TEMPLATE/knowledge.yml` | CREATE | TASK-002 | ~35 |
| `plugins/attune/skills/war-room/modules/discussion-publishing.md` | CREATE | TASK-003 | ~120 |
| `plugins/attune/skills/war-room/SKILL.md` | EXTEND | TASK-003 | +3 |
| New SessionStart hook script | CREATE | TASK-004 | ~60 |
| Hook plugin config | EXTEND | TASK-004 | +5 |
| `plugins/minister/docs/playbooks/github-program-rituals.md` | FIX | TASK-005 | ~20 delta |
| `plugins/minister/docs/playbooks/release-train-health.md` | FIX | TASK-005 | ~5 delta |
| `plugins/memory-palace/skills/knowledge-intake/modules/discussion-promotion.md` | CREATE | TASK-006 | ~100 |
| `plugins/memory-palace/skills/knowledge-intake/SKILL.md` | EXTEND | TASK-006 | +2 |
| `plugins/imbue/skills/scope-guard/modules/github-integration.md` | EXTEND | TASK-007 | +50 |
| `plugins/attune/skills/war-room/modules/discussion-publishing.md` | EXTEND | TASK-008 | +40 |

**Total**: ~630 new/modified lines across 15 files in 5 plugins + `.github/`

---

## Next Steps

1. **Review this plan** — verify architecture and task ordering
2. **Create Discussion categories** on repo (manual: Settings → Discussions → Categories)
3. **Execute Phase 1** — TASK-001 and TASK-002 in parallel
4. **Execute Phase 2** — TASK-003, TASK-004, TASK-005 in parallel
5. **Execute Phase 3** — TASK-006, TASK-007, then TASK-008
6. **Verify** — end-to-end test with war room → publish → new session retrieval
