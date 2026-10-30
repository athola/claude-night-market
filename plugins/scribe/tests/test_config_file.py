"""Contract tests for the slop-detector config-file module (Issue #136).

`.slop-config.yaml` handling the model performs is specified by
`skills/slop-detector/modules/config-file.md`. The two fields the CI
scorer reads (`allowlist`, `exclude_patterns`) are exercised against
`scripts/slop_score.py` in `tests/unit/test_slop_score.py`. These tests
pin the rest of the documented schema, defaults, and loading rules.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

CONFIG_MODULE = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "slop-detector"
    / "modules"
    / "config-file.md"
)


@pytest.fixture(scope="module")
def config_text() -> str:
    return CONFIG_MODULE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def schema(config_text: str) -> dict[str, Any]:
    block = re.search(r"```yaml\n(.*?)\n```", config_text, re.DOTALL)
    assert block, "config-file.md has no ```yaml schema example"
    return yaml.safe_load(block.group(1))


@pytest.fixture(scope="module")
def defaults(config_text: str) -> dict[str, str]:
    rows = re.findall(
        r"^\| `([\w.]+)` \| [^|]+ \| (`[^`]*`|none) \|", config_text, re.MULTILINE
    )
    return {field: default.strip("`") for field, default in rows}


@pytest.mark.unit
class TestSchemaExample:
    def test_example_declares_every_documented_top_level_field(
        self, schema: dict[str, Any]
    ) -> None:
        assert set(schema) == {
            "custom_words",
            "allowlist",
            "spelling",
            "thresholds",
            "exclude_patterns",
            "extends",
        }

    def test_example_custom_words_split_into_two_tiers(
        self, schema: dict[str, Any]
    ) -> None:
        assert set(schema["custom_words"]) == {"tier1", "tier2"}

    def test_example_thresholds_put_warn_below_error(
        self, schema: dict[str, Any]
    ) -> None:
        assert schema["thresholds"]["warn"] < schema["thresholds"]["error"]

    def test_example_spelling_mode_is_one_of_the_documented_modes(
        self, schema: dict[str, Any], config_text: str
    ) -> None:
        modes = {"american", "british", "off"}
        assert schema["spelling"] in modes
        assert all(f"`{mode}`" in config_text for mode in modes)


@pytest.mark.unit
class TestFieldReferenceDefaults:
    def test_every_schema_field_has_a_reference_row(
        self, schema: dict[str, Any], defaults: dict[str, str]
    ) -> None:
        top_level = {name.split(".")[0] for name in defaults}
        assert top_level == set(schema)

    def test_threshold_defaults_are_warn_two_and_error_five(
        self, defaults: dict[str, str]
    ) -> None:
        assert (defaults["thresholds.warn"], defaults["thresholds.error"]) == (
            "2.0",
            "5.0",
        )

    def test_list_fields_default_to_empty(self, defaults: dict[str, str]) -> None:
        empty = ["custom_words.tier1", "custom_words.tier2", "allowlist"]
        empty.append("exclude_patterns")
        assert [defaults[name] for name in empty] == ["[]"] * 4

    def test_spelling_defaults_to_american(self, defaults: dict[str, str]) -> None:
        assert defaults["spelling"] == "american"


@pytest.mark.unit
class TestLoadingRules:
    def test_discovery_stops_at_the_first_config_found(self, config_text: str) -> None:
        assert "Stop at the first `.slop-config.yaml` found" in config_text

    def test_allowlist_matching_is_case_insensitive_and_per_match(
        self, config_text: str
    ) -> None:
        assert "case-insensitive and applied per-match" in config_text

    def test_custom_words_extend_the_builtin_lists(self, config_text: str) -> None:
        assert "Append `custom_words.tier1` to the built-in TIER1" in config_text
        assert "Append `custom_words.tier2` to the built-in TIER2" in config_text

    def test_exclude_patterns_use_fnmatch(self, config_text: str) -> None:
        assert "using `fnmatch`" in config_text

    def test_audit_mode_still_reads_excluded_files(self, config_text: str) -> None:
        assert "`--audit` mode reads an excluded file anyway" in config_text
