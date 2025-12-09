"""Pytest configuration and shared fixtures for conjure tests."""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def temp_config_dir(tmp_path: Path) -> Path:
    """Create a temporary configuration directory."""
    config_dir = tmp_path / ".claude" / "hooks" / "delegation"
    config_dir.mkdir(parents=True)
    return config_dir


@pytest.fixture
def sample_config_file(temp_config_dir: Path) -> Path:
    """Create a sample configuration file."""
    config_file = temp_config_dir / "config.json"
    sample_config = {
        "services": {
            "custom_service": {
                "name": "custom_service",
                "command": "custom",
                "auth_method": "api_key",
                "auth_env_var": "CUSTOM_API_KEY",
                "quota_limits": {
                    "requests_per_minute": 30,
                    "requests_per_day": 500,
                    "tokens_per_day": 500000,
                },
            }
        }
    }
    config_file.write_text(json.dumps(sample_config, indent=2))
    return config_file


@pytest.fixture
def sample_usage_log(temp_config_dir: Path) -> Path:
    """Create a sample usage log file."""
    usage_log = temp_config_dir / "usage.jsonl"
    sample_entries = [
        {
            "timestamp": "2025-01-01T10:00:00",
            "service": "gemini",
            "command": "gemini -p test prompt",
            "success": True,
            "duration": 2.5,
            "tokens_used": 100,
            "exit_code": 0,
            "error": None,
        },
        {
            "timestamp": "2025-01-01T10:05:00",
            "service": "qwen",
            "command": "qwen -p another test",
            "success": False,
            "duration": 1.2,
            "tokens_used": 50,
            "exit_code": 1,
            "error": "Authentication failed",
        },
    ]

    with open(usage_log, "w") as f:
        for entry in sample_entries:
            f.write(json.dumps(entry) + "\n")

    return usage_log


@pytest.fixture
def sample_files(tmp_path: Path) -> list[Path]:
    """Create sample files for testing."""
    files = []

    # Python file
    py_file = tmp_path / "test.py"
    py_file.write_text("def hello():\n    print('Hello, World!')\n")
    files.append(py_file)

    # Markdown file
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test Document\n\nThis is a test markdown file.")
    files.append(md_file)

    # JSON file
    json_file = tmp_path / "test.json"
    json_file.write_text('{"name": "test", "value": 123}')
    files.append(json_file)

    return files


@pytest.fixture
def mock_subprocess_run():
    """Mock subprocess.run for testing."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "Test output"
    mock_result.stderr = ""
    return mock_result


@pytest.fixture
def mock_tiktoken_encoder():
    """Mock tiktoken encoder for testing."""
    mock_encoder = MagicMock()
    mock_encoder.encode.return_value = list(range(100))  # Mock 100 tokens
    return mock_encoder


@pytest.fixture
def delegation_service_config():
    """Sample service configuration for testing."""
    return {
        "name": "test_service",
        "command": "test",
        "auth_method": "api_key",
        "auth_env_var": "TEST_API_KEY",
        "quota_limits": {
            "requests_per_minute": 60,
            "requests_per_day": 1000,
            "tokens_per_day": 1000000,
        },
    }


@pytest.fixture
def gemini_hook_script_content():
    """Content for gemini bridge hook script."""
    return """#!/bin/bash
# Gemini bridge hook script

echo "Gemini bridge hook executed"
echo "Arguments: $@"
"""


@pytest.fixture
def sample_skill_content():
    """Sample skill file content for testing."""
    return """---
name: gemini-delegation
description: Delegate tasks to Gemini models
category: delegation
tags: [gemini, delegation, llm]
dependencies: []
author: conjure-plugin
version: 1.0.0
---

# Gemini Delegation

## Overview

This skill enables delegation of tasks to Google's Gemini models.

## Usage

Use this skill when you need to:
- Delegate complex reasoning tasks
- Generate code with Gemini
- Process large documents

## Examples

```bash
conjure gemini "Explain this code" --files src/
```


## Implementation Guide

`★ Insight ─────────────────────────────────────`
The conjure plugin follows a **unified delegation pattern** where multiple LLM
services (Gemini, Qwen) are abstracted behind a common interface. This design enables:
- **Service polymorphism**: Easy addition of new LLM providers
- **Consistent error handling**: Unified approach to timeouts and failures
- **Cross-service logging**: Centralized usage tracking and quota management
`─────────────────────────────────────────────────`

The test structure follows **behavior-driven development** principles:
- **Given/When/Then** pattern for readable test scenarios
- **Test doubles** (mocks, fixtures) for isolated unit testing
- **Integration tests** that verify end-to-end workflows
- **Edge case coverage** for timeout, authentication, and quota scenarios
"""
