# Minister Scripts

## tracker.py

CLI helper for program tracking with GitHub awareness.

### Quick Start

```
uv run python plugins/minister/scripts/tracker.py add --id GH-123 --title "Docs hardening" \
  --initiative "Docs & Enablement" --phase "Phase 2" --priority High \
  --owner "@handle" --effort 8 --due 2025-01-15 --github-issue https://github.com/org/repo/issues/123
```

```
uv run python plugins/minister/scripts/tracker.py status --github-comment
```

### Tips

- Data stored in `plugins/minister/data/project-data.json`.
- Use `--github-comment` to paste output into issues/PRs.
- Pair with `release-health-gates` skill to embed readiness summary.
