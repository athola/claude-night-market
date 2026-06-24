"""Tests for ATT-002 and ATT-003 fixes in attune_init.

ATT-002: create_project_structure raises ValueError on unsupported language.
ATT-003: Seed file content loaded from template files matches hardcoded output.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from attune_init import (
    _load_seed,  # noqa: PLC0415 - private helper under test; import once at module scope
    create_project_structure,
)


class TestATT002UnsupportedLanguageGuard:
    """Verify create_project_structure raises ValueError for unsupported languages."""

    @pytest.mark.unit
    def test_unsupported_language_raises_value_error(self, tmp_path):
        """create_project_structure('cobol') raises ValueError not silent None."""
        with pytest.raises(ValueError, match="cobol"):
            create_project_structure(tmp_path, "cobol", "my_mod", "my-proj")

    @pytest.mark.unit
    def test_error_message_lists_supported_languages(self, tmp_path):
        """ValueError message names at least one supported language."""
        with pytest.raises(ValueError) as exc_info:
            create_project_structure(tmp_path, "ruby", "my_mod", "my-proj")
        msg = str(exc_info.value).lower()
        assert "python" in msg or "rust" in msg or "typescript" in msg

    @pytest.mark.unit
    @pytest.mark.parametrize("lang", ["python", "rust", "typescript"])
    def test_supported_languages_still_work(self, tmp_path, lang):
        """Supported languages must not raise and must create files."""
        create_project_structure(tmp_path, lang, "my_mod", "my-proj")
        assert any(tmp_path.rglob("*"))


class TestATT003TemplateFiles:
    """Verify _load_seed returns content matching the shipped template files."""

    @pytest.mark.unit
    def test_python_init_template_matches_hardcoded(self):
        """python/__init__.py template matches expected content."""
        module_name = "my_module"
        expected = f'"""{module_name} package."""\n\n__version__ = "0.1.0"\n'
        assert _load_seed("python", "__init__.py", module_name=module_name) == expected

    @pytest.mark.unit
    def test_rust_main_template_matches_hardcoded(self):
        """rust/main.rs template matches expected content."""
        expected = 'fn main() {\n    println!("Hello, world!");\n}\n'
        assert _load_seed("rust", "main.rs") == expected

    @pytest.mark.unit
    def test_rust_lib_template_matches_hardcoded(self):
        """rust/lib.rs template matches expected content."""
        pn = "my-project"
        expected = (
            f"//! {pn} library\n\n"
            "pub fn hello() -> String {\n"
            f'    "Hello from {pn}!".to_string()\n'
            "}\n\n#[cfg(test)]\nmod tests {\n    use super::*;\n\n"
            "    #[test]\n    fn test_hello() {\n"
            f'        assert_eq!(hello(), "Hello from {pn}!");\n'
            "    }\n}\n"
        )
        assert _load_seed("rust", "lib.rs", project_name=pn) == expected

    @pytest.mark.unit
    def test_typescript_index_template_matches_hardcoded(self):
        """typescript/index.ts template matches expected content."""
        expected = (
            'export function hello(): string {\n  return "Hello from TypeScript!";\n}\n'
        )
        assert _load_seed("typescript", "index.ts") == expected

    @pytest.mark.unit
    def test_typescript_app_template_matches_hardcoded(self):
        """typescript/App.tsx template matches expected content."""
        pn = "my-project"
        expected = (
            'import React from "react";\n\nfunction App() {\n  return (\n'
            '    <div className="App">\n      <h1>Welcome to '
            + pn
            + "</h1>\n    </div>\n  );\n}\n\nexport default App;\n"
        )
        assert _load_seed("typescript", "App.tsx", project_name=pn) == expected
