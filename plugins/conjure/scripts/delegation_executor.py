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
import subprocess  # nosec B404
import sys
import time
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from scripts.delegation_prompt import (
    MAX_INLINE_CONTEXT_BYTES,
    _compose_prompt_with_files,
    _delivered_prompt,
    _inline_context,
    _iter_context_files,
    _prompt_argv,
    estimate_tokens,
)
from scripts.delegation_services import (
    SERVICES as SERVICE_REGISTRY,
)
from scripts.delegation_services import (
    VERIFIED_BINARIES,
    ServiceConfig,
    _apply_overrides,
    _env_satisfies,
    _expired_credentials,
    _has_credential_file,
    _missing_required_fields,
    _smart_delegate_model,
    credential_file_issues,
    credential_issues,
    resolve_env_overlay,
)
from scripts.delegation_verify import verify_service

# Names that moved to delegation_services and delegation_prompt but are
# still imported from here by delegation_setup, egregore and the tests.
__all__ = [
    "MAX_INLINE_CONTEXT_BYTES",
    "VERIFIED_BINARIES",
    "Delegator",
    "ExecutionResult",
    "LaunchSpec",
    "ServiceConfig",
    "_compose_prompt_with_files",
    "_delivered_prompt",
    "_env_satisfies",
    "_expired_credentials",
    "_has_credential_file",
    "_inline_context",
    "_iter_context_files",
    "_missing_required_fields",
    "credential_file_issues",
    "credential_issues",
    "estimate_tokens",
    "main",
    "resolve_env_overlay",
]


# Configure logging for error tracking
logger = logging.getLogger(__name__)


# Delegation is on unless someone says otherwise. The environment variable
# is read at Delegator construction and overrides the config file, so the
# narrower scope wins: an operator can decline delegation for one command
# without editing a file they then have to remember to edit back.

DELEGATION_ENV_VAR = "CONJURE_DELEGATION"
_ENV_OFF_VALUES = frozenset({"0", "off", "false", "no"})
_ENV_ON_VALUES = frozenset({"1", "on", "true", "yes"})

# Why a delegation produced no answer. Both values mean the same thing to a
# caller, which is "do this work yourself", and different things to whoever
# has to fix it: one is a switch that was thrown on purpose, the other is a
# machine with no provider that could take the work.
#: The only output format a valueless boolean flag can request.
_BOOLEAN_FORMAT = "json"

FALLBACK_DISABLED = "delegation_disabled"
FALLBACK_EXHAUSTED = "providers_exhausted"


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

    def __post_init__(self) -> None:
        """Hold the two rules the comment above states.

        Both were prose only. A success carrying an exhaustion reason is
        the one that costs: `plan_resume`, the mission orchestrator and
        the egregore summon skill all branch on this field alone, so a
        result that answered *and* reported exhaustion sends every one
        of them down the no-answer path over real output.
        """
        if self.fallback_reason is None:
            return
        if self.fallback_reason not in (FALLBACK_DISABLED, FALLBACK_EXHAUSTED):
            raise ValueError(
                f"unknown fallback_reason {self.fallback_reason!r}; expected "
                f"{FALLBACK_DISABLED!r} or {FALLBACK_EXHAUSTED!r}"
            )
        if self.success:
            raise ValueError(
                "a successful delegation carries no fallback_reason, and "
                f"this one reports {self.fallback_reason!r}"
            )


class Delegator:
    """Unified delegation executor for multiple LLM services."""

    SERVICES = SERVICE_REGISTRY

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
            # Reported at error, matching the parse failure above. This
            # returned bare at no log level, so a "services" key written as
            # a list, or as the name of one service, discarded every
            # override the operator wrote and ran the stock registry. The
            # config was read, so nothing else signalled that it had not
            # been applied.
            logger.error(
                'Delegation config %s has "services" as %s, expected an '
                "object keyed by service name. No override was applied.",
                self.config_file,
                type(services_raw).__name__,
            )
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
        """Report whether a named service can take work; see delegation_verify."""
        if service_name not in self.services:
            return False, [f"Unknown service: {service_name}"]
        return verify_service(self.services[service_name])

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
            if "model" in options and service.model_flag:
                command.extend([service.model_flag, options["model"]])
            if "output_format" in options and service.output_format_flag:
                if not service.output_format_is_boolean:
                    command.extend(
                        [service.output_format_flag, options["output_format"]],
                    )
                elif options["output_format"] == _BOOLEAN_FORMAT:
                    command.append(service.output_format_flag)
                else:
                    # Raised rather than dropped. A caller that asked for
                    # a format is entitled to know it cannot have one,
                    # and this CLI has exactly one machine-readable mode.
                    raise ValueError(
                        f"{service.name} spells its output format as the "
                        f"valueless {service.output_format_flag!r}, so it "
                        f"supports {_BOOLEAN_FORMAT!r} and not "
                        f"{options['output_format']!r}"
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
        except OSError as e:
            # Reported at warning, not debug. This is the audit trail: it
            # is what `--usage` reads and the only record that a prompt
            # left the machine. At debug, which is off in every default
            # configuration, a read-only config directory and a run where
            # no delegation happened produced the same empty log and the
            # same silence. The delegation itself already succeeded, so
            # this does not fail the call, it just stops being quiet.
            logger.warning(
                "Could not append to the delegation usage log %s (%s). "
                "The call succeeded; the audit trail did not record it.",
                self.usage_log,
                e,
            )

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
