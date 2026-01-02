# Check Async Command

## Usage

Analyzes Python async code for correctness, patterns, and potential issues.

### Basic Usage
```
/check-async
```
Analyzes async code in the current directory.

### Specific File
```
/check-async src/api/handlers.py
```

## What It Does

1. **Pattern Detection**: Identifies async/await usage patterns
2. **Issue Detection**: Finds common async pitfalls
3. **Blocking Call Detection**: Identifies blocking operations in async code
4. **Concurrency Analysis**: Reviews gather, create_task, and semaphore usage
5. **Best Practice Check**: Validates against async best practices

## Analysis Categories

- **Correctness**: Missing await, blocking calls, unclosed resources
- **Patterns**: Proper use of gather, create_task, semaphores
- **Error Handling**: CancelledError handling, timeout usage
- **Performance**: Connection pooling, rate limiting
- **Testing**: pytest-asyncio compatibility

## Common Issues Detected

- Missing `await` on coroutines
- Blocking calls (`time.sleep`, sync I/O) in async code
- Unhandled `CancelledError`
- Missing timeout handling
- Improper resource cleanup
- Missing connection pooling

## Output Format

For each file:
- Async function count
- Issues found with severity
- Pattern compliance score
- Specific recommendations

## Examples

```bash
# Check with detailed output
/check-async --verbose

# Focus on blocking calls
/check-async --blocking-only

# Include test files
/check-async --include-tests
```

## Integration

Uses the `python-async` skill's analysis tools:
- `async-analyzer`: Pattern and correctness analysis
- `concurrency-checker`: Concurrent operation validation

This command validates async code follows best practices and avoids common pitfalls.
