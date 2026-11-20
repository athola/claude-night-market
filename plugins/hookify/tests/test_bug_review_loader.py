"""Regression tests for malformed rule files that crashed the loader."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config_loader import ConfigLoader  # noqa: E402 - path injected above

GOOD_RULE = """---
name: good-rule
enabled: true
event: bash
pattern: rm
---
msg
"""


def _write(directory: Path, name: str, text: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"hookify.{name}.local.md").write_text(text)


@pytest.mark.parametrize(
    "conditions",
    [
        "conditions:\n  - field: command\n    operator: contains\n",
        "conditions:\n",
        "conditions: nope\n",
    ],
)
def test_malformed_conditions_skip_only_that_rule(
    tmp_path: Path, conditions: str
) -> None:
    """One bad rule must not stop the rest from loading."""
    _write(tmp_path, "good", GOOD_RULE)
    _write(
        tmp_path,
        "bad",
        f"---\nname: bad\nenabled: true\nevent: bash\n{conditions}---\nmsg\n",
    )
    loader = ConfigLoader(user_rules_dir=tmp_path, include_bundled=False)

    rules = loader.load_all_rules()

    assert [r.name for r in rules] == ["good-rule"]
    assert len(loader.load_errors) == 1


@pytest.mark.parametrize(
    "bad_fields",
    [
        "event: bash\npattern: 777\n",
        "event: bash\npattern: yes\n",
        "event: [bash]\npattern: rm\n",
        "event: bash\naction: [block]\npattern: rm\n",
        "event: bash\nconditions:\n  - field: command\n"
        "    operator: contains\n    pattern: 777\n",
    ],
)
def test_rule_with_non_string_field_is_skipped_and_other_rules_still_load(
    tmp_path: Path, bad_fields: str
) -> None:
    """A TypeError from one rule used to abort loading every rule."""
    _write(tmp_path, "good", GOOD_RULE)
    _write(tmp_path, "bad", f"---\nname: bad\nenabled: true\n{bad_fields}---\nmsg\n")
    loader = ConfigLoader(user_rules_dir=tmp_path, include_bundled=False)

    rules = loader.load_all_rules()

    assert [r.name for r in rules] == ["good-rule"]
    assert len(loader.load_errors) == 1
    assert "hookify.bad.local.md" in loader.load_errors[0]


@pytest.mark.parametrize("enabled", ["0", '"false"', '"no"', "1"])
@pytest.mark.parametrize("force_stdlib_parser", [False, True])
def test_enabled_must_be_a_boolean(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    enabled: str,
    force_stdlib_parser: bool,
) -> None:
    """A truthy non-bool `enabled` kept a rule the user meant to disable."""
    if force_stdlib_parser:
        monkeypatch.setattr("core.config_loader.yaml", None)
    _write(
        tmp_path,
        "off",
        f"---\nname: off\nenabled: {enabled}\nevent: bash\npattern: rm\n---\nmsg\n",
    )
    loader = ConfigLoader(user_rules_dir=tmp_path, include_bundled=False)

    assert loader.load_all_rules() == []
    assert "enabled" in loader.load_errors[0]


@pytest.mark.parametrize("missing", ["name", "enabled", "event"])
def test_rule_missing_a_required_key_is_skipped(tmp_path: Path, missing: str) -> None:
    """A KeyError escaped the loader the same way the TypeError did."""
    fields = {
        "name": "name: bad\n",
        "enabled": "enabled: true\n",
        "event": "event: bash\n",
    }
    del fields[missing]
    _write(tmp_path, "good", GOOD_RULE)
    _write(
        tmp_path, "bad", "---\n" + "".join(fields.values()) + "pattern: rm\n---\nm\n"
    )
    loader = ConfigLoader(user_rules_dir=tmp_path, include_bundled=False)

    assert [r.name for r in loader.load_all_rules()] == ["good-rule"]
    assert missing in loader.load_errors[0]
