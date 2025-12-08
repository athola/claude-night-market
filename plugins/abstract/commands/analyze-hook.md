---
name: analyze-hook
description: Analyze individual hook files for security vulnerabilities, performance issues, and compliance with best practices
usage: /analyze-hook [hook-path] [options]
---

# Analyze Hook

Analyzes individual hook files (both JSON configuration hooks and executable script hooks) for security vulnerabilities, performance issues, and compliance with Claude Code hook development best practices.

## Usage

```bash
# Analyze specific hook file
/analyze-hook hooks/pre-skill-load.json

# Analyze executable hook
/analyze-hook hooks/validate.sh

# Analyze all hooks in directory
/analyze-hook hooks/

# Security-focused analysis
/analyze-hook hooks/my-hook.py --security-scan

# Performance benchmarking
/analyze-hook hooks/slow-hook.sh --performance-check

# Compliance checking
/analyze-hook hooks/config.json --compliance-check

# Generate detailed report
/analyze-hook hooks/ --verbose --format detailed
```

## Options

- `--security-scan`: Focus on security vulnerability detection
- `--performance-check`: Analyze execution performance and resource usage
- `--compliance-check`: Validate against Claude Code hook standards
- `--verbose`: Show detailed analysis and recommendations
- `--format <type>`: Output format (summary, detailed, json, sarif)
- `--scope <type>`: Filter by hook scope (plugin, project, global)
- `--severity <level>`: Minimum severity level to report (low, medium, high, critical)

## Analysis Categories

### Security Analysis
- **Injection Vulnerabilities**: Command injection, code injection, SQL injection patterns
- **Path Traversal**: Unvalidated file paths, directory traversal attacks
- **Privilege Escalation**: Sudo usage, chmod operations, system calls
- **Input Validation**: Unsanitized user input, environment variable usage
- **Crypto Issues**: Weak encryption, hardcoded secrets, insecure randomness

### Performance Analysis
- **Execution Time**: Hook latency vs. acceptable thresholds
- **Memory Usage**: Memory consumption and potential leaks
- **I/O Operations**: File reads, network calls, blocking operations
- **Resource Efficiency**: CPU usage, pattern matching efficiency
- **Scalability**: Performance under load, large file handling

### Compliance Analysis
- **Structure Compliance**: Proper hook JSON schema, script structure
- **Documentation**: Required metadata, clear descriptions
- **Error Handling**: Proper exit codes, error reporting
- **Best Practices**: Variable quoting, set operations, timeout handling
- **Scope Appropriateness**: Correct hook placement and precedence

## Output Examples

### Basic Analysis
```bash
/analyze-hook hooks/pre-skill-load.json
# === Analysis for: hooks/pre-skill-load.json ===
# Type: Declarative Hook (JSON)
# Security Score: 85/100 (Good)
# Performance Score: 90/100 (Excellent)
# Compliance Score: 88/100 (Good)
# Overall Score: 87/100 (Good)
#
# === Issues Found ===
# MEDIUM: Missing timeout configuration for dependency_check
# LOW: Consider adding logging configuration for debugging
```

### Security Scan
```bash
/analyze-hook hooks/validate.sh --security-scan
# === Security Analysis: hooks/validate.sh ===
# Security Score: 65/100 (Needs Improvement)
#
# === Critical Issues ===
# [CRITICAL] Line 15: Potential command injection - unquoted $CLAUDE_TOOL_INPUT
# [HIGH] Line 23: Use of eval() with user input
#
# === Recommendations ===
# - Quote all environment variables: "$CLAUDE_TOOL_INPUT"
# - Replace eval() with safer alternatives
# - Add input validation for file paths
```

### Performance Check
```bash
/analyze-hook hooks/slow-hook.sh --performance-check
# === Performance Analysis: hooks/slow-hook.sh ===
# Performance Score: 45/100 (Poor)
#
# === Performance Issues ===
# [HIGH] Estimated execution time: 450ms (threshold: 100ms)
# [MEDIUM] Synchronous file operations in loop
# [LOW] Inefficient regex pattern matching
#
# === Optimization Suggestions ===
# - Use async I/O for file operations
# - Cache file statistics to reduce system calls
# - Compile regex patterns outside loops
```

## Integration with Hooks-Eval

This command integrates with the broader hooks-eval framework:

```bash
# Typical workflow
/analyze-hook hooks/ --scope-check        # Verify hook placement
/analyze-hook hooks/*.json --compliance    # Check standards compliance
/analyze-hook hooks/*.py --security-scan   # Security audit
/hooks-eval --comprehensive               # Full plugin evaluation
```

## Implementation

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/hooks_eval/hook_analyzer.py \
  --target "${1:-.}" \
  --security-scan ${2:+--$2} \
  --performance-check ${3:+--$3}
```

## Exit Codes

- `0`: Success - no issues found
- `1`: Warnings found - minor issues detected
- `2`: Errors found - significant issues requiring attention
- `3`: Critical issues found - security vulnerabilities or major problems

## Related Commands

- `/hooks-eval` - Comprehensive hook evaluation for entire plugin
- `/validate-plugin` - Complete plugin structure validation
- `/skills-eval` - Skill quality evaluation (for hooks that interact with skills)
