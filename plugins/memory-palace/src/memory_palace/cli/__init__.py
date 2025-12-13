"""Lightweight CLI entrypoint for Memory Palace utilities."""

from __future__ import annotations

import argparse
import json
from typing import TYPE_CHECKING

from memory_palace.lifecycle.autonomy_state import AutonomyStateStore

if TYPE_CHECKING:
    from collections.abc import Sequence


def build_parser() -> argparse.ArgumentParser:
    """Create the root CLI parser for Memory Palace utilities."""
    parser = argparse.ArgumentParser(
        prog="python -m memory_palace.cli",
        description="Memory Palace management commands",
    )
    subparsers = parser.add_subparsers(dest="command")
    _add_autonomy_parser(subparsers)
    _add_garden_parser(subparsers)
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
    """CLI entrypoint for memory_palace."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return

    if args.command == "autonomy":
        _handle_autonomy(args)
        return
    if args.command == "garden":
        _handle_garden(args)
        return

    parser.print_help()


def _handle_autonomy(args: argparse.Namespace) -> None:
    store = AutonomyStateStore()
    cmd = args.autonomy_command

    if cmd == "status":
        snapshot = store.snapshot()
        if getattr(args, "json", False):
            print(json.dumps(snapshot, indent=2))
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
    current_level = snapshot.get("current_level")
    effective_level = snapshot.get("effective_level")
    print(f"Current level: {current_level}")
    if effective_level is not None and effective_level != current_level:
        print(f"Effective level: {effective_level}")

    print()
    domain_controls = snapshot.get("domain_controls") or {}
    if domain_controls:
        print("Domain controls:")
        for domain in sorted(domain_controls):
            control = domain_controls[domain] or {}
            level = control.get("level", "unknown")
            locked = " (locked)" if control.get("locked") else ""
            reason = control.get("reason")
            reason_suffix = f" — {reason}" if reason else ""
            print(f"  - {domain}: level {level}{locked}{reason_suffix}")
    else:
        print("Domain controls: none configured")

    print()
    metrics = snapshot.get("metrics") or {}
    auto_approvals = metrics.get("auto_approvals", 0)
    flagged = metrics.get("flagged_requests", 0)
    blocked = metrics.get("blocked_requests", 0)
    print("Recent metrics:")
    print(f"  auto approvals: {auto_approvals}")
    print(f"  flagged requests: {flagged}")
    print(f"  blocked requests: {blocked}")

    last_decision = metrics.get("last_decision")
    last_domains = metrics.get("last_domains") or []
    if last_decision:
        domains_display = ", ".join(last_domains) if last_domains else "n/a"
        print(f"  last decision: {last_decision} (domains: {domains_display})")
    print()


def _add_garden_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    garden_parser = subparsers.add_parser(
        "garden",
        help="Lifecycle and tending utilities (garden:trust, garden:demote)",
    )
    garden_sub = garden_parser.add_subparsers(dest="garden_command", required=True)

    trust_parser = garden_sub.add_parser("trust", help="Grant trust for a specific domain")
    trust_parser.add_argument("--domain", required=True, help="Domain to trust")
    trust_parser.add_argument("--level", type=int, default=1, help="Target level for the domain")
    trust_parser.add_argument("--lock", action="store_true", help="Lock trust level for the domain")
    trust_parser.add_argument("--reason", help="Optional reason for audit log")

    demote_parser = garden_sub.add_parser("demote", help="Demote or unlock trust for a domain")
    demote_parser.add_argument("--domain", required=True)
    demote_parser.add_argument(
        "--unlock", action="store_true", help="Unlock the domain after demotion"
    )
    demote_parser.add_argument("--reason", help="Optional note for the demotion")


def _handle_garden(args: argparse.Namespace) -> None:
    store = AutonomyStateStore()
    state_location = str(store.state_path)
    if args.garden_command == "trust":
        updated = store.set_level(
            args.level,
            domain=args.domain,
            lock=True if args.lock else None,
            reason=getattr(args, "reason", None),
        )
        control = updated.domain_controls.get(args.domain.lower())
        level_value = control.level if control is not None else updated.current_level
        lock_flag = control.locked if control is not None else bool(args.lock)
        transcript_lines = [
            ("level", str(level_value)),
            ("lock", _bool_word(lock_flag)),
        ]
        reason = getattr(args, "reason", None)
        if reason:
            transcript_lines.append(("reason", reason))
        _emit_garden_transcript(
            action="trust",
            domain=args.domain,
            state_path=state_location,
            lines=transcript_lines,
        )
        print(f"Trusted {args.domain} at Level {level_value}")
        return
    if args.garden_command == "demote":
        updated = store.demote(domain=args.domain)
        if args.unlock:
            updated = store.set_level(
                updated.current_level,
                domain=args.domain,
                lock=False,
                reason=args.reason,
            )
        control = updated.domain_controls.get(args.domain.lower())
        level_value = control.level if control is not None else updated.current_level
        transcript_lines = [
            ("level", str(level_value)),
            ("unlock", _bool_word(bool(args.unlock))),
        ]
        if args.reason:
            transcript_lines.append(("reason", args.reason))
        _emit_garden_transcript(
            action="demote",
            domain=args.domain,
            state_path=state_location,
            lines=transcript_lines,
        )
        print(f"Demoted {args.domain}")
        return
    raise SystemExit(f"Unknown garden command: {args.garden_command}")


def _emit_garden_transcript(
    *,
    action: str,
    domain: str,
    state_path: str,
    lines: list[tuple[str, str]],
) -> None:
    print("Garden command transcript")
    print(f"  action: {action}")
    print(f"  domain: {domain}")
    for label, value in lines:
        print(f"  {label}: {value}")
    print(f"  state: {state_path}")


def _bool_word(value: bool) -> str:
    return "yes" if value else "no"
