"""Shared test fixtures for egregore plugin."""

from __future__ import annotations

import json

import pytest


@pytest.fixture
def egregore_dir(tmp_path):
    """Create a temporary .egregore directory."""
    d = tmp_path / ".egregore"
    d.mkdir()
    return d


@pytest.fixture
def sample_manifest(egregore_dir):
    """Create a sample manifest with one active work item."""
    manifest = {
        "project_dir": str(egregore_dir.parent),
        "created_at": "2026-03-06T10:00:00+00:00",
        "session_count": 1,
        "continuation_count": 0,
        "work_items": [
            {
                "id": "wrk_001",
                "source": "prompt",
                "source_ref": "Build a REST API",
                "branch": "egregore/wrk-001-build-a-rest-api",
                "pipeline_stage": "build",
                "pipeline_step": "execute",
                "started_at": "2026-03-06T10:00:00+00:00",
                "decisions": [],
                "attempts": 0,
                "max_attempts": 3,
                "status": "active",
                "failure_reason": None,
            }
        ],
    }
    path = egregore_dir / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2))
    return path
