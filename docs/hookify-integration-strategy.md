# Hookify & Hook-Authoring Integration Strategy

## Current State

We have three complementary hook systems:
1. **abstract:hook-authoring** - SDK-level Python hooks for plugin developers
2. **abstract:hook-scope-guide** - Architectural guidance on hook placement
3. **hookify** - Markdown-based rules for end users

## Integration Strategy

### 1. Plugin-Declared Hookify Rules
Plugins can ship with recommended hookify rules in `examples/hookify/`. For example, `plugins/parseltongue/` might include `prevent-mixed-quotes.local.md` and `warn-missing-tests.local.md`, which users can then enable via the `/hookify:install` command.

### 2. Hook Authoring -> Hookify Generation
SDK hooks can auto-generate hookify rule suggestions. A plugin's SDK hook could identify simple pattern matches during validation and suggest a corresponding hookify rule, such as warning against print statements in favor of logging.

### 3. Hookify -> Hook Integration
Hookify rules can trigger plugin-specific hooks through their configuration. By defining an `invoke_hook` action in the rule's YAML frontmatter, a match on a specific file pattern can trigger a plugin validation step like `parseltongue:validate-syntax`.

### 4. Plugin-Specific Rule Templates
Each plugin can provide templates in `skills/hookify-templates.md`. These templates offer pre-configured rules for common scenarios like preventing TODO comments in production, warning about missing type hints, or blocking commits that lack associated tests.

### 5. Context-Aware Rule Suggestions
When a user runs `/hookify` without arguments in a specific project context, the system can suggest relevant rules. In a Python project, Parseltongue might suggest code quality rules, Pensive could offer review guidelines, and Sanctum might provide git workflow safety checks.

## Implementation Plan

### Phase 1: Foundation (Current)
The initial phase is complete, with the Hookify plugin implemented, references updated in the abstract plugin, and integration with the marketplace established.

### Phase 2: Plugin Updates (Next)
The next phase involves updating each plugin that utilizes hooks. This includes adding hookify-template skills to `abstract/`, resource limit examples to `conserve/`, and review workflow requirements to `imbue/`. Knowledge intake reminders will be added to `memory-palace/`, git safety rules to `sanctum/`, and Python-specific code quality warnings to `parseltongue/`. Finally, `pensive/` will be updated with review gates for security-sensitive code.

### Phase 3: Advanced Integration
Future development will focus on a hook-to-hookify conversion tool, a rule discovery interface, and cross-plugin coordination. We also plan to implement analytics to track the effectiveness of different rules.

## Analysis of Outcomes

Integrating Hookify with the plugin ecosystem simplifies the process for authors to ship validations without the higher entry barrier of SDK hooks. For end users, this approach provides a way to customize plugin behavior without writing code and offers a gradual complexity curve from simple rules to full SDK implementations. The result is a more consistent set of validation patterns and shareable rule libraries that improve discoverability across the ecosystem.

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

Print statement detected in Python!

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
