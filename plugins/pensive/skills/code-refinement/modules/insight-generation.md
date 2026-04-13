---
name: insight-generation
description: Post codebase-wide insights from refinement analysis
---

## Code Refinement Insight Generation

After completing the code refinement analysis, post
findings as insights to GitHub Discussions for tracking.

### When to Run

Run this module AFTER the refinement analysis is complete.
Post findings of type Optimization, Bug Alert, or
Improvement.

### Process

1. Collect refinement findings from the analysis
2. Map refinement categories to insight types:
   - Duplication: `[Optimization]`
   - Algorithm issues: `[Optimization]`
   - Clean code violations: `[Improvement]`
   - Error handling gaps: `[Bug Alert]`
   - Architecture misfit: `[Improvement]`

3. Post via the insight engine:

```bash
cd /home/alext/claude-night-market
python3 -c "
import sys, json
sys.path.insert(0, 'plugins/abstract/scripts')
from insight_types import Finding
from post_insights_to_discussions import post_findings

findings = [
    Finding(
        type='$INSIGHT_TYPE',
        severity='$SEVERITY',
        skill='$SKILL_OR_FILE',
        summary='$SUMMARY',
        evidence='$EVIDENCE',
        recommendation='$RECOMMENDATION',
        source='code-refinement',
    )
]
urls = post_findings(findings)
for url in urls:
    print(f'Posted: {url}')
"
```

4. The posting script handles all dedup automatically

### Quality Filters

Only post findings that meet these criteria:

- Severity is "high" or "medium"
- The finding is specific (not generic advice)
- Evidence references concrete code locations
- Recommendation is actionable within one PR
