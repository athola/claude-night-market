# Hook Types Overview

For comprehensive hook types documentation, see:
**[Hook Types Guide](../../../../../docs/examples/hook-development/hook-types-comprehensive.md)**

## Quick Reference

### Lifecycle Hooks
- **SessionStart**: Initialization, context setup
- **SessionEnd**: Cleanup, metrics collection
- **Stop**: Graceful shutdown

### Tool Execution Hooks
- **PreToolUse**: Validation, logging, state management
- **PostToolUse**: Result processing, metrics, cleanup
- **ToolError**: Error handling, recovery

### Communication Hooks
- **UserPromptSubmit**: Input validation, routing
- **AssistantMessageChunk**: Response filtering, monitoring

### State Hooks (Advanced)
- **StateChange**: State transitions, validation
- **ContextUpdate**: Context management, optimization

## Hook Selection Guide

| Use Case | Recommended Hook | Why |
|----------|------------------|-----|
| Log all tool calls | PreToolUse | Captures before execution |
| Track execution time | Pre + PostToolUse | Measure duration |
| Validate inputs | UserPromptSubmit | Before processing |
| Filter responses | AssistantMessageChunk | Real-time filtering |
| Initialize session | SessionStart | One-time setup |
| Cleanup resources | SessionEnd/Stop | Guaranteed cleanup |

## See Complete Guide

The comprehensive hook types guide includes:
- Detailed lifecycle diagrams
- Complete code examples for each hook type
- Advanced patterns and combinations
- Performance considerations
- Migration guides

📖 **[Full Hook Types Guide](../../../../../docs/examples/hook-development/hook-types-comprehensive.md)**
