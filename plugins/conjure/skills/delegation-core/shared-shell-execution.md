---
name: shared-shell-execution
description: Shared shell execution contract for external LLM delegation services
category: delegation-infrastructure
tags: [shell-execution, delegation, cli, services]
dependencies: []
estimated_tokens: 400
---

# Shared Shell Execution Capability

## Overview

Every provider skill in this plugin delegates through one module,
`scripts/delegation_executor.py`.
The CLIs it spawns disagree about almost everything: whether the prompt
is positional or flagged, what the output-format flag is called, whether
a temperature flag exists, whether `@path` references resolve.
Each disagreement is declared as data on `ServiceConfig` rather than
branched on in the dispatcher, so adding a provider is a registry entry
and not a new code path.

## The provider contract

`ServiceConfig` is the whole contract.
The defaults reproduce the Gemini dialect, so a provider declares only
where it differs.

| Field | Default | What it controls |
|-------|---------|------------------|
| `command` | required | Binary spawned; must appear in `VERIFIED_BINARIES` |
| `subcommand` | `()` | Words between the binary and the flags |
| `prompt_flag` | `"-p"` | `None` delivers the prompt positionally |
| `output_format_flag` | `"--output-format"` | Spelling of the format flag |
| `temperature_flag` | `"--temperature"` | `None` suppresses the flag entirely |
| `inline_files` | `False` | Read file contents into the prompt |
| `stdin_prompt` | `False` | Deliver the prompt on stdin, not argv |
| `env` | `{}` | Child-only overlay; `${VAR}` names a credential |
| `version_probe` | `("--version",)` | Argv that makes the CLI state its version |
| `auth_probe` | `("auth", "status")` | Argv that reports credential state |
| `priority` | `50` | Position in the candidate order |
| `strengths` | `()` | Requirement keys this provider is preferred for |

## Supply chain

`VERIFIED_BINARIES` records the package, publisher, install command, and
source URL for every binary this module spawns.
Resolving an install command for a binary absent from that map raises
`UnverifiedBinaryError` rather than guessing one.
That is not hypothetical: #655 shipped a service naming a binary that an
unaffiliated npm package publishes.

## Delegation flow

1. `Delegator._select_service` reads the requirements and the registry to
   pick a provider.
2. `verify_service` probes the binary and its credentials, resolving the
   environment overlay first so an unset `${VAR}` is a named issue.
3. `quota_tracker` checks the provider's limits.
4. `_delivered_prompt` attaches file context by the provider's own
   convention: `@path` references, or inlined contents under a byte
   ceiling.
5. `build_command` assembles the argv from the contract fields.
6. `execute` spawns the child with the overlay applied and the prompt on
   argv or stdin.
7. `usage_logger` records the call.

## Configuration

`config.json` overrides only the fields it names.
An unrecognized field name raises rather than being ignored, and an
unlisted field keeps the value it already had, so overriding one
provider's quota cannot silently reset the flags that make its CLI work.

```json
{
  "services": {
    "gemini": {
      "quota_limits": {
        "requests_per_minute": 60,
        "requests_per_day": 1000,
        "tokens_per_day": 1000000
      }
    }
  }
}
```

## Usage

### From the command line

```bash
uv run python scripts/delegation_executor.py gemini "Analyze this module" \
  --files src/
uv run python scripts/delegation_executor.py --verify
```

### Through the Makefile

```bash
make -C plugins/conjure delegate-gemini PROMPT='Analyze this module'
make -C plugins/conjure delegate-setup
make -C plugins/conjure delegate-doctor
```

### From Python

```python
from scripts.delegation_executor import Delegator

delegator = Delegator()
result = delegator.execute(
    "gemini",
    "Analyze these files for security issues",
    files=["src/main.py", "src/auth.py"],
    options={"model": "gemini-3-pro"},
)

service, result = delegator.smart_delegate(
    "Summarize this codebase",
    files=["src"],
    requirements={"large_context": True},
)
```

`smart_delegate` returns the chosen service name alongside the result,
and passes a `--model` flag only where the provider declares model ids.
A provider that declares none keeps its CLI's own default.
