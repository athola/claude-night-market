#!/usr/bin/env python3
"""Tests for context_scanner.py - project context map generator.

Tests organized by implementation task (T001-T007).
"""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

# Import the scanner module from scripts/
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import context_scanner as cs

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_project(tmp_path: Path) -> Path:
    """Create a minimal project structure for testing."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')\n")
    (tmp_path / "src" / "utils.py").write_text("def helper(): pass\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_main.py").write_text("def test_it(): pass\n")
    (tmp_path / "README.md").write_text("# My Project\n")
    return tmp_path


@pytest.fixture()
def python_project(tmp_path: Path) -> Path:
    """Create a Python project with pyproject.toml."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("from fastapi import FastAPI\n")
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""\
        [project]
        name = "myapp"
        version = "1.0.0"
        dependencies = [
            "fastapi>=0.104.0",
            "pydantic>=2.5.0",
            "sqlalchemy>=2.0.0",
            "uvicorn[standard]>=0.24.0",
            "httpx>=0.25.0",
            "click>=8.1.0",
            "rich>=13.0.0",
            "structlog>=23.0.0",
            "alembic>=1.12.0",
            "python-dotenv>=1.0.0",
        ]

        [project.optional-dependencies]
        dev = ["pytest>=7.0.0", "ruff>=0.1.0"]

        [project.scripts]
        myapp = "myapp.cli:main"
        """)
    )
    (tmp_path / "uv.lock").write_text("# uv lockfile\n")
    return tmp_path


@pytest.fixture()
def node_project(tmp_path: Path) -> Path:
    """Create a Node.js project with package.json."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "index.ts").write_text("export default {}\n")
    (tmp_path / "package.json").write_text(
        json.dumps(
            {
                "name": "myapp",
                "version": "1.0.0",
                "main": "dist/index.js",
                "bin": {"myapp": "dist/cli.js"},
                "dependencies": {
                    "express": "^4.18.0",
                    "zod": "^3.22.0",
                    "prisma": "^5.7.0",
                },
                "devDependencies": {
                    "typescript": "^5.3.0",
                    "vitest": "^1.0.0",
                },
            },
            indent=2,
        )
    )
    (tmp_path / "yarn.lock").write_text("# yarn lockfile\n")
    return tmp_path


@pytest.fixture()
def rust_project(tmp_path: Path) -> Path:
    """Create a Rust project with Cargo.toml."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.rs").write_text("fn main() {}\n")
    (tmp_path / "Cargo.toml").write_text(
        textwrap.dedent("""\
        [package]
        name = "myapp"
        version = "0.1.0"

        [dependencies]
        tokio = { version = "1.34", features = ["full"] }
        serde = { version = "1.0", features = ["derive"] }
        axum = "0.7"
        sqlx = { version = "0.7", features = ["postgres"] }
        """)
    )
    return tmp_path


@pytest.fixture()
def go_project(tmp_path: Path) -> Path:
    """Create a Go project with go.mod."""
    (tmp_path / "cmd").mkdir()
    (tmp_path / "cmd" / "main.go").write_text("package main\n")
    (tmp_path / "go.mod").write_text(
        textwrap.dedent("""\
        module github.com/user/myapp

        go 1.21

        require (
        \tgithub.com/gin-gonic/gin v1.9.1
        \tgithub.com/jmoiron/sqlx v1.3.5
        \tgithub.com/spf13/cobra v1.8.0
        )
        """)
    )
    return tmp_path


@pytest.fixture()
def multi_lang_project(tmp_path: Path) -> Path:
    """Create a project with multiple ecosystems."""
    (tmp_path / "backend").mkdir()
    (tmp_path / "backend" / "main.py").write_text("app = Flask(__name__)\n")
    (tmp_path / "frontend").mkdir()
    (tmp_path / "frontend" / "index.ts").write_text("export {}\n")
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""\
        [project]
        name = "backend"
        dependencies = ["flask>=3.0.0"]
        """)
    )
    (tmp_path / "package.json").write_text(
        json.dumps(
            {
                "name": "frontend",
                "dependencies": {"react": "^18.2.0", "next": "^14.0.0"},
            }
        )
    )
    return tmp_path


# ---------------------------------------------------------------------------
# T001: File Tree Walker
# ---------------------------------------------------------------------------


class TestFileTreeWalker:
    """Tests for scan_directory and DirectoryInfo."""

    def test_empty_directory(self, tmp_path: Path) -> None:
        result = cs.scan_directory(tmp_path)
        assert result.total_files == 0
        assert result.directories == []

    def test_single_file(self, tmp_path: Path) -> None:
        (tmp_path / "hello.py").write_text("print('hi')\n")
        result = cs.scan_directory(tmp_path)
        assert result.total_files == 1

    def test_nested_directories(self, tmp_project: Path) -> None:
        result = cs.scan_directory(tmp_project)
        assert result.total_files == 4  # 2 src + 1 test + 1 readme
        dir_names = [d.path for d in result.directories]
        assert "src" in dir_names
        assert "tests" in dir_names

    def test_excludes_git_directory(self, tmp_project: Path) -> None:
        git_dir = tmp_project / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("core\n")
        result = cs.scan_directory(tmp_project)
        dir_names = [d.path for d in result.directories]
        assert ".git" not in dir_names

    def test_excludes_node_modules(self, tmp_project: Path) -> None:
        nm = tmp_project / "node_modules" / "express"
        nm.mkdir(parents=True)
        (nm / "index.js").write_text("module.exports = {}\n")
        result = cs.scan_directory(tmp_project)
        dir_names = [d.path for d in result.directories]
        assert "node_modules" not in dir_names

    def test_excludes_venv(self, tmp_project: Path) -> None:
        venv = tmp_project / ".venv" / "lib"
        venv.mkdir(parents=True)
        (venv / "site.py").write_text("")
        result = cs.scan_directory(tmp_project)
        dir_names = [d.path for d in result.directories]
        assert ".venv" not in dir_names

    def test_sorted_by_file_count(self, tmp_project: Path) -> None:
        result = cs.scan_directory(tmp_project)
        counts = [d.file_count for d in result.directories]
        assert counts == sorted(counts, reverse=True)

    def test_primary_language_detected(self, tmp_project: Path) -> None:
        result = cs.scan_directory(tmp_project)
        src_dir = next(d for d in result.directories if d.path == "src")
        assert src_dir.primary_language == "Python"

    def test_project_name_from_directory(self, tmp_project: Path) -> None:
        result = cs.scan_directory(tmp_project)
        assert result.project_name == tmp_project.name

    def test_does_not_follow_symlinks(self, tmp_project: Path) -> None:
        target = tmp_project / "src"
        link = tmp_project / "link_to_src"
        link.symlink_to(target)
        result = cs.scan_directory(tmp_project)
        # Should not double-count src files via symlink
        src_files = sum(
            d.file_count for d in result.directories if d.path in ("src", "link_to_src")
        )
        # link_to_src might be counted but should not recurse into it
        assert result.total_files <= 5  # 4 real + possibly the symlink dir


# ---------------------------------------------------------------------------
# T002: Python Ecosystem Detector
# ---------------------------------------------------------------------------


class TestPythonDetector:
    """Tests for detect_python ecosystem."""

    def test_detects_pyproject_toml(self, python_project: Path) -> None:
        result = cs.detect_python(python_project)
        assert result is not None
        assert len(result.dependencies) > 0

    def test_extracts_dependencies(self, python_project: Path) -> None:
        result = cs.detect_python(python_project)
        dep_names = [d.name for d in result.dependencies]
        assert "fastapi" in dep_names
        assert "pydantic" in dep_names
        assert "sqlalchemy" in dep_names

    def test_identifies_frameworks(self, python_project: Path) -> None:
        result = cs.detect_python(python_project)
        fw_names = [f.name for f in result.frameworks]
        assert "FastAPI" in fw_names

    def test_detects_uv_lockfile(self, python_project: Path) -> None:
        result = cs.detect_python(python_project)
        assert result.package_manager == "uv"

    def test_detects_poetry_lockfile(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text(
            "[tool.poetry]\nname = 'x'\n[tool.poetry.dependencies]\npython = '^3.9'\n"
        )
        (tmp_path / "poetry.lock").write_text("# poetry\n")
        result = cs.detect_python(tmp_path)
        assert result.package_manager == "poetry"

    def test_detects_requirements_txt(self, tmp_path: Path) -> None:
        (tmp_path / "requirements.txt").write_text("flask==3.0.0\nrequests>=2.31.0\n")
        result = cs.detect_python(tmp_path)
        dep_names = [d.name for d in result.dependencies]
        assert "flask" in dep_names
        assert "requests" in dep_names

    def test_extracts_cli_entry_points(self, python_project: Path) -> None:
        result = cs.detect_python(python_project)
        assert len(result.entry_points) > 0
        ep_names = [e.path for e in result.entry_points]
        assert "myapp = myapp.cli:main" in ep_names or any(
            "myapp" in e.path for e in result.entry_points
        )

    def test_no_python_files_returns_none(self, tmp_path: Path) -> None:
        (tmp_path / "hello.txt").write_text("not python\n")
        result = cs.detect_python(tmp_path)
        assert result is None

    def test_separates_dev_dependencies(self, python_project: Path) -> None:
        result = cs.detect_python(python_project)
        dev_deps = [d for d in result.dependencies if d.category == "dev"]
        assert any(d.name == "pytest" for d in dev_deps)


# ---------------------------------------------------------------------------
# T003: Multi-Ecosystem Detectors
# ---------------------------------------------------------------------------


class TestNodeDetector:
    """Tests for detect_node ecosystem."""

    def test_detects_package_json(self, node_project: Path) -> None:
        result = cs.detect_node(node_project)
        assert result is not None

    def test_extracts_dependencies(self, node_project: Path) -> None:
        result = cs.detect_node(node_project)
        dep_names = [d.name for d in result.dependencies]
        assert "express" in dep_names
        assert "zod" in dep_names

    def test_separates_dev_dependencies(self, node_project: Path) -> None:
        result = cs.detect_node(node_project)
        dev_deps = [d for d in result.dependencies if d.category == "dev"]
        assert any(d.name == "typescript" for d in dev_deps)

    def test_detects_yarn_lockfile(self, node_project: Path) -> None:
        result = cs.detect_node(node_project)
        assert result.package_manager == "yarn"

    def test_extracts_bin_entry_points(self, node_project: Path) -> None:
        result = cs.detect_node(node_project)
        assert len(result.entry_points) > 0

    def test_no_package_json_returns_none(self, tmp_path: Path) -> None:
        result = cs.detect_node(tmp_path)
        assert result is None


class TestRustDetector:
    """Tests for detect_rust ecosystem."""

    def test_detects_cargo_toml(self, rust_project: Path) -> None:
        result = cs.detect_rust(rust_project)
        assert result is not None

    def test_extracts_dependencies(self, rust_project: Path) -> None:
        result = cs.detect_rust(rust_project)
        dep_names = [d.name for d in result.dependencies]
        assert "tokio" in dep_names
        assert "serde" in dep_names
        assert "axum" in dep_names

    def test_identifies_frameworks(self, rust_project: Path) -> None:
        result = cs.detect_rust(rust_project)
        fw_names = [f.name for f in result.frameworks]
        assert "Axum" in fw_names or "Tokio" in fw_names

    def test_no_cargo_toml_returns_none(self, tmp_path: Path) -> None:
        result = cs.detect_rust(tmp_path)
        assert result is None


class TestGoDetector:
    """Tests for detect_go ecosystem."""

    def test_detects_go_mod(self, go_project: Path) -> None:
        result = cs.detect_go(go_project)
        assert result is not None

    def test_extracts_dependencies(self, go_project: Path) -> None:
        result = cs.detect_go(go_project)
        dep_names = [d.name for d in result.dependencies]
        assert any("gin" in n for n in dep_names)

    def test_identifies_frameworks(self, go_project: Path) -> None:
        result = cs.detect_go(go_project)
        fw_names = [f.name for f in result.frameworks]
        assert "Gin" in fw_names

    def test_no_go_mod_returns_none(self, tmp_path: Path) -> None:
        result = cs.detect_go(tmp_path)
        assert result is None


class TestMultiLangDetection:
    """Tests for projects with multiple ecosystems."""

    def test_detects_all_ecosystems(self, multi_lang_project: Path) -> None:
        result = cs.scan_directory(multi_lang_project)
        eco_names = [e.name for e in result.ecosystems]
        assert "Python" in eco_names
        assert "Node" in eco_names


# ---------------------------------------------------------------------------
# T004: Entry Point Detection
# ---------------------------------------------------------------------------


class TestEntryPointDetection:
    """Tests for entry point detection."""

    def test_detects_main_py(self, tmp_path: Path) -> None:
        (tmp_path / "main.py").write_text("if __name__ == '__main__': pass\n")
        result = cs.detect_entry_points(tmp_path, [])
        paths = [e.path for e in result]
        assert "main.py" in paths

    def test_detects_dunder_main(self, tmp_path: Path) -> None:
        pkg = tmp_path / "myapp"
        pkg.mkdir()
        (pkg / "__main__.py").write_text("print('run')\n")
        result = cs.detect_entry_points(tmp_path, [])
        paths = [e.path for e in result]
        assert any("__main__.py" in p for p in paths)

    def test_detects_app_py(self, tmp_path: Path) -> None:
        (tmp_path / "app.py").write_text("app = Flask(__name__)\n")
        result = cs.detect_entry_points(tmp_path, [])
        paths = [e.path for e in result]
        assert "app.py" in paths

    def test_detects_index_ts(self, tmp_path: Path) -> None:
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "index.ts").write_text("export default {}\n")
        result = cs.detect_entry_points(tmp_path, [])
        paths = [e.path for e in result]
        assert any("index.ts" in p for p in paths)

    def test_detects_main_go(self, tmp_path: Path) -> None:
        (tmp_path / "main.go").write_text("package main\n")
        result = cs.detect_entry_points(tmp_path, [])
        paths = [e.path for e in result]
        assert "main.go" in paths

    def test_detects_main_rs(self, tmp_path: Path) -> None:
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.rs").write_text("fn main() {}\n")
        result = cs.detect_entry_points(tmp_path, [])
        assert any("main.rs" in e.path for e in result)

    def test_no_entry_points_returns_empty(self, tmp_path: Path) -> None:
        (tmp_path / "lib.py").write_text("x = 1\n")
        result = cs.detect_entry_points(tmp_path, [])
        assert result == []


# ---------------------------------------------------------------------------
# T005: Strategic Summarizer
# ---------------------------------------------------------------------------


class TestStrategicSummarizer:
    """Tests for summarize() truncation and omission."""

    def test_truncates_long_directory_list(self, tmp_path: Path) -> None:
        # Create 20 directories
        for i in range(20):
            d = tmp_path / f"dir_{i:02d}"
            d.mkdir()
            (d / "file.py").write_text(f"# {i}\n")

        result = cs.scan_directory(tmp_path)
        summary = cs.summarize(result, max_dirs=8)
        assert summary.truncated_dirs == 12  # 20 - 8

    def test_truncates_long_dependency_list(self) -> None:
        deps = [cs.Dependency(f"pkg-{i}", "1.0.0", "runtime") for i in range(30)]
        summary = cs.summarize_dependencies(deps, max_items=8)
        assert len(summary.shown) == 8
        assert summary.remaining == 22

    def test_omits_empty_sections(self, tmp_path: Path) -> None:
        (tmp_path / "hello.txt").write_text("hi\n")
        result = cs.scan_directory(tmp_path)
        md = cs.render_markdown(result)
        # No frameworks detected, so section should be absent
        assert "## Frameworks" not in md

    def test_token_estimate_under_target(self, tmp_project: Path) -> None:
        result = cs.scan_directory(tmp_project)
        md = cs.render_markdown(result)
        estimated_tokens = len(md) / 4
        assert estimated_tokens < 5000


# ---------------------------------------------------------------------------
# T006: Markdown and JSON Renderers
# ---------------------------------------------------------------------------


class TestRenderers:
    """Tests for markdown and JSON output."""

    def test_markdown_has_header(self, tmp_project: Path) -> None:
        result = cs.scan_directory(tmp_project)
        md = cs.render_markdown(result)
        assert md.startswith("# Context Map:")
        assert "Files:" in md

    def test_markdown_has_structure_section(self, tmp_project: Path) -> None:
        result = cs.scan_directory(tmp_project)
        md = cs.render_markdown(result)
        assert "## Structure" in md

    def test_json_output_valid(self, tmp_project: Path) -> None:
        result = cs.scan_directory(tmp_project)
        j = cs.render_json(result)
        parsed = json.loads(j)
        assert "project_name" in parsed
        assert "total_files" in parsed
        assert "directories" in parsed

    def test_json_roundtrips(self, tmp_project: Path) -> None:
        result = cs.scan_directory(tmp_project)
        j = cs.render_json(result)
        parsed = json.loads(j)
        assert parsed["total_files"] == result.total_files

    def test_markdown_deterministic(self, tmp_project: Path) -> None:
        result = cs.scan_directory(tmp_project)
        md1 = cs.render_markdown(result, include_timestamp=False)
        md2 = cs.render_markdown(result, include_timestamp=False)
        assert md1 == md2


# ---------------------------------------------------------------------------
# T007: CLI Interface
# ---------------------------------------------------------------------------


class TestCLI:
    """Tests for the CLI interface."""

    def test_default_scans_given_path(self, tmp_project: Path) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "context_scanner.py"), str(tmp_project)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "# Context Map:" in result.stdout

    def test_json_format(self, tmp_project: Path) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS_DIR / "context_scanner.py"),
                str(tmp_project),
                "--format",
                "json",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        parsed = json.loads(result.stdout)
        assert "project_name" in parsed

    def test_invalid_path_exits_with_error(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS_DIR / "context_scanner.py"),
                "/nonexistent/path",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1

    def test_output_file(self, tmp_project: Path, tmp_path: Path) -> None:
        outfile = tmp_path / "output.md"
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS_DIR / "context_scanner.py"),
                str(tmp_project),
                "--output",
                str(outfile),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert outfile.exists()
        assert "# Context Map:" in outfile.read_text()

    def test_max_tokens_flag(self, tmp_project: Path) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS_DIR / "context_scanner.py"),
                str(tmp_project),
                "--max-tokens",
                "2000",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        # Output should be within token budget
        estimated = len(result.stdout) / 4
        assert estimated < 2500  # some tolerance


# ---------------------------------------------------------------------------
# T008: Import Graph + Hot File Detection
# ---------------------------------------------------------------------------


@pytest.fixture()
def import_graph_project(tmp_path: Path) -> Path:
    """Create a project with known import relationships."""
    src = tmp_path / "src"
    src.mkdir()
    # utils.py is imported by three files -> hot file
    (src / "utils.py").write_text("def helper(): pass\n")
    (src / "models.py").write_text("from . import utils\nclass User: pass\n")
    (src / "views.py").write_text(
        "from .models import User\nfrom .utils import helper\n"
    )
    (src / "cli.py").write_text("from src.utils import helper\nimport os\n")
    (src / "standalone.py").write_text("print('no imports')\n")
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "test"\ndependencies = []\n'
    )
    return tmp_path


class TestImportGraph:
    """Tests for import graph construction and hot file detection."""

    def test_builds_graph_from_python(self, import_graph_project: Path) -> None:
        graph = cs.build_import_graph(import_graph_project)
        assert len(graph.edges) > 0

    def test_detects_hot_files(self, import_graph_project: Path) -> None:
        graph = cs.build_import_graph(import_graph_project)
        hot = cs.detect_hot_files(graph, threshold=2)
        # utils.py is imported by models, views, cli -> hot
        hot_names = [Path(f).name for f in hot]
        assert "utils.py" in hot_names

    def test_standalone_not_hot(self, import_graph_project: Path) -> None:
        graph = cs.build_import_graph(import_graph_project)
        hot = cs.detect_hot_files(graph, threshold=2)
        hot_names = [Path(f).name for f in hot]
        assert "standalone.py" not in hot_names

    def test_js_imports(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        (src / "utils.js").write_text("export function helper() {}\n")
        (src / "app.js").write_text("import { helper } from './utils'\n")
        (src / "index.js").write_text("import './app'\nimport './utils'\n")
        graph = cs.build_import_graph(tmp_path)
        assert len(graph.edges) >= 2

    def test_empty_project_returns_empty_graph(self, tmp_path: Path) -> None:
        graph = cs.build_import_graph(tmp_path)
        assert len(graph.edges) == 0
        assert len(graph.imported_by) == 0


# ---------------------------------------------------------------------------
# T009: Route Detection
# ---------------------------------------------------------------------------


@pytest.fixture()
def fastapi_project(tmp_path: Path) -> Path:
    """Create a FastAPI project with routes."""
    (tmp_path / "app.py").write_text(
        textwrap.dedent("""\
        from fastapi import FastAPI
        app = FastAPI()

        @app.get("/users")
        def list_users(): pass

        @app.post("/users")
        def create_user(): pass

        @app.get("/users/{user_id}")
        def get_user(user_id: int): pass
        """)
    )
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "test"\ndependencies = ["fastapi"]\n'
    )
    return tmp_path


@pytest.fixture()
def flask_project(tmp_path: Path) -> Path:
    """Create a Flask project with routes."""
    (tmp_path / "app.py").write_text(
        textwrap.dedent("""\
        from flask import Flask
        app = Flask(__name__)

        @app.route("/health", methods=["GET"])
        def health(): pass

        @app.route("/api/data", methods=["POST"])
        def post_data(): pass
        """)
    )
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "test"\ndependencies = ["flask"]\n'
    )
    return tmp_path


@pytest.fixture()
def express_project(tmp_path: Path) -> Path:
    """Create an Express project with routes."""
    (tmp_path / "app.js").write_text(
        textwrap.dedent("""\
        const express = require('express');
        const app = express();

        app.get('/api/items', (req, res) => {});
        app.post('/api/items', (req, res) => {});
        router.delete('/api/items/:id', handler);
        """)
    )
    (tmp_path / "package.json").write_text(
        '{"name":"test","dependencies":{"express":"^4.0.0"}}'
    )
    return tmp_path


class TestRouteDetection:
    """Tests for API route extraction."""

    def test_detects_fastapi_routes(self, fastapi_project: Path) -> None:
        routes = cs.detect_routes(fastapi_project)
        assert len(routes) == 3
        paths = [r.path for r in routes]
        assert "/users" in paths
        assert "/users/{user_id}" in paths

    def test_detects_fastapi_methods(self, fastapi_project: Path) -> None:
        routes = cs.detect_routes(fastapi_project)
        methods = {r.method for r in routes}
        assert "GET" in methods
        assert "POST" in methods

    def test_detects_flask_routes(self, flask_project: Path) -> None:
        routes = cs.detect_routes(flask_project)
        assert len(routes) >= 2
        paths = [r.path for r in routes]
        assert "/health" in paths

    def test_detects_express_routes(self, express_project: Path) -> None:
        routes = cs.detect_routes(express_project)
        assert len(routes) >= 2
        paths = [r.path for r in routes]
        assert "/api/items" in paths

    def test_no_routes_returns_empty(self, tmp_path: Path) -> None:
        (tmp_path / "lib.py").write_text("x = 1\n")
        routes = cs.detect_routes(tmp_path)
        assert routes == []


# ---------------------------------------------------------------------------
# T010: Environment Variable Detection
# ---------------------------------------------------------------------------


@pytest.fixture()
def env_var_project(tmp_path: Path) -> Path:
    """Create a project with env var usage."""
    (tmp_path / "config.py").write_text(
        textwrap.dedent("""\
        import os
        DB_URL = os.environ["DATABASE_URL"]
        SECRET = os.getenv("SECRET_KEY", "default")
        DEBUG = os.environ.get("DEBUG", "false")
        """)
    )
    (tmp_path / "app.js").write_text(
        textwrap.dedent("""\
        const db = process.env.DATABASE_URL;
        const port = process.env.PORT || 3000;
        """)
    )
    (tmp_path / ".env.example").write_text(
        "DATABASE_URL=postgres://localhost/db\nSECRET_KEY=changeme\nREDIS_URL=\n"
    )
    return tmp_path


class TestEnvVarDetection:
    """Tests for environment variable detection."""

    def test_detects_python_environ(self, env_var_project: Path) -> None:
        env_vars = cs.detect_env_vars(env_var_project)
        names = [v.name for v in env_vars]
        assert "DATABASE_URL" in names
        assert "SECRET_KEY" in names

    def test_detects_node_process_env(self, env_var_project: Path) -> None:
        env_vars = cs.detect_env_vars(env_var_project)
        names = [v.name for v in env_vars]
        assert "PORT" in names

    def test_detects_env_example_vars(self, env_var_project: Path) -> None:
        env_vars = cs.detect_env_vars(env_var_project)
        names = [v.name for v in env_vars]
        assert "REDIS_URL" in names

    def test_deduplicates_vars(self, env_var_project: Path) -> None:
        env_vars = cs.detect_env_vars(env_var_project)
        names = [v.name for v in env_vars]
        # DATABASE_URL appears in config.py, app.js, .env.example
        assert names.count("DATABASE_URL") == 1

    def test_no_env_vars_returns_empty(self, tmp_path: Path) -> None:
        (tmp_path / "lib.py").write_text("x = 1\n")
        env_vars = cs.detect_env_vars(tmp_path)
        assert env_vars == []


# ---------------------------------------------------------------------------
# T011: Middleware Detection
# ---------------------------------------------------------------------------


@pytest.fixture()
def middleware_project(tmp_path: Path) -> Path:
    """Create a project with middleware patterns."""
    (tmp_path / "middleware.py").write_text(
        textwrap.dedent("""\
        from fastapi.middleware.cors import CORSMiddleware
        from app.auth import require_auth

        app.add_middleware(CORSMiddleware)
        """)
    )
    (tmp_path / "auth.py").write_text(
        textwrap.dedent("""\
        def authenticate(request):
            token = request.headers.get("Authorization")
            return verify_jwt(token)
        """)
    )
    (tmp_path / "limits.py").write_text(
        "from slowapi import Limiter\nlimiter = Limiter(key_func=get_remote_address)\n"
    )
    return tmp_path


class TestMiddlewareDetection:
    """Tests for middleware pattern detection."""

    def test_detects_cors(self, middleware_project: Path) -> None:
        mw = cs.detect_middleware(middleware_project)
        types = [m.kind for m in mw]
        assert "cors" in types

    def test_detects_auth(self, middleware_project: Path) -> None:
        mw = cs.detect_middleware(middleware_project)
        types = [m.kind for m in mw]
        assert "auth" in types

    def test_detects_rate_limiting(self, middleware_project: Path) -> None:
        mw = cs.detect_middleware(middleware_project)
        types = [m.kind for m in mw]
        assert "rate-limit" in types

    def test_no_middleware_returns_empty(self, tmp_path: Path) -> None:
        (tmp_path / "lib.py").write_text("x = 1\n")
        mw = cs.detect_middleware(tmp_path)
        assert mw == []


# ---------------------------------------------------------------------------
# T012: Token Savings Estimation
# ---------------------------------------------------------------------------


class TestTokenEstimation:
    """Tests for exploration token savings calculation."""

    def test_estimates_from_routes(self) -> None:
        result = cs.ScanResult(project_name="test", total_files=10)
        result.routes = [
            cs.RouteInfo("GET", "/a", "app.py"),
            cs.RouteInfo("POST", "/b", "app.py"),
        ]
        est = cs.estimate_token_savings(result)
        assert est.route_tokens == 2 * 400

    def test_estimates_from_hot_files(self) -> None:
        result = cs.ScanResult(project_name="test", total_files=10)
        result.hot_files = ["utils.py", "models.py"]
        est = cs.estimate_token_savings(result)
        assert est.hot_file_tokens == 2 * 150

    def test_total_includes_all_sources(self) -> None:
        result = cs.ScanResult(project_name="test", total_files=50)
        result.routes = [cs.RouteInfo("GET", "/a", "app.py")]
        result.hot_files = ["utils.py"]
        result.env_vars = [cs.EnvVarInfo("DB_URL", "config.py")]
        est = cs.estimate_token_savings(result)
        assert est.total > 0
        assert est.total == (
            est.route_tokens
            + est.hot_file_tokens
            + est.env_var_tokens
            + est.file_scan_tokens
        )

    def test_zero_for_empty_project(self) -> None:
        result = cs.ScanResult(project_name="test", total_files=0)
        est = cs.estimate_token_savings(result)
        assert est.total == 0


# ---------------------------------------------------------------------------
# T013: Integration - New sections in rendered output
# ---------------------------------------------------------------------------


class TestRendererIntegration:
    """Tests that new capabilities appear in rendered output."""

    def test_markdown_includes_routes_section(self, fastapi_project: Path) -> None:
        result = cs.scan_directory(fastapi_project)
        md = cs.render_markdown(result)
        assert "## Routes" in md
        assert "/users" in md

    def test_markdown_includes_hot_files_section(
        self, import_graph_project: Path
    ) -> None:
        result = cs.scan_directory(import_graph_project)
        md = cs.render_markdown(result)
        # Hot files section only appears when there are hot files
        if result.hot_files:
            assert "## Hot Files" in md

    def test_markdown_includes_env_vars_section(self, env_var_project: Path) -> None:
        result = cs.scan_directory(env_var_project)
        md = cs.render_markdown(result)
        assert "## Environment Variables" in md
        assert "DATABASE_URL" in md

    def test_markdown_includes_token_estimate(self, fastapi_project: Path) -> None:
        result = cs.scan_directory(fastapi_project)
        md = cs.render_markdown(result)
        assert "tokens saved" in md.lower() or "token savings" in md.lower()

    def test_json_includes_new_fields(self, fastapi_project: Path) -> None:
        result = cs.scan_directory(fastapi_project)
        j = cs.render_json(result)
        parsed = json.loads(j)
        assert "routes" in parsed
        assert "token_savings" in parsed


# ---------------------------------------------------------------------------
# T001: Blast Radius - Data Structure and BFS
# ---------------------------------------------------------------------------


class TestBlastRadius:
    """Tests for per-file blast radius BFS."""

    def test_direct_dependents(self, tmp_path):
        """Blast radius shows files that directly import the target."""
        (tmp_path / "core.py").write_text("x = 1\n")
        (tmp_path / "a.py").write_text("import core\n")
        (tmp_path / "b.py").write_text("import core\n")
        (tmp_path / "c.py").write_text("import a\n")

        graph = cs.build_import_graph(tmp_path)
        result = cs.blast_radius(graph, "core.py")

        assert set(result.direct) == {"a.py", "b.py"}

    def test_transitive_dependents(self, tmp_path):
        """Blast radius includes 2nd+ degree dependents with via path."""
        (tmp_path / "core.py").write_text("x = 1\n")
        (tmp_path / "a.py").write_text("import core\n")
        (tmp_path / "b.py").write_text("import a\n")

        graph = cs.build_import_graph(tmp_path)
        result = cs.blast_radius(graph, "core.py")

        assert result.direct == ["a.py"]
        assert len(result.transitive) == 1
        file, via = result.transitive[0]
        assert file == "b.py"
        assert via == "a.py"

    def test_no_dependents(self, tmp_path):
        """File with no importers has empty blast radius."""
        (tmp_path / "lonely.py").write_text("x = 1\n")

        graph = cs.build_import_graph(tmp_path)
        result = cs.blast_radius(graph, "lonely.py")

        assert result.direct == []
        assert result.transitive == []
        assert result.total_affected == 0

    def test_unknown_file_returns_empty(self, tmp_path):
        """Blast radius of a file not in the graph is empty."""
        (tmp_path / "a.py").write_text("x = 1\n")

        graph = cs.build_import_graph(tmp_path)
        result = cs.blast_radius(graph, "nonexistent.py")

        assert result.total_affected == 0

    def test_total_count(self, tmp_path):
        """total_affected is sum of direct and transitive."""
        (tmp_path / "core.py").write_text("x = 1\n")
        (tmp_path / "a.py").write_text("import core\n")
        (tmp_path / "b.py").write_text("import core\n")
        (tmp_path / "c.py").write_text("import a\n")

        graph = cs.build_import_graph(tmp_path)
        result = cs.blast_radius(graph, "core.py")

        assert result.total_affected == len(result.direct) + len(result.transitive)


class TestBlastRadiusCLI:
    """Tests for --blast CLI flag and output rendering."""

    def test_blast_flag_produces_output(self, tmp_path, capsys):
        (tmp_path / "core.py").write_text("x = 1\n")
        (tmp_path / "a.py").write_text("import core\n")

        exit_code = cs.main(["--blast", "core.py", str(tmp_path)])
        captured = capsys.readouterr()

        assert exit_code == 0
        assert "Blast Radius: core.py" in captured.out
        assert "a.py" in captured.out

    def test_blast_unknown_file_shows_no_dependents(self, tmp_path, capsys):
        (tmp_path / "a.py").write_text("x = 1\n")

        exit_code = cs.main(["--blast", "nope.py", str(tmp_path)])
        captured = capsys.readouterr()

        assert exit_code == 0
        assert "Direct dependents: 0" in captured.out

    def test_blast_shows_transitive_via(self, tmp_path, capsys):
        (tmp_path / "core.py").write_text("x = 1\n")
        (tmp_path / "a.py").write_text("import core\n")
        (tmp_path / "b.py").write_text("import a\n")

        exit_code = cs.main(["--blast", "core.py", str(tmp_path)])
        captured = capsys.readouterr()

        assert "via" in captured.out.lower() or "a.py" in captured.out


# ---------------------------------------------------------------------------
# T003: Scan Caching with Fingerprint Invalidation
# ---------------------------------------------------------------------------


class TestScanCaching:
    """Tests for scan result caching."""

    def test_compute_fingerprint_stable(self, tmp_path):
        """Same directory produces same fingerprint."""
        (tmp_path / "a.py").write_text("x = 1\n")
        fp1 = cs.compute_fingerprint(tmp_path)
        fp2 = cs.compute_fingerprint(tmp_path)
        assert fp1 == fp2

    def test_fingerprint_changes_on_new_file(self, tmp_path):
        """Adding a file changes the fingerprint."""
        (tmp_path / "a.py").write_text("x = 1\n")
        fp1 = cs.compute_fingerprint(tmp_path)
        (tmp_path / "b.py").write_text("y = 2\n")
        fp2 = cs.compute_fingerprint(tmp_path)
        assert fp1 != fp2

    def test_save_and_load_cache(self, tmp_path):
        """Cache round-trips through save/load."""
        (tmp_path / "a.py").write_text("x = 1\n")
        result = cs.scan_directory(tmp_path)
        cs.save_cache(tmp_path, result)

        cache_file = tmp_path / ".codesight-cache.json"
        assert cache_file.exists()

        loaded = cs.load_cache(tmp_path)
        assert loaded is not None
        assert loaded.project_name == result.project_name
        assert loaded.total_files == result.total_files

    def test_load_cache_returns_none_when_missing(self, tmp_path):
        """No cache file returns None."""
        loaded = cs.load_cache(tmp_path)
        assert loaded is None

    def test_load_cache_returns_none_on_fingerprint_mismatch(self, tmp_path):
        """Stale cache returns None."""
        (tmp_path / "a.py").write_text("x = 1\n")
        result = cs.scan_directory(tmp_path)
        cs.save_cache(tmp_path, result)

        # Change the project
        (tmp_path / "b.py").write_text("y = 2\n")

        loaded = cs.load_cache(tmp_path)
        assert loaded is None

    def test_no_cache_flag_skips_cache(self, tmp_path, capsys):
        """--no-cache forces a fresh scan."""
        (tmp_path / "a.py").write_text("x = 1\n")

        # First scan creates cache
        cs.main([str(tmp_path)])
        assert (tmp_path / ".codesight-cache.json").exists()

        # Second scan with --no-cache still works
        exit_code = cs.main(["--no-cache", str(tmp_path)])
        assert exit_code == 0
