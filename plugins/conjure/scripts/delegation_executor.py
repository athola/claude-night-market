#!/usr/bin/env python3
"""Shared Delegation Execution Engine.

Provide a unified execution interface for different external LLM services
with consistent error handling, logging, and resource management.
"""

import argparse
import json
import logging
import os
import subprocess  # nosec B404
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from leyline.tokens import estimate_tokens
except ImportError:  # pragma: no cover

    def estimate_tokens(files: list[str], prompt: str = "") -> int:
        """Fallback estimator when leyline isn't installed."""
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


@dataclass
class ServiceConfig:
    """Configuration for a delegation service."""

    name: str
    command: str
    auth_method: str
    auth_env_var: str | None = None
    quota_limits: dict[str, int] | None = None


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


class Delegator:
    """Unified delegation executor for multiple LLM services."""

    # Service configurations
    SERVICES = {
        "gemini": ServiceConfig(
            name="gemini",
            command="gemini",
            auth_method="api_key",
            auth_env_var="GEMINI_API_KEY",
            quota_limits={
                "requests_per_minute": 60,
                "requests_per_day": 1000,
                "tokens_per_day": 1000000,
            },
        ),
        "qwen": ServiceConfig(
            name="qwen",
            command="qwen",
            auth_method="cli",
            auth_env_var=None,
            quota_limits={
                "requests_per_minute": 120,
                "requests_per_day": 2000,
                "tokens_per_day": 2000000,
            },
        ),
    }

    def __init__(self, config_dir: Path | None = None) -> None:
        """Initialize the delegator with optional custom config directory."""
        self.config_dir = config_dir or Path.home() / ".claude" / "hooks" / "delegation"
        self.config_file = self.config_dir / "config.json"
        self.usage_log = self.config_dir / "usage.jsonl"
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Load custom configurations
        self.load_configurations()

    def load_configurations(self) -> None:
        """Load custom service configurations from config file."""
        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    custom_config = json.load(f)
                    # Merge custom configurations
                    for service_name, service_config in custom_config.get(
                        "services",
                        {},
                    ).items():
                        if service_name in self.SERVICES:
                            # Update existing service config
                            current = self.SERVICES[service_name]
                            self.SERVICES[service_name] = ServiceConfig(
                                name=current.name,
                                command=service_config.get("command", current.command),
                                auth_method=service_config.get(
                                    "auth_method",
                                    current.auth_method,
                                ),
                                auth_env_var=service_config.get(
                                    "auth_env_var",
                                    current.auth_env_var,
                                ),
                                quota_limits=service_config.get(
                                    "quota_limits",
                                    current.quota_limits,
                                ),
                            )
                        else:
                            # Add new service config
                            self.SERVICES[service_name] = ServiceConfig(
                                **service_config,
                            )
            except Exception as e:
                logger.debug(
                    "Failed to load service config for %s: %s", service_name, e
                )

    def verify_service(self, service_name: str) -> tuple[bool, list[str]]:
        """Verify a service is available and authenticated."""
        if service_name not in self.SERVICES:
            return False, [f"Unknown service: {service_name}"]

        service = self.SERVICES[service_name]
        issues = []

        # Check command availability
        try:
            # CLI tool runs commands
            subprocess.run(  # noqa: S603 # nosec B603
                [service.command, "--version"],
                capture_output=True,
                timeout=10,
                check=True,
            )
        except (
            subprocess.CalledProcessError,
            FileNotFoundError,
            subprocess.TimeoutExpired,
        ):
            issues.append(f"Command '{service.command}' not found or not working")

        # Check authentication
        if service.auth_method == "api_key" and service.auth_env_var:
            if not os.getenv(service.auth_env_var):
                issues.append(f"Environment variable {service.auth_env_var} not set")
        elif service.auth_method == "cli":
            try:
                # CLI auth check
                result = subprocess.run(  # noqa: S603 # nosec B603
                    [service.command, "auth", "status"],
                    check=False,
                    capture_output=True,
                    timeout=10,
                    text=True,
                )
                if result.returncode != 0:
                    issues.append("Service not authenticated")
            except Exception:
                issues.append("Could not verify authentication status")

        return len(issues) == 0, issues

    def build_command(
        self,
        service_name: str,
        prompt: str,
        files: list[str] | None = None,
        options: dict[str, Any] | None = None,
    ) -> list[str]:
        """Build command for delegation."""
        service = self.SERVICES[service_name]
        command = [service.command]

        # Add options
        if options:
            if "model" in options:
                command.extend(["--model", options["model"]])
            if "output_format" in options:
                if service_name == "gemini":
                    command.extend(["--output-format", options["output_format"]])
                elif service_name == "qwen":
                    command.extend(["--format", options["output_format"]])
            if "temperature" in options:
                command.extend(["--temperature", str(options["temperature"])])

        # Add prompt with files
        full_prompt = prompt
        if files:
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
                full_prompt = " ".join(file_refs) + " " + full_prompt

        command.extend(["-p", full_prompt])

        return command

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

        # Build command
        command = self.build_command(service_name, prompt, files, options)

        # Execute
        try:
            # CLI execution
            result = subprocess.run(  # noqa: S603 # nosec B603
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=Path.cwd(),
            )

            duration = time.time() - start_time
            success = result.returncode == 0

            # Estimate tokens used
            tokens_used = estimate_tokens(files or [], prompt)

            execution_result = ExecutionResult(
                success=success,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                duration=duration,
                tokens_used=tokens_used,
                service=service_name,
            )

            # Log usage
            self.log_usage(service_name, command, execution_result)

            return execution_result

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Command timed out after {timeout} seconds",
                exit_code=124,
                duration=duration,
                service=service_name,
            )
        except Exception as e:
            duration = time.time() - start_time
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=str(e),
                exit_code=1,
                duration=duration,
                service=service_name,
            )

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
    ) -> tuple[str, ExecutionResult]:
        """Automatically select and execute with best service."""
        requirements = requirements or {}

        # Service selection logic
        if requirements.get("large_context") and requirements.get("gemini_available"):
            service = "gemini"
        elif requirements.get("code_execution") and requirements.get("qwen_available"):
            service = "qwen"
        elif requirements.get("fast_response"):
            service = "gemini"  # Gemini flash is typically faster
        else:
            # Default to first available service
            for service_name in ["gemini", "qwen"]:
                is_available, _ = self.verify_service(service_name)
                if is_available:
                    service = service_name
                    break
            else:
                msg = "No delegation services available"
                raise RuntimeError(msg)

        # Execute with optimal settings
        options = {}
        if requirements.get("large_context"):
            options["model"] = (
                "gemini-2.5-pro-exp" if service == "gemini" else "qwen-max"
            )
        elif requirements.get("fast_response"):
            options["model"] = (
                "gemini-2.5-flash-exp" if service == "gemini" else "qwen-turbo"
            )

        result = self.execute(service, prompt, files, options)
        return service, result


def _print_services(delegator: Delegator) -> None:
    """Print available services."""
    for _name, _config in delegator.SERVICES.items():
        pass


def _print_usage_summary(delegator: Delegator) -> None:
    """Print usage summary report."""
    summary = delegator.get_usage_summary()
    for _stats in summary["services"].values():
        pass


def _verify_service(delegator: Delegator, service_name: str) -> None:
    """Verify a service and print results."""
    is_available, issues = delegator.verify_service(service_name)
    if is_available:
        pass
    else:
        for _issue in issues:
            pass


def _print_result(result: ExecutionResult) -> None:
    """Print execution result."""
    if result.success:
        pass
    else:
        pass


def _create_parser() -> argparse.ArgumentParser:
    """Create argument parser for CLI."""
    parser = argparse.ArgumentParser(description="Unified delegation executor")
    parser.add_argument("service", nargs="?", help="Service name (gemini, qwen, auto)")
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
        _verify_service(delegator, args.service)
        return

    if not args.service or not args.prompt:
        parser.error("service and prompt are required for delegation execution")

    if args.service == "auto":
        try:
            _, result = delegator.smart_delegate(args.prompt, args.files)
        except RuntimeError:
            return
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

    _print_result(result)


if __name__ == "__main__":
    main()
