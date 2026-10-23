"""Regression tests for API-review findings in abstract."""

from __future__ import annotations

import pytest
from abstract.errors import ErrorHandler
from abstract.frontmatter import FrontmatterProcessor
from abstract.improvement_queue import ImprovementQueue
from abstract.paths import get_config_dir
from abstract.skill_versioning import SkillVersionManager
from abstract.wrapper_base import _extract_public_symbols
from pathlib import Path
import ast
import logging
import subprocess
import sys

from abstract.config import AbstractConfig, Environment


@pytest.mark.parametrize("fmt", ["yaml", "json"])
def test_config_file_round_trips_with_environment_enum(tmp_path, fmt) -> None:
    path = tmp_path / f"c.{fmt}"
    original = AbstractConfig(environment=Environment.DEVELOPMENT)
    original.to_file(path, fmt=fmt)
    loaded = AbstractConfig.from_file(path)
    assert loaded.environment is Environment.DEVELOPMENT
    assert loaded.get_summary()
    assert loaded.skills_eval.OPTIMAL_TOKEN_RANGE == (800, 2000)


def test_config_from_file_accepts_empty_yaml(tmp_path) -> None:
    path = tmp_path / "empty.yaml"
    path.write_text("", encoding="utf-8")
    assert AbstractConfig.from_file(path).environment is AbstractConfig().environment


def test_frontmatter_parse_reports_non_mapping_block_as_invalid() -> None:

    result = FrontmatterProcessor.parse("---\n- name\n- description\n---\nbody")
    assert not result.is_valid
    assert result.parse_error is not None
    assert result.parsed == {}


def test_frontmatter_parse_accepts_crlf_line_endings() -> None:

    result = FrontmatterProcessor.parse(
        "---\r\nname: a\r\ndescription: b\r\n---\r\nbody"
    )
    assert result.is_valid, result.parse_error
    assert result.parsed == {"name": "a", "description": "b"}


def test_frontmatter_closing_fence_must_be_a_full_line() -> None:

    content = "---\nname: a\ndescription: b\n----\nbody\n"
    assert not FrontmatterProcessor.has_frontmatter(content)
    result = FrontmatterProcessor.parse(content)
    assert result.parse_error is not None
    assert "closing" in result.parse_error


def test_importing_tokens_does_not_leave_leyline_on_sys_path() -> None:

    src = Path(__file__).resolve().parents[1] / "src"
    code = (
        f"import sys; sys.path.insert(0, {str(src)!r}); before = list(sys.path); "
        "import abstract.tokens; "
        "assert sys.path == before, sys.path[:3]"
    )
    done = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=False
    )
    assert done.returncode == 0, done.stderr


def test_error_handler_does_not_duplicate_handlers_for_same_tool() -> None:

    name = "api-review-dup-handler"
    logger = logging.getLogger(name)
    try:
        ErrorHandler(name)
        ErrorHandler(name)
        assert len(logger.handlers) == 1
    finally:
        for handler in list(logger.handlers):
            logger.removeHandler(handler)
            handler.close()


def test_bump_version_raises_when_write_fails(tmp_path, monkeypatch) -> None:

    skill = tmp_path / "SKILL.md"
    skill.write_text("---\nname: x\n---\nbody\n", encoding="utf-8")
    manager = SkillVersionManager(skill)

    def _deny(*args, **kwargs):
        raise PermissionError("read-only")

    monkeypatch.setattr(type(skill), "write_text", _deny)
    with pytest.raises(OSError):
        manager.bump_version("change", {})


def test_skill_version_manager_raises_when_skill_file_unreadable(tmp_path) -> None:

    with pytest.raises(OSError):
        SkillVersionManager(tmp_path / "missing" / "SKILL.md")


@pytest.mark.parametrize("corrupt", ['{"skills": {"a": ', "[1, 2]"])
def test_improvement_queue_keeps_corrupt_file_aside(tmp_path, corrupt) -> None:

    queue_file = tmp_path / "q.json"
    queue_file.write_text(corrupt, encoding="utf-8")
    queue = ImprovementQueue(queue_file)
    queue.flag_skill("b", 0.1, "e1")
    (backup,) = tmp_path.glob("q.json.corrupt-*")
    assert backup.read_text(encoding="utf-8") == corrupt


def test_discussions_config_dir_honors_claude_home(tmp_path, monkeypatch) -> None:

    monkeypatch.setenv("CLAUDE_HOME", str(tmp_path))
    assert get_config_dir() == tmp_path / "skills" / "discussions"


def test_breaking_change_detection_sees_async_and_posonly_params() -> None:

    tree = ast.parse("async def go(a, /, b): ...\n")
    symbols = _extract_public_symbols(tree)
    assert symbols["go"]["params"] == ["a", "b"]
