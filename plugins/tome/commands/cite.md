---
name: cite
description: >-
  Generate a formatted bibliography from the most recent
  research session's findings.
usage: /tome:cite [--session <id>]
---

# Cite Command

Generate a bibliography from research findings.

## Usage

```bash
# Cite from latest session
/tome:cite

# Cite from specific session
/tome:cite --session abc123
```

## What Happens

1. Loads the specified or latest research session
2. Formats all findings as citations using channel-
   appropriate formatting
3. Outputs a numbered bibliography

## Citation Formats

- **Academic**: Author(s), "Title", Venue, Year. DOI/URL
- **GitHub**: Author, "Repo", GitHub, Stars. URL
- **Discourse**: User, "Title", Platform, Score. URL
