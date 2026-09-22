"""Configuration's accessors answer for malformed config, not just good config.

`Configuration` reads a YAML file a user wrote by hand, so every accessor
already carries an `isinstance` guard against the shape that file can
take. Nothing exercised those guards: the file's covered half was the
happy path, and the branch that runs when someone writes `skills: all`
instead of a list was never taken in a test. That branch is the whole
reason the guards exist.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from pensive.config.configuration import Configuration
from pensive.exceptions import ConfigurationError

if TYPE_CHECKING:
    from pathlib import Path

#: Values a hand-edited YAML file puts where a mapping was expected.
NOT_A_MAPPING: list[Any] = ["a string", ["a", "list"], 42, True]

#: Values a hand-edited YAML file puts where a sequence was expected.
NOT_A_SEQUENCE: list[Any] = ["a string", {"a": "mapping"}, 7]


class TestEnabledSkills:
    """The skills list, and what it answers for malformed input."""

    @pytest.mark.unit
    def test_a_missing_pensive_section_yields_no_skills(self) -> None:
        """GIVEN a config with no pensive section.

        WHEN the enabled skills are read
        THEN the list is empty
        """
        assert Configuration({}).enabled_skills == []

    @pytest.mark.unit
    @pytest.mark.parametrize("value", NOT_A_MAPPING)
    def test_a_pensive_section_that_is_not_a_mapping_yields_no_skills(
        self, value: Any
    ) -> None:
        """GIVEN a pensive key holding something other than a mapping.

        WHEN the enabled skills are read
        THEN the list is empty rather than raising AttributeError

        This is the branch that runs when someone writes `pensive: true`.
        """
        assert Configuration({"pensive": value}).enabled_skills == []

    @pytest.mark.unit
    @pytest.mark.parametrize("value", NOT_A_SEQUENCE)
    def test_a_skills_key_that_is_not_a_list_yields_no_skills(self, value: Any) -> None:
        """GIVEN a skills key holding something other than a list.

        WHEN the enabled skills are read
        THEN the list is empty

        `skills: all` parses as a string, and a string is iterable, so
        without this guard the caller would receive one skill per
        character.
        """
        assert Configuration({"pensive": {"skills": value}}).enabled_skills == []

    @pytest.mark.unit
    def test_non_string_entries_are_dropped_and_string_entries_kept(self) -> None:
        """GIVEN a skills list mixing strings with other scalars.

        WHEN the enabled skills are read
        THEN only the strings survive, in order
        """
        config = Configuration(
            {"pensive": {"skills": ["review", 3, None, "harden", {"x": 1}]}}
        )

        assert config.enabled_skills == ["review", "harden"]


class TestExcludePatterns:
    """The exclude globs, and what they answer for malformed input."""

    @pytest.mark.unit
    @pytest.mark.parametrize("value", NOT_A_MAPPING)
    def test_a_pensive_section_that_is_not_a_mapping_excludes_nothing(
        self, value: Any
    ) -> None:
        """GIVEN a pensive key holding something other than a mapping.

        WHEN the exclude patterns are read
        THEN the list is empty
        """
        assert Configuration({"pensive": value}).exclude_patterns == []

    @pytest.mark.unit
    @pytest.mark.parametrize("value", NOT_A_SEQUENCE)
    def test_an_exclude_key_that_is_not_a_list_excludes_nothing(
        self, value: Any
    ) -> None:
        """GIVEN an exclude key holding something other than a list.

        WHEN the exclude patterns are read
        THEN the list is empty

        Failing open is the safe direction here: excluding nothing
        analyzes too much, where iterating a string would exclude a
        pattern per character and analyze almost nothing.
        """
        assert Configuration({"pensive": {"exclude": value}}).exclude_patterns == []

    @pytest.mark.unit
    def test_non_string_entries_are_dropped(self) -> None:
        """GIVEN an exclude list mixing globs with other scalars.

        WHEN the exclude patterns are read
        THEN only the strings survive
        """
        config = Configuration({"pensive": {"exclude": ["*.pyc", 0, "build/"]}})

        assert config.exclude_patterns == ["*.pyc", "build/"]


class TestThresholds:
    """The thresholds mapping, and what it answers for malformed input."""

    @pytest.mark.unit
    @pytest.mark.parametrize("value", NOT_A_MAPPING)
    def test_a_pensive_section_that_is_not_a_mapping_yields_no_thresholds(
        self, value: Any
    ) -> None:
        """GIVEN a pensive key holding something other than a mapping.

        WHEN the thresholds are read
        THEN the mapping is empty
        """
        assert Configuration({"pensive": value}).thresholds == {}

    @pytest.mark.unit
    @pytest.mark.parametrize("value", NOT_A_MAPPING)
    def test_a_thresholds_key_that_is_not_a_mapping_yields_no_thresholds(
        self, value: Any
    ) -> None:
        """GIVEN a thresholds key holding something other than a mapping.

        WHEN the thresholds are read
        THEN the mapping is empty
        """
        assert Configuration({"pensive": {"thresholds": value}}).thresholds == {}

    @pytest.mark.unit
    def test_a_thresholds_mapping_is_returned_as_written(self) -> None:
        """GIVEN a thresholds mapping.

        WHEN the thresholds are read
        THEN the mapping comes back with its values unconverted

        The accessor does not coerce, so a threshold written as a
        string reaches the caller as a string.
        """
        config = Configuration({"pensive": {"thresholds": {"coverage": "80"}}})

        assert config.thresholds == {"coverage": "80"}


class TestCustomRules:
    """The custom rules list, which is read from the top level."""

    @pytest.mark.unit
    @pytest.mark.parametrize("value", NOT_A_SEQUENCE)
    def test_a_custom_rules_key_that_is_not_a_list_yields_no_rules(
        self, value: Any
    ) -> None:
        """GIVEN a custom_rules key holding something other than a list.

        WHEN the custom rules are read
        THEN the list is empty
        """
        assert Configuration({"custom_rules": value}).custom_rules == []

    @pytest.mark.unit
    def test_entries_that_are_not_mappings_are_dropped(self) -> None:
        """GIVEN a custom_rules list mixing rule mappings with scalars.

        WHEN the custom rules are read
        THEN only the mappings survive

        Every consumer subscripts a rule, so a bare string in the list
        would reach them as a TypeError far from the config file that
        caused it.
        """
        rule = {"id": "R1", "pattern": "x"}
        config = Configuration({"custom_rules": [rule, "not-a-rule", None]})

        assert config.custom_rules == [rule]

    @pytest.mark.unit
    def test_custom_rules_are_not_read_from_the_pensive_section(self) -> None:
        """GIVEN custom_rules nested under pensive rather than at the top.

        WHEN the custom rules are read
        THEN the list is empty

        Recording where the key lives: the other three accessors read
        from `pensive`, and this one does not.
        """
        config = Configuration({"pensive": {"custom_rules": [{"id": "R1"}]}})

        assert config.custom_rules == []


class TestFromFile:
    """Loading from disk, including the shapes YAML can return."""

    @pytest.mark.unit
    def test_a_missing_file_names_the_path_it_looked_for(self, tmp_path: Path) -> None:
        """GIVEN a path that does not exist.

        WHEN the configuration is loaded
        THEN ConfigurationError is raised naming that path
        """
        absent = tmp_path / "pensive.yaml"

        with pytest.raises(ConfigurationError, match=str(absent)):
            Configuration.from_file(absent)

    @pytest.mark.unit
    def test_a_path_given_as_a_string_is_accepted(self, tmp_path: Path) -> None:
        """GIVEN a path passed as a str rather than a Path.

        WHEN the configuration is loaded
        THEN it parses, because from_file converts before using it
        """
        config_file = tmp_path / "pensive.yaml"
        config_file.write_text("pensive:\n  skills:\n    - review\n")

        config = Configuration.from_file(str(config_file))

        assert config.enabled_skills == ["review"]

    @pytest.mark.unit
    def test_an_empty_file_loads_as_an_empty_configuration(
        self, tmp_path: Path
    ) -> None:
        """GIVEN a file holding nothing.

        WHEN the configuration is loaded
        THEN it is empty rather than None

        `yaml.safe_load` returns None for an empty document, and the
        accessors would all raise on that.
        """
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")

        config = Configuration.from_file(config_file)

        assert config.enabled_skills == []
        assert config.thresholds == {}

    @pytest.mark.unit
    def test_a_document_that_is_not_a_mapping_loads_as_empty(
        self, tmp_path: Path
    ) -> None:
        """GIVEN a file whose top level is a list.

        WHEN the configuration is loaded
        THEN it is empty rather than carrying the list
        """
        config_file = tmp_path / "list.yaml"
        config_file.write_text("- one\n- two\n")

        assert Configuration.from_file(config_file).get("anything") is None

    @pytest.mark.unit
    def test_broken_yaml_is_reported_as_a_syntax_error(self, tmp_path: Path) -> None:
        """GIVEN a file that is not valid YAML.

        WHEN the configuration is loaded
        THEN ConfigurationError is raised, chained to the YAML error

        The chain is what lets an operator see the line number, which
        the wrapping message does not carry.
        """
        config_file = tmp_path / "broken.yaml"
        config_file.write_text("pensive:\n  skills: [unclosed\n")

        with pytest.raises(ConfigurationError, match="YAML syntax error") as caught:
            Configuration.from_file(config_file)

        assert caught.value.__cause__ is not None


class TestMerge:
    """Merging two configurations, one level deep."""

    @pytest.mark.unit
    def test_a_key_only_the_other_has_is_added(self) -> None:
        """GIVEN two configurations with disjoint keys.

        WHEN they are merged
        THEN the result carries both
        """
        merged = Configuration({"a": 1}).merge(Configuration({"b": 2}))

        assert merged.get("a") == 1
        assert merged.get("b") == 2

    @pytest.mark.unit
    def test_a_scalar_key_is_overwritten_by_the_other(self) -> None:
        """GIVEN both configurations setting the same scalar key.

        WHEN they are merged
        THEN the other configuration wins
        """
        merged = Configuration({"a": 1}).merge(Configuration({"a": 2}))

        assert merged.get("a") == 2

    @pytest.mark.unit
    def test_two_mappings_under_one_key_are_merged_not_replaced(self) -> None:
        """GIVEN both configurations holding a mapping under one key.

        WHEN they are merged
        THEN keys from each survive and the other's value wins a clash

        Replacing outright is the tempting implementation and would
        silently drop a project's thresholds when a local override set
        only one of them.
        """
        base = Configuration({"pensive": {"skills": ["review"], "exclude": ["*.pyc"]}})
        override = Configuration({"pensive": {"skills": ["harden"]}})

        merged = base.merge(override)

        assert merged.get("pensive") == {
            "skills": ["harden"],
            "exclude": ["*.pyc"],
        }

    @pytest.mark.unit
    def test_neither_input_is_mutated_by_a_merge(self) -> None:
        """GIVEN two configurations.

        WHEN they are merged
        THEN both inputs still read as they did before

        merge() returns a new Configuration, so a caller merging a
        local override into a shared base must not corrupt the base.
        """
        base = Configuration({"pensive": {"skills": ["review"]}})
        override = Configuration({"pensive": {"skills": ["harden"]}})

        base.merge(override)

        assert base.enabled_skills == ["review"]
        assert override.enabled_skills == ["harden"]

    @pytest.mark.unit
    def test_a_mapping_is_replaced_when_the_base_value_is_a_scalar(self) -> None:
        """GIVEN a base holding a scalar where the other holds a mapping.

        WHEN they are merged
        THEN the mapping replaces the scalar

        The merge branch keys off the *base* value's type, so this is
        the else arm, and it is the asymmetry worth recording.
        """
        merged = Configuration({"pensive": 1}).merge(
            Configuration({"pensive": {"skills": ["review"]}})
        )

        assert merged.enabled_skills == ["review"]


class TestGetAndSet:
    """The untyped escape hatch."""

    @pytest.mark.unit
    def test_get_returns_the_default_for_an_absent_key(self) -> None:
        """GIVEN a configuration without the key.

        WHEN it is read with a default
        THEN the default comes back
        """
        assert Configuration({}).get("missing", "fallback") == "fallback"

    @pytest.mark.unit
    def test_set_is_visible_to_the_typed_accessors(self) -> None:
        """GIVEN a configuration built empty.

        WHEN the pensive section is set directly
        THEN the typed accessors read through to it

        set() and the properties share one dict; a copy would make this
        assignment invisible.
        """
        config = Configuration()
        config.set("pensive", {"skills": ["review"]})

        assert config.enabled_skills == ["review"]
