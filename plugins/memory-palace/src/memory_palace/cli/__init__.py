"""Lightweight CLI entrypoint for Memory Palace utilities."""

from __future__ import annotations

import argparse
import json
from typing import TYPE_CHECKING

from memory_palace.lifecycle.autonomy_state import AutonomyStateStore

if TYPE_CHECKING:
    from collections.abc import Sequence


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m memory_palace.cli",
        description="Memory Palace management commands",
    )
    subparsers = parser.add_subparsers(dest="command")
    _add_autonomy_parser(subparsers)
    return parser


def _add_autonomy_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    autonomy_parser = subparsers.add_parser(
        "autonomy",
        help="Inspect and adjust autonomy governance levels",
    )
    autonomy_sub = autonomy_parser.add_subparsers(dest="autonomy_command", required=True)

    status_parser = autonomy_sub.add_parser("status", help="Show persisted autonomy state")
    status_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit status payload as JSON instead of human-readable text",
    )

    set_parser = autonomy_sub.add_parser("set", help="Set the autonomy level")
    set_parser.add_argument("--level", type=int, required=True, help="Desired autonomy level (0-5)")
    set_parser.add_argument(
        "--domain",
        help="Optional domain override (defaults to global level when omitted)",
    )
    lock_group = set_parser.add_mutually_exclusive_group()
    lock_group.add_argument("--lock", action="store_true", help="Lock the domain override")
    lock_group.add_argument("--unlock", action="store_true", help="Unlock the domain override")
    set_parser.add_argument("--reason", help="Optional note explaining the change")

    promote_parser = autonomy_sub.add_parser(
        "promote",
        help="Increase the autonomy level by one step",
    )
    promote_parser.add_argument("--domain", help="Optional domain override to promote")

    demote_parser = autonomy_sub.add_parser(
        "demote",
        help="Decrease the autonomy level by one step",
    )
    demote_parser.add_argument("--domain", help="Optional domain override to demote")


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return

    if args.command == "autonomy":
        _handle_autonomy(args)
        return

    parser.print_help()


def _handle_autonomy(args: argparse.Namespace) -> None:
    store = AutonomyStateStore()
    cmd = args.autonomy_command

    if cmd == "status":
        snapshot = store.snapshot()
        if getattr(args, "json", False):
            pass
        else:
            _print_status(snapshot)
        return

    if cmd == "set":
        lock_flag: bool | None
        if args.lock:
            lock_flag = True
        elif args.unlock:
            lock_flag = False
        else:
            lock_flag = None
        store.set_level(
            args.level,
            domain=getattr(args, "domain", None),
            lock=lock_flag,
            reason=getattr(args, "reason", None),
        )
        snapshot = store.snapshot()
        _print_status(snapshot)
        return

    if cmd == "promote":
        store.promote(domain=getattr(args, "domain", None))
        snapshot = store.snapshot()
        _print_status(snapshot)
        return

    if cmd == "demote":
        store.demote(domain=getattr(args, "domain", None))
        snapshot = store.snapshot()
        _print_status(snapshot)
        return

    msg = f"Unknown autonomy command: {cmd}"
    raise SystemExit(msg)


def _print_status(snapshot: dict[str, object]) -> None:
    domain_controls = snapshot.get("domain_controls") or {}
    if domain_controls:
        for domain in sorted(domain_controls):
            control = domain_controls[domain] or {}
            "locked" if control.get("locked") else "override"
            f" — {control.get('reason')}" if control.get("reason") else ""
    else:
        pass

    metrics = snapshot.get("metrics") or {}
    last_decision = metrics.get("last_decision")
    metrics.get("last_domains") or []
    if last_decision:
        pass
