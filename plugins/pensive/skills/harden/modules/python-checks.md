# Python Hardening Checks

Detectors for Python codebases. Each row is a discrete check the
skill runs; each carries a CWE citation for the report.

The detection-signal column uses placeholder syntax for patterns
that the project's pre-commit security hooks block writing
literally. The hooks exist for a reason: this doc describes the
rules, but the regexes themselves live in code where the safety
review treats them as data, not source. If a future contributor
needs to inspect the literal patterns, see the corresponding
detector module under `plugins/pensive/skills/harden/detectors/`
(future work; not part of the v1 skill).

## Detection ruleset

| ID | Check | CWE | NIST SSDF | Detection signal |
|----|-------|-----|-----------|------------------|
| PY01 | Unsafe deserialization (the stdlib `pickle` family, `marshal`, `shelve`) | CWE-502 | PW.5.1 | `<unsafe-loader>.loads(` on bytes you do not control |
| PY02 | YAML loaded without a safe Loader | CWE-502 | PW.9 | `yaml.load(` without `Loader=SafeLoader` |
| PY03 | Code injection via `eval`/`exec`/`compile(...,'exec')` | CWE-94 | PW.5.1 | `<eval-family>(` with a non-constant argument |
| PY04 | Shell-command injection in a child-process call | CWE-78 | PW.5.1 | bandit B602 / B605: child-process helper invoked with the shell-mode flag and a formatted string |
| PY05 | SQL injection via string formatting | CWE-89 | PW.5.1 | `cursor.execute(f"...")` or `% ` formatting in a query |
| PY06 | Path traversal in user-supplied paths | CWE-22 | PW.5.1 | `open(user_input)` without `Path.resolve()` and `is_relative_to()` |
| PY07 | Insecure RNG used for security purposes | CWE-330 | PW.5.1 | `import random` then a token/secret/key generated from it; should be `secrets` |
| PY08 | TLS verification disabled | CWE-295 | PW.9 | `requests.*(verify=False)`, `ssl.CERT_NONE`, `disable_warnings(InsecureRequestWarning)` |
| PY09 | Hardcoded credentials | CWE-798 | PW.5.1 | regex match for `api[_-]?key`, `secret`, `token`, `passwd` literals; AWS prefixes (`AKIA...`) |
| PY10 | Subprocess invocation without timeout | CWE-400 | PW.5.1 | `<child-proc>.run/Popen` without `timeout=` |
| PY11 | Tarfile extraction without member filter | CWE-22 | PW.9 | `tarfile.*extractall(` without `filter=` (PEP 706; default became safe in 3.12+) |
| PY12 | XML XXE / billion-laughs | CWE-611, CWE-776 | PW.9 | `xml.etree.ElementTree.parse(` (use `defusedxml`) |
| PY13 | Jinja autoescape off in HTML context | CWE-79 | PW.9 | `Environment(autoescape=False)` or `Markup(user_input)` |
| PY14 | Logging secrets | CWE-532 | PW.5.1 | `logger.*(token)`, `logger.*(password)`, `logger.*(api_key)` |
| PY15 | Bare `except:` swallowing errors in security paths | CWE-754 | PW.7 | `except:` or `except Exception: pass` in auth or crypto paths |
| PY16 | Async TOCTOU (time-of-check / time-of-use) | CWE-367 | PW.5.1 | `await is_authorized(...)` then `await act(...)` without re-check |
| PY17 | Untrusted format string | CWE-134 | PW.5.1 | `(user_input).format(`, f-string built from user input, `"%" % user` |
| PY18 | Insecure temp file | CWE-377 | PW.5.1 | `tempfile.mktemp(` (use `mkstemp` or `NamedTemporaryFile`) |
| PY19 | `assert` for runtime auth check | CWE-617 | PW.5.1 | `assert user.is_admin` (assert is stripped under `python -O`) |
| PY20 | `requests` without timeout | CWE-400 | PW.5.1 | `requests.get/post(...)` without `timeout=` |
| PY21 | HTTP request smuggling on outdated frameworks | CWE-444 | RV.1 | `gunicorn<22.0.0` (CVE-2024-1135), `aiohttp<3.9.2` (CVE-2024-23829) |
| PY22 | Multipart resource exhaustion | CWE-400 | RV.1 | `python-multipart<0.0.18` (CVE-2024-47874); FastAPI route without `max_part_size` |
| PY23 | Weak hashing for passwords or auth tokens | CWE-327, CWE-328 | PW.5.1 | `hashlib.md5`, `hashlib.sha1` reachable from password / session-token paths |
| PY24 | Missing TLS 1.2 floor | CWE-326 | PW.9 | `ssl.PROTOCOL_TLSv1`, `PROTOCOL_SSLv23` without `minimum_version` |
| PY25 | Index pinning missing for PyPI consumption | CWE-829 | PW.4 | no `[[tool.uv.index]]` in `pyproject.toml`; no `--index-url` constraint in `requirements.txt` |
| PY26 | Hash-unpinned installs | CWE-494, NIST SI-7 | PW.4 | `requirements.txt` without `--hash=` lines; missing `uv.lock`/`poetry.lock` |
| PY27 | PyPI release without PEP 740 attestation | NIST SSDF PS.2.1 | PS.2 | release workflow uses static API token instead of `pypa/gh-action-pypi-publish@release/v1` (Trusted Publishers) |

## Library substitution table

When a finding fires, the proposal usually swaps the offending
library or call. The substitution table:

| Bad | Good | Why |
|-----|------|-----|
| the unsafe-deserialization stdlib family | `json` if data is JSON-shaped, otherwise `msgspec` / `pydantic` | safe-by-default deserialization |
| `yaml.load(...)` | `yaml.safe_load(...)` (or `ruamel.yaml.YAML(typ='safe')`) | rejects arbitrary tag construction |
| `eval`, `exec` | `ast.literal_eval` for constants; otherwise refactor to a typed parser | no code path executes user input |
| `random.{choice,token_bytes,...}` for security | `secrets.token_bytes/urlsafe`, `secrets.choice` | CSPRNG-backed |
| `xml.etree.ElementTree` on untrusted input | `defusedxml.ElementTree` | XXE / billion-laughs hardened |
| `urllib.request.urlopen` | `requests` (`timeout=`, `verify=True`) or `httpx` (defaults are safer) | timeout-by-default |
| `tempfile.mktemp` | `tempfile.NamedTemporaryFile(delete=False)` | atomic creation |
| `assert is_authorized()` | explicit `if not is_authorized(): raise PermissionError(...)` | survives `python -O` |
| `hashlib.md5/sha1` for passwords | `argon2-cffi`, `bcrypt`, or `passlib` | KDF with cost factor |
| static API tokens for PyPI | PyPI Trusted Publishers and sigstore attestation (PEP 740) | revocable, log-traceable, no shared secret |

## Static-analyzer integration

Run the canonical Python security tools and treat their findings
as first-class harden findings:

```bash
# Bandit ruleset (PyCQA-maintained AST scanner)
uv run bandit -r src/ -f json -o /tmp/harden-bandit.json

# pip-audit on the lockfile (PyPA + Trail of Bits, OSV-backed)
uv run pip-audit --lockfile uv.lock --format json > /tmp/harden-pipaudit.json

# osv-scanner reads pyproject + lockfiles + Cargo.lock
osv-scanner --format json . > /tmp/harden-osv.json

# semgrep with the security-audit ruleset
semgrep --config=p/python --json --output=/tmp/harden-semgrep.json
```

Findings from these tools convert to the harden schema by joining
on file:line and severity. A bandit B301 finding (the unsafe
deserialization rule) becomes the same finding shape as the
internal PY01 detector, so the report does not double-count.

## Frontier Python concerns (2025-2026)

Loaded from `frontier-checks.md` for full coverage. Brief list:

- PEP 740 sigstore attestations on PyPI (verify before install);
  see Trail of Bits' "Attestations: a new generation of
  signatures on PyPI" (Nov 2024).
- Tarfile member filter (PEP 706) — `tarfile.data_filter` default
  in Python 3.12+; verify the codebase does not still pass
  `filter=None`.
- pyproject.toml `[[tool.uv.index]]` priority pinning to defeat
  dependency confusion attacks.
- LLM SDK prompt-injection patterns and MCP server hardening
  (CWE-1426; OWASP LLM Top 10 #01, #02).
- ASGI middleware request smuggling (CVE-2024-23829 class).
- Sandboxing application code: WASM (Pyodide), gVisor, nsjail.
- Slopsquatting / package hallucination (arXiv 2406.10279):
  LLM-suggested non-existent packages later registered as
  malware. Mitigation: lockfile and `--require-hashes` and human
  review on every dep addition.

## Output schema

Each Python finding follows the schema in
`modules/proposal-shape.md`. The detection-signal text uses safe
placeholders so the doc itself does not trip secret-scanners or
the project's security pre-commit hooks; the actual scanner emits
the literal pattern with file:line context in the report.
