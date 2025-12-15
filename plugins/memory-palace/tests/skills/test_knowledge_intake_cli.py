"""Tests for knowledge intake CLI automation."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

INTAKE_CLI_PATH = (
    Path(__file__).resolve().parents[2]
    / "skills"
    / "knowledge-intake"
    / "scripts"
    / "intake_cli.py"
)


def load_cli_module():
    """Dynamically load the intake CLI module for testing."""
    spec = importlib.util.spec_from_file_location("intake_cli", INTAKE_CLI_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def _write_candidate(
    tmp_path: Path, *, title: str = "Cache Intercept Design Notes"
) -> Path:
    candidate = {
        "source": {"type": "web_fetch", "identifier": "https://example.com/cache"},
        "summary": {
            "title": title,
            "tags": ["cache", "governance", "audit"],
            "palace": "Knowledge Brain",
            "district": "Cache Layer",
        },
        "content": "Documenting how cache interception should behave for memory-palace queries.",
        "evaluation": {"autonomy_level": 0},
    }
    candidate_path = tmp_path / "candidate.json"
    candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
    return candidate_path


def test_process_candidate_generates_outputs(tmp_path: Path) -> None:
    """Ensure processing a candidate writes expected files and summary."""
    candidate_path = _write_candidate(tmp_path)
    intake_cli = load_cli_module()
    corpus_dir = intake_cli.PLUGIN_ROOT / "docs" / "knowledge-corpus"
    index_dir = intake_cli.PLUGIN_ROOT / "data" / "indexes"
    curation_log = tmp_path / "curation-log.md"

    summary = intake_cli.process_candidate(
        candidate_path=candidate_path,
        corpus_dir=corpus_dir,
        index_dir=index_dir,
        output_root=tmp_path,
        curation_log=curation_log,
        auto_accept=True,
    )

    assert summary["status"] == "applied"
    palace_entry = Path(summary["palace_entry"])
    developer_doc = Path(summary["developer_doc"])
    assert palace_entry.exists()
    assert developer_doc.exists()
    log_text = curation_log.read_text(encoding="utf-8")
    assert "Cache Intercept Design Notes" in log_text


def test_dual_output_prompt_pack(tmp_path: Path) -> None:
    """Verify dual-output prompt pack generation succeeds."""
    intake_cli = load_cli_module()
    candidate_path = _write_candidate(tmp_path, title="Garden Cache Audit")

    summary = intake_cli.process_candidate(
        candidate_path=candidate_path,
        corpus_dir=intake_cli.PLUGIN_ROOT / "docs" / "knowledge-corpus",
        index_dir=intake_cli.PLUGIN_ROOT / "data" / "indexes",
        output_root=tmp_path,
        curation_log=tmp_path / "curation-log.md",
        auto_accept=True,
        dual_output=True,
        prompt_pack="marginal-value-dual",
    )

    prompt_path = tmp_path / "docs" / "prompts" / "marginal-value-dual.md"
    assert prompt_path.exists()
    assert summary["prompt_pack"] == "marginal-value-dual"
