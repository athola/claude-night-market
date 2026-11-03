# Tracker Mechanics

What each tracker reads, so a link is made by the tool and not by hand. Checked
against vendor docs on 2026-10-30. Bitbucket was not checked.

## GitHub

- Closing keywords: `close`, `closes`, `closed`, `fix`, `fixes`, `fixed`,
  `resolve`, `resolves`, `resolved`.
- They work in the pull request description and in commit messages, and only
  when the pull request targets the default branch. The docs do not list titles.
- A keyword in a commit closes the issue but does not list the pull request as
  linked. Prefer the description.
- Write each one in full: `Resolves #10, resolves octo-org/octo-repo#100`.
- Sub-issues: 100 per parent, eight levels. Use `gh issue create --parent`.
- Issue forms are YAML in `.github/ISSUE_TEMPLATE`, in public preview. Use a
  form to enforce the shape, with one required field for why.

## GitLab

- Closing patterns add `Implement` forms and `-ing` forms to the GitHub list.
- They work in the merge request description and in commit messages, on merge to
  the default branch. The docs do not list titles.
- `Related to #5` links the issue without closing it. Use it for partial work.
- A maintainer can turn auto-close off per project under Settings > Repository.
- Templates live in `.gitlab/issue_templates/`, with `Default.md` as the
  default.

## Jira

- Keys must use capital letters: `JRA-123`.
- Put the key at the start of the pull or merge request title and in the branch
  name. Jira's own docs name title, branch, and commit message.
- From GitLab, the merge request title or description links the merge request,
  pipeline, and branch to the development panel. A commit message links only the
  commit and its deployments.
- GitLab smart commits need matching GitLab and Jira accounts, and the command
  on a one-line commit message: `KEY-123 #comment Fixed`. `#time` and `#close`
  also work. Atlassian's connected hosts are Bitbucket, GitHub, and Fisheye.
- With **Enable Jira transitions** set on the GitLab integration,
  `Closes KEY-123` closes the Jira issue on merge to the default branch. Without
  it, use a smart commit or the API.
- Through the API, read valid moves from `GET
  /rest/api/3/issue/{key}/transitions`. IDs differ per workflow.
- Descriptions in REST v3 are Atlassian Document Format, not markdown: a
  `{"type": "doc", "version": 1}` root with `code` and `link` marks for inline
  text. Search with `/rest/api/3/search/jql`, which pages by `nextPageToken`.
