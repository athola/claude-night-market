"""Service registry, config contract and credential checks for delegation.

Split out of ``delegation_executor`` so the data a provider is described
by, and the checks that read that data without spawning anything, can be
changed without touching the process that spawns. Imports flow one way:
this module knows nothing about ``Delegator``.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import MISSING, dataclass, field, fields, replace
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts.quota_tracker import (
    DEFAULT_CODEX_LIMITS,
    DEFAULT_GEMINI_LIMITS,
    DEFAULT_GLM_LIMITS,
    DEFAULT_MINIMAX_LIMITS,
    DEFAULT_MUSE_LIMITS,
    DEFAULT_OPENCODE_LIMITS,
    DEFAULT_QWEN_LIMITS,
)

# Spawning a binary by name trusts whatever PATH resolves it to, so every name
# this module spawns is recorded here with the package that publishes it and a
# source a reviewer can check. A service whose command is absent from this map
# fails its test rather than reaching a user's shell.
VERIFIED_BINARIES: dict[str, dict[str, str]] = {
    "gemini": {
        "package": "@google/gemini-cli",
        "publisher": "Google",
        "install": "npm install -g @google/gemini-cli",
        "source": "https://github.com/google-gemini/gemini-cli",
    },
    "qwen": {
        "package": "@qwen-code/qwen-code",
        "publisher": "Alibaba / QwenLM",
        "install": "npm install -g @qwen-code/qwen-code",
        "source": "https://github.com/QwenLM/qwen-code",
    },
    "mmx": {
        "package": "mmx-cli",
        "publisher": "MiniMax-AI",
        "install": "npm install -g mmx-cli",
        "source": "https://github.com/MiniMax-AI/cli",
    },
    # Spawned by the endpoint-swap services, which run the stock binary
    # against a different base URL rather than shipping a CLI of their own.
    "claude": {
        "package": "@anthropic-ai/claude-code",
        "publisher": "Anthropic",
        "install": "npm install -g @anthropic-ai/claude-code",
        "source": "https://github.com/anthropics/claude-code",
    },
    # Meta publishes no npm or PyPI artifact for Muse Code: the documented
    # install is a script served from Meta's own domain.
    "muse": {
        "package": "muse-code (standalone installer)",
        "publisher": "Meta",
        "install": "curl -fsSL https://dev.meta.ai/install.sh | sh",
        "source": "https://dev.meta.ai/docs/muse-code",
    },
    "codex": {
        "package": "@openai/codex",
        "publisher": "OpenAI",
        "install": "npm install -g @openai/codex",
        "source": "https://github.com/openai/codex",
    },
    "opencode": {
        "package": "opencode-ai",
        "publisher": "SST",
        "install": "npm install -g opencode-ai@latest",
        "source": "https://github.com/sst/opencode",
    },
    "ollama": {
        "package": "ollama",
        "publisher": "Ollama",
        "install": "curl -fsSL https://ollama.com/install.sh | sh",
        "source": "https://github.com/ollama/ollama",
    },
}


# Above this, an epoch timestamp is milliseconds rather than seconds. The
# boundary sits in the year 5138 read as seconds, so no real deadline is
# ambiguous.
_EPOCH_MILLISECOND_FLOOR = 100_000_000_000


@dataclass(frozen=True)
class ServiceConfig:
    """Configuration for a delegation service.

    Frozen because the registry is shared. ``Delegator.__init__`` copies
    the ``SERVICES`` mapping and not its values, so every Delegator in a
    process holds these same objects; while this was mutable, one field
    assignment rewrote the contract process wide. ``_apply_overrides``
    already builds a new object with ``replace``, so nothing needed to
    assign.

    The trailing fields describe the CLI contract. They exist because the
    supported CLIs genuinely diverge: ``mmx`` puts text generation behind a
    ``text chat`` subcommand, names its prompt flag ``--message``, spells
    output format ``--output``, and has no ``@path`` context syntax.
    Defaults reproduce the Gemini contract, so existing services and custom
    entries in ``config.json`` are unaffected.

    A default is a claim about a CLI, not a neutral placeholder: a provider
    that leaves ``output_format_flag`` alone is asserting that its binary
    spells the flag ``--output-format``. Four did not, and the mismatch
    only surfaced when a caller passed the matching option. Probe the
    binary before trusting a default here.
    """

    name: str
    command: str
    auth_method: str
    auth_env_var: str | None = None
    quota_limits: dict[str, int] | None = None
    # Tuple rather than list: a default_factory field would read as required
    # to _missing_required_fields and silently skip valid custom configs.
    subcommand: tuple[str, ...] = ()
    # None means the prompt is positional. ``muse exec <prompt>``,
    # ``codex exec <prompt>`` and ``opencode run <prompt>`` all take it that
    # way, so a flag name is not universal enough to be mandatory.
    prompt_flag: str | None = "-p"
    # Long form of the prompt flag, used to attach a dash-leading prompt as
    # ``--prompt=-x``. A separator does not protect a flag's value: probed on
    # 2026-08-22, ``gemini -p -- --help`` still printed the help page while
    # ``gemini --prompt=--help`` reached authentication. Positional providers
    # need no entry here; they take ``--`` instead.
    prompt_long_flag: str | None = None
    # None where the CLI takes no format value. muse and codex offer only a
    # boolean ``--json``, which a flag-and-value pair cannot express.
    # How this CLI is told which model to use. `--model` was hardcoded at
    # the call site while the comment above it claimed every flag spelling
    # comes from the config, and it is not universal: `ollama run --help`
    # (0.13.1) lists no --model at all, because `ollama run MODEL [PROMPT]`
    # takes the model positionally. None means the model is not passed as a
    # flag. Recorded from each CLI's own --help: gemini 0.26.0, qwen, codex,
    # opencode and muse document `-m, --model`; `claude --model` and
    # `mmx text chat --model` likewise.
    model_flag: str | None = "--model"
    output_format_flag: str | None = "--output-format"
    # True when the flag above takes no value. `muse exec --json` and
    # `codex exec --json` are booleans: "Emit machine-readable JSONL
    # events on stdout", read off each binary's own --help. The
    # key-and-value shape cannot express that, since `--json json` lands
    # "json" as a positional and both providers take the prompt
    # positionally, so the request used to be dropped in silence.
    output_format_is_boolean: bool = False
    temperature_flag: str | None = "--temperature"
    inline_files: bool = False
    # Prompt on stdin rather than argv. execve caps a single argument at
    # 128 KiB, which a large inlined context exceeds.
    stdin_prompt: bool = False
    # Environment applied to the child only. An endpoint-swap harness runs a
    # stock binary against a different base URL, which is environment, not
    # argv. Values may reference the caller's variables as ``${VAR}`` so a
    # credential is named here rather than stored here.
    env: dict[str, str] = field(default_factory=dict)
    # Probes, because not every CLI answers --version or `auth status`.
    version_probe: tuple[str, ...] = ("--version",)
    auth_probe: tuple[str, ...] = ("auth", "status")
    # Files the CLI writes its credentials to, ``~`` accepted. The check is
    # one-directional: all of them absent means the CLI cannot be
    # authenticated, and any of them present means only that the question
    # stays open. Presence is never evidence of a working credential.
    # `opencode auth list` exits 0 naming a credentials path that does not
    # exist, and `codex login status` prints "Logged in using ChatGPT" over
    # a refresh token that has already been spent.
    auth_files: tuple[str, ...] = ()
    # Text in the auth probe's own output that means the credential was
    # refused, whatever the exit code. qwen 0.4.0 prints
    # "[API Error: 401 Incorrect API key provided...]" and exits 0, and
    # its delegation envelope reports "is_error": false over the same
    # text, so the exit code is not a signal for this CLI and the output
    # is the only honest one. Matched case-insensitively.
    auth_failure_markers: tuple[str, ...] = ()
    # A check beyond "the binary exists". `ollama --version` answers
    # whenever ollama is installed, and says nothing about whether the
    # model named in `subcommand` was ever pulled, so `--verify` reported
    # OK for a provider that fails at spawn. The probe runs
    # `command + readiness_probe` and requires `readiness_expect` in its
    # output.
    readiness_probe: tuple[str, ...] = ()
    readiness_expect: str = ""
    readiness_hint: str = ""
    # Shown when the binary is missing, so a failure names its own remedy.
    install_hint: str = ""
    # How an operator logs this CLI in, when the CLI owns its own
    # credentials. Recorded only where the command was read off the
    # installed binary's own help output, never inferred from the
    # binary name: an invented login command is the same class of
    # error as an invented install command.
    login_hint: str = ""
    # Selection metadata. smart_delegate derives both its candidate order and
    # its model choice from these, so registering a provider is the only step
    # needed to make it selectable. The previous design kept the order and the
    # model ids in module-level dicts that had to be edited in step with
    # SERVICES, and forgetting either one failed silently or raised KeyError.
    priority: int = 50
    default_model: str | None = None
    large_context_model: str | None = None
    fast_response_model: str | None = None
    # Requirement keys this service is preferred for, e.g. ("code_execution",).
    # This is how "qwen is the one for code execution" survives the move off
    # the hardcoded if/elif chain without becoming a branch per provider.
    strengths: tuple[str, ...] = ()


def _apply_overrides(
    current: ServiceConfig, service_name: str, overrides: Any
) -> ServiceConfig:
    """Return ``current`` with the fields named in ``overrides`` replaced.

    Every field the config file does not mention keeps the value it
    already had, so a partial override cannot reset the CLI contract.
    An unrecognized field name raises rather than being ignored, matching
    the new-service branch (CJR-003: config load must not swallow
    unexpected errors).
    """
    if not isinstance(overrides, dict):
        msg = f"service config for {service_name!r} must be an object"
        raise TypeError(msg)
    known = {f.name for f in fields(ServiceConfig)}
    unknown = set(overrides) - known
    if unknown:
        msg = (
            f"unknown ServiceConfig field(s) for {service_name!r}: "
            f"{', '.join(sorted(unknown))}"
        )
        raise TypeError(msg)
    return replace(current, **{k: v for k, v in overrides.items() if k != "name"})


def _missing_required_fields(service_config: Any) -> set[str]:
    """Return required ServiceConfig fields absent from a known-only config.

    Only returns missing names when ``service_config`` is a dict whose keys
    are all recognised ServiceConfig fields: such an entry is incomplete and
    should be skipped. A dict with unknown keys (or a non-dict) returns an
    empty set so the caller lets construction raise instead of silently
    skipping malformed config (CJR-003).
    """
    if not isinstance(service_config, dict):
        return set()
    known = {f.name for f in fields(ServiceConfig)}
    keys = set(service_config)
    if not keys <= known:
        return set()
    required = {
        f.name
        for f in fields(ServiceConfig)
        if f.default is MISSING and f.default_factory is MISSING
    }
    return required - keys


_ENV_REFERENCE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


def _env_ref(variable: str) -> str:
    """Name the caller variable holding a credential, for an env overlay.

    An overlay stores the name of the variable, never the value, so nothing
    secret is written into this file or into config.json. Building the
    reference here rather than writing the literal keeps that intent
    explicit, and stops a secret scanner from reading a template as a
    hardcoded credential.
    """
    return f"${{{variable}}}"


def resolve_env_overlay(service: ServiceConfig) -> tuple[dict[str, str], list[str]]:
    """Expand ``${VAR}`` references in a service's environment overlay.

    Returns the resolved overlay and the names of any referenced variables
    that are unset. A credential is named in the config rather than stored
    there, so an unset reference is a configuration error worth reporting
    rather than a value to guess: substituting an empty string would send an
    unauthenticated request and surface as a confusing downstream 401.
    """
    resolved: dict[str, str] = {}
    missing: list[str] = []

    for key, template in service.env.items():

        def _substitute(match: re.Match[str]) -> str:
            variable = match.group(1)
            value = os.getenv(variable)
            if value is None:
                missing.append(variable)
                return ""
            return value

        resolved[key] = _ENV_REFERENCE.sub(_substitute, template)

    return resolved, missing


SERVICES: dict[str, ServiceConfig] = {
    "gemini": ServiceConfig(
        name="gemini",
        command="gemini",
        auth_method="api_key",
        auth_env_var="GEMINI_API_KEY",
        quota_limits=DEFAULT_GEMINI_LIMITS,
        prompt_long_flag="--prompt",
        # gemini 0.26.0 documents -p, -m and -o/--output-format and no
        # temperature flag; passing one exits 1 on "Unknown argument".
        temperature_flag=None,
        install_hint="npm install -g @google/gemini-cli",
        priority=10,
        default_model="gemini-3-pro",
        large_context_model="gemini-3-pro",
        fast_response_model="gemini-3-flash",
        strengths=("large_context", "fast_response"),
    ),
    "qwen": ServiceConfig(
        name="qwen",
        command="qwen",
        auth_method="cli",
        auth_env_var=None,
        quota_limits=DEFAULT_QWEN_LIMITS,
        prompt_long_flag="--prompt",
        # `qwen --help` lists no auth subcommand, so the inherited
        # ("auth", "status") probe was delivered to the model as the
        # prompt "auth status" and billed as a completion. It answered
        # `[API Error: 401 ...]` and exited 0, so it reported success
        # while paying for a rejected call, on every chain walk.
        # Credentials live in oauth_creds.json, which a `qwen` run
        # writes; settings.json exists without them, so it is not the
        # file to test.
        auth_probe=(),
        auth_files=("~/.qwen/oauth_creds.json",),
        # qwen 0.4.0 spells it -o/--output-format like gemini, so the
        # default stands. The earlier "--format" exited 1 as an unknown
        # argument. No temperature flag exists either.
        temperature_flag=None,
        install_hint="npm install -g @qwen-code/qwen-code",
        auth_failure_markers=("API Error: 401", "Incorrect API key"),
        priority=20,
        default_model="qwen-max",
        large_context_model="qwen-max",
        fast_response_model="qwen-turbo",
        strengths=("code_execution",),
    ),
    # The official MiniMax CLI is npm ``mmx-cli``, which installs a
    # binary named ``mmx``. The name ``minimax`` belongs to an unrelated
    # third-party npm package, so it must not be spawned here.
    # Credentials live in ~/.mmx/config.json via ``mmx auth login``; there
    # is no MINIMAX_API_KEY env var to check, and ``mmx auth status`` is
    # the documented way to verify them.
    "minimax": ServiceConfig(
        name="minimax",
        command="mmx",
        auth_method="cli",
        auth_env_var=None,
        quota_limits=DEFAULT_MINIMAX_LIMITS,
        subcommand=("text", "chat"),
        auth_files=("~/.mmx/config.json",),
        prompt_flag="--message",
        prompt_long_flag="--message",
        output_format_flag="--output",
        # `mmx text chat --help` documents "--temperature <n> Sampling
        # temperature (0.0, 1.0]". Declaring None dropped it silently.
        temperature_flag="--temperature",
        inline_files=True,
        install_hint="npm install -g mmx-cli",
        login_hint="mmx auth login",
        priority=30,
        default_model="MiniMax-M3",
        large_context_model="MiniMax-M3",
        fast_response_model="MiniMax-M2.7",
        strengths=("code_execution",),
    ),
    # GLM has no CLI of its own. Z.ai serves an Anthropic-compatible
    # endpoint, so the stock claude binary reaches it by environment
    # alone. ANTHROPIC_AUTH_TOKEN is the documented variable; putting the
    # key in ANTHROPIC_API_KEY is the most common way to get a 401 here.
    # Model ids from https://docs.z.ai/devpack/latest-model. GLM-5.3 was
    # mid-rollout at the time of writing: docs.z.ai/guides/llm/glm-5.3
    # still read "coming soon" while the model-switch page documented
    # glm-5.3, so glm-4.7 stays the fast-response id rather than being
    # promoted on assumption.
    "glm": ServiceConfig(
        name="glm",
        command="claude",
        auth_method="api_key",
        auth_env_var="ZAI_API_KEY",
        quota_limits=DEFAULT_GLM_LIMITS,
        # `claude --help` documents "claude [options] [prompt]" and
        # "-p, --print", so -p selects non-interactive mode and the
        # prompt is positional. Declaring it as prompt_flag worked by
        # coincidence and put glm in the wrong escaping group; as a
        # subcommand it takes `--` like the other positional providers.
        subcommand=("-p",),
        prompt_flag=None,
        temperature_flag=None,
        env={
            "ANTHROPIC_BASE_URL": "https://api.z.ai/api/anthropic",
            "ANTHROPIC_AUTH_TOKEN": _env_ref("ZAI_API_KEY"),
        },
        auth_probe=(),
        install_hint="npm install -g @anthropic-ai/claude-code",
        priority=40,
        default_model="glm-5.3",
        large_context_model="glm-5.3[1m]",
        fast_response_model="glm-4.7",
        strengths=("code_execution", "large_context"),
    ),
    # Meta's Muse Code. `muse exec <prompt>` takes the prompt positionally
    # and META_API_KEY is the documented CI auth path. There is no
    # `muse auth status`, hence the empty auth probe. No --model or
    # output-format flag is documented for `exec`, so neither is declared:
    # an undeclared model id means smart_delegate leaves the CLI default
    # alone rather than passing a flag that may not exist.
    "muse": ServiceConfig(
        name="muse",
        command="muse",
        auth_method="api_key",
        auth_env_var="META_API_KEY",
        quota_limits=DEFAULT_MUSE_LIMITS,
        subcommand=("exec",),
        auth_files=("~/.config/muse/auth.json",),
        prompt_flag=None,
        temperature_flag=None,
        # muse 0.2.1 offers only a boolean --json, which this contract's
        # flag-and-value shape cannot express; --output-format exits 2.
        output_format_flag="--json",
        output_format_is_boolean=True,
        inline_files=True,
        auth_probe=(),
        install_hint="curl -fsSL https://dev.meta.ai/install.sh | sh",
        priority=50,
        strengths=("code_execution", "large_context"),
    ),
    # `codex exec <prompt>`. auth_method is cli rather than api_key because
    # `codex login status` reports the real state whether the credential
    # came from OPENAI_API_KEY or an interactive login, and codex supports
    # both. Note openai/codex#9253: `codex login` can fail outright on a
    # headless host unless a workspace admin enabled device-code auth.
    "codex": ServiceConfig(
        name="codex",
        command="codex",
        auth_method="cli",
        auth_env_var=None,
        quota_limits=DEFAULT_CODEX_LIMITS,
        subcommand=("exec",),
        auth_files=("~/.codex/auth.json",),
        prompt_flag=None,
        temperature_flag=None,
        # codex-cli 0.77.0 has boolean --json plus --output-schema and
        # --output-last-message, both file paths. No --output-format:
        # passing it exits 2 on "unexpected argument".
        output_format_flag="--json",
        output_format_is_boolean=True,
        inline_files=True,
        auth_probe=("login", "status"),
        install_hint="npm install -g @openai/codex",
        login_hint="codex login",
        priority=60,
        strengths=("code_execution",),
    ),
    # `opencode run <prompt>`. Credentials resolve per provider, so the
    # probe lists what is configured rather than checking one variable.
    "opencode": ServiceConfig(
        name="opencode",
        command="opencode",
        auth_method="cli",
        auth_env_var=None,
        quota_limits=DEFAULT_OPENCODE_LIMITS,
        subcommand=("run",),
        auth_files=("~/.local/share/opencode/auth.json",),
        prompt_flag=None,
        temperature_flag=None,
        # opencode 1.18.18: "--format  format: default (formatted) or
        # json (raw JSON events)". --output-format exits 1.
        output_format_flag="--format",
        inline_files=True,
        auth_probe=("auth", "list"),
        install_hint="npm install -g opencode-ai@latest",
        login_hint="opencode auth",
        priority=70,
        strengths=("code_execution",),
    ),
    # Muse Glimmer is open weights, not a CLI, so a local server fronts it.
    # Ollama takes the prompt on stdin, which is what keeps a large inlined
    # context off argv and under the 128 KiB execve ceiling. No quota and
    # no auth: the model runs on this machine.
    "glimmer": ServiceConfig(
        name="glimmer",
        command="ollama",
        auth_method="none",
        auth_env_var=None,
        quota_limits=None,
        subcommand=("run", "muse-glimmer:30b"),
        prompt_flag=None,
        temperature_flag=None,
        # ollama 0.13.1 `run --help`: "ollama run MODEL [PROMPT]", and the
        # flag list carries --format, --think, --verbose and no --model.
        # The model is the positional above; passing a flag exits 1.
        model_flag=None,
        # ollama 0.13.1: "--format string  Response format (e.g. json)".
        # --output-format exits 1 on "unknown flag".
        output_format_flag="--format",
        inline_files=True,
        stdin_prompt=True,
        auth_probe=(),
        install_hint=(
            "curl -fsSL https://ollama.com/install.sh | sh "
            "&& ollama pull muse-glimmer:30b"
        ),
        readiness_probe=("list",),
        readiness_expect="muse-glimmer:30b",
        readiness_hint="Pull it with: ollama pull muse-glimmer:30b",
        priority=80,
    ),
}


def credential_issues(service: ServiceConfig) -> list[str]:
    """Report credential problems that need no subprocess to establish.

    A provider has as many credential routes as it declares, and it is
    unauthenticated only when every one of them fails. muse states both
    of its own in one error message: run `muse login`, or set
    META_API_KEY, or save credentials to auth.json. Reporting either
    absence alone called a working install broken, in opposite
    directions.

    Shared with ``delegation_setup`` so the doctor's table and the
    chain's skip decision rest on one answer. A table that disagreed
    with the thing it describes would be worse than no table.
    """
    issues = credential_file_issues(service)

    if (
        service.auth_method == "api_key"
        and service.auth_env_var
        and not _env_satisfies(service)
        and not _has_credential_file(service)
    ):
        issues.append(f"Environment variable {service.auth_env_var} not set")
    return issues


def credential_file_issues(service: ServiceConfig) -> list[str]:
    """Report what the declared credential files say about themselves.

    Split from ``credential_issues`` because the doctor reports unset
    variables through its own path and wants only these. Selecting them
    by searching the combined list for a substring worked until the
    expiry finding was worded differently, and silently dropped it.

    Empty when the environment already satisfies the provider, because a
    file is then one route among several and its state decides nothing.
    """
    if _env_satisfies(service):
        return []

    issues = [
        f"Credential {path} expired {expired_on}"
        for path, expired_on in _expired_credentials(service)
    ]
    if _has_credential_file(service) is False:
        issues.append(
            "No credential file found; looked for " + ", ".join(service.auth_files)
        )
    return issues


def _env_satisfies(service: ServiceConfig) -> bool:
    """Report whether the provider's own auth variable is set."""
    return bool(service.auth_env_var and os.getenv(service.auth_env_var))


def _expired_credentials(service: ServiceConfig) -> list[tuple[str, str]]:
    """Name each credential file that says, in itself, that it has expired.

    A credential on disk is not a credential that works. qwen's
    oauth_creds.json on the machine this was written for expired in March
    and was still there in August, so a presence check cleared it, the
    chain spent a call on it, and it answered an empty string at exit 0.

    Only a stated expiry counts. A file with no expiry field, an
    unparseable one, or a non-numeric value produces no finding, because
    ruling out a working provider costs more than the round trip this
    saves. codex writes `last_refresh`, which records a renewal rather
    than a deadline, and is deliberately not read as one.
    """
    now = time.time()
    expired: list[tuple[str, str]] = []

    for raw in service.auth_files:
        path = Path(raw).expanduser()
        try:
            payload = json.loads(path.read_text())
        except (OSError, ValueError):
            continue
        if not isinstance(payload, dict):
            continue

        for key in ("expiry_date", "expires_at", "expiry"):
            value = payload.get(key)
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                continue
            # Epoch milliseconds where the value is too large to be seconds.
            seconds = value / 1000 if value > _EPOCH_MILLISECOND_FLOOR else value
            if seconds < now:
                expired.append(
                    (raw, datetime.fromtimestamp(seconds).date().isoformat())
                )
            break

    return expired


def _has_credential_file(service: ServiceConfig) -> bool | None:
    """Report whether any declared credential file is present.

    Returns None when the service declares none, so a caller can tell
    "not applicable" from "checked and absent". Only False rules a
    provider out; True means the question is still open, because a file
    on disk says nothing about whether the token inside it still works.
    """
    if not service.auth_files:
        return None
    return any(Path(path).expanduser().is_file() for path in service.auth_files)


def _smart_delegate_model(service: ServiceConfig, requirement: str) -> str | None:
    """Resolve the model id ``smart_delegate`` selects for a service.

    The ids live on the service config, so registering a provider carries its
    own model choices with it. A service that declares none returns None and
    the CLI's own default applies. That is deliberate: the previous
    module-level table raised KeyError for any service registered without a
    matching edit here, which made a data addition fail at runtime rather
    than degrade.
    """
    preferred = {
        "large_context": service.large_context_model,
        "fast_response": service.fast_response_model,
    }.get(requirement)
    return preferred or service.default_model
