---
name: insight-generation
description: Post PR-scoped insights to GitHub Discussions
---

## PR Insight Generation

After completing the PR review analysis, generate insights
from the review findings and post them to Discussions.

### When to Run

Run this module AFTER the main review is complete and
findings have been documented. Only generate insights for
findings with severity "high" or "medium".

### Process

1. Collect review findings from the current PR analysis
2. For each high/medium finding, create a Finding object:

```bash
cd /home/alext/claude-night-market
python3 -c "
import sys, json
sys.path.insert(0, 'plugins/abstract/scripts')
from insight_types import Finding
from post_insights_to_discussions import post_findings

findings = [
    Finding(
        type='PR Finding',
        severity='$SEVERITY',
        skill='',
        summary='PR #$PR_NUMBER: $FINDING_SUMMARY',
        evidence='$EVIDENCE',
        recommendation='$RECOMMENDATION',
        source='pr-review',
        related_files=$CHANGED_FILES,
    )
]
urls = post_findings(findings)
for url in urls:
    print(f'Posted: {url}')
"
```

3. The posting script handles all dedup automatically
4. Report posted URLs in the review summary

### Finding Types

Map review categories to insight types:

| Review Category | Insight Type |
|----------------|-------------|
| Security issue | `[Bug Alert]` |
| Logic error | `[Bug Alert]` |
| Performance concern | `[Optimization]` |
| Code quality | `[Improvement]` |
| Test gap | `[PR Finding]` |
| Architecture issue | `[PR Finding]` |
