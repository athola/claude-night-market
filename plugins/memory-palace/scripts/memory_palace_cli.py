#!/usr/bin/env python3
"""Manage the Memory Palace using a command-line interface.

Provide commands for enabling, disabling, and managing the plugin,
its skills, and associated palaces. Serve as the primary entrypoint
for administrative tasks.
"""

import argparse
import json
import os
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from memory_palace.garden_metrics import compute_garden_metrics
from memory_palace.palace_manager import MemoryPalaceManager


@dataclass
class TendingOptions:
    """Define parameters for a garden tending operation.

    The process involves reviewing and maintaining a digital garden by
    identifying stale, overgrown, or archivable content based on time-based
    thresholds.
    """

    path: str | None
    now: str | None
    prune_days: int
    stale_days: int
    archive_days: int
    apply: bool
    archive_export: str | None
    prometheus: bool
    label: str | None


@dataclass
class TendingContext:
    """Hold all data and computed values for a single garden tending run.

    Includes full garden data, a list of plots, a dictionary of computed actions
    (prune, stale, archive), the run timestamp, and the path to the garden file
    being tended.
    """

    data: dict[str, Any]
    plots: list[dict[str, Any]]
    actions: dict[str, list[tuple[str, float | str]]]
    now_dt: datetime
    target_path: Path


class MemoryPalaceCLI:
    """Provide the main entrypoint for all command-line operations."""

    def __init__(self) -> None:
        """Initialize the Memory Palace CLI."""
        self.script_dir = Path(__file__).parent
        self.plugin_dir = self.script_dir.parent
        self.config_file = self.plugin_dir / "config" / "settings.json"
        self.claude_config = Path.home() / ".claude" / "settings.json"

    def _palaces_dir(self, override: str | None = None) -> str | None:
        """Resolve the palaces directory from override or environment."""
        return override or os.environ.get("PALACES_DIR")

    def _manager(self, palaces_dir: str | None = None) -> MemoryPalaceManager:
        """Create a palace manager with optional directory override."""
        return MemoryPalaceManager(
            str(self.config_file), self._palaces_dir(palaces_dir)
        )

    def print_status(self, message: str) -> None:
        """Print a status message to the console."""

    def print_success(self, message: str) -> None:
        """Print a success message to the console."""

    def print_warning(self, message: str) -> None:
        """Print a warning message to the console."""

    def print_error(self, message: str) -> None:
        """Print an error message to the console."""

    def is_enabled(self) -> bool:
        """Check if the plugin is enabled in the Claude configuration."""
        if not self.claude_config.exists():
            return False

        try:
            with open(self.claude_config) as f:
                config = json.load(f)

            # Check if memory palace is enabled and permissions are set
            permissions = config.get("permissions", {})
            allow_list = permissions.get("allow", [])

            # Check for memory palace permissions
            plugin_dir_str = str(self.plugin_dir)
            return any(plugin_dir_str in perm for perm in allow_list)
        except (json.JSONDecodeError, KeyError):
            return False

    def enable_plugin(self) -> None:
        """Enable the Memory Palace plugin.

        Add necessary permissions to the Claude configuration file and create the
        palace storage directory.
        """
        self.print_status("Enabling Memory Palace plugin...")

        # validate config directory exists
        self.claude_config.parent.mkdir(parents=True, exist_ok=True)

        # Create or update Claude config
        config: dict[str, Any] = {"permissions": {"allow": [], "deny": [], "ask": []}}

        if self.claude_config.exists():
            try:
                with open(self.claude_config) as f:
                    config = json.load(f)
            except json.JSONDecodeError:
                self.print_warning("Existing config was invalid, creating new one")

        # Add memory palace permissions
        permissions = config.setdefault("permissions", {})
        allow_list = permissions.setdefault("allow", [])

        plugin_dir_str = str(self.plugin_dir)
        memory_palace_perms = [
            f"Bash({plugin_dir_str}/tools/palace_manager.py*)",
            f"Bash({plugin_dir_str}/tools/memory_palace_cli.py*)",
            f"Read({plugin_dir_str}/**)",
            f"Write({plugin_dir_str}/**)",
            "Bash(mkdir*)",
            "Bash(ls*)",
            "Bash(find*)",
        ]

        for perm in memory_palace_perms:
            if perm not in allow_list:
                allow_list.append(perm)

        permissions["allow"] = allow_list
        config["permissions"] = permissions

        with open(self.claude_config, "w") as f:
            json.dump(config, f, indent=2)

        # Create palace directory
        palaces_dir = Path.home() / "memory-palaces"
        palaces_dir.mkdir(exist_ok=True)

        self.print_success("Memory Palace plugin enabled!")
        self.print_status(f"Palace storage directory: {palaces_dir}")
        self.print_status(f"Configuration file: {self.config_file}")

    def disable_plugin(self) -> None:
        """Disable the Memory Palace plugin.

        Remove the plugin's permissions from the Claude configuration file.
        """
        self.print_status("Disabling Memory Palace plugin...")

        if not self.claude_config.exists():
            self.print_warning("Plugin doesn't appear to be enabled")
            return

        try:
            with open(self.claude_config) as f:
                config = json.load(f)

            # Remove memory palace permissions
            permissions = config.get("permissions", {})
            allow_list = permissions.get("allow", [])

            plugin_dir_str = str(self.plugin_dir)
            allow_list = [perm for perm in allow_list if plugin_dir_str not in perm]

            permissions["allow"] = allow_list
            config["permissions"] = permissions

            with open(self.claude_config, "w") as f:
                json.dump(config, f, indent=2)

            self.print_success("Memory Palace plugin disabled!")

        except (json.JSONDecodeError, KeyError):
            self.print_error("Error updating configuration")

    def show_status(self) -> None:
        """Show the current status of the plugin."""
        self.print_status("Memory Palace Plugin Status")

        if self.is_enabled():
            self.print_success("Status: ENABLED")
        else:
            self.print_warning("Status: DISABLED")

        self.print_status("Configuration:")

        # Show palace statistics if enabled
        if self.is_enabled():
            self.print_status("Palace Statistics:")
            try:
                index = self._manager().get_master_index()
                stats = index.get("global_stats", {})
                domains = stats.get("domains", {})
                for _domain, _count in domains.items():
                    pass
            except Exception as e:
                self.print_warning(f"Could not get palace statistics: {e}")

            garden_path = Path(
                os.environ.get("GARDEN_FILE", str(self.plugin_dir / "garden.json"))
            )
            if garden_path.exists():
                self.print_status(f"Digital Garden Metrics ({garden_path}):")
                try:
                    compute_garden_metrics(garden_path)
                except Exception as e:
                    self.print_warning(f"Could not compute garden metrics: {e}")

    def garden_metrics(
        self,
        path: str | None = None,
        now: str | None = None,
        output_format: str = "json",
        label: str | None = None,
    ) -> None:
        """Compute and print digital garden metrics."""
        target = path or os.environ.get(
            "GARDEN_FILE", str(self.plugin_dir / "garden.json")
        )
        if not Path(target).exists():
            self.print_warning(f"Garden file not found: {target}")
            return

        self.print_status(f"Computing garden metrics for {target}")
        try:
            compute_garden_metrics(
                Path(target),
                datetime.fromisoformat(now) if now else None,
            )
            if output_format == "brief":
                pass
            elif output_format == "prometheus":
                label_val = label or Path(target).stem

                def line(metric: str, value: Any) -> str:
                    return f'{metric}{{garden="{label_val}"}} {value}'

            else:
                pass
        except Exception as e:
            self.print_error(f"Metrics failed: {e}")

    def garden_tend(self, opts: TendingOptions, include_palaces: bool = False) -> None:
        """Report and optionally apply tending actions to a digital garden.

        If include_palaces is True, also check palace health and report
        entries needing cleanup.
        """
        # Check palace health first if requested
        if include_palaces:
            print("Palace Health Check")
            print("=" * 50)
            self.prune_check(stale_days=opts.stale_days)
            print()

        target_env = os.environ.get("GARDEN_FILE", self.plugin_dir / "garden.json")
        target_path = Path(opts.path or target_env)
        if not target_path.exists():
            self.print_warning(f"Garden file not found: {target_path}")
            return

        now_dt = datetime.fromisoformat(opts.now) if opts.now else datetime.now(UTC)
        with target_path.open(encoding="utf-8") as f:
            data = json.load(f)

        plots = data.get("garden", {}).get("plots", [])
        if not plots:
            self.print_warning("No plots found in garden.")
            return

        def days_since(ts: str) -> float:
            return (now_dt - datetime.fromisoformat(ts)).total_seconds() / 86400

        actions = self._compute_tending_actions(
            plots,
            now_dt,
            opts.prune_days,
            opts.stale_days,
            opts.archive_days,
        )
        ctx = TendingContext(
            data=data,
            plots=plots,
            actions=actions,
            now_dt=now_dt,
            target_path=target_path,
        )
        self._emit_tending_report(ctx, opts)

        if opts.apply:
            self._apply_tending_actions(ctx, opts)

    def _compute_tending_actions(
        self,
        plots: list[dict[str, Any]],
        now_dt: datetime,
        prune_threshold_days: int,
        stale_days: int,
        archive_days: int,
    ) -> dict[str, list[tuple[str, float | str]]]:
        """Compute tending actions based on plot freshness.

        Args:
            plots: A list of plot dictionaries.
            now_dt: The current datetime to compare against.
            prune_threshold_days: The age in days to flag a plot for pruning.
            stale_days: The age in days to flag a plot as stale.
            archive_days: The age in days to flag a plot for archiving.

        Returns:
            A dictionary of actions, with keys "prune", "stale", and "archive".

        """
        actions: dict[str, list[tuple[str, float | str]]] = {
            "prune": [],
            "stale": [],
            "archive": [],
        }

        for plot in plots:
            last = plot.get("last_tended")
            name = plot.get("name", "<unnamed>")
            if not last:
                actions["prune"].append((name, "never tended"))
                continue

            days = (now_dt - datetime.fromisoformat(last)).total_seconds() / 86400
            if days >= archive_days:
                actions["archive"].append((name, round(days, 2)))
            elif days >= stale_days:
                actions["stale"].append((name, round(days, 2)))
            elif days >= prune_threshold_days:
                actions["prune"].append((name, round(days, 2)))

        return actions

    def _emit_tending_report(self, ctx: TendingContext, opts: TendingOptions) -> None:
        """Print the tending report to the console.

        Args:
            ctx: The TendingContext for the current run.
            opts: The TendingOptions for the current run.

        """
        self.print_status(f"Tending report for {ctx.target_path}")
        if opts.prometheus:
            label_val = opts.label or ctx.target_path.stem

            def line(metric: str, value: Any) -> str:
                return f'{metric}{{garden="{label_val}"}} {value}'

            return

        if ctx.actions["prune"]:
            for _name, _age in ctx.actions["prune"]:
                pass
        if ctx.actions["stale"]:
            for _name, _age in ctx.actions["stale"]:
                pass
        if ctx.actions["archive"]:
            for _name, _age in ctx.actions["archive"]:
                pass
        if not any(ctx.actions.values()):
            self.print_success("All plots are fresh within cadence.")

    def _apply_tending_actions(self, ctx: TendingContext, opts: TendingOptions) -> None:
        """Apply computed tending actions to the garden file.

        Create a backup of the garden file, then update plots in the garden data
        based on computed actions. Update `last_tended` timestamp for pruned
        plots, and move archived plots to the `compost` list.

        Args:
            ctx: The TendingContext for the current run.
            opts: The TendingOptions for the current run.

        """
        self.print_status("Applying tending actions (backup will be created).")
        backup = Path(str(ctx.target_path) + ".bak")
        shutil.copyfile(ctx.target_path, backup)

        updated_plots: list[dict[str, Any]] = []
        compost = ctx.data.get("garden", {}).setdefault("compost", [])
        archived: list[dict[str, Any]] = []

        archive_names = {name for name, _ in ctx.actions["archive"]}
        prune_names = {name for name, _ in ctx.actions["prune"]}

        for plot in ctx.plots:
            name = plot.get("name", "<unnamed>")
            if name in archive_names:
                plot["archived_at"] = ctx.now_dt.isoformat()
                compost.append(plot)
                archived.append(plot)
                continue
            if name in prune_names:
                plot["last_tended"] = ctx.now_dt.isoformat()
            updated_plots.append(plot)

        ctx.data.setdefault("garden", {})["plots"] = updated_plots
        ctx.data["garden"]["compost"] = compost

        with ctx.target_path.open("w", encoding="utf-8") as file:
            json.dump(ctx.data, file, indent=2)

        if opts.archive_export and archived:
            export_path = Path(opts.archive_export)
            with export_path.open("w", encoding="utf-8") as file:
                json.dump({"archived": archived}, file, indent=2)
            self.print_success(f"Archived plots exported to {export_path}")

        self.print_success(f"Tending applied. Backup saved to {backup}")

    def list_skills(self) -> None:
        """List the available skills in the Memory Palace."""
        self.print_status("Available Memory Palace Skills:")

        skills_dir = self.plugin_dir / "skills"
        if not skills_dir.exists():
            self.print_warning("No skills directory found")
            return

        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir():
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    # Extract description from skill file
                    try:
                        with open(skill_file) as f:
                            content = f.read()

                        # Extract description from YAML frontmatter
                        for line in content.split("\n"):
                            if line.startswith("description:"):
                                line.split(":", 1)[1].strip().strip('"')
                                break

                    except Exception as e:
                        self.print_warning(
                            f"Could not read skill {skill_dir.name}: {e}"
                        )

    def create_palace(self, name: str, domain: str, metaphor: str = "building") -> bool:
        """Create a new memory palace with a given name, domain, and metaphor.

        Args:
            name: The name of the palace.
            domain: The knowledge domain of the palace (e.g., "programming").
            metaphor: The architectural metaphor for the palace (e.g., "building").

        Returns:
            True if the palace was created successfully, False otherwise.

        """
        if not name or not domain:
            self.print_error("Usage: create <name> <domain> [metaphor]")
            return False

        self.print_status(f"Creating palace '{name}' in domain '{domain}'...")

        try:
            manager = self._manager()
            manager.create_palace(name, domain, metaphor)
            return True
        except Exception as e:
            self.print_error(f"Failed to create palace: {e}")
            return False

    def list_palaces(self) -> bool:
        """List all available memory palaces."""
        try:
            palaces = self._manager().list_palaces()
            if palaces:
                print("Available Memory Palaces:")
                print("-" * 60)
                for palace in palaces:
                    print(f"  {palace['id']}: {palace['name']}")
                    print(
                        f"    Domain: {palace['domain']}, Entries: {palace.get('concept_count', 0)}"
                    )
                print("-" * 60)
                print(f"Total: {len(palaces)} palaces")
            else:
                print(
                    "No palaces found. Create one with: /palace create <name> <domain>"
                )
            return True
        except Exception as e:
            self.print_error(f"Failed to list palaces: {e}")
            return False

    def sync_queue(self, auto_create: bool = False, dry_run: bool = False) -> bool:
        """Sync intake queue into palaces."""
        try:
            queue_path = self.plugin_dir / "data" / "intake_queue.jsonl"
            results = self._manager().sync_from_queue(
                str(queue_path),
                auto_create=auto_create,
                dry_run=dry_run,
            )

            if dry_run:
                print("DRY RUN - No changes made")
                print("-" * 40)

            print(f"Processed: {results['processed']} items")
            print(f"Skipped: {results['skipped']} items")

            if results["palaces_updated"]:
                print(f"Palaces updated: {', '.join(results['palaces_updated'])}")
            if results["palaces_created"]:
                print(f"Palaces created: {', '.join(results['palaces_created'])}")
            if results["unmatched"]:
                print(f"Unmatched queries: {len(results['unmatched'])}")
                for q in results["unmatched"][:5]:
                    print(f"  - {q}")

            return True
        except Exception as e:
            self.print_error(f"Failed to sync queue: {e}")
            return False

    def prune_check(self, stale_days: int = 90) -> bool:
        """Check palaces for entries needing cleanup."""
        try:
            results = self._manager().prune_check(stale_days=stale_days)

            print("Palace Prune Check")
            print("=" * 50)
            print(f"Palaces checked: {results['palaces_checked']}")
            print()

            if (
                results["total_stale"] == 0
                and results["total_low_quality"] == 0
                and results["total_duplicates"] == 0
            ):
                print("No cleanup needed - all palaces are healthy!")
                return True

            print("Recommendations:")
            print("-" * 50)

            if results["total_stale"] > 0:
                print(f"  Stale entries (>{stale_days} days): {results['total_stale']}")
            if results["total_low_quality"] > 0:
                print(
                    f"  Low quality entries (score<0.3): {results['total_low_quality']}"
                )
            if results["total_duplicates"] > 0:
                print(f"  Duplicate entries: {results['total_duplicates']}")

            print()
            for rec in results.get("recommendations", []):
                print(f"  {rec['palace_name']} ({rec['palace_id']}):")
                if rec["stale"]:
                    print(f"    - {len(rec['stale'])} stale entries")
                if rec["low_quality"]:
                    print(f"    - {len(rec['low_quality'])} low quality entries")

            if results.get("duplicates"):
                print()
                print("  Duplicates found:")
                for dup in results["duplicates"][:5]:
                    print(f"    - '{dup['query']}' in {len(dup['locations'])} places")

            print()
            print("Run '/palace prune --apply' to clean up (requires approval)")
            return True
        except Exception as e:
            self.print_error(f"Failed to check palaces: {e}")
            return False

    def prune_apply(self, actions: list[str]) -> bool:
        """Apply prune actions after user approval."""
        try:
            results = self._manager().prune_check()
            if not results["recommendations"]:
                print("No cleanup needed.")
                return True

            removed = self._manager().apply_prune(results, actions)
            print("Prune Applied:")
            print(f"  Stale removed: {removed['stale']}")
            print(f"  Low quality removed: {removed['low_quality']}")
            return True
        except Exception as e:
            self.print_error(f"Failed to apply prune: {e}")
            return False

    def search_palaces(self, query: str, search_type: str = "semantic") -> bool:
        """Search for a query across all memory palaces."""
        if not query:
            self.print_error("Usage: search <query> [semantic|exact|fuzzy]")
            return False

        self.print_status(f"Searching for '{query}'...")

        try:
            results = self._manager().search_palaces(query, search_type)
            if results:
                for result in results:
                    for _match in result["matches"]:
                        pass
            else:
                pass
            return True
        except Exception as e:
            self.print_error(f"Search failed: {e}")
            return False

    def install_skills(self) -> bool:
        """Install the Memory Palace skills into Claude's skill directory."""
        self.print_status("Installing Memory Palace skills...")

        # Find Claude's skills directory
        claude_dir = Path.home() / ".claude"
        skills_dir = None

        # Look for possible skills directories
        for path in claude_dir.rglob("skills"):
            if path.is_dir():
                skills_dir = path
                break

        if not skills_dir:
            self.print_error("Could not find Claude skills directory")
            return False

        memory_palace_skills_dir = skills_dir / "memory-palace"

        # Remove existing installation if present
        if memory_palace_skills_dir.exists():
            shutil.rmtree(memory_palace_skills_dir)

        # Copy skills
        source_skills = self.plugin_dir / "skills"
        if source_skills.exists():
            shutil.copytree(source_skills, memory_palace_skills_dir)
            self.print_success(f"Skills installed to: {memory_palace_skills_dir}")
            return True
        self.print_error("No skills directory found in plugin")
        return False

    def run_palace_manager(self, args: list[str]) -> bool:
        """Handle a subset of palace_manager commands directly."""
        if not args:
            self.print_error("No manager arguments provided")
            return False

        manager = self._manager()
        command = args[0]

        if command == "delete" and len(args) > 1:
            palace_id = args[1]
            if manager.delete_palace(palace_id):
                return True
            self.print_error(f"Palace with ID {palace_id} not found.")
            return False

        if command == "status":
            index = manager.get_master_index()
            stats = index.get("global_stats", {})
            for _domain, _count in stats.get("domains", {}).items():
                pass
            return True

        self.print_warning(f"Manager command not supported: {' '.join(args)}")
        return False

    def export_palaces(self, destination: str, palaces_dir: str | None = None) -> None:
        """Export all palaces to a JSON file."""
        self.print_status(f"Exporting palaces to {destination}")
        try:
            manager = self._manager(palaces_dir)
            manager.export_state(destination)
        except Exception as e:
            self.print_error(f"Export failed: {e}")

    def import_palaces(
        self,
        source: str,
        keep_existing: bool = True,
        palaces_dir: str | None = None,
    ) -> None:
        """Import palaces from a JSON file."""
        self.print_status(f"Importing palaces from {source}")
        try:
            manager = self._manager(palaces_dir)
            manager.import_state(source, keep_existing=keep_existing)
        except Exception as e:
            self.print_error(f"Import failed: {e}")


def build_parser() -> argparse.ArgumentParser:
    """Construct and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Memory Palace Plugin CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s enable                 # Enable the plugin
  %(prog)s create 'Code Fortress' programming --metaphor fortress
  %(prog)s search 'Rust ownership'
  %(prog)s status                 # Show current status
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("enable", help="Enable the memory palace plugin")
    subparsers.add_parser("disable", help="Disable the memory palace plugin")
    subparsers.add_parser("status", help="Show plugin status and statistics")
    subparsers.add_parser("skills", help="List available skills")
    subparsers.add_parser("install", help="Install skills into Claude")

    garden_parser = subparsers.add_parser("garden", help="Digital garden utilities")
    garden_sub = garden_parser.add_subparsers(dest="garden_cmd", help="Garden commands")

    garden_metrics_parser = garden_sub.add_parser(
        "metrics", help="Compute digital garden metrics"
    )
    garden_metrics_parser.add_argument(
        "--path",
        help="Path to garden JSON (default: GARDEN_FILE or ./garden.json)",
    )
    garden_metrics_parser.add_argument(
        "--now",
        help="Override timestamp (ISO 8601) for reproducible runs",
    )
    garden_metrics_parser.add_argument(
        "--format",
        choices=["json", "brief", "prometheus"],
        default="json",
        help="Output format",
    )
    garden_metrics_parser.add_argument(
        "--label", help="Prometheus label (defaults to file stem)"
    )

    garden_tend_parser = garden_sub.add_parser(
        "tend",
        help="Report tending actions based on freshness cadence",
    )
    garden_tend_parser.add_argument(
        "--path",
        help="Path to garden JSON (default: GARDEN_FILE or ./garden.json)",
    )
    garden_tend_parser.add_argument("--now", help="Override timestamp (ISO 8601)")
    garden_tend_parser.add_argument(
        "--prune-days",
        type=int,
        default=2,
        help="Days since tend to flag for quick prune",
    )
    garden_tend_parser.add_argument(
        "--stale-days",
        type=int,
        default=7,
        help="Days since tend to flag as stale",
    )
    garden_tend_parser.add_argument(
        "--archive-days",
        type=int,
        default=30,
        help="Days since tend to flag for archive",
    )
    garden_tend_parser.add_argument(
        "--apply",
        action="store_true",
        help=(
            "Write back updates: set last_tended for pruned plots and "
            "move archived plots to compost"
        ),
    )
    garden_tend_parser.add_argument(
        "--archive-export",
        help="Path to write archived plots (JSON) when applying",
    )
    garden_tend_parser.add_argument(
        "--prometheus",
        action="store_true",
        help="Emit tending counts in Prometheus format",
    )
    garden_tend_parser.add_argument(
        "--label",
        help="Prometheus garden label (defaults to file stem)",
    )
    garden_tend_parser.add_argument(
        "--palaces",
        action="store_true",
        help="Also check palace health and report entries needing cleanup",
    )

    export_parser = subparsers.add_parser(
        "export", help="Export all palaces to a bundle"
    )
    export_parser.add_argument(
        "--destination", required=True, help="Destination JSON path"
    )
    export_parser.add_argument("--palaces-dir", help="Override palaces directory")

    import_parser = subparsers.add_parser("import", help="Import palaces from a bundle")
    import_parser.add_argument("--source", required=True, help="Source bundle JSON")
    import_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing palaces with same IDs",
    )
    import_parser.add_argument("--palaces-dir", help="Override palaces directory")

    create_parser = subparsers.add_parser("create", help="Create a new memory palace")
    create_parser.add_argument("name", help="Palace name")
    create_parser.add_argument("domain", help="Palace domain")
    create_parser.add_argument(
        "--metaphor", default="building", help="Architectural metaphor"
    )

    subparsers.add_parser("list", help="List all memory palaces")

    sync_parser = subparsers.add_parser("sync", help="Sync intake queue into palaces")
    sync_parser.add_argument(
        "--auto-create",
        action="store_true",
        help="Create new palaces for unmatched domains",
    )
    sync_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying",
    )

    prune_parser = subparsers.add_parser("prune", help="Check/apply palace cleanup")
    prune_parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply prune actions (requires prior check)",
    )
    prune_parser.add_argument(
        "--stale-days",
        type=int,
        default=90,
        help="Days before entry is considered stale (default: 90)",
    )

    search_parser = subparsers.add_parser("search", help="Search across all palaces")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument(
        "--type",
        default="semantic",
        choices=["semantic", "exact", "fuzzy"],
        help="Search type",
    )

    manager_parser = subparsers.add_parser(
        "manager", help="Run palace manager directly"
    )
    manager_parser.add_argument(
        "manager_args",
        nargs=argparse.REMAINDER,
        help="Arguments to pass to palace_manager.py",
    )

    return parser


def main() -> None:
    """CLI entrypoint."""
    cli = MemoryPalaceCLI()
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    def handle_garden() -> None:
        if args.garden_cmd == "metrics":
            cli.garden_metrics(args.path, args.now, args.format, args.label)
        elif args.garden_cmd == "tend":
            cli.garden_tend(
                TendingOptions(
                    path=args.path,
                    now=args.now,
                    prune_days=args.prune_days,
                    stale_days=args.stale_days,
                    archive_days=args.archive_days,
                    apply=args.apply,
                    archive_export=args.archive_export,
                    prometheus=args.prometheus,
                    label=args.label,
                ),
                include_palaces=getattr(args, "palaces", False),
            )
        else:
            parser.print_help()

    handlers = {
        "enable": lambda: cli.enable_plugin(),
        "disable": lambda: cli.disable_plugin(),
        "status": lambda: cli.show_status(),
        "skills": lambda: cli.list_skills(),
        "install": lambda: cli.install_skills(),
        "create": lambda: cli.create_palace(args.name, args.domain, args.metaphor),
        "list": lambda: cli.list_palaces(),
        "sync": lambda: cli.sync_queue(
            auto_create=getattr(args, "auto_create", False),
            dry_run=getattr(args, "dry_run", False),
        ),
        "prune": lambda: (
            cli.prune_apply(["stale", "low_quality"])
            if getattr(args, "apply", False)
            else cli.prune_check(stale_days=getattr(args, "stale_days", 90))
        ),
        "search": lambda: cli.search_palaces(args.query, args.type),
        "garden": handle_garden,
        "export": lambda: cli.export_palaces(args.destination, args.palaces_dir),
        "import": lambda: cli.import_palaces(
            args.source,
            keep_existing=not args.overwrite,
            palaces_dir=args.palaces_dir,
        ),
        "manager": lambda: cli.run_palace_manager(args.manager_args),
    }

    handler = handlers.get(args.command)
    if handler:
        handler()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
