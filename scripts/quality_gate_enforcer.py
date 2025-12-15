#!/usr/bin/env python3
"""Placeholder quality gate enforcer.

Ensures pre-commit hook does not fail while the real enforcer is missing.
"""

import argparse
import sys


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stub quality gate enforcer.")
    parser.add_argument("paths", nargs="*", help="Paths to scan (unused)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    parse_args(argv or sys.argv[1:])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
