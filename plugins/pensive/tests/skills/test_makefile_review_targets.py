"""Variable assignments and special targets were parsed as targets (PEN-6)."""

from __future__ import annotations

from unittest.mock import MagicMock

from pensive.skills.makefile_review import MakefileReviewSkill


def _context(content: str) -> MagicMock:
    context = MagicMock()
    context.get_file_content.return_value = content
    return context


def test_variable_assignment_is_not_a_target() -> None:
    content = "CC := gcc\nOUT ::= bin\n.PHONY: build\nall:\n\ttrue\nbuild:\n\ttrue\n"
    report = MakefileReviewSkill().analyze_makefile_structure(_context(content))
    assert report["missing_phony"] == ["all"]


def test_mutual_dependency_reported_once() -> None:
    content = "a: b\n\ttrue\nb: a\n\ttrue\n"
    report = MakefileReviewSkill().analyze_dependencies(_context(content))
    assert len(report["circular_dependencies"]) == 1


def test_main_target_in_a_python_makefile_is_not_missing_sources() -> None:
    """`main:` was held to a main.c rule in any Makefile (PEN-6)."""
    content = "main: build\n\tuv run python -m app\nbuild:\n\tuv sync\n"
    report = MakefileReviewSkill().analyze_dependencies(_context(content))
    assert not any("main target" in m for m in report["missing_dependencies"])


def test_main_target_without_main_c_is_flagged_in_a_c_makefile() -> None:
    content = "main: util.o\n\tgcc -o main util.o\nutil.o: util.c\n\tgcc -c util.c\n"
    report = MakefileReviewSkill().analyze_dependencies(_context(content))
    assert any("main target" in m for m in report["missing_dependencies"])


def test_tool_names_inside_words_are_not_commands() -> None:
    """`performing` matched `rm` as a substring (PEN-6)."""
    content = ".PHONY: a\na:\n\t@echo performing a comparison\n"
    report = MakefileReviewSkill().analyze_makefile_structure(_context(content))
    assert report["error_handling"] == []
