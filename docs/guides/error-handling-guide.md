# Error Handling Guide

**Last Updated**: 2025-01-08

## Overview

Comprehensive error handling patterns and troubleshooting strategies for Claude Night Market plugins. For detailed tutorial with code examples, see [error-handling-tutorial.md](../../book/src/tutorials/error-handling-tutorial.md).

## Error Classification System

Based on leyline:error-patterns standard:

- **Critical (E001-E099)**: Halt execution immediately
- **Recoverable (E010-E099)**: Retry with exponential backoff
- **Warnings (E020-E099)**: Log and continue

See tutorial for detailed classification and code examples.

## Plugin-Specific Patterns

### abstract: Core Infrastructure

**Common failures**: TDD test mismatches, skill discovery issues, anti-rationalization traps

**Skill Tool Unavailable Fallback**:
```
# Instead of: Skill(sanctum:commit-messages)
# Use:        Read plugins/sanctum/skills/commit-messages/SKILL.md
```

### conserve: Context Optimization

**Common failures**: Context pressure, module deadlocks, memory fragmentation

**Recovery thresholds**: 95% aggressive compaction, 85% selective, 70% monitor

### memory-palace: Knowledge Management

**Common failures**: Content fetching, storage conflicts, index corruption

**Health checks**: Storage availability, index integrity, search functionality, concurrency safety

### parseltongue: Python Development

**Common failures**: Event loop blocking, task leaks, deadlocks

**Prevention**: Use async equivalents, track all tasks, set timeouts

### sanctum: Git Workflows

**Common failures**: Test generation errors, import resolution, mock configuration

**CI/CD recovery**: Automated detection and recovery actions based on error type

## Troubleshooting Workflow

### Step 1: Quick Diagnosis

Use health check scripts to identify the issue:

```bash
# Check overall system health
python -m abstract.tools.health_check

# Check specific plugin
python -m memory_palace.tools.health_check

# Check quota status
python conjure/scripts/quota_tracker.py --status
```

### Step 2: Identify Error Category

Match error code to category:

- **E001-E099**: Critical → Stop and investigate
- **E010-E099**: Recoverable → Retry with backoff
- **E020-E099**: Warning → Log and continue

### Step 3: Apply Recovery Strategy

Follow the recovery steps for the specific scenario:

1. **Critical**: Halt execution, preserve state, alert operators
2. **Recoverable**: Retry with exponential backoff (1s, 2s, 4s, 8s)
3. **Warning**: Log metric, continue execution, monitor trends

### Step 4: Document and Prevent

After resolution:

1. Document root cause and resolution
2. Add health check for early detection
3. Implement prevention measures
4. Share learnings with team

## Integration with leyline:error-patterns

The error handling system integrates with `leyline`'s error pattern infrastructure:

### Shared Error Infrastructure

```python
from leyline.error_patterns import (
    ErrorClassifier,
    RecoveryStrategy,
    ErrorLogger,
    HealthChecker
)

class SkillErrorClassifier(ErrorClassifier):
    """Skill-specific error classification"""

    def classify(self, error: Exception) -> ErrorCategory:
        if isinstance(error, SkillNotFoundError):
            return ErrorCategory.CRITICAL
        elif isinstance(error, TemporaryServiceError):
            return ErrorCategory.RECOVERABLE
        else:
            return ErrorCategory.WARNING
```

### Unified Logging and Monitoring

```python
from leyline.error_patterns import ErrorLogger

logger = ErrorLogger(service="abstract")

try:
    skill.execute()
except Exception as e:
    logger.log_error(
        error=e,
        context={"skill": skill.name, "input": input_data},
        recovery_strategy=recovery_strategy
    )
```

## Best Practices

### 1. Fail Fast, Fail Clearly

```python
# Good: Specific error with context
def load_skill(skill_name: str) -> Skill:
    if not skill_exists(skill_name):
        raise SkillNotFoundError(
            skill_name,
            searched_paths=get_skill_search_paths()
        )

# Bad: Generic error
def load_skill(skill_name: str) -> Skill:
    if not skill_exists(skill_name):
        raise Exception("Skill not found")
```

### 2. Provide Recovery Guidance

```python
# Good: Error with recovery steps
raise QuotaExceededError(
    service="gemini",
    quota_type="rpm",
    current=65,
    limit=60,
    recovery_steps=[
        "Wait 60 seconds for rate limit window to reset",
        "Reduce request frequency",
        "Consider upgrading quota limits"
    ]
)

# Bad: Error without guidance
raise Exception("Quota exceeded")
```

### 3. Log Structured Data

```python
# Good: Structured logging
logger.error(
    "skill_execution_failed",
    extra={
        "skill_name": skill.name,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "input_size": len(input_data),
        "execution_time": elapsed_time,
        "traceback": traceback.format_exc()
    }
)

# Bad: Unstructured logging
logger.error(f"Error executing skill: {error}")
```

### 4. Implement Circuit Breakers

```python
class CircuitBreaker:
    """Prevent cascading failures"""

    def __init__(self, failure_threshold: int = 5):
        self.failure_threshold = failure_threshold
        self.failure_count = 0
        self.state = "closed"  # closed, open, half-open

    def call(self, func: Callable, *args, **kwargs):
        if self.state == "open":
            raise CircuitBreakerOpenError(
                "Circuit breaker is open. "
                f"Failures: {self.failure_count}/{self.failure_threshold}"
            )

        try:
            result = func(*args, **kwargs)
            self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
            raise
```

## Testing Error Scenarios

### Unit Testing Error Handling

```python
def test_skill_not_found_error():
    """Test SkillNotFoundError provides helpful guidance"""
    with pytest.raises(SkillNotFoundError) as exc_info:
        load_skill("nonexistent:skill")

    error = exc_info.value
    assert error.skill_name == "nonexistent:skill"
    assert len(error.searched_paths) > 0
    assert "verify SKILL.md" in str(error).lower()
```

### Integration Testing Recovery

```python
@pytest.mark.asyncio
async def test_quota_exceeded_recovery():
    """Test exponential backoff on quota exceeded"""
    tracker = GeminiQuotaTracker()

    # Simulate quota exceeded
    with patch.object(tracker, 'record_request') as mock_record:
        mock_record.side_effect = QuotaExceededError()

        with pytest.raises(QuotaExceededError):
            await tracker.execute_with_retry("test prompt")

        # Verify backoff was attempted
        assert mock_record.call_count == 3  # 3 retries
```

## Monitoring and Alerting

### Key Metrics to Track

1. **Error Rate**: Errors per minute by category
2. **Recovery Success Rate**: Percentage of errors successfully recovered
3. **Mean Time to Recovery (MTTR)**: Average time to resolve errors
4. **Circuit Breaker Trips**: Number of times circuit breakers opened

### Alert Thresholds

```yaml
alerts:
  - name: high_critical_error_rate
    condition: error_rate{category="critical"} > 5
    duration: 5m
    action: page_on_call

  - name: high_recovery_failure_rate
    condition: recovery_success_rate < 0.8
    duration: 10m
    action: create_ticket

  - name: circuit_breaker_open
    condition: circuit_breaker_state{state="open"} > 0
    duration: 1m
    action: alert_team
```

## Resources

### Documentation

- [Error Handling Template](../error-handling-template.md)
- [Plugin Development Guide](./plugin-dependency-pattern.md)
- [Architecture Decisions](../adr/)

### Related Skills

- `abstract:skill-authoring` - Creating robust skills
- `sanctum:test-updates` - Test-driven error handling
- `conserve:context-optimization` - Managing context pressure

### Tools

- `leyline:error-patterns` - Shared error infrastructure
- Health check scripts in each plugin
- Error logging and monitoring systems

## Conclusion

Effective error handling is critical for a reliable developer experience. By following these patterns, integrating with shared infrastructure, and implementing comprehensive troubleshooting, you can build skills that are both powerful and dependable.

Remember: **Good error handling is invisible until something goes wrong – then it's invaluable.**
