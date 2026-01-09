# Error Handling Guide

**Last Updated**: 2025-01-08
**Applies to**: All plugins and skills in the Claude Night Market ecosystem

## Overview

This guide provides comprehensive error handling patterns, troubleshooting strategies, and recovery mechanisms for skills and plugins across the Claude Night Market ecosystem. It builds upon the [error handling template](../error-handling-template.md) and provides real-world implementation examples.

## Why Error Handling Matters

### Critical Benefits

1. **Developer Experience**: Clear error messages with actionable guidance reduce debugging time
2. **Reliability**: Graceful degradation prevents cascading failures across the system
3. **Observability**: Structured error logging enables monitoring and alerting
4. **Maintainability**: Consistent error patterns make code easier to understand and modify

### Real-World Impact

- **Faster Resolution**: Step-by-step troubleshooting guides reduce mean-time-to-resolution
- **Better UX**: Users receive helpful error messages instead of cryptic failures
- **Proactive Prevention**: Health checks detect issues before they become critical

## Error Classification System

The ecosystem uses a standardized error classification system:

### Critical Errors (E001-E099)

System failures requiring immediate halt:

- **E001-E099**: Authentication and authorization failures
- **E020-E099**: Resource exhaustion (memory, disk, API quotas)
- **E040-E099**: Critical service dependencies unavailable
- **E060-E099**: Data corruption or integrity violations

**Response**: Immediately halt execution, log full context, alert operators

### Recoverable Errors (E010-E099)

Temporary issues with retry potential:

- **E010-E099**: Network timeouts and connection issues
- **E030-E099**: Temporary service unavailability
- **E050-E099**: Configuration issues (can be corrected)
- **E070-E099**: Rate limiting (backoff and retry)

**Response**: Log warning, attempt recovery with exponential backoff, escalate if retries exhausted

### Warnings (E020-E099)

Low-severity issues that don't block execution:

- **E020-E099**: Performance degradations
- **E080-E099**: Best practice violations
- **E090-E099**: Deprecated API usage

**Response**: Log informational message, continue execution, track metrics

## Implementation Patterns by Plugin

### abstract: Core Infrastructure

#### Skill Authoring (`plugins/abstract/skills/skill-authoring/SKILL.md`)

**Common Failure Scenarios**:

1. **TDD Test Failures**
   - **Symptom**: Test fails after implementation
   - **Root Cause**: Test mismatch with requirements or implementation bug
   - **Resolution**: Review test assertions, verify business logic, check edge cases
   - **Prevention**: Write tests first, keep tests simple and focused

2. **Skill Discovery Issues**
   - **Symptom**: Skill not found in skill registry
   - **Root Cause**: Missing or incorrect frontmatter, file location mismatch
   - **Resolution**: Verify SKILL.md frontmatter, check file path, restart Claude Code
   - **Prevention**: Use `abstract:plugin-validator` before committing

3. **Anti-Rationalization Traps**
   - **Symptom**: "This is simple enough to skip the skill"
   - **Root Cause**: Cognitive bias toward rationalization
   - **Resolution**: Always invoke skill if >1% chance it applies
   - **Prevention**: Follow red flags checklist in skill documentation

**Error Code Examples**:

```python
# E011: Skill discovery failure
class SkillNotFoundError(Exception):
    """Raised when a skill cannot be found in the registry"""
    def __init__(self, skill_name: str, searched_paths: list[Path]):
        self.skill_name = skill_name
        self.searched_paths = searched_paths
        super().__init__(
            f"Skill '{skill_name}' not found. "
            f"Searched {len(searched_paths)} locations. "
            f"Verify SKILL.md frontmatter and file location."
        )
```

### conserve: Context Optimization

#### Context Optimization (`plugins/conserv/skills/context-optimization/SKILL.md`)

**Common Failure Scenarios**:

1. **Context Pressure**
   - **Symptom**: Token limit approaching rapidly
   - **Root Cause**: Too much context loaded, inefficient summarization
   - **Resolution**: Trigger aggressive context compaction, prioritize recent context
   - **Prevention**: Monitor token usage proactively, set thresholds at 70%

2. **Module Coordination Deadlock**
   - **Symptom**: Multiple modules waiting for each other
   - **Root Cause**: Circular dependencies in context optimization
   - **Resolution**: Break circular dependency, prioritize one module
   - **Prevention**: Design modules with clear priority levels

3. **Memory Fragmentation**
   - **Symptom**: High memory usage with low actual context
   - **Root Cause**: Inefficient context storage, duplicate data
   - **Resolution**: Compact context, remove duplicates, restart session
   - **Prevention**: Use structured context format, avoid redundancy

**Recovery Strategy**:

```python
def handle_context_pressure(current_tokens: int, limit: int) -> Action:
    usage_ratio = current_tokens / limit

    if usage_ratio >= 0.95:
        # Critical: Emergency compaction
        return Action.COMPACT_AGGRESSIVE
    elif usage_ratio >= 0.85:
        # Warning: Selective compaction
        return Action.COMPACT_SELECTIVE
    elif usage_ratio >= 0.70:
        # Advisory: Log and monitor
        return Action.LOG_AND_MONITOR
    else:
        # Normal: No action
        return Action.CONTINUE
```

### memory-palace: Knowledge Management

#### Knowledge Intake (`plugins/memory-palace/skills/knowledge-intake/SKILL.md`)

**Common Failure Scenarios**:

1. **Content Fetching Failures**
   - **Symptom**: Unable to retrieve content from URL
   - **Root Cause**: Network issues, invalid URL, server errors
   - **Resolution**: Retry with exponential backoff, try alternative sources
   - **Prevention**: Validate URL format, check server availability first

2. **Storage Conflicts**
   - **Symptom**: Duplicate entry or version conflict
   - **Root Cause**: Concurrent updates, identifier collision
   - **Resolution**: Merge or version the entries, use conflict resolution
   - **Prevention**: Use unique identifiers, implement optimistic locking

3. **Index Corruption**
   - **Symptom**: Search returns incorrect or no results
   - **Root Cause**: Damaged index file, incomplete indexing
   - **Resolution**: Rebuild index from source data
   - **Prevention**: Regular index validation, atomic updates

**Health Check Implementation**:

```python
def check_knowledge_base_health() -> HealthStatus:
    checks = [
        check_storage_availability,
        check_index_integrity,
        check_search_functionality,
        check_concurrency_safety,
    ]

    results = [check() for check in checks]
    failed = [r for r in results if not r.passed]

    if failed:
        return HealthStatus(
            healthy=False,
            issues=[f.error for f in failed],
            recovery_steps=[f.recovery for f in failed]
        )

    return HealthStatus(healthy=True)
```

### parseltongue: Python Development

#### Python Async (`plugins/parseltongue/skills/python-async/SKILL.md`)

**Common Failure Scenarios**:

1. **Event Loop Blocking**
   - **Symptom**: Async operations stall or timeout
   - **Root Cause**: Synchronous code blocking event loop, long-running computations
   - **Resolution**: Move blocking operations to executor, use async equivalents
   - **Prevention**: Profile async code, avoid `time.sleep()`, use `asyncio.sleep()`

2. **Task Leaks**
   - **Symptom**: Memory usage grows, tasks never complete
   - **Root Cause**: Fire-and-forget tasks without proper cleanup, unawaited coroutines
   - **Resolution**: Track all tasks, implement task cleanup, use `asyncio.gather()`
   - **Prevention**: Always await or track tasks, use task groups

3. **Deadlocks**
   - **Symptom**: Application hangs, multiple tasks waiting
   - **Root Cause**: Circular wait conditions, incorrect lock ordering
   - **Resolution**: Break circular waits, reorder lock acquisition, add timeouts
   - **Prevention**: Use lock hierarchy, avoid nested locks, set timeouts

**Detection and Resolution**:

```python
async def detect_event_loop_block(timeout: float = 1.0) -> bool:
    """Check if event loop is blocked"""
    try:
        await asyncio.wait_for(
            asyncio.sleep(0),
            timeout=timeout
        )
        return False  # Not blocked
    except asyncio.TimeoutError:
        return True  # Blocked

async def prevent_task_leaks():
    """Ensure all tasks are properly tracked"""
    tasks = asyncio.all_tasks()
    main_task = asyncio.current_task()

    # Filter out the main task
    background_tasks = [t for t in tasks if t != main_task]

    # Wait for all background tasks with timeout
    await asyncio.wait_for(
        asyncio.gather(*background_tasks, return_exceptions=True),
        timeout=30.0
    )
```

### sanctum: Git Workflows

#### Test Updates (`plugins/sanctum/skills/test-updates/SKILL.md`)

**Common Failure Scenarios**:

1. **Test Generation Failures**
   - **Symptom**: Generated tests don't compile or fail unexpectedly
   - **Root Cause**: Missing imports, incorrect assertions, incompatible mocks
   - **Resolution**: Review generated code, add missing imports, fix assertions
   - **Prevention**: Validate generated tests before committing, use test templates

2. **Import Resolution Issues**
   - **Symptom**: Module not found errors in tests
   - **Root Cause**: Incorrect PYTHONPATH, missing test dependencies
   - **Resolution**: Update test configuration, install dependencies, check imports
   - **Prevention**: Use consistent import structure, document test dependencies

3. **Mock Configuration Errors**
   - **Symptom**: Mocks don't behave as expected
   - **Root Cause**: Incorrect mock setup, missing return values, wrong patch targets
   - **Resolution**: Verify mock configuration, check patch targets, add assertions
   - **Prevention**: Use explicit mock setup, document mock behavior

**CI/CD Integration**:

```python
def handle_test_failure(test_name: str, error: Exception) -> TestRecoveryAction:
    """Determine recovery action based on error type"""

    if isinstance(error, ImportError):
        return TestRecoveryAction(
            action="INSTALL_DEPENDENCIES",
            message=f"Missing import in {test_name}: {error}",
            command="pip install -e .[test]"
        )

    elif isinstance(error, AssertionError):
        return TestRecoveryAction(
            action="REVIEW_ASSERTION",
            message=f"Assertion failed in {test_name}: {error}",
            command=f"pytest {test_name} -vv"
        )

    elif isinstance(error, MockError):
        return TestRecoveryAction(
            action="FIX_MOCK",
            message=f"Mock configuration error in {test_name}: {error}",
            command=f"pytest {test_name} --tb=short"
        )

    else:
        return TestRecoveryAction(
            action="ESCALATE",
            message=f"Unexpected error in {test_name}: {error}",
            command=None
        )
```

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
