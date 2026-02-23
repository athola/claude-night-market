# Promote Community Learnings

Check GitHub Discussions for highly-voted learnings and promote them to Issues.

## Usage

```bash
/abstract:promote-discussions
```

## Purpose

Part of Issue #69 Phase 6c, this command scans athola/claude-night-market Discussions in the "Learnings" category for items that have received sufficient community votes (fire emoji reactions) and promotes them to GitHub Issues for team triage.

## What It Does

1. **Loads config** from `~/.claude/skills/discussions/config.json`
   - `promotion_threshold`: Minimum fire reactions to promote (default: 3)
   - `promotion_emoji`: Reaction type to count (default: fire)
2. **Queries Discussions** in the "Learnings" category via `gh api graphql`
3. **Checks reaction counts** for fire emoji specifically
4. **Promotes qualifying items** by creating GitHub Issues with:
   - Title: `[Community Learning] {discussion title}`
   - Body: Link to discussion, vote count, original content summary
5. **Tracks promotions** in `~/.claude/skills/discussions/promoted.json` to avoid duplicates

## Instructions

When this command is invoked:

1. Run `plugins/abstract/scripts/promote_discussion_to_issue.py`
2. Report results to the user:
   - If items were promoted: list the created Issue URLs
   - If no items met the threshold: report the current threshold and suggest waiting for more votes
   - If an error occurred: report the error and suggest checking `gh auth status`

## Prerequisites

- GitHub CLI (`gh`) must be installed and authenticated
- User must have write access to athola/claude-night-market (for Issue creation)

## Configuration

Edit `~/.claude/skills/discussions/config.json`:

```json
{
  "promotion_threshold": 3,
  "promotion_emoji": "🔥"
}
```

## Related

- `/abstract:aggregate-logs` - Generates LEARNINGS.md and posts to Discussions (Phase 6a)
- `/abstract:improve-skills` - Implements improvements locally (Phase 5)

## Version

1.0.0 (Phase 6c implementation)
