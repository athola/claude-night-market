"""Planted positive control for the harden scanner.

Two findings the scanner must raise before any clean run elsewhere is
reportable. Scored by tests/unit/harden/test_scanner_cli.py. Do not fix.
"""

import pickle
import subprocess


def load_untrusted(blob: bytes) -> object:
    return pickle.loads(blob)  # planted: deserialization of untrusted input


def run_forever(cmd: list[str]) -> int:
    return subprocess.run(cmd, check=False).returncode  # planted: no timeout
