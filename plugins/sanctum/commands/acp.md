---
description: Add all changes, commit with conventional message, and push to PR branch.
model_hint: fast
---

# Add, Commit, Push

Stage all changes, generate a conventional commit message, commit,
and push to the current branch. One-shot workflow for when changes
are ready to go.

## Steps

1. **Gather context** (run in parallel):
   - `git status -sb`
   - `git diff --stat` (unstaged + staged)
   - `git diff` (full diff for commit message)
   - `git log --oneline -5`
   - `git branch --show-current`
   - `git rev-parse --abbrev-ref @{upstream} 2>/dev/null` (check if tracking remote)

2. **If no changes exist** (nothing staged or unstaged), tell the
   user and stop.

3. **Stage all changes**:
   - `git add` each changed and untracked file by name
   - Do NOT use `git add -A` or `git add .`
   - Do NOT stage `.env`, credentials, or secrets files
   - Do NOT stage `.claude/state/` directory

4. **Draft a conventional commit message** following the same rules
   as `/commit-msg`:
   - Type: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`,
     `style`, `perf`, `ci`
   - Scope: from the changed directory or module
   - Summary: imperative mood, 50 chars max
   - Body: what and why, wrapped at 72 chars
   - No AI attribution, no emojis, no slop

5. **Commit** with the drafted message. Use a HEREDOC:
   ```bash
   git commit -m "$(cat <<'EOF'
   <message>
   EOF
   )"
   ```

6. **If the commit fails** due to pre-commit hooks, fix the issues
   and create a new commit. Do NOT use `--no-verify`.

7. **Push** to the current branch:
   - If tracking a remote branch: `git push`
   - If no upstream set: `git push -u origin <branch>`

8. **Report** the commit hash, branch, and remote URL.
