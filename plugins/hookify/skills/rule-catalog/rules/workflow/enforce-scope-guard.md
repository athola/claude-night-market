---
name: enforce-scope-guard
enabled: true
event: prompt
action: warn
conditions:
  - field: user_prompt
    operator: regex_match
    pattern: (add|create|implement|build).*(feature|component|module|system)
---

**Scope-guard check required!**

Imbue's scope-guard prevents over-engineering. Before proceeding:

**Run scope evaluation:**
```bash
Skill(imbue:scope-guard)
```

**Worthiness formula:**
```
Score = (BizValue + TimeCrit + RiskReduce) / (Complexity + TokenCost + ScopeDrift)

> 2.0  - Implement now
1.0-2.0 - Discuss first
< 1.0  - Defer to backlog
```

**Current branch status:**
- Check: `git diff --stat main | tail -1`
- Thresholds: 1000/1500/2000 lines

**Anti-overengineering rules:**
- No abstraction until 3rd use case
- Ask clarifying questions BEFORE solutions
- Stay within branch budget
