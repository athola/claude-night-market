# ruff: noqa: D101,D102,D103,D205,D212,E501
"""Tests for the package-hallucination guard logic.

Feature: Defend against package hallucination and slopsquatting

As the imbue verification spine
I want to detect installs of nonexistent or typosquatted packages
So that hallucinated dependencies (5.2-21.7% of LLM suggestions,
Spracklen 2024) never reach the environment unverified.

The pure logic lives in hooks/shared/package_guard.py so it can be
tested without network access. The registry lookup is injected as a
function, so these tests never touch PyPI/npm/crates.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


@pytest.fixture
def pg():
    """Import the package_guard shared module via importlib."""
    shared = Path(__file__).resolve().parents[3] / "hooks" / "shared"
    module_path = shared / "package_guard.py"
    spec = importlib.util.spec_from_file_location("package_guard", module_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["package_guard"] = mod
    spec.loader.exec_module(mod)
    return mod


class TestParsePackages:
    """Feature: extract installed package names from a shell command."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "command,expected",
        [
            ("pip install requests numpy", [("pypi", "requests"), ("pypi", "numpy")]),
            ("pip3 install requests", [("pypi", "requests")]),
            ("python -m pip install flask", [("pypi", "flask")]),
            ("uv pip install httpx", [("pypi", "httpx")]),
            ("uv add pydantic", [("pypi", "pydantic")]),
            ("npm install react", [("npm", "react")]),
            ("npm i lodash", [("npm", "lodash")]),
            ("yarn add typescript", [("npm", "typescript")]),
            ("pnpm add vite", [("npm", "vite")]),
            ("cargo add serde", [("crates", "serde")]),
            ("git status", []),
            ("echo pip install foo", []),
        ],
        ids=[
            "pip-multi",
            "pip3",
            "python-m-pip",
            "uv-pip",
            "uv-add",
            "npm-install",
            "npm-i",
            "yarn-add",
            "pnpm-add",
            "cargo-add",
            "non-install",
            "install-in-string-arg",
        ],
    )
    def test_parse(self, pg, command, expected):
        assert pg.parse_packages(command) == expected

    @pytest.mark.unit
    def test_strips_versions_and_flags(self, pg):
        cmd = "pip install --upgrade requests==2.31.0 -r requirements.txt"
        assert pg.parse_packages(cmd) == [("pypi", "requests")]

    @pytest.mark.unit
    def test_skips_local_and_vcs_targets(self, pg):
        cmd = "pip install -e . git+https://github.com/x/y.git ./local"
        assert pg.parse_packages(cmd) == []

    @pytest.mark.unit
    def test_strips_npm_scope_version(self, pg):
        assert pg.parse_packages("npm install left-pad@1.3.0") == [("npm", "left-pad")]

    @pytest.mark.unit
    def test_preserves_npm_scoped_name_drops_version(self, pg):
        """Scenario: a scoped @scope/name keeps its scope, loses its version."""
        assert pg.parse_packages("npm install @types/node@20.1.0") == [
            ("npm", "@types/node")
        ]

    @pytest.mark.unit
    def test_bare_version_token_yields_no_package(self, pg):
        """Scenario: a token that is only a version specifier is dropped."""
        assert pg.parse_packages("pip install ==1.0") == []


class TestLevenshtein:
    """Feature: edit distance for typosquat detection."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "a,b,expected",
        [
            ("requests", "requests", 0),
            ("requests", "reqeusts", 2),
            ("numpy", "numpi", 1),
            ("abc", "", 3),
            ("", "abc", 3),
            ("", "", 0),
        ],
    )
    def test_distance(self, pg, a, b, expected):
        assert pg.levenshtein(a, b) == expected


class TestNearestKnown:
    """Feature: flag names suspiciously close to a popular package."""

    @pytest.mark.unit
    def test_typo_of_popular_pkg_is_flagged(self, pg):
        assert pg.nearest_known("reqeusts", "pypi") == "requests"

    @pytest.mark.unit
    def test_known_pkg_itself_is_not_flagged(self, pg):
        assert pg.nearest_known("requests", "pypi") is None

    @pytest.mark.unit
    def test_distant_name_is_not_flagged(self, pg):
        assert pg.nearest_known("my-internal-tool-xyz", "pypi") is None


class TestAssessPackages:
    """Feature: classify each package as ok, typosquat, or nonexistent."""

    @pytest.mark.unit
    def test_typosquat_detected_without_network(self, pg):
        findings = pg.assess_packages("pip install reqeusts", registry_fn=None)
        assert len(findings) == 1
        assert findings[0]["kind"] == "typosquat"
        assert findings[0]["name"] == "reqeusts"
        assert "requests" in findings[0]["detail"]

    @pytest.mark.unit
    def test_known_popular_package_passes_clean(self, pg):
        # requests is known-popular, so no network call and no finding.
        findings = pg.assess_packages("pip install requests", registry_fn=None)
        assert findings == []

    @pytest.mark.unit
    def test_nonexistent_package_flagged_via_registry(self, pg):
        # registry_fn returns False => definitively absent => hallucination.
        def fake_registry(name, ecosystem):
            return False

        findings = pg.assess_packages(
            "pip install totally-made-up-pkg-9000", registry_fn=fake_registry
        )
        assert len(findings) == 1
        assert findings[0]["kind"] == "nonexistent"

    @pytest.mark.unit
    def test_unknown_but_real_package_passes(self, pg):
        def fake_registry(name, ecosystem):
            return True

        findings = pg.assess_packages(
            "pip install some-real-but-niche-lib", registry_fn=fake_registry
        )
        assert findings == []

    @pytest.mark.unit
    def test_unknown_name_without_registry_is_silent(self, pg):
        """Scenario: with no registry_fn, an unknown non-typo name is not flagged.

        Offline-only mode relies on the typosquat signal alone; a name
        that is neither known-popular nor a typo produces no finding.
        """
        findings = pg.assess_packages(
            "pip install some-niche-internal-lib", registry_fn=None
        )
        assert findings == []

    @pytest.mark.unit
    def test_offline_unknown_package_is_unverified_not_blocked(self, pg):
        def offline_registry(name, ecosystem):
            return None  # could not determine

        findings = pg.assess_packages(
            "pip install some-niche-lib", registry_fn=offline_registry
        )
        # Unverified is reported but is not a hard nonexistent finding.
        assert all(f["kind"] != "nonexistent" for f in findings)
