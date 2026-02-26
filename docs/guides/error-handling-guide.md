# Error Handling Guide

This guide details error handling patterns and troubleshooting strategies for Night Market plugins.

## Error Classification System

Night Market uses the `leyline:error-patterns` standard for classification:

- **Critical (E001-E099)**: Halt execution immediately.
- **Recoverable (E010-E099)**: Retry using exponential backoff.
- **Warnings (E020-E099)**: Log the event and continue execution.

## Plugin-Specific Patterns

### abstract: Core Infrastructure

Common failures include TDD test mismatches, skill discovery errors, and anti-rationalization triggers. If the Skill tool is unavailable, read the `SKILL.md` file directly from the plugin directory as a secondary strategy.

### conserve: Context Optimization

Failures typically involve context pressure, module deadlocks, or memory fragmentation. Recovery thresholds trigger at specific levels: 95% for aggressive compaction, 85% for selective removal, and 70% for standard monitoring.

### memory-palace: Knowledge Management

Failures occur during content fetching, storage access, or index synchronization. Health checks verify storage availability, index integrity, and concurrency safety.

### parseltongue: Python Development

Common issues include event loop blocking and task leaks. Prevent these by using async-native libraries, tracking all spawned tasks, and enforcing timeouts on network operations.

### sanctum: Git Workflows

Failures often involve test generation errors or mock misconfigurations. CI/CD pipelines use automated detection to trigger recovery actions based on the specific error code.

## Troubleshooting Workflow

### Step 1: Diagnosis

Execute health check scripts to identify the failing component:

```bash
# System-wide health check
python -m abstract.tools.health_check

# Plugin-specific check
python -m memory_palace.tools.health_check

# Quota status check
python conjure/scripts/quota_tracker.py --status
```

### Step 2: Identification

Map the error code to its category: Critical (Stop), Recoverable (Retry), or Warning (Log).

### Step 3: Recovery

Apply the strategy corresponding to the category. Critical errors require halting execution and preserving state for manual investigation. Recoverable errors use exponential backoff (1s, 2s, 4s, 8s). Warnings are logged as metrics for trend monitoring.

### Step 4: Prevention

After resolution, document the root cause and add a health check test to detect the failure early in future runs. Implement prevention measures and update relevant team documentation.

## Integration with leyline:error-patterns

The error handling system uses `leyline`'s shared infrastructure for classification and logging.

### Shared Infrastructure

Implement `ErrorClassifier` for plugin-specific logic. For example, a skill classifier might mark `SkillNotFoundError` as critical and `TemporaryServiceError` as recoverable.

### Unified Logging

Use `ErrorLogger` to capture structured data. Include the error instance, context such as skill name and input data, and the applied recovery strategy.

## Best Practices

### 1. Fail Fast and Explicitly

Raise specific exceptions that include debugging context. For example, `SkillNotFoundError` should report the searched paths rather than a generic "Skill not found" message.

### 2. Provide Recovery Steps

Include actionable recovery steps in the exception. A `QuotaExceededError` should detail the current usage, the limit, and the recommended wait time or frequency reduction.

### 3. Use Structured Logging

Log error data as structured fields rather than formatted strings. Include the skill name, error type, input size, execution time, and stack trace to allow for efficient filtering and analysis.

### 4. Implement Circuit Breakers

Use circuit breakers to prevent cascading failures. A breaker monitors failure counts and transitions to an 'open' state after a threshold, blocking subsequent calls until the system stabilizes.

## Testing

### Unit Testing

Verify that exceptions provide the necessary guidance. Tests should assert that error messages contain specific verification steps or searched paths.

### Integration Testing

Test recovery logic by simulating failures. For example, use a mock to trigger `QuotaExceededError` and verify that the system attempts the correct number of retries with exponential backoff.

## Monitoring

Track error rates by category, recovery success percentages, and mean time to recovery (MTTR). Alert thresholds should trigger based on critical error rates or circuit breaker transitions.
