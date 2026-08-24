---
name: glimmer-delegation
description: Delegates tasks to a locally served Muse Glimmer via ollama. Use when delegation-core selects glimmer or the prompt must not leave the machine.
alwaysApply: false
category: delegation-implementation
tags:
- glimmer
- ollama
- local
- delegation
dependencies:
- delegation-core
tools:
- ollama
- delegation_executor.py
usage_patterns:
- local-model-delegation
- offline-fallback
complexity: intermediate
model_hint: standard
estimated_tokens: 550
references:
- delegation-core/shared-shell-execution.md
---

## Table of Contents

- [Overview](#overview)
- [When To Use](#when-to-use)
- [When NOT To Use](#when-not-to-use)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Smart Delegation](#smart-delegation)
- [Glimmer-Specific Details](#glimmer-specific-details)
- [Exit Criteria](#exit-criteria)

# Glimmer Delegation

## Overview

Glimmer is Meta's Muse Glimmer served locally through ollama, so a
delegation to it spends no quota and sends no prompt off the machine.
It is the last entry in the candidate order for the same reason it is
the safe one: a local 30B model is slower and weaker than any of the
network providers ahead of it.

## When To Use

- `delegation-core` selected `glimmer` for the task
- Every network provider is exhausted and the work still has to happen
- The prompt must not leave the machine, whatever the cost in quality

## When NOT To Use

- The task needs the strongest available model. Glimmer is the floor,
  not a peer of the network providers
- `ollama list` shows no `muse-glimmer:30b`. A registered provider
  whose model was never pulled fails at the first delegation, not at
  registration

## Prerequisites

### Installation

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull muse-glimmer:30b
```

Both steps are required. Installing ollama registers the binary and
pulls nothing, so `ollama --version` answering is not evidence that a
delegation will succeed.

### Authentication

None. `auth_method` is `"none"` and the auth probe is empty, because a
local server has no credential to check.

## Quick Start

### Using the shared delegation executor

```bash
uv run python scripts/delegation_executor.py glimmer "Summarize" \
  --files src/
```

### Through the Makefile

```bash
make -C plugins/conjure delegate-glimmer PROMPT='Summarize' FILES='src/'
```

### Direct CLI usage

```bash
ollama run muse-glimmer:30b "Explain this module"
```

## Smart Delegation

`glimmer` carries `priority=80`, the highest number in the registry,
which places it last in the candidate order. It declares no model ids,
because the model is fixed by the subcommand rather than chosen per
call.

## Glimmer-Specific Details

| Property | Value |
|----------|-------|
| Binary | `ollama` |
| Headless form | `ollama run muse-glimmer:30b` |
| Prompt delivery | stdin |
| File context | inlined into the prompt |
| Version probe | `ollama --version` |
| Auth probe | none |
| Output format flag | `--format` |
| Model flag | none |

Read off `ollama run --help` at 0.13.1: the usage line is `ollama run
MODEL [PROMPT] [flags]`, so the model is positional and is carried by
the subcommand. The flag list has no `--model`, which is why this
service declares `model_flag=None`; passing one exits 1 on an unknown
flag. `--format string` is documented there and is the reason
`output_format_flag` is `--format` rather than the registry default
`--output-format`, which the same CLI rejects.

No temperature flag is declared. `ollama run --help` documents none,
and inventing one is the error class `install_hint` and `login_hint`
already guard against.

## Exit Criteria

- [ ] `ollama` resolves on PATH and answers `ollama --version`
- [ ] `ollama list` includes `muse-glimmer:30b` before a task is
      delegated; an absent model stops execution with the pull command
      rather than failing inside the delegation
- [ ] The built command is `ollama run muse-glimmer:30b` with the
      prompt on stdin and no prompt flag
- [ ] No `--model` flag appears in the built command
- [ ] Output saved to `delegations/glimmer/YYYYMMDD_HHMMSS.md`
- [ ] This skill ran because `delegation-core` selected `glimmer`, or
      because the prompt was required to stay local
