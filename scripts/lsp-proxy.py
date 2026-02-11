#!/usr/bin/env python3
"""LSP proxy that gracefully handles missing language servers.

If the target server binary is found, execs into it directly.
If not, runs a minimal no-op LSP server that handles the protocol
handshake correctly — preventing Claude Code from hanging.

Usage in .cclsp.json:
  "command": ["python3", "scripts/lsp-proxy.py", "pylsp"]
  "command": ["python3", "scripts/lsp-proxy.py", "typescript-language-server", "--stdio"]
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from typing import Optional


def find_and_exec(argv: list) -> None:
    """If the target binary exists, exec into it and never return."""
    binary = argv[0]
    if shutil.which(binary):
        os.execvp(binary, argv)
        # execvp only returns on failure
        sys.exit(1)


def read_message() -> Optional[dict]:
    """Read a single LSP JSON-RPC message from stdin."""
    # Read headers until blank line
    content_length = 0
    while True:
        line = sys.stdin.readline()
        if not line:
            return None
        line = line.strip()
        if not line:
            break
        if line.lower().startswith("content-length:"):
            content_length = int(line.split(":", 1)[1].strip())

    if content_length == 0:
        return None

    body = sys.stdin.read(content_length)
    if not body:
        return None

    return json.loads(body)


def send_message(msg: dict) -> None:
    """Write a single LSP JSON-RPC message to stdout."""
    body = json.dumps(msg)
    header = f"Content-Length: {len(body)}\r\n\r\n"
    sys.stdout.write(header)
    sys.stdout.write(body)
    sys.stdout.flush()


def run_noop_server(server_name: str) -> None:
    """Minimal LSP server: handles initialize/shutdown/exit, ignores the rest."""
    while True:
        msg = read_message()
        if msg is None:
            break

        method = msg.get("method", "")
        msg_id = msg.get("id")

        if method == "initialize":
            send_message({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "capabilities": {},
                    "serverInfo": {
                        "name": f"noop-lsp ({server_name} not installed)",
                        "version": "0.1.0",
                    },
                },
            })
        elif method == "shutdown":
            send_message({"jsonrpc": "2.0", "id": msg_id, "result": None})
        elif method == "exit":
            break
        elif msg_id is not None:
            # Request (has id) we don't handle — return empty result
            send_message({"jsonrpc": "2.0", "id": msg_id, "result": None})
        # Notifications (no id) are silently ignored


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: lsp-proxy.py <server-binary> [args...]", file=sys.stderr)
        sys.exit(1)

    server_argv = sys.argv[1:]
    server_name = server_argv[0]

    # Try to exec the real server — only returns if binary not found
    find_and_exec(server_argv)

    # Binary not found — run no-op server
    run_noop_server(server_name)


if __name__ == "__main__":
    main()
