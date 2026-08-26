#!/usr/bin/env python3
"""Guided setup for delegation providers.

Reports which provider CLIs are present and authenticated, and installs the
missing ones after an explicit confirmation.

The provenance map in ``delegation_executor`` is the only source of install
commands. That is the load-bearing constraint here: this module runs shell
pipelines with ``-g`` scope, and #655 shipped a service naming a binary that
an unaffiliated package publishes. Resolving a command for an unrecorded
binary raises instead of falling back to a guess, so the failure mode is a
refusal rather than an arbitrary install.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess  # nosec B404
import sys
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from scripts.delegation_executor import (
    VERIFIED_BINARIES,
    Delegator,
    credential_file_issues,
    resolve_env_overlay,
)
from scripts.provider_ledger import ProviderLedger, ProviderRecord

_PROBE_TIMEOUT_SECONDS = 10

# Outcomes of one install offer. Three, not two: an operator who declines
# has made a choice, and reporting that as a failed install turns the
# ordinary path through `--all`, where somebody wants two of eight CLIs,
# into a non-zero exit and a red build.
INSTALLED = "installed"
DECLINED = "declined"
FAILED = "failed"


class UnverifiedBinaryError(RuntimeError):
    """Raised when an install is requested for a binary with no provenance."""


@dataclass(frozen=True)
class ProviderState:
    """What is true about one provider on this machine right now."""

    name: str
    binary: str
    installed: bool
    version: str | None
    authenticated: bool
    issues: tuple[str, ...]
    missing_variables: tuple[str, ...]
    # False when the provider's credentials live inside the CLI. The probe
    # spawns each installed binary for its version and nothing more: an auth
    # probe per provider would multiply the cost of a status table by the
    # number of CLIs, and several prompt on failure. So for those providers
    # it has no evidence either way, and `authenticated` below is an absence
    # of findings rather than a finding.
    auth_checked: bool = True
    login_hint: str = ""


def _probe_version(binary: str, probe: Sequence[str]) -> str | None:
    """Return the CLI's reported version, or None if it will not say.

    A CLI that is present but cannot answer its own version probe is still
    usable, so this reports None rather than treating it as an error.
    """
    try:
        result = subprocess.run(  # nosec B603
            [binary, *probe],
            capture_output=True,
            text=True,
            timeout=_PROBE_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    if result.returncode != 0:
        return None

    output = (result.stdout or result.stderr or "").strip()
    return output.splitlines()[0] if output else None


def _missing_credentials(delegator: Delegator, name: str) -> list[str]:
    """Name each unset variable the provider needs, once.

    A variable can be required twice over: glm names ZAI_API_KEY both as its
    auth variable and as the value of its ANTHROPIC_AUTH_TOKEN overlay. That
    is one thing to fix, so it is reported once. Deduplication preserves
    first-seen order rather than sorting, so the overlay variable an operator
    is most likely to be missing stays at the top.

    Deliberately env-only: this runs for every provider on every invocation,
    so it must not depend on spawning each CLI.
    """
    service = delegator.services[name]

    _, missing_overlay = resolve_env_overlay(service)
    candidates = list(missing_overlay)

    if (
        service.auth_method == "api_key"
        and service.auth_env_var
        and not os.getenv(service.auth_env_var)
    ):
        candidates.append(service.auth_env_var)

    return list(dict.fromkeys(candidates))


def probe_provider(delegator: Delegator, name: str) -> ProviderState:
    """Read one provider's installed and authenticated state."""
    service = delegator.services[name]
    installed = shutil.which(service.command) is not None

    missing_variables = _missing_credentials(delegator, name)

    issues: list[str] = []
    if not installed:
        issues.append(f"{service.command} is not installed")
    issues.extend(
        f"environment variable {variable} is not set" for variable in missing_variables
    )

    # The same answer the chain skips on, so the table cannot disagree with
    # the thing it describes. This part reads the filesystem and the
    # environment and spawns nothing; the version probe below does spawn
    # each installed binary, which is why _missing_credentials above is
    # deliberately env-only. The constraint is that authentication is
    # never decided by running a provider's own CLI, not that the table
    # runs no process at all.
    file_issues = credential_file_issues(service)
    issues.extend(issue[0].lower() + issue[1:] for issue in file_issues)

    return ProviderState(
        missing_variables=tuple(missing_variables),
        name=name,
        binary=service.command,
        installed=installed,
        version=_probe_version(service.command, service.version_probe)
        if installed
        else None,
        authenticated=installed and not issues,
        issues=tuple(issues),
        # A cli-auth provider is normally unknown, because this table does
        # not spawn the CLI that holds the answer. An absent credential
        # file is the exception: it is evidence, and it is a negative, so
        # the cell can say "missing" instead of shrugging. A present file
        # buys nothing and leaves the provider unknown.
        auth_checked=service.auth_method != "cli" or bool(file_issues),
        login_hint=service.login_hint,
    )


def probe_all(delegator: Delegator) -> list[ProviderState]:
    """Read every registered provider, in the delegator's own order."""
    return [probe_provider(delegator, name) for name in delegator.candidate_order()]


def render_status(states: Sequence[ProviderState]) -> str:
    """Render the provider table an operator reads before deciding anything."""
    header = ("PROVIDER", "BINARY", "INSTALLED", "AUTH")
    rows = [
        (
            state.name,
            state.binary,
            "yes" if state.installed else "NO",
            _auth_cell(state),
        )
        for state in states
    ]
    table = [header, *rows]
    widths = [max(len(row[i]) for row in table) for i in range(len(header))]

    return "\n".join(
        "  ".join(value.ljust(widths[i]) for i, value in enumerate(row)).rstrip()
        for row in table
    )


def _auth_cell(state: ProviderState) -> str:
    """Render one provider's authentication cell.

    Three states, not two. A provider that is not installed reports "-"
    rather than "missing": its credentials are not the thing to fix yet. A
    provider whose CLI owns its credentials reports "unknown", because this
    table never runs that CLI's auth probe and so holds no evidence either
    way. Only "ok" and "missing" are claims, and both rest on a check that
    actually ran.
    """
    if not state.installed:
        return "-"
    if not state.auth_checked:
        return "unknown"
    if state.authenticated:
        return "ok"
    return "missing"


def install_command_for(binary: str) -> str:
    """Return the vouched-for install command for a binary.

    Raises rather than returning a default: an unrecorded binary is one no
    reviewer has checked, and inventing a command for it is how a mistyped
    name becomes a global install of somebody else's package.
    """
    record = VERIFIED_BINARIES.get(binary)
    if record is None:
        msg = (
            f"{binary!r} has no entry in VERIFIED_BINARIES, so no install "
            f"command can be offered for it. Add the official package, "
            f"publisher and source URL first."
        )
        raise UnverifiedBinaryError(msg)
    return record["install"]


def _default_confirm(prompt: str) -> bool:
    """Ask the operator to approve one install."""
    print(prompt)
    try:
        answer = input("Run this now? [y/N] ").strip().lower()
    except EOFError:
        return False
    return answer in {"y", "yes"}


def install_provider(
    binary: str,
    confirm: Callable[[str], bool] = _default_confirm,
    runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
) -> str:
    """Install one provider CLI after the operator approves the command.

    The prompt names the publisher and source URL because several of these
    install by piping a remote script into a shell. Approving that without
    seeing who serves it is not consent.

    Returns:
        One of ``INSTALLED``, ``DECLINED`` or ``FAILED``.

    """
    command = install_command_for(binary)
    record = VERIFIED_BINARIES[binary]

    prompt = (
        f"{binary}: not installed\n"
        f"  package    {record['package']}\n"
        f"  publisher  {record['publisher']}\n"
        f"  source     {record['source']}\n"
        f"  command    {command}"
    )
    if not confirm(prompt):
        return DECLINED

    # Several install strings are shell pipelines, so a shell has to run
    # them. Naming /bin/sh in the argv rather than passing shell=True keeps
    # the interpreter explicit and the string in a position that can never be
    # re-split. The string is never caller-supplied: install_command_for has
    # already established it came from the reviewed provenance map.
    result = runner(["/bin/sh", "-c", command], check=False)  # nosec B603
    return INSTALLED if result.returncode == 0 else FAILED


def doctor_lines(states: Sequence[ProviderState]) -> list[str]:
    """Describe each unhealthy provider and the command that resolves it."""
    lines: list[str] = []

    for state in states:
        if state.installed and not state.auth_checked:
            lines.append(f"{state.name}:")
            lines.append("  - this CLI owns its credentials, so the probe cannot")
            lines.append("    confirm them without spawning it")
            if state.login_hint:
                lines.append(f"    check: {state.login_hint}")
            continue

        if state.authenticated:
            continue

        lines.append(f"{state.name}:")
        for issue in state.issues:
            lines.append(f"  - {issue}")

        # Only an absent binary is fixed by installing it. Printing an
        # install command at a provider that is present and merely missing a
        # credential sends the operator to fix the wrong thing.
        if not state.installed:
            try:
                lines.append(f"    fix: {install_command_for(state.binary)}")
            except UnverifiedBinaryError as exc:
                lines.append(f"    fix: unavailable ({exc})")

        lines.extend(
            f"    fix: export {variable}=<your key>"
            for variable in state.missing_variables
        )

        # A provider whose credentials live inside its CLI is fixed by
        # logging in, not by exporting anything. The condition was a
        # substring test over the issue prose, so it fired only for the
        # one sentence that says "credential file". An expired credential
        # produces no such sentence: the file is present, and this table
        # deliberately does not spawn the CLI that would find out, so the
        # provider lands in the auth-unknown cell. That is exactly the
        # case an operator needs the login command for, and it was the
        # case that never printed it.
        #
        # Structural now: offer the command wherever the provider is
        # installed and its authentication is not confirmed. A provider
        # confirmed authenticated gets nothing, which is what keeps this
        # from printing under every row.
        if (
            state.login_hint
            and state.installed
            and not (state.authenticated and state.auth_checked)
        ):
            lines.append(f"    fix: {state.login_hint}")

    return lines


def write_ledger(
    states: Sequence[ProviderState],
    path: Path | None = None,
    now: float | None = None,
) -> ProviderLedger:
    """Store this probe round so the next caller does not repeat it.

    ``ProviderState.authenticated`` defaults True for providers whose
    credentials live inside the CLI, because the status table does not
    spawn the probe that would find out; ``auth_checked`` is what says
    so. Only a checked confirmation reaches the ledger, so "we did not
    look" cannot be read back as "it works".
    """
    stamp = time.time() if now is None else now
    ledger = ProviderLedger(path)
    for state in states:
        confirmed = state.authenticated and state.auth_checked and not state.issues
        ledger.record(
            ProviderRecord(
                name=state.name,
                binary=state.binary,
                installed=state.installed,
                version=state.version,
                auth_confirmed_at=stamp if confirmed else None,
                recorded_at=stamp,
                last_error=state.issues[0] if state.issues else None,
            )
        )
    ledger.save()
    return ledger


def render_available(ledger: ProviderLedger) -> str:
    """Name the harnesses conjure can call on this machine right now."""
    ready = ledger.available()
    if not ready:
        return (
            "No provider is confirmed ready. Run --doctor for the reason "
            "per provider, or --install <service> to add one."
        )
    return "Available to conjure: " + ", ".join(ready)


def install_every_missing(states: Sequence[ProviderState]) -> int:
    """Offer each uninstalled provider in turn, and report the outcomes."""
    missing = [state for state in states if not state.installed]
    if not missing:
        print("Every registered provider is already installed.")
        return 0

    outcomes = {}
    for state in missing:
        try:
            outcomes[state.name] = install_provider(state.binary)
        except UnverifiedBinaryError as exc:
            # A provider registered in the operator's own config.json has
            # no VERIFIED_BINARIES entry, and this loop let the exception
            # out: the run died mid-sweep on a traceback, after installing
            # some providers and before offering the rest. Refusing to
            # invent an install command is correct; taking the whole sweep
            # down with it is not.
            print(f"{state.name}: no install command ({exc})", file=sys.stderr)
            outcomes[state.name] = FAILED

    declined = [name for name, out in outcomes.items() if out == DECLINED]
    failed = [name for name, out in outcomes.items() if out == FAILED]
    if declined:
        print(f"Skipped at your request: {', '.join(declined)}")
    if failed:
        print(f"Install failed: {', '.join(failed)}", file=sys.stderr)
        return 1
    return 0


def _create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the setup CLI."""
    parser = argparse.ArgumentParser(
        description="Report and install delegation provider CLIs",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show the provider status table (default)",
    )
    parser.add_argument(
        "--doctor",
        action="store_true",
        help="Explain each unhealthy provider and how to fix it",
    )
    parser.add_argument(
        "--install",
        metavar="SERVICE",
        help="Install one provider's CLI after confirmation",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="With --install omitted, offer every missing provider in turn",
    )
    parser.add_argument(
        "--available",
        action="store_true",
        help="Name the harnesses confirmed ready to take delegation work",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for delegation setup."""
    args = _create_parser().parse_args(argv)
    delegator = Delegator()
    states = probe_all(delegator)
    ledger = write_ledger(states)

    if args.available:
        print(render_available(ledger))
        return 0

    if args.install:
        if args.install not in delegator.services:
            print(f"Unknown service: {args.install}", file=sys.stderr)
            return 1
        binary = delegator.services[args.install].command
        return 0 if install_provider(binary) != FAILED else 1

    if args.all:
        return install_every_missing(states)

    print(render_status(states))

    if args.doctor:
        lines = doctor_lines(states)
        if lines:
            print()
            print("\n".join(lines))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
