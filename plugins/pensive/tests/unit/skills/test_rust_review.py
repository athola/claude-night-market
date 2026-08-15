"""Content tests for rust-review skill modules.

Verifies that the production war-story patterns added in 2026-05
are present and correctly cross-referenced across modules:
  - mlock memory-pinning guidance in unsafe-audit.md
  - Kernel paging as Level 6 latency in concurrency-patterns.md
  - Box<dyn> dispatch overhead (Pattern E2) in iterator-and-allocation-slop.md
  - mlock checklist item in SKILL.md
"""

from __future__ import annotations

from pathlib import Path

import pytest

_MODULES = Path(__file__).parents[3] / "skills" / "rust-review" / "modules"
_SKILL = Path(__file__).parents[3] / "skills" / "rust-review" / "SKILL.md"


class TestMlockGuidance:
    """Feature: unsafe-audit module covers mlock production gotchas.

    As a Rust reviewer auditing unsafe libc::mlock calls,
    I need the unsafe-audit module to surface the four production
    pitfalls (RLIMIT, alignment, ENOMEM, lifetime),
    so that a review catches them without needing external references.
    """

    @pytest.fixture
    def module_content(self) -> str:
        return (_MODULES / "unsafe-audit.md").read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_rlimit_memlock_documented(self, module_content: str) -> None:
        """Given the mlock section
        Then it must document the RLIMIT_MEMLOCK requirement.
        """
        assert "RLIMIT_MEMLOCK" in module_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_page_alignment_documented(self, module_content: str) -> None:
        """Given the mlock section
        Then it must require page-aligned allocation.
        """
        assert "page-align" in module_content or "posix_memalign" in module_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_enomem_fallback_documented(self, module_content: str) -> None:
        """Given the mlock section
        Then it must specify ENOMEM as a recoverable error with fallback.
        """
        assert "ENOMEM" in module_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_lifetime_coupling_documented(self, module_content: str) -> None:
        """Given the mlock section
        Then it must document the buffer-lifetime / munlock coupling.
        """
        assert "munlock" in module_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_symptom_described(self, module_content: str) -> None:
        """Given a reviewer who has not seen this bug before
        Then the section must describe the production symptom
        so it is recognisable without prior experience.
        """
        # The key symptom: tokio-console doesn't help; kernel paging is the cause
        assert "tokio-console" in module_content or "page" in module_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_safety_comment_example_present(self, module_content: str) -> None:
        """Given the module requires SAFETY comments on mlock call sites
        Then a concrete example comment must exist.
        """
        assert "SAFETY:" in module_content


class TestKernelPagingLatencyTier:
    """Feature: concurrency-patterns module includes Level 6 kernel paging.

    As a Rust reviewer analysing real-time Tokio pipelines,
    I need the cost hierarchy to include kernel page faults
    so that production-only latency spikes are classifiable
    using the same framework as concurrency costs.
    """

    @pytest.fixture
    def module_content(self) -> str:
        return (_MODULES / "concurrency-patterns.md").read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_level_6_present_in_hierarchy(self, module_content: str) -> None:
        """Given the cost hierarchy table
        Then Level 6 must be a row.
        """
        assert "| 6 |" in module_content or "Level 6" in module_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_kernel_page_fault_named(self, module_content: str) -> None:
        """Given Level 6
        Then it must be identified as a kernel page fault.
        """
        assert (
            "page fault" in module_content.lower()
            or "page-fault" in module_content.lower()
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_tokio_console_blind_spot_noted(self, module_content: str) -> None:
        """Given the diagnostic guidance
        Then it must note that tokio-console misses this latency tier.
        """
        assert "tokio-console" in module_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_mlock_cross_reference_present(self, module_content: str) -> None:
        """Given the fix is mlock
        Then the module must cross-reference the unsafe-audit module.
        """
        assert "unsafe-audit" in module_content


class TestBoxDynDispatchPattern:
    """Feature: iterator-and-allocation-slop covers Box<dyn> hot-loop overhead.

    As a Rust reviewer auditing performance-sensitive code,
    I need Pattern E2 to explain that dyn dispatch is an inlining
    barrier independent of heap allocation,
    so that JVM-background developers understand the difference.
    """

    @pytest.fixture
    def module_content(self) -> str:
        return (_MODULES / "iterator-and-allocation-slop.md").read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_pattern_e2_present(self, module_content: str) -> None:
        """Given the allocation slop module
        Then Pattern E2 must exist.
        """
        assert "E2" in module_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_vtable_overhead_explained(self, module_content: str) -> None:
        """Given Pattern E2
        Then it must explain the vtable / inlining-barrier mechanism.
        """
        assert "vtable" in module_content or "inlining barrier" in module_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_dispatch_vs_allocation_distinguished(self, module_content: str) -> None:
        """Given the key lesson that &dyn has the same overhead as Box<dyn>
        Then the module must state this distinction explicitly.
        """
        assert "&dyn" in module_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_batch_first_fix_documented(self, module_content: str) -> None:
        """Given the recommended fix is to flip the loop order
        Then the module must describe the batch-first pattern.
        """
        assert "batch" in module_content.lower() or "flip" in module_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_enum_dispatch_fix_documented(self, module_content: str) -> None:
        """Given enum dispatch is an alternative fix
        Then the module must mention it.
        """
        assert "enum" in module_content.lower() and "dispatch" in module_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detection_command_present(self, module_content: str) -> None:
        """Given reviewers need a grep/rg command to find the pattern
        Then a detection command must be present.
        """
        assert "Vec<Box<dyn" in module_content


class TestSkillChecklistMlock:
    """Feature: SKILL.md safety checklist includes mlock item.

    As a reviewer running the Rust review workflow,
    I need the quick checklist in SKILL.md to include the mlock
    verification item so that it surfaces in every audit pass,
    not only when the reviewer remembers to load unsafe-audit.md.
    """

    @pytest.fixture
    def skill_content(self) -> str:
        return _SKILL.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_mlock_in_safety_checklist(self, skill_content: str) -> None:
        """Given the Safety checklist in SKILL.md
        Then it must include an mlock/munlock item.
        """
        assert "mlock" in skill_content
