---
name: shared-shell-execution
description: Shared shell execution contract for external LLM delegation services
category: delegation-infrastructure
tags: [shell-execution, delegation, cli, services]
dependencies: []
estimated_tokens: 2300
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
| `glm` | claude 2.1.240 | `-p` | positional | `--output-format` | none |
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
Those two reasons are not the same reason, and the probe cannot say so.
The cached credentials do load, and the delegation fails anyway,
because the account requires `GOOGLE_CLOUD_PROJECT`.
`FAILED` was the right answer for a cause it never named.

**qwen** deprecated `-p` in favor of a positional prompt, which still
works but is documented for removal.
More importantly, it exits 0 on a rejected credential: `qwen auth
status` prints `[API Error: 401 Incorrect API key provided]` and exits
0, and a real delegation returns an envelope carrying
`"subtype":"success","is_error":false` while the result text holds the
same error.
Exit code is not a success signal for this CLI, and `--verify` reports
`qwen: OK` today because of it.
That envelope is reachable only with `--output-format json`, which the
executor sends when the caller asks for a format and not otherwise.
Without it the CLI writes nothing but a newline on a rejected
credential, so the documented invocation answers `Success:` and a blank
line.
That byte matters: an empty stdout would have printed `No output`, and
a newline is truthy, so the absence arrives unnamed.
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
returns `echo: say hi`, but no caller reaches that path through this
module: `--provider` is not a `ServiceConfig` field, so the free run
exists for a hand-typed command and not for a delegation.
Through the executor, muse stops at `META_API_KEY`.

**codex** answers `Logged in using ChatGPT` and exits 0 from `codex
login status`, which records that a login happened rather than that the
credential still works.
On this host the probe kept reporting success while the delegation
failed with `your refresh token was already used`.
Its diagnostics go to stderr and reached 123 KB for a four-word prompt,
594 of those lines unrelated skill-loading errors, with the sentence
naming the failure on the last one.

**muse and codex** both control JSON with a valueless `--json`.
The contract emits a flag and a value together, and neither CLI can
take that shape: both take the prompt positionally, so a stray `json`
would displace it.
Both therefore declare no format flag, and a caller's `output_format`
request is dropped without a signal.
Tracked in issue #684.

**opencode** exits 0 from `auth list` whether or not any credential is
stored, reporting the count in its output instead.
It reports zero and exits 0 anyway, then falls back at run time to
whatever provider variables the environment holds.
`OPENAI_API_KEY` selected `gpt-5.3-chat-latest` here, and the
delegation ended at `Could not find the appropriate key in your
authentication token`, so the probe's exit code described the file it
read and not the credential it would use.
It spells the format flag `--format` and offers `--variant` where other
CLIs offer a temperature.

**glimmer** takes the prompt on stdin, which is what keeps a large
inlined context off argv and under the 128 KiB `execve` ceiling.
Its probe checks the `ollama` binary rather than the model named in its
subcommand, so `--verify` answers `glimmer: OK` on a host where
`ollama list` is empty.
The delegation does not fail at spawn: `ollama run` accepts the model
name and tries to pull it, so the failure arrives from the registry as
a 412 asking for a newer ollama.
That attempt writes spinner escapes to a captured stdout, so the
result the caller receives carries terminal control bytes wrapped
around the error text.
Tracked in issue #685.

### What a delegation actually returns

`--verify` answers a narrower question than the one a caller asks, and
the gap is measurable rather than theoretical.
Every row below ran the documented invocation from `plugins/conjure` on
2026-08-22 against the credentials this host happened to hold.

| Provider | `--verify` | Delegation | Elapsed | What the caller receives |
|----------|-----------|------------|---------|--------------------------|
| `glm` | OK | exit 0 | 11.8s | `pong`, the one path that completes |
| `qwen` | OK | exit 0 | 2.8s | `Success:` and a blank line |
| `codex` | OK | exit 1 | 10.4s | 123 KB of stderr, cause on the last line |
| `opencode` | OK | exit 1 | 3.6s | The provider rejects the token |
| `glimmer` | OK | exit 1 | 0.9s | A model pull fails with 412 |
| `gemini` | FAILED | exit 1 | 8.4s | A failure the probe did not name |
| `minimax` | FAILED | exit 1 | 0.2s | The JSON error the probe predicted |
| `muse` | FAILED | exit 1 | 0.3s | The credential the probe named |

Five probes answered `OK` and one delegation returned an answer.
Read the other way, the three probes that answered `FAILED` were right
every time, so the failure is one-directional: `FAILED` is a finding
and `OK` is an absence of one.
Callers that gate on `--verify` should treat it as a way to skip a
provider rather than as a promise about the one it keeps.

Two truncations decide how much of that reaches the caller.
`_print_result` cuts a successful stdout at 200 characters and prints a
failed stderr whole, so a long answer is lost on the quiet path while
all 123 KB of codex's noise arrives on the loud one.
Every CLI here puts its diagnosis at the tail, which is the half a
head-truncation would remove.

### What the failure shapes look like

A negative sweep on 2026-08-22 ran each shape below against the real
binaries and a real filesystem rather than a mock.
Argument parsing, file reading and `execve` all happen before any
network call, so most of these cost nothing to reproduce.

| Shape | Result |
|-------|--------|
| Prompt `""`, or absent | exit 2 from `parser.error` |
| Bare `--verify` | exit 2 |
| Unknown service name | `KeyError` traceback, exit 1 |
| Prompt `--usage` | exit 0, prints the usage report, delegates nothing |
| Context file absent | dropped, no signal at any log level |
| Context file oversized | cut, and the marker names the ceiling |
| Prompt past 128 KiB | `OSError` E2BIG, reported as a named failure |
| Shell metacharacters | one literal argv entry, no expansion |
| `--timeout 1` | exit 1, `Command timed out after 1 seconds` |
| `--format yaml` | exit 1, the CLI lists the values it accepts |

Four of those change caller code.

**A prompt beginning with a dash was read as a flag by seven of the
eight providers, and is now escaped.**
The first account of this named the three positional-prompt providers
and implied a flag protected the rest.
Probing the other four disproved that: `gemini -p "--help"`, `qwen -p
"--help"` and `mmx text chat --message "--help"` each printed a help
page and exited 0, exactly as `muse exec "--help"` did.
Only glimmer was immune, because its prompt goes on stdin and never
reaches a parser that reads flags.

The two escapes are not interchangeable, which is why one field could
not cover both.
An end-of-options `--` protects the next positional argument, so it
closes the positional providers and does nothing for a flag's operand:
`gemini -p -- "--help"` still printed the help page.
Attaching the value does close it, and needs the long spelling, so
`prompt_long_flag` names `--prompt` for gemini and qwen and `--message`
for minimax.
Both escapes apply only to a prompt that begins with a dash, so every
ordinary invocation builds the argv it always built.

`glm` moved groups in the process.
`claude --help` documents `claude [options] [prompt]` and `-p,
--print`, so `-p` selects non-interactive mode and the prompt is
positional.
Declaring it as a `prompt_flag` produced working argv by coincidence
and put glm in the group the separator cannot help; it is now a
subcommand, and takes `--` like the other positional providers.

The entry points still differ, and the executor's own layer is
unchanged.
`delegation_executor.py gemini "--usage"` prints the usage report and
exits 0 without delegating, because argparse reads it before any of
this applies.
Passing `--` first is the escape there: `gemini -- "--usage"` delivers
the string as a prompt.

**Absent context is the one loss that goes unnamed.**
An oversized file is cut, marked in the prompt as `[context truncated
at 98304 bytes; N file(s) included]`, and logged at warning level.
A file that cannot be resolved contributes nothing and says nothing,
even at debug.
Passing a good path and a bad one together returns a prompt built from
the good one alone, which reads as complete: nothing in it separates
one file requested from two requested and one lost.

**The inline ceiling bounds file context, not the prompt.**
`MAX_INLINE_CONTEXT_BYTES` is 96 KiB, which leaves headroom under the
128 KiB `execve` limit for the prompt that carries it.
A prompt is never capped, so a large enough one reaches that limit on
its own: 127 KiB spawned and 128 KiB, which is `MAX_ARG_STRLEN`
exactly, failed with `[Errno 7] Argument list too long`.
The executor turns that into `success=False` and a stderr naming the
cause rather than truncating behind the caller's back, which is the
behavior to keep.

**Asking for JSON can hide the error it was meant to reveal.**
`--format json` is how qwen's rejected credential becomes visible at
all, and through the command line it becomes less visible instead.
The envelope front-loads its `system` and `init` entries, so the 401
sat 1041 bytes into a 2075-byte answer while `_print_result` kept the
first 200 and exited 0.
The error is in the result the Python caller receives, and not in the
line the shell caller reads.

Two smaller asymmetries are worth knowing before debugging one.
`verify_service` answers an unknown service with a named issue while
`execute` raises `KeyError`, so the same typo is a diagnosis on one
path and a traceback on the other.
And in `config.json` a misspelled field raises `TypeError` naming the
field, while a missing brace is swallowed at debug level and leaves the
defaults in place, so the louder mistake is the smaller one.

`VERIFIED_BINARIES` does not gate any of this.
A service added through `config.json` registers under whatever binary
it names, verifies as `not found`, and executes to exit 127.
The map gates install advice in `delegation_setup.py`, where
`install_command_for` raises `UnverifiedBinaryError` rather than
guessing a command, which is the check #655 exists to keep.

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

What a delegation returns needs the executor rather than the binary,
because the question there is what reaches a caller.
Run the pair per provider and compare, from `plugins/conjure`:

```bash
uv run python scripts/delegation_executor.py codex --verify
uv run python scripts/delegation_executor.py codex "Reply with: pong"
```

Redirect each to a file before reading it: codex answers a four-word
prompt with 123 KB of stderr, and the line that explains the failure is
the last one.

The failure shapes need no credentials, and the two that matter most
are one command each:

```bash
uv run python scripts/delegation_executor.py gemini "--usage"
uv run python -c "import sys; sys.path.insert(0, '.'); \
from scripts.delegation_executor import _delivered_prompt, Delegator; \
print(repr(_delivered_prompt(Delegator().services['minimax'], 'ASK', ['/nope'])))"
```

The first prints a usage report and exits 0.
The second prints `'ASK'`, which is the whole signal a caller gets when
the context it asked for did not resolve.

Reproducing any of this writes to the same log `--usage` reads.
Nothing marks a probe as a probe, so a sweep of the eight providers
skews the report it will later be read from: this round left 27 rows in
a log that held 6.
The effect stops there. Quota lives in its own store under
`~/.claude/hooks/gemini`, and `_select_service` orders candidates by
priority and strengths without consulting usage at all, so probe
traffic changes what `--usage` says and not what runs.

A CLI that branches on a terminal needs one to show the other branch.
`tmux` is what separates "the probe is broken" from "the CLI asked a
question":

```bash
tmux new-session -d -s probe -x 200 -y 50 'mmx auth status; sleep 20'
sleep 5
tmux capture-pane -t probe -p
tmux kill-session -t probe
```

Run that against every live `auth_probe` and only `mmx` blocks.
`qwen auth status`, `codex login status` and `opencode auth list` print
the same bytes to a terminal as to a pipe, and `gemini auth status`
exits 1 with a stack trace either way.
One TTY branch in four is the reason `capture_output=True` is
load-bearing rather than the reason to distrust every probe.

No delegation reaches a browser.
The login flows behind four of these CLIs are OAuth and do, so the two
are worth keeping apart: `mmx auth login` offers two OAuth
destinations before it offers an API key.
Driving one under Playwright was tried and dropped.
Completing an OAuth flow authenticates a real account, which is not a
probe, and this host has no browser to drive: `DISPLAY` is unset and
neither Chrome nor Chromium is installed, so the handoff would go
through `wslview` to the Windows host and out of Playwright's reach.

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

Run these from `plugins/conjure`.
The module imports its siblings as `scripts.quota_tracker`, so the same
command from the repository root exits 1 on `ModuleNotFoundError`
before it reads its arguments.

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

result = delegator.smart_delegate(
    "Summarize this codebase",
    files=["src"],
    requirements={"large_context": True},
)
if result.fallback_reason:
    for attempt in result.attempts:
        print(attempt.service, attempt.reason)
    # No provider answered. Do the work here.
```

`smart_delegate` returns one `ExecutionResult`, with the answering
provider in `result.service`.
It used to return that name in a tuple alongside the result, which was
redundant once the chain became the thing that chose the provider.

It walks the registry order and returns the first real answer, treating
a missing binary, a failed exit and an exit-0 empty stdout alike as
reasons to try the next provider.
A `--model` flag goes out only where the provider declares model ids.
A provider that declares none keeps its CLI's own default.

When the chain is exhausted, or when delegation is turned off,
`result.fallback_reason` is set (`providers_exhausted` or
`delegation_disabled`) and `result.attempts` names what each provider
did.
It does not raise: with delegation on by default, an operator who has
installed no CLI is the ordinary case rather than an error condition.
