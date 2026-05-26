# NIST and CWE Citation Backbone

Every finding in a hardening report carries a citation. This
module is the lookup table.

## NIST SSDF (SP 800-218) practice mapping

The Secure Software Development Framework defines four practice
groups: Prepare the Organization (PO), Protect Software (PS),
Produce Well-Secured Software (PW), Respond to Vulnerabilities
(RV). Findings map to PW and RV most often.

| Practice | What it requires | Detector signal |
|----------|------------------|-----------------|
| PW.4 | Reuse existing well-secured software | dependencies pinned, scanned, attested |
| PW.5 | Create source code aligned with secure practices | linter enforces auth/crypto/serialization rules |
| PW.6 | Configure compilation, build processes, links | RUSTFLAGS hardening, Python `-W error`, reproducible builds |
| PW.7 | Review and analyze human-readable code | SAST run in CI; findings tracked |
| PW.8 | Test executable code | fuzz coverage, mutation tests, property tests |
| PW.9 | Configure software with secure default settings | yaml SafeLoader, TLS verify on, autoescape on |
| RV.1 | Identify, confirm vulnerabilities on a continuous basis | dependency scanner runs on every push |
| RV.2 | Assess, prioritize, remediate vulnerabilities | severity policy, SLA per severity |
| RV.3 | Analyze vulnerabilities to identify root causes | post-incident notes feed PW.4-9 |

The skill's executive summary lists each practice and whether the
codebase has at least one detector firing for it. Coverage <80%
of PW.4-PW.9 is itself a finding (RV.1 unmet).

## CWE Top 25 (2024) mapping

The skill prioritizes detectors that map to the CWE Top 25 most
dangerous software weaknesses. Per-finding citations name the
specific CWE, not just "Top 25."

| CWE | Title | Languages most often hit |
|-----|-------|--------------------------|
| CWE-79 | Cross-site Scripting | Python, JS |
| CWE-787 | Out-of-bounds Write | Rust unsafe, C/C++ FFI |
| CWE-89 | SQL Injection | Python, Rust |
| CWE-352 | CSRF | Python web frameworks |
| CWE-22 | Path Traversal | All |
| CWE-125 | Out-of-bounds Read | Rust unsafe, C/C++ FFI |
| CWE-78 | OS Command Injection | Python (subprocess), shell scripts |
| CWE-416 | Use After Free | Rust unsafe, C/C++ |
| CWE-862 | Missing Authorization | Web layer |
| CWE-434 | Unrestricted File Upload | Web layer |
| CWE-94 | Code Injection | Python (eval/exec), template engines |
| CWE-20 | Improper Input Validation | All |
| CWE-77 | Command Injection | All shell-out paths |
| CWE-287 | Improper Authentication | Auth layer |
| CWE-269 | Improper Privilege Management | Container, sudo |
| CWE-502 | Deserialization of Untrusted Data | Python, Java |
| CWE-200 | Exposure of Sensitive Information | Logs, errors, telemetry |
| CWE-863 | Incorrect Authorization | Web layer |
| CWE-918 | Server-Side Request Forgery | URL fetchers |
| CWE-119 | Improper Restriction of Operations within Memory Buffer | Rust unsafe, C/C++ |
| CWE-476 | NULL Pointer Dereference | Rust unsafe, C/C++ |
| CWE-798 | Use of Hard-coded Credentials | All |
| CWE-190 | Integer Overflow or Wraparound | All |
| CWE-400 | Uncontrolled Resource Consumption | All |
| CWE-306 | Missing Authentication for Critical Function | Web/API layer |

## OWASP ASVS level targets

Findings track the ASVS level they aim at:

| Level | Target | Skill default |
|-------|--------|---------------|
| L1 | Opportunistic attacker | always |
| L2 | Targeted attacker | when secrets-bearing config detected |
| L3 | Determined attacker | only on `--focus all` with `--strict` |

## RustSec advisory database

For Rust findings, cite the specific advisory ID
(RUSTSEC-YYYY-NNNN). The `cargo audit` JSON output contains
these directly. Use them in the proposal's reversal plan to
explain *why* the upgrade is required.

## How findings cite

Each finding's `Citation:` line names:

1. Primary CWE (always)
2. NIST SSDF practice (always; pick the closest match)
3. Optional: OWASP ASVS section, RustSec ID, PEP number, CVE

Example:

```
Citation: CWE-502 (Deserialization of Untrusted Data),
NIST SSDF PW.7 (Review and analyze human-readable code),
OWASP ASVS V5.5 (Deserialization Prevention).
```

A finding with no primary CWE cannot be classified above
ADVISORY severity.
