# Project hooks

## slop-scan-before-post

A `PreToolUse` hook on `Bash` that blocks AI-slop from reaching public
channels. It guards the posting chokepoint that every content workflow
shares: the `gh` command line.

### What it covers

The repo already scans markdown docs for slop before merge
(`.claude/rules/slop-scan-for-docs.md`) and sanctum strips slop from git
output (`plugins/sanctum/commands/shared/output-hygiene.md`). This hook
covers the third surface: prose crafted and posted straight to GitHub by
workflows such as `minister:create-issue`, `attune:war-room`,
`abstract:insight-engine`, `egregore:summon`, and `tome:synthesize`.
Because all of them post through `gh`, one hook guards them all without
changing their code.

### How it works

1. It reads the Bash command from the hook payload on stdin.
2. It matches content-posting `gh` forms (issue, PR, and discussion
   `create`, `comment`, `edit`, `review`, plus `gh api` against those
   endpoints). Read-only forms like `gh pr view` are ignored.
3. It extracts the post body from `--body`, `gh api -f body=`, or a
   resolved `--body-file PATH`.
4. It scans the body for slop markers. An extracted body gets the full
   marker set (em-dash, smart quotes, arrows, double-dash, `+` as a
   conjunction, tier-1 filler words). When the body cannot be isolated,
   only the unambiguous unicode markers are matched against the whole
   command, which keeps false positives near zero.
5. A match exits `2` and explains the fix on stderr. A clean payload, a
   non-posting command, or any parse error exits `0`. The hook fails open
   so it never wedges legitimate work.

### Known limits

Bodies supplied through an interactive editor or piped on stdin
(`--body-file -`) cannot be read in advance, so they pass unscanned. Run
`Skill(scribe:slop-detector)` on that text by hand.

### Tests

```bash
python3 -m pytest .claude/hooks/test_slop_scan_before_post.py -q
```
