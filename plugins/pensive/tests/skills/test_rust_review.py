"""Test suite for RustReviewSkill.

This module has been split into focused sub-modules for maintainability:

- test_rust_review_safety.py          -- TestRustReviewSafety
                                         (unsafe code, ownership, data races,
                                         memory safety, panic propagation,
                                         async/await patterns)
- test_rust_review_build_reporting.py -- TestRustReviewBuildReporting
                                         (Cargo.toml dependencies, macros,
                                         traits, const generics, build
                                         optimization, security report,
                                         severity categorization,
                                         best practices)
- test_rust_review_patterns.py        -- TestRustReviewPatterns
                                         (silent returns, collection types,
                                         SQL injection, cfg(test) misuse,
                                         error messages, duplicate validators,
                                         builtin trait preference,
                                         boundary/gap tests)

All tests remain discoverable by pytest via the sub-modules above.
This file is retained for git blame continuity.
"""
