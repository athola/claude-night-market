#!/usr/bin/env python3
"""Detect which agentic framework is running and report capabilities.

Checks environment variables and directory patterns to identify
Claude Code, OpenClaw, NemoClaw, or generic MCP environments.
Used by the night-market bootstrapper to adapt installation
and behavior guidance.

Usage:
    python scripts/framework_detect.py
    python scripts/framework_detect.py --json
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass, field


@dataclass
class FrameworkInfo:
    """Detected framework information."""

    name: str
    version: str = "unknown"
    install_hint: str = ""
    capabilities: dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "version": self.version,
            "install_hint": self.install_hint,
            "capabilities": self.capabilities,
        }


# Capability templates per framework
_CAPABILITIES = {
    "claude-code": {
        "skills": True,
        "agents": True,
        "hooks": True,
        "commands": True,
        "mcp": True,
        "a2a": False,
    },
    "openclaw": {
        "skills": True,
        "agents": False,
        "hooks": False,
        "commands": False,
        "mcp": True,
        "a2a": False,
    },
    "nemoclaw": {
        "skills": True,
        "agents": False,
        "hooks": False,
        "commands": False,
        "mcp": True,
        "a2a": False,
    },
    "unknown": {
        "skills": False,
        "agents": False,
        "hooks": False,
        "commands": False,
        "mcp": True,
        "a2a": True,
    },
}

_INSTALL_HINTS = {
    "claude-code": (
        "Install the full plugin: claude plugin install athola/claude-night-market"
    ),
    "openclaw": (
        "Install from ClawHub: openclaw skills install night-market\n"
        "Or add the bridge plugin: "
        "openclaw plugin add bridge/openclaw/"
    ),
    "nemoclaw": (
        "Install from ClawHub (NemoClaw-compatible): "
        "openclaw skills install night-market\n"
        "Skills run within OpenShell sandbox automatically."
    ),
    "unknown": (
        "Use the MCP server for universal tool access, "
        "or A2A agent cards for agent discovery.\n"
        "MCP config: bridge/mcp/.mcp.json\n"
        "A2A cards: bridge/a2a/agent-cards.json"
    ),
}


def detect_framework() -> FrameworkInfo:
    """Detect the active agentic framework from environment."""

    # NemoClaw check first (runs on top of OpenClaw)
    if os.environ.get("NEMOCLAW_SANDBOX"):
        return FrameworkInfo(
            name="nemoclaw",
            version=os.environ.get("NEMOCLAW_VERSION", "unknown"),
            install_hint=_INSTALL_HINTS["nemoclaw"],
            capabilities=_CAPABILITIES["nemoclaw"],
        )

    # Claude Code
    if os.environ.get("CLAUDE_CODE_VERSION"):
        return FrameworkInfo(
            name="claude-code",
            version=os.environ.get("CLAUDE_CODE_VERSION", "unknown"),
            install_hint=_INSTALL_HINTS["claude-code"],
            capabilities=_CAPABILITIES["claude-code"],
        )

    # OpenClaw
    if os.environ.get("OPENCLAW_HOME"):
        return FrameworkInfo(
            name="openclaw",
            version=os.environ.get("OPENCLAW_VERSION", "unknown"),
            install_hint=_INSTALL_HINTS["openclaw"],
            capabilities=_CAPABILITIES["openclaw"],
        )

    # Unknown / generic MCP
    return FrameworkInfo(
        name="unknown",
        version="n/a",
        install_hint=_INSTALL_HINTS["unknown"],
        capabilities=_CAPABILITIES["unknown"],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Detect active agentic framework")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    args = parser.parse_args()

    info = detect_framework()

    if args.json:
        print(json.dumps(info.to_dict(), indent=2))
        return

    print(f"Framework: {info.name}")
    print(f"Version:   {info.version}")
    print()
    print("Capabilities:")
    for cap, supported in info.capabilities.items():
        marker = "+" if supported else "-"
        print(f"  [{marker}] {cap}")
    print()
    print("Install:")
    for line in info.install_hint.split("\n"):
        print(f"  {line}")


if __name__ == "__main__":
    main()
