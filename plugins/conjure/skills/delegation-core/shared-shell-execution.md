---
name: shared-shell-execution
description: Shared shell execution contract for external LLM delegation services
category: delegation-infrastructure
tags: [shell-execution, delegation, cli, services]
dependencies: []
estimated_tokens: 1100
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
| `output_format_flag` | `"--output-format"` | Spelling; `None` emits no format flag |
| `temperature_flag` | `"--temperature"` | `None` suppresses the flag entirely |
| `inline_files` | `False` | Read file contents into the prompt |
| `stdin_prompt` | `False` | Deliver the prompt on stdin, not argv |
| `env` | `{}` | Child-only overlay; `${VAR}` names a credential |
| `version_probe` | `("--version",)` | Argv that makes the CLI state its version |
| `auth_probe` | `("auth", "status")` | Argv that reports credential state |
| `priority` | `50` | Position in the candidate order |
| `strengths` | `()` | Requirement keys this provider is preferred for |

## The provider dialects

The table below was probed against the installed binaries on
2026-08-22, not read off documentation.
Flag spellings drift between releases, so the versions are part of the
claim: re-probe before trusting a row against a newer CLI.

| Provider | Binary (version) | Subcommand | Prompt | Format flag | Temperature |
|----------|------------------|------------|--------|-------------|-------------|
| `gemini` | gemini 0.26.0 | none | `-p` | `--output-format` | none |
| `qwen` | qwen 0.4.0 | none | `-p`, deprecated | `--output-format` | none |
| `minimax` | mmx 1.0.19 | `text chat` | `--message` | `--output` | `--temperature` |
| `glm` | claude 2.1.240 | none | `-p` | `--output-format` | none |
| `muse` | muse 0.2.1 | `exec` | positional | boolean `--json` | none |
| `codex` | codex-cli 0.77.0 | `exec` | positional | boolean `--json` | none |
| `opencode` | opencode 1.18.18 | `run` | positional | `--format` | none |
| `glimmer` | ollama 0.13.1 | `run <model>` | stdin | `--format` | none |

Four of the eight disagreed with what the registry declared, and the
mismatch was reachable from a documented invocation: passing
`--format json` reached the CLI as an unknown argument.
`TestFlagSpellingsMatchTheRealClis` pins every spelling above against
argv, so the suite stays hermetic while the binaries stay the source.

### What each CLI does that changes caller code

**gemini** documents no temperature flag and exits 1 on one.
Its `auth status` subcommand is not a status report: it attempts
authentication and can exit with a stack trace.
That probe never runs, because gemini authenticates by API key and the
registry checks `GEMINI_API_KEY` instead.
The check errs the safe way: a host holding cached OAuth credentials
reports `FAILED` for the unset variable rather than claiming a health it
has not confirmed.

**qwen** deprecated `-p` in favor of a positional prompt, which still
works but is documented for removal.
More importantly, it exits 0 on a rejected credential: `qwen auth
status` prints `[API Error: 401 Incorrect API key provided]` and exits
0, and a real delegation returns an envelope carrying
`"subtype":"success","is_error":false` while the result text holds the
same error.
Exit code is not a success signal for this CLI, and `--verify` reports
`qwen: OK` today because of it.
Tracked in issue #685.

**minimax** is the one provider in the fleet that accepts a
temperature, and it branches its output on whether stdout is a
terminal.
With stdout captured it answers `{"error": {"code": 3, ...}}` and exits
3.
With stdout attached to a terminal it opens an interactive picker
asking how to authenticate, and waits.
`verify_service` passes `capture_output=True`, which is what keeps the
probe on the first path, so that argument is load-bearing rather than
incidental: streaming the probe's output for friendlier progress
reporting would hang it until the timeout.

**glm** has no CLI of its own.
The stock `claude` binary reaches Z.ai through the environment overlay,
so its failures read as Anthropic errors and the credential to check is
`ZAI_API_KEY`.

**muse** writes diagnostics to stderr and the result to stdout, so the
captured stdout is clean even though a run prints workspace and skill
warnings.
`muse exec --provider echo "say hi"` runs without credentials and
returns `echo: say hi`, which makes it the one provider that can be
exercised end to end for free.

**codex** reports credentials honestly: `codex login status` answers
`Logged in using ChatGPT` and exits 0 only when a login exists.

**muse and codex** both control JSON with a valueless `--json`.
The contract emits a flag and a value together, and neither CLI can
take that shape: both take the prompt positionally, so a stray `json`
would displace it.
Both therefore declare no format flag, and a caller's `output_format`
request is dropped without a signal.
Tracked in issue #684.

**opencode** exits 0 from `auth list` whether or not any credential is
stored, reporting the count in its output instead.
It spells the format flag `--format` and offers `--variant` where other
CLIs offer a temperature.

**glimmer** takes the prompt on stdin, which is what keeps a large
inlined context off argv and under the 128 KiB `execve` ceiling.
Its probe checks the `ollama` binary rather than the model named in its
subcommand, so `--verify` answers `glimmer: OK` on a host where
`ollama list` is empty and every delegation would fail at spawn.
Tracked in issue #685.

### Reproducing the probes

Each row above came from asking the binary rather than the docs.
Redirect stderr into the pipe: `mmx` prints its help there, so a probe
that drops stderr reports every `mmx` flag as absent.

```bash
gemini --help 2>&1 | grep -i 'output-format\|temperature'
mmx text chat --help 2>&1 | grep -i temperature
codex exec --output-format json >/dev/null 2>&1; echo "exit=$?"
```

A rejected format flag exits 2 on `codex` and `muse`, and 1 on
`opencode`, `qwen` and `ollama`.

Two behaviors need a terminal, because the CLI branches on one.
Run those under `tmux`, which is what separates "the probe is broken"
from "the CLI asked a question":

```bash
tmux new-session -d -s probe -x 200 -y 50 'mmx auth status; sleep 20'
sleep 5
tmux capture-pane -t probe -p
tmux kill-session -t probe
```

Nothing in this flow reaches a browser, so browser automation has no
target here.

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
uv run python scripts/delegation_executor.py gemini --verify
```

`--verify` names one service.
Bare, it exits 2: `main` routes the flag only when a service is given,
and the Makefile, the README and the provider skills all pass one.
`make -C plugins/conjure delegate-verify` is the loop over every
registered service.

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
