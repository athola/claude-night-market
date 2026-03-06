---
name: campsite-check
enabled: true
event: prompt
action: info
conditions:
  - field: user_prompt
    operator: regex_match
    pattern: \b(commit|done|complete|finish|PR|pull.request|prepare.pr|merge)\b
---

**Stewardship: Leave the campsite better than you found it.**

Before wrapping up, consider one small improvement to the plugin
you've been working in:

- Is the README current? Stale docs mislead future contributors.
- Did you notice a confusing variable name or missing type hint?
- Could a brief comment explain a non-obvious decision?
- Is there a TODO you could resolve in under 2 minutes?

These small acts compound. Each one serves the contributor who
arrives after you.

See `STEWARDSHIP.md` for the five stewardship principles, or
invoke `Skill(leyline:stewardship)` for layer-specific guidance.
