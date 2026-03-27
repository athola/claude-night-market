"""Tests for memory_palace_cli.py MemoryPalaceCLI class and CLI parser.

This module has been split into focused sub-modules for maintainability:

- test_memory_palace_cli_core.py    -- TendingOptions/TendingContext,
                                       CLI construction, print helpers,
                                       is_enabled/enable/disable/show_status
- test_memory_palace_cli_garden.py  -- garden_metrics(), garden_tend(),
                                       _compute_tending_actions()
- test_memory_palace_cli_palaces.py -- list/create/search/sync palaces,
                                       prune check/apply, install skills,
                                       run_palace_manager, export/import,
                                       _palaces_dir, duplicate reporting
- test_memory_palace_cli_parser.py  -- build_parser(), main() dispatch

Shared helpers (_default_tending_opts, _garden_data_with_plots) live in
conftest.py in this directory.

All tests remain discoverable by pytest via the sub-modules above.
This file is retained for git blame continuity.
"""
