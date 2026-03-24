# PR/MR Review: Mandatory Outputs Enforcement and Options

Enforcement checks to verify all required outputs were produced, and
the full list of command options.

> **See Also**:
> [Main Command](../../pr-review.md) |
> [Workflow Index](review-workflow.md) |
> [Phases 1-4](review-workflow-phases-1-4.md) |
> [Phases 5-6](review-workflow-phases-5-6.md) |
> [Framework](review-framework.md) |
> [Configuration](review-configuration.md)

---

## Mandatory Outputs Enforcement

**CRITICAL: The /pr-review command is NOT complete unless ALL of these outputs exist:**

| Output | Phase | Verification |
|--------|-------|--------------|
| Review comment | Phase 4 | `gh pr view --json comments` contains "PR Review" |
| Test plan comment | Phase 5 | `gh pr view --json comments` contains "Test Plan" |
| PR description | Phase 6 | `gh pr view --json body` is non-empty and contains "Review Summary" |

**Enforcement Check (run at end of review):**

```bash
# Validate all mandatory outputs
PR_NUMBER=${1:-$(gh pr view --json number -q '.number')}

REVIEW_EXISTS=$(gh pr view $PR_NUMBER --json comments --jq '[.comments[].body | contains("PR Review")] | any')
TEST_PLAN_EXISTS=$(gh pr view $PR_NUMBER --json comments --jq '[.comments[].body | ascii_downcase | contains("test plan")] | any')
DESCRIPTION_EXISTS=$(gh pr view $PR_NUMBER --json body --jq '.body | length > 0')

echo "=== Mandatory Output Verification ==="
echo "Review comment:  $( [[ $REVIEW_EXISTS == "true" ]] && echo "✅" || echo "❌ MISSING" )"
echo "Test plan:       $( [[ $TEST_PLAN_EXISTS == "true" ]] && echo "✅" || echo "❌ MISSING" )"
echo "PR description:  $( [[ $DESCRIPTION_EXISTS == "true" ]] && echo "✅" || echo "❌ MISSING" )"

if [[ $REVIEW_EXISTS != "true" ]] || [[ $TEST_PLAN_EXISTS != "true" ]] || [[ $DESCRIPTION_EXISTS != "true" ]]; then
  echo ""
  echo "⚠️  PR review INCOMPLETE - mandatory outputs missing"
  echo "Run /pr-review-enforcer $PR_NUMBER to fix"
  exit 1
fi

echo ""
echo "✅ All mandatory outputs verified for PR #$PR_NUMBER"
```

**If verification fails, the review is INCOMPLETE. Go back and complete missing phases.**

## Options

- `--scope-mode`: Set strictness level (default: standard)
  - `strict`: All requirements must be complete
  - `standard`: Core requirements required
  - `flexible`: MVP implementation acceptable
- `--auto-approve-safe-prs`: Auto-approve PRs with no issues
- `--no-auto-issues`: **Skip automatic issue creation** for out-of-scope items (issues are created by default)
- `--dry-run`: Generate report in conversation without posting to GitHub
- `--local [path]`: Write full report to a local `.md` file instead
  of posting to the PR. Default path: `.pr-review/pr-<number>-review.md`.
  Skips API calls, issue creation, and PR description updates.
  Unlike `--dry-run`, produces a permanent file.
- `--no-line-comments`: Skip individual line comments, only submit summary review
- `--skip-version-check`: **BYPASS version validation** (maintainer override)
  - Use when: intentional version skew, non-release PR touching version files
  - Alternative: Add `skip-version-check` label to PR or `[skip-version-check]` in PR description
  - **Still runs validation** but marks issues as [WAIVED] instead of [BLOCKING]
- `pr-number`/`pr-url`: Target specific PR (default: current branch)
