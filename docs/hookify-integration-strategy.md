# Hookify & Hook-Authoring Integration Strategy

## Current State

We have three complementary hook systems:
1. **abstract:hook-authoring** - SDK-level Python hooks for plugin developers
2. **abstract:hook-scope-guide** - Architectural guidance on hook placement
3. **hookify** - Markdown-based rules for end users

## Integration Vision

### 1. Plugin-Declared Hookify Rules

Plugins can ship with recommended hookify rules in `examples/hookify/`:

```
plugins/parseltongue/
├── examples/
│   └── hookify/
│       ├── prevent-mixed-quotes.local.md
│       └── warn-missing-tests.local.md
```

Users can enable with:
```bash
/hookify:install parseltongue:prevent-mixed-quotes
```

### 2. Hook Authoring → Hookify Generation

SDK hooks can auto-generate hookify rule suggestions:

```python
# In plugin's SDK hook
@hook("PreToolUse")
async def validate_python(input_data, tool_id, context):
    # ... complex validation ...

    # Suggest simple hookify rule for common case
    if is_simple_pattern_match:
        suggest_hookify_rule(
            name="warn-print-statements",
            pattern=r"print\(",
            message="Consider using logging instead"
        )
```

###  3. Hookify → Hook Integration

Hookify rules can trigger plugin-specific hooks:

```yaml
---
name: require-parseltongue-validation
event: file
action: warn
on_match:
  invoke_hook: parseltongue:validate-syntax
conditions:
  - field: file_path
    operator: regex_match
    pattern: \.py$
---
```

### 4. Plugin-Specific Rule Templates

Each plugin provides templates in `skills/hookify-templates.md`:

```markdown
# Parseltongue Hookify Templates

## Prevent TODO comments in production
## Warn about missing type hints
## Block commits without tests
```

### 5. Context-Aware Rule Suggestions

When user runs `/hookify` without args in a Python project:
- Parseltongue suggests Python-specific rules
- Pensive suggests code review rules
- Sanctum suggests git workflow rules

## Implementation Plan

### Phase 1: Foundation (Current)
- ✅ Hookify plugin implemented
- ✅ References fixed in abstract plugin
- ✅ Marketplace integration

### Phase 2: Plugin Updates (Next)
For each plugin with hooks:

1. **abstract/**
   - Add hookify-template skill
   - Example: "Prevent skill modifications without validation"

2. **conserve/**
   - Add hookify examples for resource limits
   - Example: "Warn when file operations exceed 1MB"

3. **imbue/**
   - Add hookify examples for review workflows
   - Example: "Require evidence before completing review"

4. **memory-palace/**
   - Add hookify examples for knowledge intake
   - Example: "Remind to tag knowledge entries"

5. **sanctum/**
   - Add hookify examples for git safety
   - Example: "Block force push to main"

6. **parseltongue/**
   - Add hookify examples for code quality
   - Example: "Warn about print statements in Python"

7. **pensive/**
   - Add hookify examples for review gates
   - Example: "Require security review for auth code"

### Phase 3: Advanced Integration
- Hook-to-hookify conversion tool
- Hookify rule discovery UI
- Cross-plugin rule coordination
- Rule effectiveness analytics

## Benefits

### For Plugin Authors
- Easier to ship simple validations
- Lower barrier than SDK hooks
- Can provide both SDK + hookify options

### For End Users
- Can customize plugin behavior without code
- Gradual complexity curve: rules → hooks → SDK
- Clear separation of concerns

### For Ecosystem
- Consistent validation patterns
- Shareable rule libraries
- Better discoverability

## Example: Parseltongue + Hookify

**parseltongue/examples/hookify/warn-print-debug.local.md:**
```yaml
---
name: warn-print-debug
enabled: true
event: file
action: warn
conditions:
  - field: file_path
    operator: regex_match
    pattern: \.py$
  - field: new_text
    operator: regex_match
    pattern: ^\s*print\(
---

🐛 **Print statement detected in Python!**

Parseltongue detected a print() call. Consider using logging:

\`\`\`python
import logging
logger = logging.getLogger(__name__)
logger.debug("Debug info", extra={"data": value})
\`\`\`

Or use:
- `/parseltongue:suggest-logging` for auto-conversion
- Disable this rule: `enabled: false`
```

**Integration hooks:**
```python
# parseltongue can detect when hookify triggers and offer deeper help
@hook("PostHookifyMatch")
async def offer_logging_conversion(match_data):
    if match_data["rule_name"] == "warn-print-debug":
        return {
            "suggestions": [
                "/parseltongue:convert-to-logging",
                "/parseltongue:add-logger-config"
            ]
        }
```

## Migration Path

1. **Week 1**: Update all plugins with hookify examples
2. **Week 2**: Add hookify-template skills
3. **Week 3**: Implement hook-to-hookify suggestions
4. **Week 4**: Build rule discovery system

## Success Metrics

- Number of active hookify rules per user
- Reduction in unwanted behaviors
- Plugin adoption rates
- User feedback on rule complexity
