"""The spoke-to-spoke check must not read fenced code blocks as references.

``_check_hub_spoke_pattern`` scans each module for mentions of its sibling
modules and reports any hit as a hub-spoke violation. It scanned the raw
file text, so a fenced block or an ASCII directory tree counted the same as
a live cross-link::

    ```
    modules/
    ├── authentication.md (300 lines)
    └── error-handling.md (200 lines)
    ```

That block is *documentation of the hub-spoke pattern itself*. The four
skills that explain modular authoring (skill-authoring, shared-patterns,
hooks-eval, skills-eval) were the heaviest offenders precisely because
they demonstrate the layout they teach: 69 of the validator's 80 findings
were this false positive.

The finding count stayed invisible because the validator printed its
issues and exited 0 until ``fix(gates): make quality gates able to fail``.
A gate nobody could fail is a gate nobody had to keep honest.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from abstract_validator import AbstractValidator

HUB = """---
name: demo-skill
description: Demo skill for hub-spoke checking
category: testing
---

## Overview

Demo hub.

## Quick Start

See `modules/alpha.md` and `modules/beta.md`.

## Detailed Resources

- Alpha: `modules/alpha.md`
- Beta: `modules/beta.md`
"""

# Mentions beta.md only inside a fenced block, as illustration.
ALPHA_ILLUSTRATIVE = """# Alpha

Explaining the layout this skill recommends:

```
modules/
├── alpha.md
└── beta.md
```

Nothing above is a link.
"""

# Mentions beta.md in live prose, outside any fence.
ALPHA_REAL_CROSSLINK = """# Alpha

For the rest, read `modules/beta.md`.
"""


def _build(tmp_path: Path, alpha_body: str) -> AbstractValidator:
    """Create a one-skill plugin tree with two modules."""
    skill = tmp_path / "skills" / "demo-skill"
    modules = skill / "modules"
    modules.mkdir(parents=True)
    (skill / "SKILL.md").write_text(HUB)
    (modules / "alpha.md").write_text(alpha_body)
    (modules / "beta.md").write_text("# Beta\n\nStandalone.\n")
    return AbstractValidator(tmp_path)


def _hub_spoke_issues(validator: AbstractValidator) -> list[str]:
    """Only the spoke-to-spoke findings, which is what this test pins."""
    return [i for i in validator._check_hub_spoke_pattern() if "hub-spoke" in i]


def test_fenced_block_mention_is_not_a_cross_reference(tmp_path: Path) -> None:
    """A module name inside a fence is illustration, not a link."""
    issues = _hub_spoke_issues(_build(tmp_path, ALPHA_ILLUSTRATIVE))
    assert not issues, (
        "A fenced code block demonstrating a modules/ layout was counted as a "
        "spoke-to-spoke reference:\n  " + "\n  ".join(issues)
    )


def test_real_cross_reference_is_still_reported(tmp_path: Path) -> None:
    """Stripping fences must not blind the check to genuine cross-links."""
    issues = _hub_spoke_issues(_build(tmp_path, ALPHA_REAL_CROSSLINK))
    assert issues, (
        "alpha.md points readers at modules/beta.md in live prose. That is the "
        "violation this check exists to catch, and it must survive the fix."
    )


# ---------------------------------------------------------------------------
# Quick Start / Resources ordering
#
# ``_check_progressive_disclosure`` located the Detailed Resources heading with
# ``content.find("## Detailed Resources") or content.find("## Resources")``.
# ``str.find`` returns -1 when the needle is absent, and -1 is truthy, so the
# ``or`` never reached its second branch and ``detailed_pos`` stayed -1. The
# guard below it then read ``if detailed_pos and quick_pos > detailed_pos``,
# which is ``-1 is truthy`` and ``any position > -1``: every skill using the
# plain ``## Resources`` heading was reported as mis-ordered no matter where
# its headings actually sat. modular-skills, rules-eval and skills-eval all
# order these correctly and all three were flagged.
# ---------------------------------------------------------------------------

ORDERED = """---
name: ordered-skill
description: Correctly ordered skill
category: testing
---

## Overview

Body.

## Quick Start

Do the thing.

## Resources

- More detail.
"""

MISORDERED = """---
name: misordered-skill
description: Incorrectly ordered skill
category: testing
---

## Overview

Body.

## Resources

- More detail.

## Quick Start

Do the thing.
"""


def _disclosure_issues(tmp_path: Path, content: str, name: str) -> list[str]:
    """Progressive-disclosure findings for a single skill body."""
    skill = tmp_path / "skills" / name
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(content)
    validator = AbstractValidator(tmp_path)
    return validator._check_progressive_disclosure(content, name)


def test_quick_start_before_resources_is_accepted(tmp_path: Path) -> None:
    """``## Resources`` after ``## Quick Start`` is the correct order."""
    issues = _disclosure_issues(tmp_path, ORDERED, "ordered-skill")
    assert not [i for i in issues if "Quick Start should come before" in i], (
        "Quick Start precedes Resources here, so no ordering issue should be "
        f"reported. Got: {issues}"
    )


def test_resources_before_quick_start_is_reported(tmp_path: Path) -> None:
    """The genuine mis-ordering must still be caught."""
    issues = _disclosure_issues(tmp_path, MISORDERED, "misordered-skill")
    assert [i for i in issues if "Quick Start should come before" in i], (
        f"Resources precedes Quick Start here and must be reported. Got: {issues}"
    )
