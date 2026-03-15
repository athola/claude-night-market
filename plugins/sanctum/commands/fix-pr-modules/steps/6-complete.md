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
| **6.7** | Tooling Reflection | Post night-market tooling observations to Discussions |

---

## Sub-Step 6.7: Tooling Reflection (Night-Market Feedback Loop)

After completing the workflow, reflect on the *tooling itself*
(skills, agents, commands, hooks) rather than the repo code.

**Ask yourself:**

- Did any skill behave unexpectedly or have unclear guidance?
- Was an agent slow, redundant, or missing context?
- Did a command skip steps it shouldn't have, or require
  unnecessary manual intervention?
- Did a hook fire incorrectly or miss a case?

**If yes**, post to the **night-market** GitHub Discussions
(Learnings category). Always target https://github.com/athola/claude-night-market/discussions,
not the current repo:

```bash
# Always target the night-market repo for tooling feedback
NM_OWNER="athola"
NM_REPO="claude-night-market"

NM_REPO_ID=$(gh api graphql \
  -f query="query { repository(owner: \"$NM_OWNER\", name: \"$NM_REPO\") { id } }" \
  --jq '.data.repository.id')

NM_CAT_ID=$(gh api graphql \
  -f query="query { repository(owner: \"$NM_OWNER\", name: \"$NM_REPO\") { discussionCategories(first: 20) { nodes { id slug } } } }" \
  --jq '.data.repository.discussionCategories.nodes[] | select(.slug == "learnings") | .id')

gh api graphql -f query='mutation($repoId: ID!, $categoryId: ID!, $title: String!, $body: String!) {
  createDiscussion(input: { repositoryId: $repoId, categoryId: $categoryId, title: $title, body: $body }) {
    discussion { url }
  }
}' \
  -f repoId="$NM_REPO_ID" \
  -f categoryId="$NM_CAT_ID" \
  -f title="[Workflow] <observation title>" \
  -f body="<observation body>"
```

**If no observations**, skip this step silently.

> **Key distinction**: Repo-specific learnings (code, bugs,
> architecture) stay in the current repo as issues or docs.
> Tooling learnings (skill/agent/command/hook behavior) always
> go to https://github.com/athola/claude-night-market/discussions
> so the night-market framework can improve.

---

> **Back to**: [Main Workflow](../workflow-steps.md)
