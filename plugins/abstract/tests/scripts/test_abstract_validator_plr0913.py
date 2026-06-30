"""PLR0913 regression tests for abstract_validator.py.

The PLR0913 refactor wrapped the six keyword arguments to
format_validator_report() into a single ValidatorReport dataclass.
These tests assert that generate_report() constructs a ValidatorReport
with the correct metadata fields and that the formatted output
contains them.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from abstract_validator import AbstractValidator


class TestAbstractValidatorReportMetadata:
    """Feature: generate_report() passes metadata labels via ValidatorReport.

    As a plugin maintainer
    I want the generate_report() output to include all section labels
    So that downstream parsers can locate the Infrastructure and Skills data.
    """

    def test_generate_report_contains_infrastructure_provided_label(
        self,
        temp_skill_dir: Path,
        sample_skill_content: str,
    ) -> None:
        """Scenario: generate_report() includes the Infrastructure Provided label.

        Given a skill directory with one valid SKILL.md
        When generate_report() is called
        Then the returned string contains "Infrastructure Provided".
        And the string contains the "Skills with Patterns" label.
        """
        skill_dir = temp_skill_dir / "meta-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(sample_skill_content)

        validator = AbstractValidator(temp_skill_dir)
        report = validator.generate_report()

        assert "Infrastructure Provided" in report
        assert "Skills with Patterns" in report

    def test_generate_report_title_and_root_present(
        self,
        temp_skill_dir: Path,
        sample_skill_content: str,
    ) -> None:
        """Scenario: generate_report() includes canonical title and plugin root.

        Given a skill directory with one valid SKILL.md
        When generate_report() is called
        Then the report title "Abstract Plugin Infrastructure Report" is present.
        And the plugin root path appears in the output.
        """
        skill_dir = temp_skill_dir / "infra-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(sample_skill_content)

        validator = AbstractValidator(temp_skill_dir)
        report = validator.generate_report()

        assert "Abstract Plugin Infrastructure Report" in report
        assert str(temp_skill_dir) in report
