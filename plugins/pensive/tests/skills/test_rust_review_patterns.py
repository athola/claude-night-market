"""Tests for RustReviewSkill code pattern analysis.

Covers:
- TestRustReviewPatterns: silent returns, collection type
  suggestions, SQL injection, cfg(test) misuse, error message
  quality, duplicate validators, builtin trait preference,
  and boundary/gap tests
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from pensive.skills.rust_review import RustReviewSkill


@pytest.mark.unit
class TestRustReviewPatterns:
    """Test suite for Rust code pattern detection."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test."""
        self.skill = RustReviewSkill()
        self.mock_context = Mock()
        self.mock_context.repo_path = Path(tempfile.gettempdir()) / "test_repo"
        self.mock_context.working_dir = Path(tempfile.gettempdir()) / "test_repo"

    # ── silent returns ────────────────────────────────────────────

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_silent_returns(self, mock_skill_context) -> None:
        """Given let-else with bare return, skill flags silent discards."""
        code = """
        fn process(items: Vec<Option<i32>>) {
            for item in items {
                let Some(value) = item else { return; };
                println!("{}", value);
            }
        }
        """
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze_silent_returns(mock_skill_context, "lib.rs")
        assert "silent_returns" in result
        assert len(result["silent_returns"]) >= 1
        assert all(r["type"] == "silent_discard" for r in result["silent_returns"])

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_silent_returns_propagation_not_flagged(self, mock_skill_context) -> None:
        """Given proper error propagation, skill produces no findings."""
        code = """
        fn process(r: Result<i32, String>) -> Result<(), String> {
            let value = r?;
            println!("{}", value);
            Ok(())
        }
        """
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze_silent_returns(mock_skill_context, "lib.rs")
        assert result["silent_returns"] == []

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_silent_returns_let_else_continue(self, mock_skill_context) -> None:
        """Given let-else with bare continue, skill flags the silent discard."""
        code = """
        fn process_all(items: Vec<Option<i32>>) {
            for item in items {
                let Some(v) = item else { continue; };
                println!("{}", v);
            }
        }
        """
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze_silent_returns(mock_skill_context, "lib.rs")
        assert len(result["silent_returns"]) >= 1

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_silent_returns_match_arm(self, mock_skill_context) -> None:
        """Given match arm with bare return, skill flags it."""
        code = """
        fn handle(r: Result<i32, String>) {
            match r {
                Ok(v) => println!("{}", v),
                Err(_) => return,
            }
        }
        """
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze_silent_returns(mock_skill_context, "lib.rs")
        assert len(result["silent_returns"]) >= 1

    # ── collection types ──────────────────────────────────────────

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_vec_contains_as_set(self, mock_skill_context) -> None:
        """Given Vec.contains, skill suggests HashSet."""
        code = """
        fn check_duplicates(ids: &Vec<u64>, new_id: u64) -> bool {
            ids.contains(&new_id)
        }
        """
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze_collection_types(mock_skill_context, "lib.rs")
        assert "collection_type_suggestions" in result
        assert len(result["collection_type_suggestions"]) >= 1
        assert all(
            s["type"] == "vec_as_set_or_map"
            for s in result["collection_type_suggestions"]
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_vec_dedup_pattern(self, mock_skill_context) -> None:
        """Given Vec.dedup, skill flags set-semantics misuse."""
        code = """
        fn unique_ids(mut ids: Vec<u64>) -> Vec<u64> {
            ids.sort();
            ids.dedup();
            ids
        }
        """
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze_collection_types(mock_skill_context, "lib.rs")
        assert len(result["collection_type_suggestions"]) >= 1

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_vec_linear_find(self, mock_skill_context) -> None:
        """Given Vec.iter().find(), skill suggests HashMap."""
        code = """
        fn get_user(users: &Vec<User>, id: u64) -> Option<&User> {
            users.iter().find(|u| u.id == id)
        }
        """
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze_collection_types(mock_skill_context, "lib.rs")
        assert len(result["collection_type_suggestions"]) >= 1

    # ── sql injection ─────────────────────────────────────────────

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_sql_format_interpolation(self, mock_skill_context) -> None:
        """Given format! with SQL keyword and {}, skill flags injection risk."""
        code = r"""
        fn get_user_query(name: &str) -> String {
            format!("SELECT * FROM users WHERE name = '{}'", name)
        }
        """
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze_sql_injection(mock_skill_context, "db.rs")
        assert "sql_injection_risks" in result
        assert len(result["sql_injection_risks"]) >= 1
        assert all(
            r["type"] == "sql_format_interpolation"
            for r in result["sql_injection_risks"]
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_sql_injection_parameterized_not_flagged(self, mock_skill_context) -> None:
        """Given parameterized queries, skill produces no findings."""
        code = """
        async fn get_user(pool: &PgPool, id: i64) {
            sqlx::query_as("SELECT * FROM users WHERE id = $1")
                .bind(id)
                .fetch_one(pool)
                .await
        }
        """
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze_sql_injection(mock_skill_context, "db.rs")
        assert result["sql_injection_risks"] == []

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_sql_injection_lowercase_keyword_detected(self, mock_skill_context) -> None:
        """Given lowercase SQL keywords in format!, skill still flags."""
        code = r"""
        fn query(user: &str) -> String {
            format!("select * from accounts where username = '{}'", user)
        }
        """
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze_sql_injection(mock_skill_context, "db.rs")
        assert len(result["sql_injection_risks"]) >= 1

    # ── cfg(test) misuse ──────────────────────────────────────────

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_cfg_test_on_standalone_fn(self, mock_skill_context) -> None:
        """Given #[cfg(test)] on a standalone fn, skill flags misuse."""
        code = """pub struct Validator;

#[cfg(test)]
fn test_helper() -> i32 { 42 }

impl Validator {
    pub fn validate(&self) -> bool { true }
}
"""
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze_cfg_test_misuse(mock_skill_context, "lib.rs")
        assert "cfg_test_misuse" in result
        assert len(result["cfg_test_misuse"]) >= 1
        assert all(
            m["type"] == "cfg_test_outside_mod" for m in result["cfg_test_misuse"]
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_cfg_test_inside_mod_tests_not_flagged(self, mock_skill_context) -> None:
        """Given #[cfg(test)] mod tests block, skill produces no findings."""
        code = """
pub fn add(a: i32, b: i32) -> i32 { a + b }

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_add() {
        assert_eq!(add(1, 2), 3);
    }
}
"""
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze_cfg_test_misuse(mock_skill_context, "lib.rs")
        assert result["cfg_test_misuse"] == []

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_cfg_test_on_impl_block(self, mock_skill_context) -> None:
        """Given #[cfg(test)] on an impl block outside mod tests, skill flags."""
        code = """pub struct Service;

#[cfg(test)]
impl Service {
    pub fn mock_method(&self) -> i32 { 0 }
}
"""
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze_cfg_test_misuse(mock_skill_context, "lib.rs")
        assert len(result["cfg_test_misuse"]) >= 1

    # ── error messages ────────────────────────────────────────────

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_short_error_messages(self, mock_skill_context) -> None:
        """Given short strings in Err/panic/expect, skill flags them."""
        code = """
        fn parse(s: &str) -> i32 {
            s.parse().expect("bad input")
        }

        fn only_positive(n: i32) {
            if n <= 0 {
                panic!("negative");
            }
        }
        """
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze_error_messages(mock_skill_context, "lib.rs")
        assert "poor_error_messages" in result
        assert len(result["poor_error_messages"]) >= 2
        assert all(
            m["type"] == "short_error_message" for m in result["poor_error_messages"]
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_long_error_messages_not_flagged(self, mock_skill_context) -> None:
        """Given descriptive error messages, skill produces no findings."""
        code = """
        fn parse(s: &str) -> i32 {
            s.parse().expect("expected a valid integer in the config field")
        }
        """
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze_error_messages(mock_skill_context, "lib.rs")
        assert result["poor_error_messages"] == []

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_short_err_string_detected(self, mock_skill_context) -> None:
        """Given Err with a short bare string literal, skill flags it."""
        code = """
        fn validate(n: i32) -> Result<(), &'static str> {
            if n < 0 { return Err("negative"); }
            Ok(())
        }
        """
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze_error_messages(mock_skill_context, "lib.rs")
        assert len(result["poor_error_messages"]) >= 1

    # ── duplicate validators ──────────────────────────────────────

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_duplicate_validator_functions(self, mock_skill_context) -> None:
        """Given 3+ validate_* functions, skill flags consolidation candidates."""
        code = """
        fn validate_email(s: &str) -> bool { s.contains('@') }
        fn validate_phone(s: &str) -> bool { s.len() >= 10 }
        fn validate_username(s: &str) -> bool { s.len() >= 3 }
        fn validate_password(s: &str) -> bool { s.len() >= 8 }
        """
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze_duplicate_validators(
            mock_skill_context, "validators.rs"
        )
        assert "duplicate_validators" in result
        assert "consolidation_candidates" in result
        assert len(result["duplicate_validators"]) == 4
        assert len(result["consolidation_candidates"]) >= 1
        candidate = result["consolidation_candidates"][0]
        assert candidate["prefix"] == "validate_"
        assert len(candidate["functions"]) == 4

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_two_validators_no_consolidation_candidate(
        self, mock_skill_context
    ) -> None:
        """Given only 2 validate_* functions, no consolidation candidate raised."""
        code = """
        fn validate_email(s: &str) -> bool { s.contains('@') }
        fn validate_phone(s: &str) -> bool { s.len() >= 10 }
        """
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze_duplicate_validators(
            mock_skill_context, "validators.rs"
        )
        assert len(result["duplicate_validators"]) == 2
        assert result["consolidation_candidates"] == []

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_mixed_prefix_validator_groups(self, mock_skill_context) -> None:
        """Given 3 check_* and 3 verify_* functions, both groups are candidates."""
        code = """
        fn check_age(n: u32) -> bool { n >= 18 }
        fn check_balance(n: i64) -> bool { n >= 0 }
        fn check_status(s: &str) -> bool { s == "active" }

        fn verify_signature(sig: &[u8]) -> bool { !sig.is_empty() }
        fn verify_timestamp(ts: u64) -> bool { ts > 0 }
        fn verify_nonce(n: u64) -> bool { n > 0 }
        """
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze_duplicate_validators(
            mock_skill_context, "validators.rs"
        )
        prefixes = {c["prefix"] for c in result["consolidation_candidates"]}
        assert "check_" in prefixes
        assert "verify_" in prefixes

    # ── prefer-builtins: conversion helpers ──────────────────────

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_parse_helper_as_fromstr(self, mock_skill_context) -> None:
        """Given fn parse_foo(s: &str), skill flags as FromStr candidate."""
        code = """
        struct Config { name: String }

        fn parse_config(s: &str) -> Config {
            Config { name: s.to_string() }
        }
        """
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze_builtin_preference(mock_skill_context, "config.rs")
        assert "builtin_preference_issues" in result
        issues = result["builtin_preference_issues"]
        assert len(issues) >= 1
        assert any("FromStr" in i["trait"] for i in issues)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_from_helper_as_from_trait(self, mock_skill_context) -> None:
        """Given fn foo_from_bar(), skill flags as From trait candidate."""
        code = """
        struct Foo { val: i32 }
        struct Bar { val: i32 }

        fn foo_from_bar(b: Bar) -> Foo {
            Foo { val: b.val }
        }
        """
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze_builtin_preference(mock_skill_context, "types.rs")
        issues = result["builtin_preference_issues"]
        assert len(issues) >= 1
        assert any("From" in i["trait"] for i in issues)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_to_method_as_into(self, mock_skill_context) -> None:
        """Given fn to_bar(&self), skill flags as Into/From candidate."""
        code = """
        struct Foo { val: i32 }

        impl Foo {
            fn to_bar(&self) -> Bar {
                Bar { val: self.val }
            }
        }
        """
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze_builtin_preference(mock_skill_context, "types.rs")
        issues = result["builtin_preference_issues"]
        assert len(issues) >= 1
        assert any("Into" in i["trait"] for i in issues)

    # ── prefer-builtins: standard traits ─────────────────────────

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_default_helper(self, mock_skill_context) -> None:
        """Given fn default_config() -> Config, skill flags as Default."""
        code = """
        struct Config { timeout: u64 }

        fn default_config() -> Config {
            Config { timeout: 30 }
        }
        """
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze_builtin_preference(mock_skill_context, "config.rs")
        issues = result["builtin_preference_issues"]
        assert len(issues) >= 1
        assert any("Default" in i["trait"] for i in issues)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_display_helper(self, mock_skill_context) -> None:
        """Given fn format_error(&e), skill flags as Display candidate."""
        code = """
        struct MyError { msg: String }

        fn format_error(e: &MyError) -> String {
            format!("Error: {}", e.msg)
        }
        """
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze_builtin_preference(mock_skill_context, "errors.rs")
        issues = result["builtin_preference_issues"]
        assert len(issues) >= 1
        assert any("Display" in i["trait"] for i in issues)

    # ── prefer-builtins: error conversions ───────────────────────

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_error_conversion_helper(self, mock_skill_context) -> None:
        """Given fn io_to_my_error(e), skill flags as From<Error>."""
        code = """
        struct MyError { inner: String }

        fn io_to_my_error(e: std::io::Error) -> MyError {
            MyError { inner: e.to_string() }
        }
        """
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze_builtin_preference(mock_skill_context, "errors.rs")
        issues = result["builtin_preference_issues"]
        assert len(issues) >= 1
        assert any("From<Error>" in i["trait"] for i in issues)

    # ── prefer-builtins: manual combinators ──────────────────────

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_manual_map_pattern(self, mock_skill_context) -> None:
        """Given match Some(x) => Some(f(x)), None => None, skill flags."""
        code = """
        fn transform(opt: Option<i32>) -> Option<String> {
            match opt {
                Some(x) => Some(x.to_string()),
                None => None,
            }
        }
        """
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze_builtin_preference(mock_skill_context, "lib.rs")
        issues = result["builtin_preference_issues"]
        assert len(issues) >= 1
        assert any(i.get("clippy_lint") == "clippy::manual_map" for i in issues)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_manual_unwrap_or(self, mock_skill_context) -> None:
        """Given match Some(x) => x, None => default, skill flags."""
        code = """
        fn get_or_default(opt: Option<i32>) -> i32 {
            match opt {
                Some(x) => x,
                None => 0,
            }
        }
        """
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze_builtin_preference(mock_skill_context, "lib.rs")
        issues = result["builtin_preference_issues"]
        assert len(issues) >= 1
        assert any("unwrap_or" in i.get("replacement", "") for i in issues)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_is_some_unwrap(self, mock_skill_context) -> None:
        """Given if x.is_some() { x.unwrap() }, skill flags."""
        code = """
        fn process(opt: Option<i32>) {
            if opt.is_some() {
                let val = opt.unwrap();
                println!("{}", val);
            }
        }
        """
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze_builtin_preference(mock_skill_context, "lib.rs")
        issues = result["builtin_preference_issues"]
        assert len(issues) >= 1

    # ── prefer-builtins: clippy lint references ───────────────────

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_clippy_lint_reference_included(self, mock_skill_context) -> None:
        """Given a manual_map finding, output includes clippy lint name."""
        code = """
        fn transform(opt: Option<i32>) -> Option<String> {
            match opt {
                Some(x) => Some(x.to_string()),
                None => None,
            }
        }
        """
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze_builtin_preference(mock_skill_context, "lib.rs")
        issues = result["builtin_preference_issues"]
        lint_issues = [i for i in issues if i.get("clippy_lint")]
        assert len(lint_issues) >= 1
        assert "clippy::" in lint_issues[0]["clippy_lint"]

    # ── prefer-builtins: false positive suppression ───────────────

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_builder_method_not_flagged(self, mock_skill_context) -> None:
        """Given fn with_timeout(self, t), skill produces no finding."""
        code = """
        struct Config { timeout: u64 }

        impl Config {
            fn with_timeout(self, t: u64) -> Self {
                Config { timeout: t }
            }
        }
        """
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze_builtin_preference(mock_skill_context, "config.rs")
        assert result["builtin_preference_issues"] == []

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_lossy_conversion_not_flagged(self, mock_skill_context) -> None:
        """Given fn to_lossy_ascii(), skill produces no finding."""
        code = """
        struct Text { data: Vec<u8> }

        impl Text {
            fn to_lossy_ascii(&self) -> String {
                String::from_utf8_lossy(&self.data).to_string()
            }
        }
        """
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze_builtin_preference(mock_skill_context, "text.rs")
        assert result["builtin_preference_issues"] == []

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_multi_param_conversion_not_flagged(self, mock_skill_context) -> None:
        """Given fn parse_with_options(s, opts), skill produces no finding."""
        code = """
        struct Config { name: String }
        struct ParseOptions { strict: bool }

        fn parse_config(s: &str, opts: &ParseOptions) -> Config {
            Config { name: s.to_string() }
        }
        """
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze_builtin_preference(mock_skill_context, "config.rs")
        assert result["builtin_preference_issues"] == []

    # ── boundary and gap tests ────────────────────────────────────

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_vec_position_as_set(self, mock_skill_context) -> None:
        """Given Vec.iter().position(), skill flags as set/map candidate."""
        code = """
        fn find_index(items: &Vec<String>, target: &str) -> Option<usize> {
            items.iter().position(|s| s == target)
        }
        """
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze_collection_types(mock_skill_context, "lookup.rs")
        issues = result["collection_type_suggestions"]
        assert len(issues) >= 1

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_error_message_boundary_20_chars_not_flagged(
        self, mock_skill_context
    ) -> None:
        """Given a 20-char error string, skill does not flag it."""
        code = """
        fn fail() -> Result<(), String> {
            Err("exactly twenty chars")
        }
        """
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze_error_messages(mock_skill_context, "err.rs")
        assert result["poor_error_messages"] == []

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_duplicate_validators_boundary_exactly_three(
        self, mock_skill_context
    ) -> None:
        """Given exactly 3 check_* fns, skill produces a consolidation candidate."""
        code = """
        fn check_alpha(v: &str) -> bool { !v.is_empty() }
        fn check_beta(v: &str) -> bool { v.len() > 3 }
        fn check_gamma(v: &str) -> bool { v.starts_with('x') }
        """
        mock_skill_context.get_file_content.return_value = code
        result = self.skill.analyze_duplicate_validators(
            mock_skill_context, "validators.rs"
        )
        assert len(result["consolidation_candidates"]) == 1
        assert result["consolidation_candidates"][0]["prefix"] == "check_"
