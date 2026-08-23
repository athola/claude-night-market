---
name: shell-review
description: Audit shell scripts for correctness, safety, and portability.
---

# Shell Script Review Command

Audit shell scripts for correctness, safety, and portability.

## Usage

```bash
/shell-review [path/to/script.sh]
```

Without arguments, reviews all `.sh` files in `scripts/` and `.git/hooks/`.

## What It Does

Runs `Skill(pensive:shell-review)`, which carries the workflow, the
checklist, and the output format. The skill is the one copy of that
methodology; this command is the entry point that invokes it.
