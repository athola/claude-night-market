---
name: validate-hook
description: |
  Hook validation with security scan, performance check, and compliance verification.

  Triggers: validate hook, hook security, hook performance, hook compliance,
  hook audit, check hook, verify hook, hook safety

  Use when: developing hooks and need validation before deployment, auditing
  existing hooks for security vulnerabilities, checking hook performance,
  verifying compliance with best practices, before committing hook changes

  DO NOT use when: creating new hooks - use /create-hook instead.
  DO NOT use when: evaluating all hooks in plugin - use /hooks-eval instead.
  DO NOT use when: deciding hook placement - use hook-scope-guide skill.

  Use this command before deploying any hook to production.
usage: /validate-hook [hook-path] [--security] [--performance] [--compliance] [--all]
---

# Validate Hook Command

Comprehensive validation for Claude Code and SDK hooks. Performs security scanning, performance analysis, and compliance verification to ensure hooks are safe, efficient, and correctly implemented.

## Usage

```bash
# Validate all aspects (default)
/validate-hook hooks/my-hook.py

# Validate specific aspects
/validate-hook hooks/my-hook.py --security
/validate-hook hooks/my-hook.py --performance
/validate-hook hooks/my-hook.py --compliance

# Validate all hooks in directory
/validate-hook hooks/ --all

# Generate detailed report
/validate-hook hooks/my-hook.py --report

# Auto-fix issues where possible
/validate-hook hooks/my-hook.py --fix
```

## Validation Categories

### Security Scan (`--security`)

Checks for security vulnerabilities and unsafe patterns.

#### Input Validation

**Checks**:
- Are tool inputs validated before use?
- Are expected data types enforced?
- Are input sizes bounded?
- Are dangerous inputs sanitized?

**Example Issues**:

```python
# L FAIL: No input validation
def on_tool_use(context, tool_name, tool_input):
    command = tool_input["command"]  # Unsafe!
    os.system(command)

#  PASS: Proper validation
def on_tool_use(context, tool_name, tool_input):
    if "command" not in tool_input:
        raise ValueError("Missing required field: command")

    command = str(tool_input["command"])
    if len(command) > 1000:
        raise ValueError("Command too long")

    # Whitelist validation
    allowed_commands = ["ls", "pwd", "git status"]
    if command not in allowed_commands:
        raise ValueError(f"Command not allowed: {command}")
```

#### Secret Exposure

**Checks**:
- No API keys/tokens in logs?
- No credentials in error messages?
- Sensitive data redacted in output?
- Environment variables handled safely?

**Example Issues**:

```python
# L FAIL: Logging secrets
def on_tool_start(context, tool_name, tool_input):
    logger.info(f"API key: {os.getenv('API_KEY')}")  # Unsafe!
    logger.info(f"Full input: {tool_input}")  # May contain secrets!

#  PASS: Redacted logging
def on_tool_start(context, tool_name, tool_input):
    redacted_input = redact_secrets(tool_input)
    logger.info(f"Sanitized input: {redacted_input}")
```

#### Injection Risks

**Checks**:
- User input sanitized before command execution?
- SQL queries use parameterization?
- Shell commands avoid injection?
- Template rendering escapes user data?

**Example Issues**:

```python
# L FAIL: Command injection risk
def on_tool_use(context, tool_name, tool_input):
    filename = tool_input["file"]
    os.system(f"cat {filename}")  # Injection possible!

#  PASS: Safe execution
def on_tool_use(context, tool_name, tool_input):
    filename = tool_input["file"]
    # Validate filename
    if not re.match(r'^[\w\-\.]+$', filename):
        raise ValueError("Invalid filename")
    # Use subprocess with list args
    subprocess.run(["cat", filename], check=True)
```

#### Sandbox Compliance

**Checks**:
- Respects file system boundaries?
- No network access unless authorized?
- No privilege escalation attempts?
- Resource limits respected?

#### Error Handling

**Checks**:
- Fails safely on errors?
- No sensitive data in exceptions?
- Errors logged appropriately?
- No silent failures?

**Security Scan Output**:

```
=================================================
SECURITY SCAN
=================================================
Hook: hooks/gemini/bridge.on_tool_start
Date: 2025-12-06 14:23:18

INPUT VALIDATION
-------------------------------------------------
 Tool input type checking present
 Input size bounds enforced
 ERROR: No validation for 'command' field (line 42)
  Risk: Command injection
  Severity: CRITICAL
  Fix: Add whitelist or regex validation

SECRET EXPOSURE
-------------------------------------------------
 No API keys in logs
 WARNING: Potential secret logging at line 67
  Code: logger.debug(f"Full context: {context}")
  Risk: Context may contain sensitive data
  Severity: HIGH
  Fix: Redact sensitive fields before logging

INJECTION RISKS
-------------------------------------------------
 No SQL queries
 Subprocess uses list arguments
 No eval() or exec() usage
 Template rendering escaped

SANDBOX COMPLIANCE
-------------------------------------------------
 File access within allowed paths
 No network calls
 No privilege escalation
 Resource limits enforced

ERROR HANDLING
-------------------------------------------------
 Try/except blocks present
 Errors logged appropriately
� SUGGESTION: Add specific error types for better handling
  Line: 89
  Current: except Exception as e
  Suggested: except (ValueError, IOError) as e

SUMMARY
-------------------------------------------------
Total Checks: 18
Passed: 13 (72%)
Warnings: 2
Errors: 1
Critical: 1

Security Score: 67/100

RECOMMENDATION: Fix CRITICAL issues before deployment
```

### Performance Check (`--performance`)

Analyzes hook efficiency and resource usage.

#### Async Usage

**Checks**:
- Async/await used for I/O operations?
- No blocking calls in async context?
- Proper async error handling?
- Concurrent operations optimized?

**Example Issues**:

```python
# L FAIL: Blocking in async context
async def on_tool_start(context, tool_name, tool_input):
    time.sleep(1)  # Blocks entire event loop!
    data = requests.get(url)  # Blocking I/O!

#  PASS: Proper async
async def on_tool_start(context, tool_name, tool_input):
    await asyncio.sleep(1)  # Non-blocking
    async with aiohttp.ClientSession() as session:
        data = await session.get(url)  # Async I/O
```

#### Timeout Handling

**Checks**:
- Reasonable timeout limits set?
- Timeouts enforced for external calls?
- No infinite loops?
- Timeout errors handled gracefully?

**Example Issues**:

```python
# L FAIL: No timeout
def on_tool_use(context, tool_name, tool_input):
    response = requests.get(url)  # No timeout!

#  PASS: Timeout enforced
def on_tool_use(context, tool_name, tool_input):
    try:
        response = requests.get(url, timeout=15)
    except requests.Timeout:
        logger.warning("Request timed out")
        return {"status": "timeout"}
```

#### Memory Management

**Checks**:
- No unbounded data accumulation?
- Large objects cleaned up?
- No memory leaks in loops?
- Generators used for large datasets?

**Example Issues**:

```python
# L FAIL: Unbounded accumulation
def on_tool_use(context, tool_name, tool_input):
    all_results = []
    for item in large_dataset:  # Loads entire dataset!
        all_results.append(process(item))
    return all_results

#  PASS: Streaming processing
def on_tool_use(context, tool_name, tool_input):
    def process_stream():
        for item in large_dataset:  # Generator
            yield process(item)
    return {"results": list(itertools.islice(process_stream(), 100))}
```

#### I/O Efficiency

**Checks**:
- Batched writes where appropriate?
- File handles closed properly?
- No unnecessary I/O operations?
- Caching used effectively?

#### Early Returns

**Checks**:
- Quick validation before expensive operations?
- Early exit on errors?
- No unnecessary processing?

**Performance Check Output**:

```
=================================================
PERFORMANCE CHECK
=================================================
Hook: hooks/gemini/bridge.on_tool_start
Date: 2025-12-06 14:23:18

ASYNC USAGE
-------------------------------------------------
 Async/await properly used
 No blocking calls in async context
 Async error handling present
 Concurrent operations with gather()

TIMEOUT HANDLING
-------------------------------------------------
 Timeout set for API calls (15s)
 Timeout error handling present
� SUGGESTION: Consider shorter timeout for health checks
  Line: 45
  Current: timeout=15
  Suggested: timeout=5 for non-critical checks

MEMORY MANAGEMENT
-------------------------------------------------
 No unbounded accumulation
 Large objects properly scoped
� SUGGESTION: Consider batching log writes
  Line: 78-92
  Current: Individual writes in loop
  Suggested: Batch writes every 100 iterations

LATENCY OPTIMIZATION
-------------------------------------------------
 Early validation returns
 Expensive operations deferred
 Caching implemented
 No redundant processing

I/O EFFICIENCY
-------------------------------------------------
 File handles closed (context managers)
 Minimal I/O operations
 Buffered writes used
� SUGGESTION: Cache repeated file reads
  Line: 134
  Called in loop: read_config()

SUMMARY
-------------------------------------------------
Total Checks: 15
Passed: 12 (80%)
Suggestions: 3
Issues: 0

Performance Score: 90/100

Estimated Latency: 12-18ms
Max Memory: ~2.3MB
Throughput: ~450 calls/sec

RECOMMENDATION: Performance good. Consider suggestions for optimization.
```

### Compliance Check (`--compliance`)

Verifies hook follows Claude Code/SDK specifications.

#### Hook Type Validity

**Checks**:
- Hook type is known event type?
- Hook file named correctly?
- Hook location valid?

**Known Hook Types**:
- `on_tool_start` / `before_tool_use`
- `after_tool_use` / `on_tool_end`
- `on_error`
- `on_context_update`
- `before_request`
- `after_response`

#### Signature Correctness

**Checks**:
- Function signature matches hook type?
- Required parameters present?
- Return type correct?
- Type hints accurate?

**Example Issues**:

```python
# L FAIL: Wrong signature
def on_tool_start(tool_name):  # Missing context parameter!
    pass

#  PASS: Correct signature
def on_tool_start(context: HookContext, tool_name: str, tool_input: dict) -> Optional[dict]:
    pass
```

#### Return Semantics

**Checks**:
- Return value type matches specification?
- Return value structure valid?
- Optional returns handled correctly?
- Modifying hooks return modified data?

**Example Issues**:

```python
# L FAIL: Wrong return type for modifying hook
def before_tool_use(context, tool_name, tool_input):
    tool_input["extra"] = "data"
    # Missing return! Must return modified input

#  PASS: Returns modified input
def before_tool_use(context, tool_name, tool_input):
    tool_input["extra"] = "data"
    return tool_input
```

#### SDK Compatibility

**Checks**:
- Imports from correct SDK version?
- Uses supported API methods?
- No deprecated functionality?
- Version constraints specified?

#### Scope Appropriateness

**Checks**:
- Hook scope matches usage (global/plugin/skill)?
- No global hooks that should be plugin-scoped?
- Skill hooks don't affect other skills?

**Compliance Check Output**:

```
=================================================
COMPLIANCE CHECK
=================================================
Hook: hooks/gemini/bridge.on_tool_start
Date: 2025-12-06 14:23:18

HOOK TYPE VALIDITY
-------------------------------------------------
 Valid hook type: on_tool_start
 File naming correct: bridge.on_tool_start
 Location valid: hooks/gemini/
 Hook registered properly

SIGNATURE CORRECTNESS
-------------------------------------------------
 Correct parameter count
 Required parameters present
 Parameter types correct
 Return type annotation present
 Type hints accurate

RETURN SEMANTICS
-------------------------------------------------
 Return type matches specification (Optional[dict])
 Return value structure valid
 None return handled (pass-through)
 Modified data returned when appropriate

SDK COMPATIBILITY
-------------------------------------------------
 Imports from correct SDK (v2024.1)
 Uses supported API methods
 No deprecated functionality
� SUGGESTION: Pin SDK version in requirements
  Current: claude-code-sdk>=2024.1
  Suggested: claude-code-sdk>=2024.1,<2025.0

SCOPE APPROPRIATENESS
-------------------------------------------------
 Hook scope: plugin (gemini)
 Scope matches usage pattern
� SUGGESTION: Consider plugin scope instead of global
  Context: Hook only used for Gemini delegation
  Current: Affects all tool calls
  Suggested: Scope to plugin or specific tools

DOCUMENTATION
-------------------------------------------------
 Docstring present
 Parameters documented
 Return value documented
 Example usage provided

SUMMARY
-------------------------------------------------
Total Checks: 18
Passed: 16 (89%)
Suggestions: 2
Issues: 0

Compliance Score: 95/100

RECOMMENDATION: Fully compliant. Consider suggestions for best practices.
```

## Combined Report

```bash
/validate-hook hooks/my-hook.py --all

=================================================
COMPREHENSIVE HOOK VALIDATION
=================================================
Hook: hooks/my-hook.py
Date: 2025-12-06 14:23:18

SECURITY: 67/100 (1 critical, 2 warnings)
PERFORMANCE: 90/100 (3 suggestions)
COMPLIANCE: 95/100 (2 suggestions)

Overall Score: 84/100

CRITICAL ISSUES (MUST FIX)
-------------------------------------------------
1. [SECURITY] Command injection vulnerability (line 42)
   Fix: Add input validation for 'command' field

HIGH PRIORITY WARNINGS
-------------------------------------------------
2. [SECURITY] Potential secret logging (line 67)
   Fix: Redact sensitive fields before logging

SUGGESTIONS (RECOMMENDED)
-------------------------------------------------
3. [PERFORMANCE] Batch log writes (line 78-92)
4. [PERFORMANCE] Cache repeated file reads (line 134)
5. [COMPLIANCE] Pin SDK version in requirements
6. [COMPLIANCE] Consider plugin scope instead of global

PASSED CHECKS: 41/51 (80%)

RECOMMENDATION
-------------------------------------------------
Fix critical security issue before deployment.
Address warnings for production readiness.
Consider suggestions for optimization.

Next Steps:
  1. Fix line 42: Add command validation
  2. Fix line 67: Implement secret redaction
  3. Re-run: /validate-hook hooks/my-hook.py --security
  4. Apply suggestions if time permits
```

## Exit Codes

Useful for CI/CD integration:

- **0**: All checks passed (score e95)
- **1**: Warnings present (score 80-94)
- **2**: Errors found (score 60-79)
- **3**: Critical security issues (score <60)

```bash
#!/bin/bash
# CI/CD usage
/validate-hook hooks/*.py --all
exit_code=$?

if [ $exit_code -eq 3 ]; then
  echo "CRITICAL: Security issues found. Blocking deployment."
  exit 1
elif [ $exit_code -eq 2 ]; then
  echo "ERROR: Issues found. Review required."
  exit 1
else
  echo "Validation passed. Proceeding with deployment."
fi
```

## Auto-Fix Mode

```bash
/validate-hook hooks/my-hook.py --fix

=================================================
AUTO-FIX MODE
=================================================
Hook: hooks/my-hook.py

Analyzing... [��������������������] 100%

Found 3 auto-fixable issues:

1. [SECURITY] Missing input validation (line 42)
   Fix: Add type checking and bounds
   Apply? (y/n): y 

2. [PERFORMANCE] Missing timeout (line 56)
   Fix: Add timeout=15
   Apply? (y/n): y 

3. [COMPLIANCE] Missing type hints (line 23)
   Fix: Add parameter annotations
   Apply? (y/n): y 

Applied 3 fixes.
Backup saved: hooks/my-hook.py.bak

Re-validating...

NEW SCORE: 92/100 (was 84/100)

Remaining issues require manual review.
```

## Best Practices

### When to Validate

- Before committing new hooks
- After modifying existing hooks
- Before deploying to production
- As part of CI/CD pipeline
- Quarterly security audits

### Score Interpretation

- **95-100**: Excellent, production ready
- **80-94**: Good, address warnings before production
- **60-79**: Needs work, fix errors
- **<60**: Not production ready, critical issues

### Common Patterns

**Good Hook Structure**:

```python
"""
Hook: on_tool_start
Description: Validates tool inputs before execution
Scope: Plugin (security-plugin)
"""

from typing import Optional
import logging

logger = logging.getLogger(__name__)

async def on_tool_start(
    context: HookContext,
    tool_name: str,
    tool_input: dict
) -> Optional[dict]:
    """
    Validates tool inputs and sanitizes sensitive data.

    Args:
        context: Hook execution context
        tool_name: Name of tool being executed
        tool_input: Tool input parameters

    Returns:
        Modified tool_input if validation passes, None for pass-through

    Raises:
        ValueError: If validation fails
    """
    # Early validation
    if not isinstance(tool_input, dict):
        raise ValueError("Tool input must be dict")

    # Input sanitization
    sanitized = sanitize_input(tool_input)

    # Timeout enforcement
    try:
        result = await asyncio.wait_for(
            process_input(sanitized),
            timeout=15.0
        )
    except asyncio.TimeoutError:
        logger.warning(f"Processing timeout for {tool_name}")
        return None

    # Return modified input
    return result
```

## Integration

Part of the hook development workflow:

1. Create hook skeleton
2. Implement functionality
3. **`/validate-hook`** � Security, performance, compliance check
4. Fix issues and re-validate
5. Test with `/test-skill`
6. Deploy with confidence

## Implementation

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/hook_validator.py \
  --hook "${1}" \
  --security="${2:-true}" \
  --performance="${3:-true}" \
  --compliance="${4:-true}" \
  --report
```

## See Also

- `/analyze-hook` - Hook complexity and impact analysis
- `/validate-plugin` - Full plugin structure validation
- `/test-skill` - Test skills that use hooks
- `docs/hook-scope-guide.md` - Hook scoping best practices
- `skills/hooks-eval/` - Hook evaluation framework
