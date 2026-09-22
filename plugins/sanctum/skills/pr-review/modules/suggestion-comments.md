# Suggestion Comments

A suggestion block is a review comment the author applies with one
click. It is the most concise form a finding on a diff line can take:
the fix is the comment, and the platform turns it into a commit. This
module is the posting contract for both platforms and the rule
`--concise` adds on top.

Reader: a practitioner running `/pr-review` against GitHub or GitLab.

## The Suggestion Fence

Both platforms read a fenced block whose language is `suggestion`. The
body is the replacement text for the anchored line or lines.

GitHub, replacing the one line the comment is anchored to:

````markdown
```suggestion
    return cursor.execute("SELECT * FROM t WHERE id = ?", (uid,))
```
````

GitLab carries a line-range suffix. `-N` is lines above the anchored
line, `+M` lines below; `-0+0` replaces the anchored line alone.
GitLab caps a range at 100 lines above and 100 below.

````markdown
```suggestion:-0+0
    return cursor.execute("SELECT * FROM t WHERE id = ?", (uid,))
```
````

The body replaces the whole line, indentation included. Copy the
leading whitespace from the diff.

Sources: [GitLab suggestions][gl-sugg]; GitHub's
[commenting on a pull request][gh-comment], where the Suggestion button
inserts this fence.

## GitHub: Reviews API

Post through the reviews endpoint with a `comments` array, as
`modules/github-comments.md` describes. A suggestion is the comment
body, and nothing else changes.

```bash
gh api repos/{owner}/{repo}/pulls/{pr_number}/reviews \
  --method POST \
  --input - <<'EOF_JSON'
{
  "event": "COMMENT",
  "body": "Suggestions inline.",
  "comments": [
    {
      "path": "db/queries.py",
      "line": 89,
      "side": "RIGHT",
      "body": "```suggestion\n    return cursor.execute(\"SELECT * FROM t WHERE id = ?\", (uid,))\n```"
    }
  ]
}
EOF_JSON
```

For a block that replaces several lines, anchor the range with
`start_line` and `start_side` for the first line and `line` and
`side` for the last, then put every replacement line in the fence.
`side` is `RIGHT` for additions and context, `LEFT` for deletions
([REST reference][gh-rest]).

## GitLab: Positioned Discussion

`glab mr note` cannot anchor to a line. A suggestion needs a
positioned discussion, which takes the file, the line, and three SHAs
from the merge request's current version
([GitLab discussions API][gl-disc]).

```bash
# The three SHAs come from the latest MR version.
read -r BASE HEAD START < <(glab api "projects/:id/merge_requests/${MR}/versions" \
  --jq '.[0] | "\(.base_commit_sha) \(.head_commit_sha) \(.start_commit_sha)"')

glab api "projects/:id/merge_requests/${MR}/discussions" -X POST \
  -f 'position[position_type]=text' \
  -f "position[base_sha]=${BASE}" \
  -f "position[head_sha]=${HEAD}" \
  -f "position[start_sha]=${START}" \
  -f 'position[new_path]=db/queries.py' \
  -f 'position[old_path]=db/queries.py' \
  -F 'position[new_line]=89' \
  -f 'body=```suggestion:-0+0
    return cursor.execute("SELECT * FROM t WHERE id = ?", (uid,))
```'
```

`:id` is the project path, URL-encoded, or its numeric ID; `glab`
resolves `:id` from the current repository. `position[new_line]` is
the line in the file after the change. A comment on a removed line
uses `position[old_line]` instead. `position[old_path]` and
`position[new_path]` are both required for a text position. They are
equal unless the file was renamed.

## When Not to Use a Suggestion

A suggestion asserts that the reviewer knows the exact replacement.
Where that is not true, a plain comment is the honest shape:

- The fix touches lines outside the diff, which neither platform can
  anchor. Say what to change and where.
- The fix is a missing test, a missing file, or a deletion of more
  than the range allows.
- The finding is a question. A suggestion answers a question the
  author has not been asked yet.
- Two readings of the code are defensible and the choice is theirs.

Under `--hold-insights`, the last two are held in chat first.

## Under `--concise`

Every finding on a diff line is posted as a suggestion block. A
sentence beside the block is added only for clarification purposes:
when the change would otherwise puzzle the author, or when the block
fixes a symptom and the sentence names the cause. No Why, Proof, or
Teachable Moment is posted. Findings with no line to anchor to go in
the summary review, one line each, and the summary is the only other
comment. The test plan and the description update are not posted.

The full report, with its educational paragraphs, is still written to
the `--local` path, so the reviewer keeps what the author did not
need.

[gl-sugg]: https://docs.gitlab.com/user/project/merge_requests/reviews/suggestions/
[gl-disc]: https://docs.gitlab.com/api/discussions/
[gh-comment]: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/reviewing-changes-in-pull-requests/commenting-on-a-pull-request
[gh-rest]: https://docs.github.com/en/rest/pulls/comments?apiVersion=2022-11-28
