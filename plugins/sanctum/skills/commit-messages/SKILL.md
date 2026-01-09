---
name: commit-messages
description: |

Triggers: messages, conventional-commits, git, changelog, commit
  Generate conventional commit messages from staged changes with correct type/scope.

  Triggers: commit message, conventional commit, git commit
  Use when: generating commit messages in conventional commits format
  DO NOT use when: full PR preparation - use pr-prep instead.
category: artifact-generation
tags: [git, commit, conventional-commits, changelog]
tools: [Bash, Write, TodoWrite]
complexity: low
estimated_tokens: 600
dependencies:
  - sanctum:shared
  - sanctum:git-workspace-review
---

# Conventional Commit Workflow

## When to Use
Use this skill to write a commit message for staged changes.
As a prerequisite, run `Skill(sanctum:git-workspace-review)` so the repository path, status, and diffs are already captured. If that skill reveals no staged changes, stage the desired files before continuing.

## Required Steps
1. **Classify the change**
   - Choose the correct type: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `style`, `perf`, or `ci`.
   - Select a concise scope (directory/module or `core`, `cli`, etc.). The scope is optional but preferred.
   - Decide if the change is breaking. If so, plan a `BREAKING CHANGE:` footer.
2. **Draft the message**
   - Subject: `<type>(<scope>): <imperative summary>` (scope optional, ≤50 characters).
   - Body: Wrap at 72 characters per line, explain the "what" and "why", and list key bullets if useful.
   - Footer: Add `BREAKING CHANGE: …` or issue references if needed.
3. **Write the output**
   - The prompt passes a destination path (e.g., `{0|commit_msg.txt}`).
   - Overwrite the file with only the final commit message—no commentary.
4. **Preview**
   - Display the file path and contents (`cat <file>` or `sed -n '1,120p' <file>`) for confirmation.

## Guardrails
- **No AI attribution**: Never add Co-Authored-By lines mentioning Claude, Opus, Sonnet, Haiku, or any AI assistant.
- **No AI slop**: Avoid filler words and phrases common in AI-generated text (e.g., "leverage", "streamline", "robust", "seamless").
- **No emojis**: Keep commit messages professional and plain text only.
- **Human voice**: Write as if a human developer authored the message directly.
- Use the present-tense, imperative style for the subject line.
- Include a multi-line body for any non-trivial change (more than one file or complex logic).
- If multiple types apply, pick the highest-impact type (e.g., `feat` over `chore`).

## Integration Notes
- Combine with `Skill(imbue:catchup)` or `/git-catchup` when you need additional context before drafting.
- If unsure about the type or scope, rerun the diff commands or consult the specification or plan before finalizing.
## Troubleshooting

### Common Issues

**Pre-commit hooks failing**
Run `SKIP=... git commit` to bypass temporarily, then fix issues

**Merge conflicts**
Use `git merge --abort` to reset, then resolve conflicts carefully

**Commit rejected**
Check hook output and fix reported issues before committing again
