---
name: shared-shell-execution
description: Shared shell execution patterns for external LLM delegation services
category: delegation-infrastructure
tags: [shell-execution, delegation, cli, services]
dependencies: []
estimated_tokens: 400
---

# Shared Shell Execution Capability

## Overview

This module provides shared shell execution functionality for all delegation services (Gemini, Qwen, etc.). It standardizes command construction, execution, error handling, and logging across different external LLM services.

## Core Components

### 1. Service Registry
```python
class DelegationService:
    """Registry for external LLM delegation services"""

    def __init__(self, name: str, command_prefix: str, auth_method: str):
        self.name = name
        self.command_prefix = command_prefix
        self.auth_method = auth_method
        self.quota_manager = None
        self.usage_logger = None
```

### 2. Command Builder
```python
class CommandBuilder:
    """Builds standardized commands for different services"""

    def build_command(self, service: DelegationService, prompt: str,
                     files: List[str], options: Dict) -> str:
        """Build service-specific command with standard options"""
```

### 3. Execution Engine
```python
class ExecutionEngine:
    """Handles command execution with common patterns"""

    def execute(self, command: str, service: DelegationService) -> ExecutionResult:
        """Execute command with error handling and logging"""
```

## Supported Services

### Gemini CLI
```bash
# Standard pattern
gemini -p "@path/to/file Analyze this code"
gemini --model gemini-2.5-pro-exp -p "..."
gemini --output-format json -p "..."
```

### Qwen CLI (when available)
```bash
# Assuming Qwen has similar CLI interface
qwen -p "@path/to/file Analyze this code"
qwen --model qwen-max -p "..."
qwen --format markdown -p "..."
```

## Common Delegation Flow

1. **Service Selection**: Choose appropriate service based on task requirements
2. **Authentication**: Verify service authentication using service-specific methods
3. **Quota Check**: Check service-specific limits and usage
4. **Command Construction**: Build standardized command using shared builder
5. **Execution**: Execute with common error handling and logging
6. **Result Processing**: Standardized result validation and integration

## Configuration

### Service Configuration
```json
{
  "services": {
    "gemini": {
      "command": "gemini",
      "auth_method": "api_key",
      "quota_limits": {
        "requests_per_minute": 60,
        "requests_per_day": 1000,
        "tokens_per_day": 1000000
      }
    },
    "qwen": {
      "command": "qwen",
      "auth_method": "mcp",
      "quota_limits": {
        "requests_per_minute": 120,
        "requests_per_day": 2000,
        "tokens_per_day": 2000000
      }
    }
  }
}
```

## Usage Examples

### Basic Delegation
```python
from delegation_core import Delegator

delegator = Delegator()
result = delegator.delegate(
    service="gemini",
    prompt="Analyze these files for security issues",
    files=["src/main.py", "src/auth.py"],
    options={"model": "gemini-2.0-pro-exp"}
)
```

### Service Selection Based on Requirements
```python
# Auto-select best service
result = delegator.smart_delegate(
    prompt="Summarize this large codebase",
    files=["src/**/*"],
    requirements={"large_context": True, "fast_response": False}
)
```
