# Step 6: Complete (Threads, Issues, Summary)

> **Navigation**: [<- Step 5: Validate](5-validate.md) | [Main Workflow](../workflow-steps.md)

**Purpose**: Resolve threads, create issues for deferred items, and post summary.

**Platform Note**: Commands below show GitHub (`gh`) examples. Check session context for `git_platform:` and consult `Skill(leyline:git-platform)` for GitLab (`glab`) / Bitbucket equivalents. GitLab uses "merge request" terminology and `glab api graphql` for thread resolution.

**CRITICAL WORKFLOW GUARDRAIL**

**NEVER skip this step unless you are NOT the PR author. If you are the PR author and received review comments, you MUST complete this step. There are NO exceptions.**

Load: [Pre-Check](6-complete/pre-check.md)

**If you are NOT the PR author**, you may skip to Step 6.4. Otherwise, continue below.

---

## Sub-Module Navigation

Step 6 is organized into sub-modules. Execute them in order:

| Sub-Step | Module | Purpose |
|----------|--------|---------|
| **Pre** | [Pre-Check](6-complete/pre-check.md) | Validate reviews submitted and threads resolved |
| **6.0** | [Reconciliation](6-complete/reconciliation.md) | Reconcile ALL unworked items + enforcement |
| **6.1-6.2** | [Issue Creation](6-complete/issue-creation.md) | Create issues for suggestions and deferred items |
| **6.3** | [Thread Resolution](6-complete/thread-resolution.md) | Reply to and resolve every review thread |
| **6.4** | [Issue Linkage](6-complete/issue-linkage.md) | Link/close related issues |
| **6.5** | [Summary](6-complete/summary.md) | Post summary comment to PR |
| **6.6** | [Verification](6-complete/verification.md) | Final verification and workflow gate |

---

> **Back to**: [Main Workflow](../workflow-steps.md)
