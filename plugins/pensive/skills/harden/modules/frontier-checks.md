# Frontier Hardening Checks (2025-2026)

Forward-facing checks that defend against threats just emerging
in production. Findings here are usually MEDIUM by default
because exploitation is non-trivial; promote to HIGH when the
codebase has a high-value attack surface (auth provider, signing
service, data plane).

## Post-quantum migration readiness

The NSA CNSA 2.0 timeline targets quantum-resistant crypto for
NSS by 2030; PCI DSS 4.0.1 expects an inventory by 2026. Most
application code is not the right place to swap algorithms, but
the *crypto-agility* posture is.

| ID | Check | Citation | Detection |
|----|-------|----------|-----------|
| PQ01 | Signing/verification has a single hard-coded algorithm | NIST IR 8547 | `algorithms = ["RS256"]` or `algorithms = ["EdDSA"]` literal in JWT/JWS code |
| PQ02 | Algorithm selection driven by config, not code | NIST IR 8547 | move the algorithm list behind a `signing_algorithms` config field |
| PQ03 | Inventory of crypto APIs in the repo | NIST CNSA 2.0 | no `docs/crypto-inventory.md` or equivalent |
| PQ04 | TLS clients accept algorithm downgrade silently | CWE-757 | `requests` / `reqwest` defaults without minimum-TLS pin |

The proposal for PQ02 is usually a small refactor: move
`algorithms = ["EdDSA"]` into a config table the operator can
override. The skill does not propose ML-DSA / Falcon migration
in application code (still specialist work).

## LLM and agentic supply chain

A new failure mode in 2025: AI assistants suggest dependencies
that look plausible but do not exist (or are typosquats). The
checks below defend the development pipeline itself.

| ID | Check | Citation | Detection |
|----|-------|----------|-----------|
| LLM01 | Index pinning to defeat dependency confusion | OWASP LLM Top 10 #08 | `pyproject.toml` lacks `[[tool.uv.index]]` priority order |
| LLM02 | New deps require human review | OWASP LLM Top 10 #08 | no CI rule blocking auto-merge on dep PRs |
| LLM03 | LLM SDK calls validate role/instruction boundaries | OWASP LLM Top 10 #01 | system prompt concatenated with user input without separator/role |
| LLM04 | Tool-use response sanitization | OWASP LLM Top 10 #02 | tool output rendered to UI/terminal without escape |
| LLM05 | MCP server allowlist of tools | OWASP LLM Top 10 #02 | MCP config mounts every tool from a server (no allowlist) |
| LLM06 | Agent action audit trail | OWASP LLM Top 10 #06 | no log of tool invocations with inputs |

## Sandbox / isolation posture

For codebases that execute user-supplied or AI-supplied code:

| ID | Check | Why | Today's option |
|----|-------|-----|----------------|
| SB01 | User code runs in same process as host | host privilege escalation | Pyodide WASM (Python), wasmtime (Rust) |
| SB02 | Network egress unrestricted from sandbox | data exfiltration | gVisor egress policy, NetworkPolicy in K8s |
| SB03 | Filesystem capabilities ambient | path-based attacks | `cap-std` (Rust), bind-mount only required dirs |
| SB04 | Resource limits absent | DoS via runaway workload | cgroup `memory.max`, `cpu.max`; `prlimit` in containers |

## eBPF / runtime security hooks

Production codebases benefit from runtime monitoring even when
the static defenses are good. The skill flags absence:

| ID | Check | Tool | What it catches |
|----|-------|------|-----------------|
| RT01 | Runtime detection layer present | Falco / Tetragon / Tracee | unexpected syscalls, container escapes |
| RT02 | App emits structured audit events | OpenTelemetry traces with semantic conventions | post-incident reconstruction |
| RT03 | Deployment includes seccomp/apparmor profile | runtime config | exploit blast-radius capping |

## Differential-privacy / PETs awareness

For codebases that handle aggregable user data (analytics, ML
training, telemetry):

| ID | Check | Citation | Signal |
|----|-------|----------|--------|
| DP01 | Aggregations expose per-user values without noise | NIST SP 800-188 | counts/means published without DP budget |
| DP02 | Logs retain raw PII beyond retention window | GDPR Art. 5 | log retention config absent or > 30 days for PII fields |

## Memory-safety migration triage (when C/C++ is present)

Per CISA's "Secure by Design" pledge and the ONCD memory-safety
report (Feb 2024), new code in safety-critical contexts should
be in a memory-safe language by default. The skill flags the
opportunity, not the migration:

| ID | Check | Signal | Proposal |
|----|-------|--------|----------|
| MS01 | C/C++ code paths handle untrusted input | parser, network code in C/C++ | rewrite or wrap behind a Rust shim |
| MS02 | C-style string handling | `strcpy`, `sprintf`, `gets` | move to Rust or use `safestr`/`absl::Cord` |

## Output

Findings here use the same schema as the other modules. Severity
is **MEDIUM** by default; promote to HIGH when:

- The repo is an auth/signing/credentialing service (PQ findings)
- The repo ships an MCP server or agent harness (LLM findings)
- The repo has untrusted-code-exec posture (SB findings)
- The repo handles regulated PII (DP findings)
