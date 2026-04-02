"""Venv provisioning for the oracle inference daemon."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ProvisionResult:
    """Result of a provisioning attempt."""

    success: bool
    message: str


def get_oracle_data_dir() -> Path:
    """Return the oracle data directory."""
    env_dir = os.environ.get("CLAUDE_PLUGIN_DATA", "")
    if env_dir:
        return Path(env_dir)
    return Path.home() / ".oracle-inference"


def get_venv_path() -> Path:
    """Return the path to the oracle venv."""
    return get_oracle_data_dir() / "venv"


def is_provisioned(venv_path: Path) -> bool:
    """Return True if the venv has a working Python binary."""
    python = venv_path / "bin" / "python"
    if sys.platform == "win32":
        python = venv_path / "Scripts" / "python.exe"
    return python.exists()


def get_python_path(venv_path: Path) -> Path:
    """Return the path to the venv's Python binary."""
    if sys.platform == "win32":
        return venv_path / "Scripts" / "python.exe"
    return venv_path / "bin" / "python"


def provision_venv(venv_path: Path) -> ProvisionResult:
    """Provision a Python 3.11+ venv with onnxruntime."""
    try:
        result = subprocess.run(
            ["uv", "venv", "--python", "3.11", str(venv_path)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            return ProvisionResult(
                success=False,
                message=f"Failed to create venv: {result.stderr.strip()}",
            )

        python = str(get_python_path(venv_path))
        result = subprocess.run(
            ["uv", "pip", "install", "--python", python, "onnxruntime"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            return ProvisionResult(
                success=False,
                message=f"Failed to install onnxruntime: {result.stderr.strip()}",
            )

        return ProvisionResult(
            success=True,
            message=f"Oracle venv provisioned at {venv_path}",
        )

    except FileNotFoundError:
        return ProvisionResult(
            success=False,
            message=(
                "uv not found. Install it first: "
                "curl -LsSf https://astral.sh/uv/install.sh | sh"
            ),
        )
    except subprocess.TimeoutExpired:
        return ProvisionResult(
            success=False,
            message="Provisioning timed out. Check your network connection.",
        )
