---
name: test-skill-wrapper
description: Wrapper around superpowers:test-driven-development for skill development workflows
usage: /test-skill-wrapper [skill-path] [--phase red|green|refactor]
extends: "superpowers:test-driven-development"
---

# Test Skill Wrapper Command

Maintains backward compatibility with /test-skill while leveraging superpowers:test-driven-development.

## Implementation

```python
# When command is invoked:
wrapper = TestSkillWrapper()
result = wrapper.execute({
    "skill-path": args.skill_path,
    "phase": args.phase
})
```

## Migration Path

1. Existing /test-skill continues to work
2. New features added via superpower extensions
3. Gradual migration of users to enhanced workflow