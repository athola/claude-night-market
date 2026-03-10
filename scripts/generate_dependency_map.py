#!/usr/bin/env python3
"""Generate plugin dependency map by scanning Makefiles and pyproject.toml.

Scans:
- Makefile `-include` directives (build-time deps)
- pyproject.toml dependencies (runtime deps)
- Python imports in src/ and scripts/ (runtime coupling)

Output: JSON to stdout (--stdout) or docs/plugin-dependencies.json
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path


def find_plugins(plugins_dir: Path) -> list:
    """Find all plugin directories."""
    plugins = []
    for d in sorted(plugins_dir.iterdir()):
        if d.is_dir() and (d / ".claude-plugin" / "plugin.json").exists():
            plugins.append(d.name)
    return plugins


def scan_makefile_deps(plugin_dir: Path, all_plugins: list) -> list:
    """Scan Makefile for -include directives referencing other plugins."""
    makefile = plugin_dir / "Makefile"
    if not makefile.exists():
        return []

    deps = []
    content = makefile.read_text(encoding="utf-8")
    seen = set()

    for line in content.splitlines():
        # Match variable assignments like ABSTRACT_DIR := ../abstract
        var_match = re.match(
            r"^\s*(\w+_DIR)\s*:=\s*\.\./(\w[\w-]*)",
            line,
        )
        if var_match:
            dep_plugin = var_match.group(2)
            if dep_plugin in all_plugins and dep_plugin not in seen:
                seen.add(dep_plugin)
                deps.append(
                    {
                        "plugin": dep_plugin,
                        "type": "build",
                        "reason": f"Makefile variable ({var_match.group(1)})",
                    }
                )
            continue

        # Fallback: match literal includes like -include ../someplugin/path
        # NOTE: Real Makefiles use variable-expanded paths caught above.
        # This branch exists for repos that use literal relative paths.
        inc_match = re.match(r"^-?include\s+.*\.\./(\w[\w-]*)/(.+)", line)
        if inc_match:
            dep_plugin = inc_match.group(1)
            if dep_plugin in all_plugins and dep_plugin not in seen:
                seen.add(dep_plugin)
                deps.append(
                    {
                        "plugin": dep_plugin,
                        "type": "build",
                        "reason": f"Makefile include ({inc_match.group(2)})",
                    }
                )

    return deps


def scan_pyproject_deps(
    plugin_dir: Path,
    all_plugins: list,
) -> list:
    """Scan pyproject.toml for inter-plugin dependencies."""
    pyproject = plugin_dir / "pyproject.toml"
    if not pyproject.exists():
        return []

    deps = []
    seen = set()
    content = pyproject.read_text(encoding="utf-8")

    # Build a mapping of normalized names to original plugin names
    plugin_names = {}
    for p in all_plugins:
        plugin_names[p] = p
        plugin_names[p.replace("-", "_")] = p
        plugin_names[p.replace("-", "")] = p

    for line in content.splitlines():
        line_stripped = line.strip().strip('"').strip("'").strip(",")
        for norm_name, orig_name in plugin_names.items():
            if norm_name == plugin_dir.name or norm_name == plugin_dir.name.replace(
                "-", "_"
            ):
                continue
            if re.match(
                rf"^{re.escape(norm_name)}(\s*[><=!]|$)",
                line_stripped,
            ):
                if orig_name not in seen:
                    seen.add(orig_name)
                    deps.append(
                        {
                            "plugin": orig_name,
                            "type": "runtime",
                            "reason": "pyproject.toml dependency",
                        }
                    )
                break
    return deps


def scan_python_imports(
    plugin_dir: Path,
    plugin_name: str,
    all_plugins: list,
) -> list:
    """Scan Python files for cross-plugin imports."""
    deps = []
    seen = set()

    # Normalize for import matching
    import_names = {}
    for p in all_plugins:
        import_names[p.replace("-", "_")] = p

    src_dirs = [plugin_dir / "src", plugin_dir / "scripts"]
    for src_dir in src_dirs:
        if not src_dir.exists():
            continue
        for py_file in src_dir.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for line in content.splitlines():
                # Skip comments
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                for imp_name, orig_name in import_names.items():
                    if orig_name == plugin_name:
                        continue
                    if orig_name in seen:
                        continue
                    pattern = rf"(?:from|import)\s+{re.escape(imp_name)}\b"
                    if re.search(pattern, line):
                        seen.add(orig_name)
                        deps.append(
                            {
                                "plugin": orig_name,
                                "type": "runtime",
                                "reason": f"Python import in {py_file.name}",
                            }
                        )
    return deps


def generate_map(plugins_dir: Path) -> dict:
    """Generate the full dependency map."""
    all_plugins = find_plugins(plugins_dir)

    dependencies = {}
    reverse_index = {}

    # Initialize reverse index for all plugins
    for plugin in all_plugins:
        reverse_index[plugin] = []

    # Scan each plugin for its dependencies
    for plugin in all_plugins:
        plugin_dir = plugins_dir / plugin
        all_deps = []
        all_deps.extend(scan_makefile_deps(plugin_dir, all_plugins))
        all_deps.extend(scan_pyproject_deps(plugin_dir, all_plugins))
        all_deps.extend(
            scan_python_imports(plugin_dir, plugin, all_plugins),
        )

        # Deduplicate and build reverse index
        seen_plugins = set()
        for dep in all_deps:
            dep_name = dep["plugin"]
            if dep_name in seen_plugins:
                continue
            seen_plugins.add(dep_name)
            if dep_name not in reverse_index[plugin]:
                reverse_index[plugin].append(dep_name)

    # Build forward dependencies (which plugins are depended on)
    for plugin in all_plugins:
        # Find all plugins that depend on this one
        dependents = [
            p for p, deps in reverse_index.items() if plugin in deps and p != plugin
        ]
        if dependents:
            dep_type = "build"
            reason = "Shared infrastructure"
            # Check if all other plugins depend on it
            non_self = [p for p in all_plugins if p != plugin]
            if set(dependents) == set(non_self):
                dependents_val = ["*"]
            else:
                dependents_val = sorted(dependents)
            dependencies[plugin] = {
                "dependents": dependents_val,
                "type": dep_type,
                "reason": reason,
            }

    # Clean up reverse index: remove self-refs, sort, drop empties
    clean_reverse = {}
    for plugin in all_plugins:
        filtered = sorted(d for d in reverse_index[plugin] if d != plugin)
        if filtered:
            clean_reverse[plugin] = filtered

    return {
        "version": "1.0.0",
        "generated": datetime.date.today().isoformat(),
        "dependencies": dependencies,
        "reverse_index": clean_reverse,
    }


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(
        description="Generate plugin dependency map",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print to stdout instead of writing file",
    )
    parser.add_argument(
        "--output",
        default="docs/plugin-dependencies.json",
        help="Output file path (default: docs/plugin-dependencies.json)",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    plugins_dir = repo_root / "plugins"

    if not plugins_dir.exists():
        print("Error: plugins/ directory not found", file=sys.stderr)
        sys.exit(1)

    dep_map = generate_map(plugins_dir)

    output = json.dumps(dep_map, indent=2, sort_keys=False) + "\n"

    if args.stdout:
        print(output, end="")
    else:
        out_path = repo_root / args.output
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output, encoding="utf-8")
        print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
