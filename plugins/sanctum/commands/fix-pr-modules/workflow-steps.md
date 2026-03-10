# Fix PR: Workflow Steps

Detailed step-by-step guide for fix-pr command execution.

> **See Also**: [Main Command](../fix-pr.md) | [Configuration](configuration-options.md) | [Troubleshooting](troubleshooting-fixes.md)

## Overview

The fix-pr workflow consists of 6 sequential steps. Each step builds on the previous and can be skipped when appropriate.

## Quick Navigation

| Step | Name | Purpose | When to Skip |
|------|------|---------|--------------|
| **[1](steps/1-analyze.md)** | [Analyze](steps/1-analyze.md) | Understand PR and gather comments | Already familiar with PR |
| **[2](steps/2-triage.md)** | [Triage](steps/2-triage.md) | Classify by type and priority | Single simple fix |
| **[3](steps/3-plan.md)** | [Plan](steps/3-plan.md) | Generate fix strategies | Fixes are obvious |
| **[4](steps/4-fix.md)** | [Fix](steps/4-fix.md) | Apply code changes | Made changes manually |
| **[5](steps/5-validate.md)** | [Validate](steps/5-validate.md) | Test and verify fixes | Already validated |
| **[6](steps/6-complete.md)** | [Complete](steps/6-complete.md) | **Reply to & resolve threads** | **⛔ NEVER SKIP** |

> **⚠️ Step 6 is MANDATORY.** The workflow is incomplete until all review threads are replied to and resolved. See [Mandatory Exit Gate](../fix-pr.md#mandatory-exit-gate).

## Workflow Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  1. Analyze │ ──▶ │  2. Triage  │ ──▶ │   3. Plan   │
│   (Context) │     │ (Classify)  │     │ (Strategy)  │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
                                               ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ 6. Complete │ ◀── │ 5. Validate │ ◀── │   4. Fix    │
│  (Threads)  │     │   (Test)    │     │  (Changes)  │
└─────────────┘     └─────────────┘     └─────────────┘
```

## Step Details

### [Step 1: Analyze (Discovery & Context)](steps/1-analyze.md)

Understand the PR and gather all review comments.

**Key Actions:**
- Identify target PR
- Check/add PR description
- Fetch review threads (GraphQL)
- Detect feedback types
- Analyze with superpowers

**Output:** PR metadata, all review comments, initial analysis

---

### [Step 2: Triage (Classification)](steps/2-triage.md)

Classify comments by type and priority.

**Categories:**
- 🔴 **Fix Now**: Security, bugs, blockers
- 🟡 **This PR**: In-scope improvements
- 📋 **Backlog**: Create GitHub issues
- ⏭️ **Skip**: Informational, praise

**Output:** Classified comment list with priorities

---

### [Step 3: Plan (Fix Strategy)](steps/3-plan.md)

Generate fix strategies for actionable comments.

**Commit Strategies:**
- **Single**: Simple fixes, few comments
- **Separate**: Complex fixes, multiple categories
- **Manual**: User controls commits

**Output:** Fix plan with strategies per comment

---

### [Step 4: Fix (Apply Changes)](steps/4-fix.md)

Apply code changes systematically.

**Process:**
1. Read code context (±20 lines)
2. Apply fix with Edit tool
3. Verify no new issues
4. Commit changes

**Output:** Applied fixes, commits created

---

### [Step 5: Validate (Test & Verify)](steps/5-validate.md)

Ensure all fixes are correct and quality gates pass.

**Validation Steps:**
- Version validation (if applicable)
- Execute automated test plan
- Agent-verify manual test plan (creative verification)
- Run quality gates
- Document results

**Output:** All tests passing, quality gates green,
manual test plan agent-verified with evidence

---

### [Step 6: Complete (Threads, Issues, Summary)](steps/6-complete.md)

Resolve threads, create issues, and post summary.

**MANDATORY for PR authors receiving review comments.**

**Sub-Modules:**
| Sub-Step | Module | Purpose |
|----------|--------|---------|
| **6.0** | [Reconciliation](steps/6-complete/reconciliation.md) | Reconcile ALL unworked items + enforcement |
| **6.1-6.2** | [Issue Creation](steps/6-complete/issue-creation.md) | Create issues for suggestions/deferred items |
| **6.3** | [Thread Resolution](steps/6-complete/thread-resolution.md) | Reply to and resolve ALL review threads |
| **6.4** | [Issue Linkage](steps/6-complete/issue-linkage.md) | Link/close related issues |
| **6.5** | [Summary](steps/6-complete/summary.md) | Post summary comment to PR |
| **6.6** | [Verification](steps/6-complete/verification.md) | Final verification and workflow gate |

**Output:** All threads resolved, ALL unworked items tracked as issues, summary posted

---

## Critical Workflows

### Thread Resolution (Step 6.3)

**MANDATORY** - You MUST reply to and resolve each review thread:

```bash
# Reply to thread
gh api graphql -f query='
mutation {
  addPullRequestReviewThreadReply(input: {
    pullRequestReviewThreadId: "PRRT_xxx"
    body: "Fixed - [description]"
  }) { comment { id } }
}'

# Resolve thread
gh api graphql -f query='
mutation {
  resolveReviewThread(input: {threadId: "PRRT_xxx"}) {
    thread { isResolved }
  }
}'
```

See [Step 6: Complete](steps/6-complete.md) for full details.

### Version Validation (Step 5.1)

If version issues were flagged, re-validate before proceeding:

| Project Type | Files to Check |
|--------------|----------------|
| claude-marketplace | marketplace.json, plugin.json files |
| python | pyproject.toml, __version__ in code |
| node | package.json, package-lock.json |
| rust | Cargo.toml, Cargo.lock |

See [Step 5: Validate](steps/5-validate.md) for validation scripts.

---

## Module Reference

This workflow documentation is modularized for efficient context loading:

```
fix-pr-modules/
├── workflow-steps.md          # This file (hub/navigation)
├── configuration-options.md   # Command configuration
├── troubleshooting-fixes.md   # Common issues
└── steps/
    ├── 1-analyze.md          # Discovery & Context
    ├── 2-triage.md           # Classification
    ├── 3-plan.md             # Fix Strategy
    ├── 4-fix.md              # Apply Changes
    ├── 5-validate.md         # Test & Verify
    ├── 6-complete.md         # Hub: Pre-check + navigation
    └── 6-complete/           # Sub-modules for Step 6
        ├── reconciliation.md # 6.0: Reconcile items + enforcement
        ├── issue-creation.md # 6.1-6.2: Create suggestion/deferred issues
        ├── thread-resolution.md # 6.3: Reply + resolve threads
        ├── issue-linkage.md  # 6.4: Link/close related issues
        ├── summary.md        # 6.5: Post summary comment
        └── verification.md   # 6.6: Final gate + verification
```
