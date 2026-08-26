---
name: harden
description: Active security hardening of the existing codebase, with a report and concrete proposals to apply.
---

# Harden Codebase Command

Active security hardening for the existing codebase, paired with a
report and concrete proposals you can apply. Complements the
Claude Code built-in `/security-review` (which scans pending diff)
by scanning the whole repository against citation-backed checks
from NIST SSDF, CWE Top 25, and language-specific frontier
practices for Python and Rust.

## Usage

```bash
# Default: full codebase, report + interactive proposals
/harden

# Narrow to a focus area
/harden --focus python
/harden --focus rust
/harden --focus deps
/harden --focus secrets
/harden --focus ci
/harden --focus hooks
/harden --focus all

# Read-only report; no proposals applied
/harden --report-only

# Apply approved proposals without prompting per-file
/harden --auto-apply minor

# File GitHub issues for findings above a severity
/harden --file-issues high

# Dry-run: produce the report without writing anything
/harden --dry-run

# Restrict to one tier of audit depth
/harden --tier 1   # git-history triage only
/harden --tier 2   # targeted areas
/harden --tier 3   # full codebase
```

## What It Does

1. **Discovery.** Detects languages, build files, CI workflows,
   hooks, and secret-bearing config in the repo.
2. **Citation-backed scan.** Runs the `pensive:harden` skill,
   which composes existing skills:
   - `pensive:rust-review` for deep Rust audits
   - `leyline:supply-chain-advisory` for dependency posture
   - `leyline:authentication-patterns` for auth/credential review
   - `leyline:content-sanitization` for input handling
   - `abstract:hook-authoring` for hook-security checks
   - `pensive:safety-critical-patterns` for NASA Power-of-10
   - `pensive:tiered-audit` for tier discipline
3. **Findings classification.** Each finding ships with a
   severity, a CWE/NIST citation, the detection signal in code,
   and a concrete proposed remediation.
4. **Active hardening proposals.** For approved findings, the
   command proposes a specific diff or config change with a
   blast-radius assessment (per `pensive:blast-radius`).
5. **Approval gate.** You decide per-finding: apply, file as
   issue, defer to backlog, or reject.
6. **Validation.** After applying, re-runs gates (tests, lint,
   type-check) to confirm no behavior change.
7. **Report.** Markdown report saved to
   `reviews/harden-<date>.md`; summary posted to GitHub
   Discussions via `abstract:post_review_insights` when run on a
   PR.

## Scope

- **Python** (frontier 2025-2026): unsafe-deserialization
  alternatives, tarfile member filter (PEP 706), pip-audit /
  osv-scanner, typosquatting and dependency confusion defenses,
  PEP 740 sigstore attestations, async TOCTOU patterns, MCP
  server hardening, prompt-injection patterns in LLM SDK
  clients.
- **Rust** (frontier 2025-2026): `cargo-audit` / `cargo-deny` /
  `cargo-vet` / `cargo-supply-chain`, `#![forbid(unsafe_code)]`
  coverage, `subtle` and `zeroize` for sensitive-data paths,
  `loom` model-checking opportunities, RustSec advisories.
- **Cross-cutting**: SLSA build-level posture, SBOM generation
  (CycloneDX/SPDX), gitleaks/trufflehog secret scanning,
  pre-commit security hooks, container hardening when
  Dockerfiles are present.
- **CI/CD**: GitHub Actions pinned-by-SHA discipline, OIDC
  publishing, restricted token scopes.
- **Hooks**: Claude Code hook-event security per
  `abstract:hook-authoring`.

## Out of Scope

- Pending-diff review (use Claude Code built-in `/security-review`).
- Architecture-level threat modeling (use a war-room session
  via `attune:war-room`).
- Cryptographic protocol review (specialist work; the skill flags
  but does not propose crypto fixes).

## Output

- `reviews/harden-<date>.md`: full markdown report with
  findings table, citation column, and per-finding proposal.
- Optional GitHub issues for findings above the chosen severity.
- Applied diffs as discrete commits per finding (one finding =
  one commit, so revert is per-finding).

## See Also

- `Skill(pensive:harden)`: the skill this command invokes
- `pensive:rust-review`, `pensive:bug-review`,
  `pensive:safety-critical-patterns` (composed)
- `leyline:supply-chain-advisory`,
  `leyline:authentication-patterns`,
  `leyline:content-sanitization` (composed)
- Built-in `/security-review`: pending-diff scanner (different
  scope)
