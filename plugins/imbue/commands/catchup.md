---
name: catchup
description: Context recovery after session breaks. Summarize recent git changes, extract key decisions, and identify pending work.
usage: /catchup [baseline]
---

# Catchup on Changes

Rapidly acquires context on recent changes using imbue's catchup methodology: confirm context, capture delta, extract insights, and record follow-ups.

Invoke `Skill(imbue:catchup)`, which carries the four-step methodology, the
output format and its sections, and the token-conservation rules.

## Usage

```bash
# Catchup from last known state
/catchup

# Catchup from specific baseline
/catchup HEAD~10

# Catchup from date
/catchup --since "2 days ago"
```

## Examples

```bash
/catchup
# Output:
# Catchup Summary
# ===============
# Scope: feature/payments branch
# Baseline: main (merge-base)
# Current: HEAD (15 commits ahead)
#
# Key Changes:
# - Payment processing overhaul (12 files)
# - New Stripe integration (3 files)
# - Test coverage additions (8 files)
#
# Follow-ups:
# - [ ] Review Stripe API key handling
# - [ ] Verify webhook endpoint security

/catchup --since "1 week ago"
# Week-based catchup with date filtering
```
