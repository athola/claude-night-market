---
module: empirical-baseline
category: reference
dependencies: [Read]
estimated_tokens: 600
---

# Empirical Baseline (2025-Q1 2026)

**Treat AI-generated artifacts as unreviewed contractor
work, not as junior-developer work.** The cross-study
record is unambiguous about which defect classes occur at
which rates; calibrate the cleanup priorities accordingly.

This module is reference material. Cite from it when a
finding's severity needs justification. Re-validate the
numbers every six months: the empirical landscape moves
fast.

## Headline ratios (CodeRabbit, December 2025)

Analysis of 470 GitHub PRs (320 AI-co-authored, 150
human-only), normalized to issues per 100 PRs with
Poisson rate ratios.

| Defect class | AI vs. human multiplier |
|---|---|
| Total issues | ~1.7x |
| Critical issues | ~1.4x |
| Logic / correctness | 1.75x |
| Algorithm + business logic errors | >2x |
| Error handling gaps | ~2x |
| Code readability | >3x |
| Naming inconsistency | ~2x |
| Improper password handling | ~2x |
| Insecure object references | ~2x |
| Cross-site scripting (XSS) | 2.74x |
| Insecure deserialization | ~1.8x |
| Excessive I/O operations | ~8x |

**Cleanup priority implication:** weight logic/correctness,
error-handling gaps, readability/naming, and excessive I/O
checks more heavily than the average linter would. These
are the categories where AI-amplified rates are highest.

## Quality and maintainability data

From GitClear's analysis of 211M changed lines, 2020-2024:

- **Code duplication**: 5+-line duplicated blocks grew
  ~8x. In 2024, copy-pasted lines exceeded refactored
  (moved) lines for the first time on record.
- **Code churn**: code reverted or rewritten within two
  weeks rose from a 3.1-3.3% baseline (2021) to 5.7-7.9%
  (2024-2025).
- **Refactoring rate**: cleanup-of-existing-code as a
  share of changed lines collapsed from ~25% (2021) to
  <10% (2024). AI accelerates "add new" while suppressing
  "improve existing."

From METR's July 2025 randomized controlled trial on 16
experienced OSS contributors:

- Developers expected a 24% speedup.
- Developers reported feeling 20% faster.
- Developers were measurably **19% slower**.

**Cleanup-phase implication**: when an AI agent (or a
human + AI) reports that a module has been cleaned up, do
not trust the felt-productivity report. Verify with
external metrics: lint counts, defect counts, test pass
rates, mutation kill rates.

## Maintainability dominates correctness

From Sonar's December 2025 leaderboard analysis across
GPT-5.2 High, GPT-5.1 High, Gemini 3 Pro, Opus 4.5
Thinking, and Claude Sonnet 4.5:

- 92-96% of detected issues across all models are "code
  smells" (maintainability), not correctness.

**Implication**: the cleanup payoff is heaviest in
readability, structure, and dead-code removal: not in
correctness fixes. Optimize the slop-detector for those
categories.

## Model-specific failure patterns

From Sonar's evaluation work, also Q4 2025:

| Model | Distinctive failure mode |
|---|---|
| GPT-5.2 High | ~470 concurrency issues per MLOC (2x next-closest, 6x Gemini 3 Pro). Expect Send/Sync mistakes, MutexGuard-across-await, broken channel patterns. |
| Claude Sonnet 4.5 | ~195 resource-management leaks per MLOC (~4x GPT-5.1). 198 blocker-severity vulns per MLOC (vs 44 for Opus 4.5 Thinking). Expect file/socket lifetime mistakes, missed Drop ordering, path-traversal-class flaws. |
| Gemini 3 Pro | ~200 control-flow mistakes per MLOC, ~4x Opus 4.5 Thinking. Expect incorrect match arms, off-by-one loops, missed early returns. |
| Opus 4.5 Thinking | Best on security (44 blocker vulns/MLOC) but tends toward verbose, abstraction-heavy code. |

**General correlation Sonar identified**: as models reason
harder ("Thinking" / "High"), outputs grow more verbose
and more cyclomatically complex. The cleanup burden
scales with reasoning depth, not just code volume.

## Hallucination patterns by model family

From cross-evaluation work (Anthropic + DEV.to community
benchmarks, Q1 2026):

| Family | Tendency |
|---|---|
| GPT-5.x | **Fabricates**: invents function names, library methods, config keys, API endpoints that look plausible but do not exist. Verify every `use`/`import`, every dep, every method, every config flag. |
| Claude 4.x | **Omits**: silently skips edge cases, drops a match arm, leaves None-paths unhandled. Errors of omission are easier to find in review than confident fabrications, but more likely to slip through tests that mirror the implementation. |
| Both | Produce plausible doc comments that paraphrase the function name without adding information. |

**Implication for the slop-detector audit**:

- For Claude-generated code: weight toward incomplete
  match arms, missing error paths, skipped edge cases.
- For GPT-generated code: weight toward fabricated
  identifiers, made-up clippy/lint names, hallucinated
  crate/package names, and concurrency mistakes.

If you cannot tell which model generated a region, run
the full audit. It is never wrong, just sometimes
redundant.

## Security baseline

From Veracode's 2025 GenAI Code Security Report,
re-tested March 2026:

- **45%** of AI-generated code samples on
  security-sensitive tasks fail OWASP Top 10 tests.
- **86%** failed XSS-defense tasks.
- **88%** failed log-injection defense.
- The pass rate has not improved across multiple testing
  cycles.

From Apiiro's Fortune-50 enterprise study (Dec 2024 -
Jun 2025):

- AI-assisted developers commit code at **3-4x** their
  non-AI peer rate.
- Their monthly *security findings* rose **~10x**.
- A **153% increase** in design-level security flaws
  specifically (auth bypasses, IDOR, missing
  trust-boundary validation, broken session management)
 flaws line-level patches cannot fix.

From Trend Micro's TrendAI report (March 2026):

- AI-related CVEs reached **4.42% of all CVEs in 2025**
  (up 34.6% YoY).
- 2,130 AI CVEs disclosed in 2025 alone.
- 26.2% of scored AI CVEs are high-severity.
- Includes the **slopsquatting** attack class: adversaries
  registering hallucinated package names that AI tools
  recommend.

**Implication**: the slop-detector should treat unverified
package recommendations as critical findings (see
`hallucination-detection.md` Class 2).

## What this baseline does *not* mean

These are important so the data does not produce its own
bad cleanup decisions:

1. **It does not mean AI code is always worse than human
   code.** GitClear's January 2026 follow-up using direct
   API integration found a substantial productivity
   multiplier for "Power Users" of AI tools. The
   defect/duplication problem is real *and* the
   productivity gain is real; both can be true.
2. **It does not mean ban AI tooling.** It means: spend
   the saved time on review, not on accepting more PRs.
3. **It does not validate prose-level "AI tells" as proof
   of authorship.** Em-dash density, vocabulary
   clustering, and similar surface signals are *triage
   hints*, not evidence. Do not gate human work on them.
   Do not accuse contributors based on them.
4. **It does not justify aggressive over-cleanup.** See
   `anti-goals.md`. The slop-detector is a tool for
   reviewers, not a hammer for autonomous agents.

## Currency note

Model behavior changes faster than these notes can. The
specific multipliers above will be wrong in 12 months.
The *pattern*. AI artifacts have predictable defect
profiles that differ by family and by reasoning depth —
will persist.

Re-validate the model-specific numbers every six months
against:

- Sonar's live LLM leaderboard
- The latest CodeRabbit / Apiiro / Veracode quarterly
  reports
- Your own internal defect data, if you track it

The goal of this module is not to memorize numbers. It is
to give the slop-detector and its users a defensible
posture: *informed skepticism*, calibrated to data, not
performative caution.

## Sources for citation

When a slop-detector finding needs justification, cite
from:

- **CodeRabbit, *State of AI vs Human Code Generation***
  (Dec 17, 2025): ratios.
- **GitClear, *AI Copilot Code Quality: 2025 Data*** (2025):
  duplication, churn, refactoring rate.
- **METR**, arXiv:2507.09089 (July 2025): productivity
  perception vs. reality.
- **Sonar LLM leaderboard** (live, Q4 2025+): model-specific
  failure modes.
- **Apiiro, *4× Velocity, 10× Vulnerabilities*** (June 2025):
  security findings rate.
- **Veracode, *2025 GenAI Code Security Report*** (Aug 2025,
  March 2026 update): OWASP fail rates.
- **Trend Micro, *TrendAI 2025*** (March 2026): CVE share,
  slopsquatting.
- **AI Code in the Wild**, arXiv:2512.18567 (Dec 2025):
  repository-scale empirical study.
- **Antislop**, arXiv:2510.15061 (Oct 2025, ICLR 2026): most
  rigorous current paper on prose slop.
