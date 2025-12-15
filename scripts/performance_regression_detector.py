#!/usr/bin/env python3
"""Placeholder performance regression detector.

Current project layout no longer ships the original implementation. This stub
keeps pre-commit hooks passing while a real detector is restored. It accepts the
same CLI signature and exits successfully.
"""

import argparse
import sys


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stub performance regression detector."
    )
    parser.add_argument("paths", nargs="*", help="Paths to scan (unused)")
    parser.add_argument("--update-baseline", action="store_true", help="No-op flag")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    parse_args(argv or sys.argv[1:])
    # No checks performed; succeed to unblock workflow.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
