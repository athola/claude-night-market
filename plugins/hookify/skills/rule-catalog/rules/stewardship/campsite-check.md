---
name: campsite-check
enabled: true
event: prompt
action: info
conditions:
  - field: user_prompt
    operator: regex_match
    pattern: \b(commit|done|complete|finish|PR|pull\.request|prepare\.pr|merge)\b
---

**Stewardship: Leave the campsite better than you found it.**

Before wrapping up, a brief reflection on the work just done:

- **Care**: What did you leave better for the next person?
- **Curiosity**: What did you learn about this code?
- **Humility**: Where were you uncertain? Did you handle
  it honestly?
- **Diligence**: Did you follow through on the small things?
- **Foresight**: Will your choices be easy to change tomorrow?

If any prompt surfaces an improvement you can make in under
a minute, consider making it now. Small acts compound.

For deeper reflection, see `modules/reflection.md` in
`Skill(leyline:stewardship)`. Record voluntary improvements
with the stewardship tracker.
