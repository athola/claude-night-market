#!/usr/bin/env python3
"""Parse .claude/doc-sync.yaml and verify documentation stays in sync.

Reads mappings from the config, resolves source globs, extracts registered
items from each plugin.json, compares against markdown target tables, and
reports (or fixes) discrepancies.

Target: Python 3.9+
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(2)


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------


def find_repo_root() -> Path:
    """Walk up from cwd to find the repo root (.git directory)."""
    p = Path.cwd()
    while p != p.parent:
        if (p / ".git").exists():
            return p
        p = p.parent
    return Path.cwd()


def load_config(config_path: Path) -> dict[str, Any]:
    """Load and validate the doc-sync YAML config."""
    if not config_path.exists():
        print(f"ERROR: Config not found: {config_path}", file=sys.stderr)
        sys.exit(2)
    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict) or "version" not in data:
        print("ERROR: Invalid config - missing 'version' key", file=sys.stderr)
        sys.exit(2)
    if data["version"] != 1:
        print(f"ERROR: Unsupported config version: {data['version']}", file=sys.stderr)
        sys.exit(2)
    if "mappings" not in data or not data["mappings"]:
        print("ERROR: Config has no mappings", file=sys.stderr)
        sys.exit(2)
    return data


# ---------------------------------------------------------------------------
# Source extraction
# ---------------------------------------------------------------------------


def strip_value(value: str, prefix: str | None, suffix: str | None) -> str:
    """Strip prefix and/or suffix from a value."""
    if prefix and value.startswith(prefix):
        value = value[len(prefix) :]
    if suffix and value.endswith(suffix):
        value = value[: -len(suffix)]
    return value


def extract_items_from_source(
    source_path: Path,
    extract_rules: list[dict[str, str]],
) -> dict[str, list[tuple[str, str]]]:
    """Extract named items from a plugin.json source file.

    Returns a dict mapping extract type (e.g. "skills") to list of
    (item_name, plugin_name) tuples.
    """
    with open(source_path, encoding="utf-8") as f:
        data = json.load(f)

    plugin_name = data.get("name", source_path.parent.parent.name)
    results: dict[str, list[tuple[str, str]]] = {}

    for rule in extract_rules:
        key = rule["path"]
        prefix = rule.get("strip_prefix")
        suffix = rule.get("strip_suffix")
        raw_items = data.get(key, [])
        items = []
        for item in raw_items:
            name = strip_value(item, prefix, suffix)
            items.append((name, plugin_name))
        results[key] = items

    return results


def resolve_sources(
    source_glob: str,
    root: Path,
    extract_rules: list[dict[str, str]],
) -> dict[str, list[tuple[str, str]]]:
    """Resolve glob pattern and aggregate items from all matching sources."""
    pattern = str(root / source_glob)
    matched = sorted(glob.glob(pattern))
    if not matched:
        print(f"WARNING: No files matched source glob: {source_glob}", file=sys.stderr)

    aggregated: dict[str, list[tuple[str, str]]] = {}
    for path_str in matched:
        source_path = Path(path_str)
        items = extract_items_from_source(source_path, extract_rules)
        for key, item_list in items.items():
            aggregated.setdefault(key, []).extend(item_list)

    return aggregated


# ---------------------------------------------------------------------------
# Target parsing
# ---------------------------------------------------------------------------


def find_section_range(
    lines: list[str], section_heading: str
) -> tuple[int, int] | None:
    """Find the line range of a markdown section (from heading to next heading).

    Returns (start_line, end_line) where start_line is the heading itself
    and end_line is the line before the next same-or-higher-level heading.
    """
    heading_level = 0
    start = -1

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("#"):
            continue
        match = re.match(r"^(#{1,6})\s+(.+?)(?:\s*#*)?\s*$", stripped)
        if not match:
            continue
        level = len(match.group(1))
        text = match.group(2).strip()

        if text == section_heading:
            heading_level = level
            start = i
            continue

        if start >= 0 and level <= heading_level:
            return (start, i)

    if start >= 0:
        return (start, len(lines))
    return None


def extract_table_names(lines: list[str], start: int, end: int) -> set[str]:
    """Extract item names from a markdown table within a section.

    Expects names in the first column, formatted as `name` (backtick-wrapped).
    """
    names: set[str] = set()
    for i in range(start, end):
        line = lines[i].strip()
        if not line.startswith("|"):
            continue
        # Skip header and separator rows
        if re.match(r"^\|[-\s|]+\|$", line):
            continue
        cells = [c.strip() for c in line.split("|")]
        # cells[0] is empty (before first |), cells[1] is first column
        if len(cells) >= 2:
            name_cell = cells[1]
            # Extract from backtick-wrapped or slash-prefixed names
            bt_match = re.match(r"^`(.+?)`$", name_cell)
            if bt_match:
                names.add(bt_match.group(1))
            elif name_cell.startswith("`/") or name_cell.startswith("/"):
                clean = name_cell.strip("`").lstrip("/")
                names.add(clean)
    return names


# ---------------------------------------------------------------------------
# Comparison and reporting
# ---------------------------------------------------------------------------


class Discrepancy:
    """A single sync discrepancy."""

    def __init__(
        self, kind: str, item: str, plugin: str, target: str, extract_type: str
    ):
        self.kind = kind  # "missing" or "extra"
        self.item = item
        self.plugin = plugin
        self.target = target
        self.extract_type = extract_type

    def __str__(self) -> str:
        if self.kind == "missing":
            return f"  MISSING in {self.target}: `{self.item}` (from {self.plugin}, type={self.extract_type})"
        return f"  EXTRA in {self.target}: `{self.item}` (not in any source, type={self.extract_type})"


def compare_mapping(
    mapping: dict[str, Any],
    root: Path,
    defaults: dict[str, Any],
) -> list[Discrepancy]:
    """Compare a single mapping's sources against its targets."""
    source_glob = mapping["source"]
    extract_rules = mapping["extract"]
    targets = mapping["targets"]

    source_items = resolve_sources(source_glob, root, extract_rules)
    discrepancies: list[Discrepancy] = []

    on_missing = defaults.get("on_missing", "warn")
    on_extra = defaults.get("on_extra", "warn")

    for target_cfg in targets:
        target_path = root / target_cfg["path"]
        section_template = target_cfg["section"]

        if not target_path.exists():
            print(f"WARNING: Target file not found: {target_path}", file=sys.stderr)
            continue

        lines = target_path.read_text(encoding="utf-8").splitlines()

        for extract_type, items in source_items.items():
            # Resolve the section heading placeholder
            type_label = extract_type.rstrip("s")  # skills -> skill
            # Capitalize for heading: "skill" -> "Skill"
            section_heading = section_template.replace(
                "{type}", type_label.capitalize()
            )

            section_range = find_section_range(lines, section_heading)
            if section_range is None:
                print(
                    f"WARNING: Section '{section_heading}' not found in {target_cfg['path']}",
                    file=sys.stderr,
                )
                continue

            start, end = section_range
            target_names = extract_table_names(lines, start, end)

            # Items in source but not target
            if on_missing != "ignore":
                for name, plugin in items:
                    # For commands, check with and without leading /
                    check_names = {name, name.lstrip("/")}
                    if name.startswith("/"):
                        check_names.add(name[1:])
                    else:
                        check_names.add("/" + name)
                    if not check_names & target_names:
                        discrepancies.append(
                            Discrepancy(
                                "missing",
                                name,
                                plugin,
                                target_cfg["path"],
                                extract_type,
                            )
                        )

            # Items in target but not source
            if on_extra != "ignore":
                # Build lookup including /command variants
                source_lookup: set[str] = set()
                for name, _ in items:
                    source_lookup.add(name)
                    source_lookup.add(name.lstrip("/"))
                    if not name.startswith("/"):
                        source_lookup.add("/" + name)
                for tname in target_names:
                    check = {tname, tname.lstrip("/"), "/" + tname}
                    if not check & source_lookup:
                        discrepancies.append(
                            Discrepancy(
                                "extra", tname, "?", target_cfg["path"], extract_type
                            )
                        )

    return discrepancies


# ---------------------------------------------------------------------------
# Fix mode
# ---------------------------------------------------------------------------


def apply_fixes(
    discrepancies: list[Discrepancy],
    mapping: dict[str, Any],
    root: Path,
) -> int:
    """Insert missing rows into target markdown tables. Returns count of fixes."""
    # Only fix missing items
    missing = [d for d in discrepancies if d.kind == "missing"]
    if not missing:
        return 0

    # Group by (target, extract_type)
    groups: dict[tuple[str, str], list[Discrepancy]] = {}
    for d in missing:
        key = (d.target, d.extract_type)
        groups.setdefault(key, []).append(d)

    targets_cfg = {t["path"]: t for t in mapping["targets"]}
    fixed = 0

    for (target_rel, extract_type), items in groups.items():
        target_path = root / target_rel
        if not target_path.exists():
            continue

        target_cfg = targets_cfg.get(target_rel)
        if not target_cfg:
            continue

        lines = target_path.read_text(encoding="utf-8").splitlines()
        type_label = extract_type.rstrip("s")
        section_heading = target_cfg["section"].replace(
            "{type}", type_label.capitalize()
        )
        section_range = find_section_range(lines, section_heading)
        if section_range is None:
            continue

        _start, end = section_range
        fmt = target_cfg["format"]

        # Insert new rows before the section ends (before next heading or EOF)
        insert_at = end
        # Walk back to find the last table row
        for i in range(end - 1, _start, -1):
            if lines[i].strip().startswith("|"):
                insert_at = i + 1
                break

        new_lines: list[str] = []
        for d in sorted(items, key=lambda x: x.item.lower()):
            row = fmt.replace("{name}", d.item)
            row = row.replace("{plugin}", d.plugin)
            row = row.replace("{type}", extract_type)
            row = row.replace("{description}", "TODO")
            new_lines.append(row)
            fixed += 1

        for idx, new_line in enumerate(new_lines):
            lines.insert(insert_at + idx, new_line)

        target_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return fixed


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify documentation stays in sync with plugin sources."
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to doc-sync.yaml (default: .claude/doc-sync.yaml)",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Write missing entries into target files",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on any discrepancy (warnings become errors)",
    )
    args = parser.parse_args()

    root = find_repo_root()

    if args.config:
        config_path = Path(args.config)
    else:
        config_path = root / ".claude" / "doc-sync.yaml"

    config = load_config(config_path)
    defaults = config.get("defaults", {})

    all_discrepancies: list[Discrepancy] = []

    for mapping in config["mappings"]:
        name = mapping.get("name", "<unnamed>")
        print(f"Checking mapping: {name}")
        discs = compare_mapping(mapping, root, defaults)
        all_discrepancies.extend(discs)

    if not all_discrepancies:
        print("\nAll targets are in sync.")
        return 0

    # Report
    missing = [d for d in all_discrepancies if d.kind == "missing"]
    extra = [d for d in all_discrepancies if d.kind == "extra"]

    if missing:
        print(f"\n{len(missing)} missing item(s):")
        for d in sorted(missing, key=lambda x: x.item.lower()):
            print(str(d))

    if extra:
        print(f"\n{len(extra)} extra item(s):")
        for d in sorted(extra, key=lambda x: x.item.lower()):
            print(str(d))

    # Fix mode
    if args.fix:
        if not defaults.get("auto_fix", False) and not args.fix:
            print("\nauto_fix is disabled in config. Pass --fix to override.")
        else:
            total_fixed = 0
            for mapping in config["mappings"]:
                mapping_discs = [d for d in all_discrepancies if d.kind == "missing"]
                fixed = apply_fixes(mapping_discs, mapping, root)
                total_fixed += fixed
            if total_fixed:
                print(f"\nFixed {total_fixed} missing item(s).")
            else:
                print("\nNo fixes applied.")

    total = len(all_discrepancies)
    print(f"\nTotal discrepancies: {total}")

    if args.strict:
        return 1
    # Return 1 only if on_missing or on_extra is "error"
    if defaults.get("on_missing") == "error" and missing:
        return 1
    if defaults.get("on_extra") == "error" and extra:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
