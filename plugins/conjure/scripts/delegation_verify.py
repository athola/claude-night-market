"""Provider verification for delegation: whether a service can take work.

Split out of ``delegation_executor`` so the probes that decide whether a
provider is usable (environment overlay, credential files, the binary,
its auth probe, its readiness probe) can change without touching the
code that spawns a delegation. This module spawns only probes.
"""

from __future__ import annotations

import os
import subprocess  # nosec B404

from scripts.delegation_services import (
    ServiceConfig,
    credential_issues,
    resolve_env_overlay,
)


def verify_service(service: ServiceConfig) -> tuple[bool, list[str]]:
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
            combined = f"{result.stdout}{result.stderr}".lower()
            refused = [
                marker
                for marker in service.auth_failure_markers
                if marker.lower() in combined
            ]
            if result.returncode != 0:
                issues.append("Service not authenticated")
            elif refused:
                issues.append(
                    f"Service not authenticated: the probe exited 0 and "
                    f"reported {refused[0]!r}"
                )
        except (
            subprocess.CalledProcessError,
            FileNotFoundError,
            subprocess.TimeoutExpired,
            OSError,
        ):
            issues.append("Could not verify authentication status")

    if issues:
        return False, issues

    # Last, and only for a provider that declares one: the binary
    # being present is not the same question as the provider being
    # able to serve a delegation.
    if service.readiness_probe:
        issues.extend(readiness_issues(service, child_env))

    return len(issues) == 0, issues


def readiness_issues(service: ServiceConfig, child_env: dict[str, str]) -> list[str]:
    """Run a provider's readiness probe and report what it says."""
    try:
        result = subprocess.run(  # nosec B603
            [service.command, *service.readiness_probe],
            check=False,
            capture_output=True,
            timeout=15,
            text=True,
            env=child_env,
        )
    except (OSError, subprocess.SubprocessError):
        return [f"Could not run the {service.name} readiness probe"]

    if result.returncode != 0:
        return [f"{service.name} readiness probe exited {result.returncode}"]
    if service.readiness_expect and service.readiness_expect not in result.stdout:
        remedy = f". {service.readiness_hint}" if service.readiness_hint else ""
        return [
            f"{service.name} is installed but {service.readiness_expect!r} "
            f"is not available to it{remedy}"
        ]
    return []
