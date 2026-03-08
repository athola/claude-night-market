"""Tests for seed_corpus.py topic loading and data structures.

Feature: Knowledge corpus seeding from YAML topic data

As a corpus maintainer
I want seed_corpus.py to load topics from YAML and generate entries
So that the cache interceptor has a rich knowledge base.

Note: generate_entries() is currently a stub pending full migration.
Tests verify the data loading pipeline and stubs' behavior.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "seed_corpus.py"


def _load_seed_module():
    """Load seed_corpus.py as a module for testing."""
    spec = importlib.util.spec_from_file_location("seed_corpus", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules["seed_corpus"] = module
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


@pytest.fixture
def seed_module():
    """Load and return the seed_corpus module."""
    return _load_seed_module()


class TestVariationDataclass:
    """Feature: Variation holds concrete knowledge entry metadata."""

    def test_variation_fields(self, seed_module) -> None:
        """Given all fields, Variation stores them correctly."""
        v = seed_module.Variation(
            slug="test-slug",
            title="Test Title",
            language="python",
            focus="testing",
            keywords=["unit", "pytest"],
            summary="A test variation",
            playbook_steps=["step1", "step2"],
        )
        assert v.slug == "test-slug"
        assert v.title == "Test Title"
        assert v.language == "python"
        assert v.focus == "testing"
        assert v.keywords == ["unit", "pytest"]
        assert v.summary == "A test variation"
        assert len(v.playbook_steps) == 2


class TestTopicDataclass:
    """Feature: Topic groups multiple variations for seeding."""

    def test_topic_fields(self, seed_module) -> None:
        """Given all fields, Topic stores them correctly."""
        t = seed_module.Topic(
            slug="topic-1",
            title="Topic One",
            palace="Learning",
            district="Methods",
            tags=["learning", "practice"],
            base_keywords=["study", "review"],
            variations=[],
        )
        assert t.slug == "topic-1"
        assert t.title == "Topic One"
        assert t.palace == "Learning"
        assert t.district == "Methods"
        assert t.tags == ["learning", "practice"]
        assert len(t.base_keywords) == 2
        assert t.variations == []

    def test_topic_from_dict(self, seed_module) -> None:
        """Given a dict with variations, from_dict creates Topic."""
        data = {
            "slug": "async-patterns",
            "title": "Async Patterns",
            "palace": "Programming",
            "district": "Concurrency",
            "tags": ["async", "python"],
            "base_keywords": ["async", "await"],
            "variations": [
                {
                    "slug": "v1",
                    "title": "Basic Async",
                    "language": "python",
                    "focus": "intro",
                    "keywords": ["asyncio"],
                    "summary": "Intro to async",
                    "playbook_steps": ["import asyncio"],
                },
            ],
        }
        topic = seed_module.Topic.from_dict(data)
        assert topic.slug == "async-patterns"
        assert len(topic.variations) == 1
        assert topic.variations[0].slug == "v1"
        assert topic.variations[0].language == "python"

    def test_topic_from_dict_no_variations(self, seed_module) -> None:
        """Given a dict without variations key, creates Topic with empty list."""
        data = {
            "slug": "bare",
            "title": "Bare Topic",
            "palace": "P",
            "district": "D",
            "tags": [],
            "base_keywords": [],
        }
        topic = seed_module.Topic.from_dict(data)
        assert topic.variations == []


class TestLoadTopics:
    """Feature: load_topics reads from YAML file."""

    def test_load_topics_missing_file_raises(
        self, seed_module, tmp_path: Path
    ) -> None:
        """Given missing YAML file, load_topics raises FileNotFoundError."""
        with patch.object(
            seed_module,
            "SEED_TOPICS_FILE",
            tmp_path / "nonexistent.yaml",
        ):
            with pytest.raises(FileNotFoundError) as exc_info:
                seed_module.load_topics()
            assert "Seed topics file not found" in str(exc_info.value)

    def test_load_topics_from_yaml(
        self, seed_module, tmp_path: Path
    ) -> None:
        """Given valid YAML, load_topics returns list of Topic objects."""
        yaml_content = """
topics:
  - slug: test-topic
    title: Test Topic
    palace: Testing
    district: Unit
    tags: [test]
    base_keywords: [testing]
    variations:
      - slug: v1
        title: Var 1
        language: python
        focus: testing
        keywords: [pytest]
        summary: Test variation
        playbook_steps: [step1]
"""
        yaml_file = tmp_path / "topics.yaml"
        yaml_file.write_text(yaml_content, encoding="utf-8")

        with patch.object(seed_module, "SEED_TOPICS_FILE", yaml_file):
            topics = seed_module.load_topics()

        assert len(topics) == 1
        assert topics[0].slug == "test-topic"
        assert len(topics[0].variations) == 1

    def test_load_topics_empty_yaml(
        self, seed_module, tmp_path: Path
    ) -> None:
        """Given YAML with no topics, returns empty list."""
        yaml_file = tmp_path / "empty.yaml"
        yaml_file.write_text("topics: []\n", encoding="utf-8")

        with patch.object(seed_module, "SEED_TOPICS_FILE", yaml_file):
            topics = seed_module.load_topics()

        assert topics == []


class TestGenerateEntries:
    """Feature: generate_entries is a stub that returns empty list."""

    def test_generate_entries_returns_list(
        self, seed_module, tmp_path: Path
    ) -> None:
        """Given valid topics YAML, generate_entries returns a list.

        Note: generate_entries is a stub; it calls load_topics()
        but returns an empty list pending full implementation.
        """
        yaml_file = tmp_path / "topics.yaml"
        yaml_file.write_text(
            "topics:\n  - slug: t\n    title: T\n"
            "    palace: P\n    district: D\n"
            "    tags: []\n    base_keywords: []\n",
            encoding="utf-8",
        )

        with patch.object(seed_module, "SEED_TOPICS_FILE", yaml_file):
            entries = seed_module.generate_entries()

        assert isinstance(entries, list)


class TestStubFunctions:
    """Feature: Stub functions raise NotImplementedError."""

    @pytest.mark.parametrize(
        "func_name",
        [
            "seed_cache_catalog",
            "write_markdown",
            "update_keyword_index",
            "update_query_templates",
        ],
        ids=[
            "seed_cache_catalog",
            "write_markdown",
            "update_keyword_index",
            "update_query_templates",
        ],
    )
    def test_stub_raises_not_implemented(
        self, seed_module, func_name: str
    ) -> None:
        """Given a stub function, calling it raises NotImplementedError."""
        func = getattr(seed_module, func_name)
        with pytest.raises(NotImplementedError) as exc_info:
            if func_name == "write_markdown":
                func({})
            else:
                func([])
        assert "deferred" in str(exc_info.value).lower()
