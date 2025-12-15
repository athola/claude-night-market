#!/usr/bin/env python3
"""Placeholder plugin API compatibility checker.

The previous implementation is absent; this stub maintains passing hooks until
the real checker is reinstated.
"""

import argparse
import sys


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stub plugin API compatibility checker."
    )
    parser.add_argument("paths", nargs="*", help="Plugin paths (unused)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    parse_args(argv or sys.argv[1:])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
