---
name: validate-hook
description: Validate hooks for security, performance, and SDK compliance
usage: /validate-hook [hook-path] [--security] [--performance] [--compliance] [--all] [--fix] [--report]
modules: [security-checks, performance-checks, compliance-checks]
---

# Validate Hook Command

<identification>
triggers: validate hook, hook security, hook performance, hook compliance, hook audit, check hook, verify hook

use_when:
- Developing hooks and need validation before deployment
- Auditing existing hooks for security vulnerabilities
- Checking hook performance and timeout compliance
- Verifying compliance with SDK best practices
- Before committing hook changes

do_not_use_when:
- Creating new hooks - use /create-hook instead
- Evaluating all hooks in plugin - use /hooks-eval instead
- Deciding hook placement - use hook-scope-guide skill
</identification>

Detailed validation for Claude Code and SDK hooks. Performs security scanning, performance analysis, and compliance verification.

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
Checks for security vulnerabilities and unsafe patterns:
- **Input Validation**: Type checking, size bounds, sanitization
- **Command Injection**: Shell command safety, parameter escaping
- **Path Traversal**: Path validation, directory restrictions
- **Data Leakage**: PII handling, credential exposure
- **Privilege Escalation**: Permission checks, sandboxing

**Score**: PASS (100%), WARN (80-99%), FAIL (<80%)

### Performance Check (`--performance`)
Analyzes hook efficiency and resource usage:
- **Timeout Compliance**: Execution within limits (1-10s typical)
- **Resource Usage**: Memory, CPU, file handles
- **Blocking Operations**: Async patterns, non-blocking I/O
- **Caching**: Result caching, expensive operation optimization
- **Early Exits**: Fast-path optimization

**Score**: OPTIMAL (>90%), ACCEPTABLE (70-90%), POOR (<70%)

### Compliance Check (`--compliance`)
Verifies SDK and best practice adherence:
- **SDK Version**: Compatible with installed version
- **Hook Schema**: Correct frontmatter, required fields
- **Output Format**: Valid JSON structure
- **Error Handling**: Try-catch blocks, graceful failures
- **Logging**: Structured logging, appropriate levels

**Score**: COMPLIANT (100%), MINOR ISSUES (95-99%), NON-COMPLIANT (<95%)

## Combined Report

```
VALIDATION REPORT: hooks/pre-tool-use.py
==========================================
SECURITY:     PASS (100%) - No issues found
PERFORMANCE:  WARN (85%)  - Consider async for file I/O
COMPLIANCE:   PASS (100%) - Fully compliant

OVERALL: PASS with 1 warning

Issues Found:
[PERFORMANCE/WARN] Line 45: Synchronous file read
  Impact: May block execution for large files
  Fix: Use async file I/O or implement timeout

Recommendations:
- Consider adding result caching for expensive operations
- Add unit tests for error paths
```

## Exit Codes

- `0`: PASS - Hook validated successfully
- `1`: WARN - Issues found, review recommended
- `2`: FAIL - Critical issues, must fix before deployment

## Auto-Fix Mode

```bash
/validate-hook hooks/my-hook.py --fix
```

Automatically applies fixes for common issues:
- Add missing input validation
- Implement timeout guards
- Fix JSON output structure
- Add error handling wrappers

**Note**: Review auto-fixes before committing.

## Detailed Validation Guides

For comprehensive validation patterns, see the validate-hook source code and examples in the abstract validation framework.

## Best Practices

**When to Validate**:
- Before every hook commit
- After modifying hook logic
- Before production deployment
- During security audits
- After SDK updates

**Score Interpretation**:
- **100%**: Production ready
- **95-99%**: Minor improvements recommended
- **80-94%**: Review and fix warnings
- **<80%**: Critical issues, must fix

**Common Patterns**:
- Validate inputs at entry points
- Use timeouts for all external operations
- Implement graceful error handling
- Cache expensive computations
- Log security-relevant events

## Integration

```bash
# Typical hook development workflow
/create-hook my-hook                # Create hook
/validate-hook hooks/my-hook.py     # Validate implementation
/hooks-eval --hook my-hook          # Evaluate in plugin context
git commit -m "Add validated hook"  # Commit validated hook
```

## Implementation

Uses the abstract validation framework:
```python
from abstract.validation import HookValidator

validator = HookValidator()
results = validator.validate_hook("hooks/my-hook.py")

if results.security.passed and results.performance.score > 80:
    print("Hook validated successfully")
else:
    print(f"Issues found: {results.issues}")
```

## See Also

- **/create-hook**: Create new hooks
- **/hooks-eval**: Evaluate all plugin hooks
- **abstract:hook-authoring**: Hook development guide
- **abstract:hook-scope-guide**: Hook placement strategy
