#!/usr/bin/env python3
"""Shared Delegation Execution Engine.

Unify execution interface for external LLM services with consistent error
handling, logging, and resource management.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import subprocess  # nosec B404
import sys
import time
from dataclasses import MISSING, dataclass, field, fields, replace
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from scripts.quota_tracker import (
    DEFAULT_CODEX_LIMITS,
    DEFAULT_GEMINI_LIMITS,
    DEFAULT_GLM_LIMITS,
    DEFAULT_MINIMAX_LIMITS,
    DEFAULT_MUSE_LIMITS,
    DEFAULT_OPENCODE_LIMITS,
    DEFAULT_QWEN_LIMITS,
)

try:
    from leyline.tokens import estimate_tokens
except ImportError:  # pragma: no cover

    def estimate_tokens(files: list[str], prompt: str = "") -> int:
        """Estimate tokens as fallback when leyline isn't installed."""
        total = len(prompt) // 4

        skip_dirs = {
            ".git",
            ".venv",
            "venv",
            "node_modules",
            "__pycache__",
            "dist",
            "build",
        }
        for p in files:
            path = Path(p)
            if path.is_file():
                try:
                    total += (
                        len(path.read_text(encoding="utf-8", errors="replace")) // 4
                    )
                except OSError:
                    pass
            elif path.is_dir():
                for child in path.rglob("*"):
                    if any(part in skip_dirs for part in child.parts):
                        continue
                    if child.is_file():
                        try:
                            total += (
                                len(child.read_text(encoding="utf-8", errors="replace"))
                                // 4
                            )
                        except OSError:
                            pass

        return total


# Configure logging for error tracking
logger = logging.getLogger(__name__)

# Linux caps a single argv entry at MAX_ARG_STRLEN (128 KiB). A CLI without a
# file-reference syntax must carry file contents inside the prompt argument, so
# inlined context is bounded well below that ceiling and the remainder is
# reported as truncated rather than failing the exec with E2BIG.
MAX_INLINE_CONTEXT_BYTES = 96 * 1024

# Below this much remaining budget a file cannot carry useful content, so the
# walk stops instead of emitting header-only blocks.
_MIN_INLINE_FILE_BYTES = 512

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


# Delegation is on unless someone says otherwise. The environment variable
# is read at Delegator construction and overrides the config file, so the
# narrower scope wins: an operator can decline delegation for one command
# without editing a file they then have to remember to edit back.
# Above this, an epoch timestamp is milliseconds rather than seconds. The
# boundary sits in the year 5138 read as seconds, so no real deadline is
# ambiguous.
_EPOCH_MILLISECOND_FLOOR = 100_000_000_000

DELEGATION_ENV_VAR = "CONJURE_DELEGATION"
_ENV_OFF_VALUES = frozenset({"0", "off", "false", "no"})
_ENV_ON_VALUES = frozenset({"1", "on", "true", "yes"})

# Why a delegation produced no answer. Both values mean the same thing to a
# caller, which is "do this work yourself", and different things to whoever
# has to fix it: one is a switch that was thrown on purpose, the other is a
# machine with no provider that could take the work.
FALLBACK_DISABLED = "delegation_disabled"
FALLBACK_EXHAUSTED = "providers_exhausted"


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
    output_format_flag: str | None = "--output-format"
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
    An unrecognised field name raises rather than being ignored, matching
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


@dataclass(frozen=True)
class LaunchSpec:
    """Inputs for spawning a single delegation subprocess."""

    cmd: list[str]
    service_name: str
    prompt: str
    files: list[str] | None
    timeout: int
    start_time: float
    env: dict[str, str] | None = None
    stdin_input: str | None = None


@dataclass(frozen=True)
class Attempt:
    """One provider's turn at a delegation, and what came of it.

    Kept per provider rather than collapsed into a single message because
    "delegation failed" is not something an operator can act on. Whether
    every CLI is missing or every credential has expired decides what they
    do next, and only the trail distinguishes the two.
    """

    service: str
    reason: str
    exit_code: int | None = None


@dataclass
class ExecutionResult:
    """Result of a delegation execution."""

    success: bool
    stdout: str
    stderr: str
    exit_code: int
    duration: float
    tokens_used: int | None = None
    service: str | None = None
    # Populated by smart_delegate only. A direct execute() call is one
    # provider by name and has no chain to report.
    attempts: tuple[Attempt, ...] = ()
    # Set when no provider answered, naming which of the two causes it was.
    # None on every result that carries an answer, so a caller tests this
    # field rather than inferring intent from an exit code.
    fallback_reason: str | None = None


class Delegator:
    """Unified delegation executor for multiple LLM services."""

    # Service configurations
    SERVICES = {
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
            output_format_flag=None,
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
            output_format_flag=None,
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
            priority=80,
        ),
    }

    def __init__(self, config_dir: Path | None = None) -> None:
        """Initialize the delegator with optional custom config directory."""
        self.config_dir = config_dir or Path.home() / ".claude" / "hooks" / "delegation"
        self.config_file = self.config_dir / "config.json"
        self.usage_log = self.config_dir / "usage.jsonl"
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Per-instance copy to avoid mutating class-level default
        self.services = dict(self.SERVICES)

        # Delegation is on until something turns it off. Resolved once here
        # rather than per call so that a disabled delegator costs nothing:
        # the caller learns the answer without a provider being probed.
        self.delegation_enabled = True
        self.delegation_off_reason: str | None = None
        self._config_off_reason: str | None = None

        # Load custom configurations
        self.load_configurations()
        self._resolve_delegation_policy()

    def _resolve_delegation_policy(self) -> None:
        """Decide whether delegation runs, and record why when it does not.

        Two switches, environment over file. The file is the machine-wide
        answer for an operator who does not want external CLIs at all; the
        variable is the answer for a single run, which is what a prompt
        that should not leave the machine needs.

        Anything the variable spells that is neither on nor off is ignored
        rather than guessed at, and the file's answer stands.
        """
        raw = os.environ.get(DELEGATION_ENV_VAR)
        if raw is not None:
            spelling = raw.strip().lower()
            if spelling in _ENV_OFF_VALUES:
                self.delegation_enabled = False
                self.delegation_off_reason = (
                    f"{DELEGATION_ENV_VAR}={raw} in the environment"
                )
                return
            if spelling in _ENV_ON_VALUES:
                self.delegation_enabled = True
                self.delegation_off_reason = None
                return

        if self._config_off_reason is not None:
            self.delegation_enabled = False
            self.delegation_off_reason = self._config_off_reason

    def _read_config(self) -> dict[str, Any] | None:
        """Parse the config file. ``None`` means there is no config file.

        Absent and unreadable are different events and must not collapse
        into one answer: an operator who never wrote a config wants the
        default posture, while a config that cannot be parsed is a switch
        that was thrown and cannot be read. Only the first is a reason to
        carry on.

        Opening directly rather than testing ``exists()`` first also
        closes the window between the two calls.
        """
        try:
            with open(self.config_file) as handle:
                return cast("dict[str, Any]", json.load(handle))
        except FileNotFoundError:
            return None

    def load_configurations(self) -> None:
        """Load custom service configurations from config file.

        A config that cannot be read fails closed. Delegation is on by
        default, so treating an unparseable file as saying nothing would
        let a single trailing comma undo the operator's opt-out and ship
        prompts, and up to 96 KiB of inlined source, to an external CLI.
        The error is reported at ``error`` because the previous ``debug``
        is off in every default configuration, so the switch flipped back
        on with nothing printed to any stream.
        """
        try:
            custom_config = self._read_config()
        except (json.JSONDecodeError, OSError) as exc:
            logger.error(
                "Cannot read delegation config %s (%s). Delegation is off "
                "until the file parses.",
                self.config_file,
                exc,
            )
            self._config_off_reason = (
                f"config {self.config_file} could not be read ({exc})"
            )
            return
        if custom_config is None:
            return

        # Absent means on. Only an explicit false opts out, so a config
        # file written for some other key cannot turn delegation off as a
        # side effect.
        if custom_config.get("enabled") is False:
            self._config_off_reason = f'"enabled": false in config {self.config_file}'

        # Merge custom configurations
        services_raw = custom_config.get("services", {})
        if not isinstance(services_raw, dict):
            return
        for service_name, service_config in services_raw.items():
            if service_name in self.services:
                # Override only the keys the file names. Listing fields by
                # hand here reset every unlisted one to its default, so
                # overriding minimax's quota silently dropped the
                # subcommand and prompt flag that make its CLI contract
                # work.
                current = self.services[service_name]
                self.services[service_name] = _apply_overrides(
                    current, service_name, service_config
                )
            else:
                # Add a new service. An entry that uses only known fields
                # but omits required ones is incomplete and skipped so the
                # defaults survive. An entry with unknown fields is
                # malformed and is allowed to raise (CJR-003: config load
                # must not swallow unexpected errors).
                missing = _missing_required_fields(service_config)
                if missing:
                    logger.warning(
                        "Skipping incomplete service config %r: "
                        "missing required field(s) %s",
                        service_name,
                        ", ".join(sorted(missing)),
                    )
                    continue
                self.services[service_name] = ServiceConfig(
                    **service_config,
                )

    def verify_service(self, service_name: str) -> tuple[bool, list[str]]:
        """Report whether a service can take work, cheapest question first.

        The chain skips a provider that fails here, so this is the only
        thing standing between an unauthenticated CLI and a full
        delegation round trip. Ordering matters as much as the checks: a
        question answered by reading the environment must not wait behind
        a process spawn that cannot change the answer.

        The order is environment, then credential files, then the binary,
        then the CLI's own probe. Each stage short-circuits, so a provider
        ruled out by a variable or a missing file costs no subprocess at
        all.
        """
        if service_name not in self.services:
            return False, [f"Unknown service: {service_name}"]

        service = self.services[service_name]

        # An overlay naming an unset variable is reported here rather than at
        # spawn time, so `--verify` is the one place a misconfigured
        # endpoint-swap service is diagnosed.
        overlay, missing_vars = resolve_env_overlay(service)
        issues: list[str] = [
            f"Environment variable {variable} is referenced by the "
            f"{service.name} environment overlay but is not set"
            for variable in missing_vars
        ]

        issues.extend(credential_issues(service))

        if issues:
            return False, issues

        child_env = {**os.environ, **overlay}

        # Check command availability with the service's own probe. Not every
        # CLI answers --version, so the argv comes from the config.
        if service.version_probe:
            try:
                subprocess.run(  # nosec B603
                    [service.command, *service.version_probe],
                    capture_output=True,
                    timeout=10,
                    check=True,
                    env=child_env,
                )
            except FileNotFoundError:
                remedy = (
                    f". Install with: {service.install_hint}"
                    if service.install_hint
                    else ""
                )
                issues.append(f"Command '{service.command}' not found{remedy}")
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                issues.append(f"Command '{service.command}' not found or not working")

        if issues:
            return False, issues

        # The CLI's own probe runs last because it is the most expensive and
        # the least conclusive. Three of the four that declare one exit 0
        # whatever the credential state, so it can only add a failure the
        # cheaper checks missed.
        if service.auth_method == "cli" and service.auth_probe:
            try:
                result = subprocess.run(  # nosec B603
                    [service.command, *service.auth_probe],
                    check=False,
                    capture_output=True,
                    timeout=10,
                    text=True,
                    env=child_env,
                )
                if result.returncode != 0:
                    issues.append("Service not authenticated")
            except (
                subprocess.CalledProcessError,
                FileNotFoundError,
                subprocess.TimeoutExpired,
                OSError,
            ):
                issues.append("Could not verify authentication status")

        return len(issues) == 0, issues

    def build_command(
        self,
        service_name: str,
        prompt: str,
        files: list[str] | None = None,
        options: dict[str, Any] | None = None,
        *,
        delivered: str | None = None,
    ) -> list[str]:
        """Build command for delegation.

        ``delivered`` lets execute() pass the prompt it already assembled,
        so an inline_files service does not walk and read the same files
        twice. Standalone callers omit it and it is computed here.
        """
        service = self.services[service_name]
        command = [service.command, *service.subcommand]

        # Add options. Every flag spelling comes from the service config, so a
        # CLI that names things differently is a data change, not a new branch.
        if options:
            if "model" in options:
                command.extend(["--model", options["model"]])
            if "output_format" in options and service.output_format_flag:
                command.extend(
                    [service.output_format_flag, options["output_format"]],
                )
            if "temperature" in options and service.temperature_flag:
                command.extend(
                    [service.temperature_flag, str(options["temperature"])],
                )

        full_prompt = (
            delivered
            if delivered is not None
            else _delivered_prompt(service, prompt, files)
        )

        # A stdin-delivering service keeps the prompt out of argv entirely, so
        # there is nothing to append. A service with no prompt_flag takes it
        # positionally (``muse exec <prompt>``).
        if not service.stdin_prompt:
            command.extend(_prompt_argv(service, full_prompt))

        return command

    def _launch_process(self, spec: LaunchSpec) -> ExecutionResult:
        """Spawn subprocess and return ExecutionResult, handling all error paths."""
        try:
            result = subprocess.run(  # nosec B603
                spec.cmd,
                check=False,
                capture_output=True,
                text=True,
                timeout=spec.timeout,
                cwd=Path.cwd(),
                env=spec.env,
                input=spec.stdin_input,
            )
            return ExecutionResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                duration=time.time() - spec.start_time,
                tokens_used=estimate_tokens(spec.files or [], spec.prompt),
                service=spec.service_name,
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Command timed out after {spec.timeout} seconds",
                exit_code=124,
                duration=time.time() - spec.start_time,
                service=spec.service_name,
            )
        except FileNotFoundError as e:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Command not found: {e}",
                exit_code=127,
                duration=time.time() - spec.start_time,
                service=spec.service_name,
            )
        except Exception as e:
            logger.exception("Unexpected error executing delegation")
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=str(e),
                exit_code=1,
                duration=time.time() - spec.start_time,
                service=spec.service_name,
            )

    def execute(
        self,
        service_name: str,
        prompt: str,
        files: list[str] | None = None,
        options: dict[str, Any] | None = None,
        timeout: int = 300,
    ) -> ExecutionResult:
        """Execute delegation command."""
        start_time = time.time()
        service = self.services[service_name]
        delivered = _delivered_prompt(service, prompt, files)
        command = self.build_command(
            service_name, prompt, files, options, delivered=delivered
        )
        overlay, _ = resolve_env_overlay(service)
        execution_result = self._launch_process(
            LaunchSpec(
                cmd=command,
                service_name=service_name,
                prompt=prompt,
                files=files,
                timeout=timeout,
                start_time=start_time,
                # Extend the caller's environment rather than replacing it: a
                # child spawned with only the overlay would lose PATH.
                env={**os.environ, **overlay},
                stdin_input=delivered if service.stdin_prompt else None,
            )
        )
        self.log_usage(service_name, command, execution_result)
        return execution_result

    def log_usage(
        self,
        service_name: str,
        command: list[str],
        result: ExecutionResult,
    ) -> None:
        """Log usage for tracking and analysis."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "service": service_name,
            "command": " ".join(command),
            "success": result.success,
            "duration": result.duration,
            "tokens_used": result.tokens_used,
            "exit_code": result.exit_code,
            "error": result.stderr if not result.success else None,
        }

        try:
            with open(self.usage_log, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logger.debug("Failed to write usage log: %s", e)

    def _init_service_stats(self) -> dict[str, Any]:
        """Initialize empty service statistics dictionary."""
        return {"requests": 0, "successful": 0, "tokens_used": 0, "total_duration": 0}

    def _update_service_stats(
        self,
        summary: dict[str, Any],
        entry: dict[str, Any],
    ) -> None:
        """Update service statistics from a log entry."""
        service = entry["service"]
        if service not in summary["services"]:
            summary["services"][service] = self._init_service_stats()

        summary["services"][service]["requests"] += 1
        if entry["success"]:
            summary["services"][service]["successful"] += 1
        summary["services"][service]["tokens_used"] += entry.get("tokens_used", 0)
        summary["services"][service]["total_duration"] += entry.get("duration", 0)

    def _calculate_rates(self, summary: dict[str, Any]) -> None:
        """Calculate success rates and averages for summary."""
        total = summary["total_requests"]
        summary["success_rate"] = (
            (summary["successful_requests"] / total) * 100 if total > 0 else 0
        )

        for service_data in summary["services"].values():
            reqs = service_data["requests"]
            service_data["success_rate"] = (
                (service_data["successful"] / reqs) * 100 if reqs > 0 else 0
            )
            service_data["avg_duration"] = (
                service_data["total_duration"] / reqs if reqs > 0 else 0
            )

    def get_usage_summary(self, days: int = 7) -> dict[str, Any]:
        """Get usage summary for the last N days."""
        if not self.usage_log.exists():
            return {"total_requests": 0, "success_rate": 0, "services": {}}

        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        summary: dict[str, Any] = {
            "total_requests": 0,
            "successful_requests": 0,
            "services": {},
        }

        try:
            with open(self.usage_log) as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entry_time = datetime.fromisoformat(
                            entry["timestamp"],
                        ).timestamp()

                        if entry_time >= cutoff_time:
                            summary["total_requests"] += 1
                            if entry["success"]:
                                summary["successful_requests"] += 1
                            self._update_service_stats(summary, entry)

                    except (json.JSONDecodeError, KeyError):
                        continue

            self._calculate_rates(summary)

        except OSError as e:
            logger.warning("Failed to analyze usage: %s", e)

        return summary

    def smart_delegate(
        self,
        prompt: str,
        files: list[str] | None = None,
        requirements: dict[str, Any] | None = None,
    ) -> ExecutionResult:
        """Work down the provider chain until one answers, or report that none did.

        Returns the answering provider's result, or a result carrying a
        ``fallback_reason`` and the trail of what each provider did. It
        does not raise on an empty chain: with delegation on by default,
        an operator who has installed no CLI is the ordinary case rather
        than the exceptional one, and a traceback is the wrong shape for a
        state the caller recovers from by doing the work itself.

        The chain stops at the first real answer. It is a fallback and not
        a fan-out, so the cost of the new default stays one provider deep
        on a working machine.
        """
        if not self.delegation_enabled:
            return self._no_delegation(
                FALLBACK_DISABLED,
                f"Delegation is off: {self.delegation_off_reason}",
            )

        requirements = requirements or {}
        attempts: list[Attempt] = []

        for service_name in self._ordered_candidates(requirements):
            # A caller that already knows a service is up says so, and is
            # taken at its word. Probing it anyway would spend a subprocess
            # to re-learn what the caller just said, on every task, now that
            # delegation runs by default.
            if not requirements.get(f"{service_name}_available"):
                is_available, problems = self.verify_service(service_name)
                if not is_available:
                    attempts.append(
                        Attempt(service=service_name, reason="; ".join(problems))
                    )
                    continue

            result = self.execute(
                service_name,
                prompt,
                files,
                self._smart_options(service_name, requirements),
            )
            if _answered(result):
                # The chain names the service rather than trusting the result
                # to carry it: smart_delegate is what chose the provider, and
                # a caller reading result.service after a fallback chain
                # wants the one that answered.
                return replace(
                    result,
                    service=service_name,
                    attempts=(
                        *attempts,
                        Attempt(
                            service=service_name,
                            reason="answered",
                            exit_code=result.exit_code,
                        ),
                    ),
                )

            attempts.append(
                Attempt(
                    service=service_name,
                    reason=_failure_reason(result),
                    exit_code=result.exit_code,
                )
            )

        return self._no_delegation(
            FALLBACK_EXHAUSTED,
            "No provider answered; handle this task locally.",
            attempts=tuple(attempts),
        )

    @staticmethod
    def _no_delegation(
        reason: str,
        message: str,
        attempts: tuple[Attempt, ...] = (),
    ) -> ExecutionResult:
        """Build the result that hands the work back to the caller."""
        return ExecutionResult(
            success=False,
            stdout="",
            stderr=message,
            exit_code=1,
            duration=0.0,
            attempts=attempts,
            fallback_reason=reason,
        )

    def _smart_options(
        self,
        service_name: str,
        requirements: dict[str, Any],
    ) -> dict[str, Any]:
        """Resolve the model a stated requirement asks this service for."""
        for requirement in ("large_context", "fast_response"):
            if requirements.get(requirement):
                model = _smart_delegate_model(self.services[service_name], requirement)
                return {"model": model} if model else {}
        return {}

    def candidate_order(self) -> list[str]:
        """Return registered service names in declared preference order.

        Public because delegation_setup builds its operator-facing table
        from it: a report that walked a private ordering would drift from
        the one selection actually uses.

        Derived from the registry, so a provider becomes selectable the moment
        it is registered. The previous hardcoded list meant a service could be
        registered, authenticated, and still never chosen.
        """
        return sorted(
            self.services,
            key=lambda name: (self.services[name].priority, name),
        )

    def _ordered_candidates(self, requirements: dict[str, Any]) -> list[str]:
        """Order every registered provider by how well it fits the request.

        Ordering only. Probing belongs to the caller walking this list,
        because the chain has to know why each provider dropped out and a
        function that returns one winner cannot say.

        A caller that already knows a service is up says so with
        ``{"<name>_available": True}`` and that service goes first. The key
        is generated from the registry rather than enumerated, so it works
        for every provider instead of the three that used to be spelled
        out here.
        """
        candidates = self.candidate_order()

        asserted = [n for n in candidates if requirements.get(f"{n}_available")]

        # Services declaring a requested strength are probed first; everything
        # else keeps its registry order behind them.
        wanted = {key for key, value in requirements.items() if value}
        preferred = [
            n
            for n in candidates
            if n not in asserted and wanted & set(self.services[n].strengths)
        ]
        rest = [n for n in candidates if n not in asserted and n not in preferred]

        return asserted + preferred + rest


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


def _answered(result: ExecutionResult) -> bool:
    """Report whether a provider produced something a caller can use.

    An exit code is not enough on its own. This repository has recorded
    ``opencode run`` exiting 0 with an empty stdout, and every CLI but the
    stdin one printing a help page at exit 0 for a dash-leading prompt.
    Both are successes by returncode and answers to nobody, and a chain
    that stopped at either would hand back silence.
    """
    return result.success and bool(result.stdout.strip())


def _failure_reason(result: ExecutionResult) -> str:
    """Describe why a provider that ran did not answer."""
    if result.success:
        return "exit 0 with an empty answer"
    detail = result.stderr.strip().splitlines()
    summary = detail[0] if detail else "no stderr"
    return f"exit {result.exit_code}: {summary}"


def _iter_context_files(files: list[str]) -> list[Path]:
    """Expand the requested paths into a stable list of readable files."""
    skip_dirs = {".git", ".venv", "venv", "node_modules", "__pycache__"}
    resolved: list[Path] = []
    for file_path in files:
        path = Path(file_path)
        if path.is_file():
            resolved.append(path)
        elif path.is_dir():
            for child in sorted(path.rglob("*")):
                if any(part in skip_dirs for part in child.parts):
                    continue
                if child.is_file():
                    resolved.append(child)
    return resolved


def _inline_context(files: list[str]) -> str:
    """Read file contents into a prompt block for CLIs without ``@path``.

    Reading the filesystem is a trust boundary, so unreadable files are
    skipped rather than aborting the delegation. The byte budget is an OS
    limit (see MAX_INLINE_CONTEXT_BYTES), and hitting it is reported in the
    prompt and the log instead of silently dropping context.
    """
    blocks: list[str] = []
    used = 0
    truncated = False

    for path in _iter_context_files(files):
        remaining = MAX_INLINE_CONTEXT_BYTES - used
        if remaining <= _MIN_INLINE_FILE_BYTES:
            truncated = True
            break

        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            logger.warning("Skipping unreadable context file %s: %s", path, e)
            continue

        header = f"--- BEGIN FILE: {path} ---\n"
        footer = f"\n--- END FILE: {path} ---"
        budget = remaining - len(header.encode("utf-8")) - len(footer.encode("utf-8"))
        if budget <= 0:
            # The markers alone outgrow what is left, which a deep path can
            # do while `remaining` still clears _MIN_INLINE_FILE_BYTES. Skip
            # rather than slice: a negative bound counts from the end of the
            # file, so the tighter the budget the more it would admit, and
            # the argument would exceed the execve limit this ceiling exists
            # to stay under.
            truncated = True
            continue
        encoded = content.encode("utf-8")
        if len(encoded) > budget:
            # Carry as much of the file as fits rather than dropping it whole:
            # one oversized file must not yield a prompt with no context at all.
            content = encoded[:budget].decode("utf-8", errors="ignore")
            content += f"\n[file truncated at {budget} bytes]"
            truncated = True

        block = header + content + footer
        blocks.append(block)
        used += len(block.encode("utf-8")) + 1

    if truncated:
        logger.warning(
            "Inline context truncated at %d bytes; %d file(s) included",
            MAX_INLINE_CONTEXT_BYTES,
            len(blocks),
        )
        blocks.append(
            f"[context truncated at {MAX_INLINE_CONTEXT_BYTES} bytes; "
            f"{len(blocks)} file(s) included]"
        )

    return "\n".join(blocks)


def _prompt_argv(service: ServiceConfig, prompt: str) -> list[str]:
    """Return the argv tail that delivers ``prompt`` as data, never as flags.

    Every CLI in the registry except the stdin one reads a dash-leading
    prompt as its own flag and answers with a help page, exiting 0. That
    is indistinguishable from an answer to a caller, and it needs no
    credential to trigger. The two escapes are not interchangeable:

    - a positional provider takes ``--``, which ends option parsing
    - a provider whose flag takes a value needs the value attached, as
      ``--prompt=<text>``, because ``--`` protects the next positional
      argument and not the flag's operand

    Both are applied only to a prompt that begins with a dash, so an
    ordinary call builds the argv it always built.
    """
    needs_escape = prompt.startswith("-")

    if service.prompt_flag is None:
        return ["--", prompt] if needs_escape else [prompt]

    if needs_escape and service.prompt_long_flag:
        return [f"{service.prompt_long_flag}={prompt}"]

    return [service.prompt_flag, prompt]


def _delivered_prompt(
    service: ServiceConfig,
    prompt: str,
    files: list[str] | None,
) -> str:
    """Build the prompt text as the service will receive it, files included.

    Shared by ``build_command`` and ``execute`` so the argv form and the stdin
    form cannot drift: a stdin-delivering service must send exactly what an
    argv-delivering one would have carried.
    """
    if files:
        return _compose_prompt_with_files(service, prompt, files)
    return prompt


def _compose_prompt_with_files(
    service: ServiceConfig,
    prompt: str,
    files: list[str],
) -> str:
    """Attach file context to a prompt using the service's own convention."""
    if service.inline_files:
        context = _inline_context(files)
        return f"{context}\n\n{prompt}" if context else prompt

    file_refs = []
    for file_path in files:
        path = Path(file_path)
        if path.exists():
            if path.is_file():
                file_refs.append(f"@{file_path}")
            elif path.is_dir():
                # Use glob pattern for directories
                file_refs.append(f"@{file_path}/**/*")
    if file_refs:
        return " ".join(file_refs) + " " + prompt
    return prompt


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


def _print_services(delegator: Delegator) -> None:
    """Print available services."""
    for name, config in delegator.services.items():
        print(f"  {name}: {config.command} (auth: {config.auth_method})")


def _print_usage_summary(delegator: Delegator) -> None:
    """Print usage summary report."""
    summary = delegator.get_usage_summary()
    print(f"Total requests: {summary['total_requests']}")
    print(f"Success rate: {summary.get('success_rate', 0):.1f}%")
    for svc_name, stats in summary["services"].items():
        rate = stats.get("success_rate", 0)
        print(f"  {svc_name}: {stats['requests']} requests, {rate:.1f}% success")


def _verify_service(delegator: Delegator, service_name: str) -> bool:
    """Verify a service, print results, and report the verdict to the caller.

    Returns the verdict rather than discarding it. An earlier version printed
    "FAILED" and returned None, so ``--verify`` exited 0 whatever it found and
    every caller checking the exit code was reading a constant.
    """
    is_available, issues = delegator.verify_service(service_name)
    if is_available:
        print(f"{service_name}: OK")
    else:
        print(f"{service_name}: FAILED")
        for issue in issues:
            print(f"  - {issue}")
    return is_available


def _report_fallback(result: ExecutionResult) -> None:
    """Tell the caller no delegation happened, and what to do about it.

    Printed to stderr and paired with a non-zero exit so that a script
    piping stdout cannot mistake an absent answer for an empty one. The
    per-provider trail goes out too: "delegation failed" leaves an
    operator nowhere, while "every CLI is missing" and "every credential
    expired" point at different fixes.
    """
    print(f"Delegation produced no answer ({result.fallback_reason}).", file=sys.stderr)
    print(result.stderr, file=sys.stderr)
    for attempt in result.attempts:
        print(f"  {attempt.service}: {attempt.reason}", file=sys.stderr)


def _print_result(result: ExecutionResult) -> bool:
    """Print execution result and report whether it succeeded."""
    if result.success:
        print(f"Success: {result.stdout[:200] if result.stdout else 'No output'}")
    else:
        print(f"Failed: {result.stderr}")
    return result.success


def _create_parser() -> argparse.ArgumentParser:
    """Create argument parser for CLI."""
    parser = argparse.ArgumentParser(description="Unified delegation executor")
    parser.add_argument(
        "service",
        nargs="?",
        help="Service name (gemini, qwen, minimax, auto)",
    )
    parser.add_argument("prompt", nargs="?", help="Prompt to send to the service")
    parser.add_argument("--files", nargs="+", help="Files to include")
    parser.add_argument("--model", help="Model to use")
    parser.add_argument("--format", help="Output format")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds")
    parser.add_argument("--verify", action="store_true", help="Verify service only")
    parser.add_argument("--usage", action="store_true", help="Show usage summary")
    parser.add_argument(
        "--list-services",
        action="store_true",
        help="List available services",
    )
    return parser


def main() -> None:
    """CLI interface for delegation executor."""
    parser = _create_parser()
    args = parser.parse_args()
    delegator = Delegator()

    if args.list_services:
        _print_services(delegator)
        return

    if args.usage:
        _print_usage_summary(delegator)
        return

    if args.verify and args.service:
        if not _verify_service(delegator, args.service):
            raise SystemExit(1)
        return

    if not args.service or not args.prompt:
        parser.error("service and prompt are required for delegation execution")

    if args.service == "auto":
        result = delegator.smart_delegate(args.prompt, args.files)
        if result.fallback_reason:
            _report_fallback(result)
            raise SystemExit(1)
    else:
        options: dict[str, Any] = {}
        if args.model:
            options["model"] = args.model
        if args.format:
            options["output_format"] = args.format
        result = delegator.execute(
            args.service,
            args.prompt,
            args.files,
            options,
            args.timeout,
        )

    if not _print_result(result):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
