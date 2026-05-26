---
id: qa-testing-tiers
title: Seven-Tier QA Testing Taxonomy
maturity: evergreen
importance_score: 82
routing_type: meta
tags:
  - testing
  - quality-assurance
  - tool-selection
  - taxonomy
sources:
  - https://github.com/pytest-dev/pytest
  - https://vitest.dev/api/vi
  - https://testing-library.com/docs/guiding-principles/
  - https://github.com/testcontainers/testcontainers-java
  - https://github.com/microsoft/playwright
  - https://github.com/HypothesisWorks/hypothesis
  - https://github.com/stryker-mutator/stryker-js
  - https://github.com/labgrid-project/labgrid
related_artifacts:
  - github://athola/claude-night-market/issues/519
  - plugins/parseltongue/skills/python-testing/SKILL.md
  - plugins/pensive/skills/test-review/SKILL.md
discussion_url: https://github.com/athola/claude-night-market/discussions/520
discussion_number: 520
promoted_at: 2026-05-09T23:15:00Z
last_updated: 2026-05-09
---

## Synopsis

Seven testing tiers, each with a distinct purpose and a stable
tool taxonomy. This entry is a lookup table: given a question
("how do I verify behavior X?"), pick the tier, then pick the
language-appropriate tool from the per-tier table. The seven
tiers are not interchangeable, and the cost-per-test rises by
roughly an order of magnitude across the chain.

## The seven tiers

| Tier | Verifies | Cost | Stability |
|------|----------|------|-----------|
| Unit | One function/method in isolation | $ | High |
| Component | One sub-system with real internals, mocked deps | $$ | High |
| Integration | Real wiring of multiple modules/services | $$$ | Medium |
| E2E | Full stack from user input to user output | $$$$ | Low |
| Invariant | Universal properties over generated inputs | $$ | High |
| Mutation | Quality of the test suite itself | $$$ | High |
| Hardware | Behavior on physical devices | $$$$$ | Low |

## Per-tier tool maps

### Unit (function-level)

| Lang | Tool | Notable feature |
|------|------|-----------------|
| Python | pytest | fixtures, parametrize |
| JS/TS | vitest | `vi.fn` / `vi.spyOn` / `vi.mock` (taxonomy) |
| Go | `go test` | table-driven subtests (idiomatic) |
| Java | JUnit5 | `@ParameterizedTest`, lifecycle hooks |
| Rust | `cargo test` | doc tests, integration tests in `tests/` |

Pattern: AAA (Arrange-Act-Assert) is universal scaffolding.
Test-double taxonomy converges on five terms: dummy, fake,
stub, spy, mock. Coverage tiers from cheapest to strongest:
line, branch, mutation.

### Component (sub-system isolation)

| Stack | Tool | Boundary |
|-------|------|----------|
| React/Vue | Testing Library | DOM-observable behavior |
| Spring Boot | `@WebMvcTest` and `@MockBean` | web slice; persistence excluded |
| NestJS | Testing module | controller and DI graph |
| FastAPI | `TestClient` | router and deps; mocked I/O |
| Multi-stack | Playwright component | real browser, between unit and E2E |

Pattern: assert on user-observable behavior, not on instance
state. Snapshot/visual checks supplement DOM assertions; they
do not replace them.

### Integration (wiring of real modules)

| Concern | Tool |
|---------|------|
| Ephemeral databases | Testcontainers (JVM, Go, Node, Rust, Python, .NET) |
| HTTP boundary stubs | WireMock, MockServer |
| Consumer-driven contracts | Pact (multi-language) |
| Spring auto-config harness | PlaytikaOSS/testcontainers-spring-boot |

Pattern: per-class container lifecycle by default. Reuse is
experimental and trades isolation for speed. Per-test stub
reset is mandatory to prevent bleed-through.

### E2E (full stack)

| Surface | Default | Alternatives |
|---------|---------|--------------|
| Browser | Playwright | Cypress, Selenium, WebdriverIO |
| Mobile (cross-platform) | Maestro | Appium |
| Mobile (React Native) | Detox | Maestro |
| API functional | Bruno | Postman/Newman, Hurl |
| API load | k6 | Gatling, Locust |

Locator hierarchy (Playwright canon, applies broadly):
`getByRole` first, `getByLabel` second, `getByText` third,
`getByTestId` last. Test data is owned per-test for parallel
safety: create, run, clean up.

### Invariant (property-based)

| Lang | Tool | Stateful mode |
|------|------|---------------|
| Python | Hypothesis | `RuleBasedStateMachine` |
| JS/TS | fast-check | `fc.commands` |
| Rust | proptest | proptest-stateful |
| Haskell | QuickCheck | StateMachine |
| Scala | ScalaCheck | Stateful |
| C/C++ | libFuzzer and custom | structure-aware via FuzzedDataProvider |

Property catalog: round-trip, commutativity, idempotence,
oracle/model equivalence, metamorphic relations. Stateful
tests are the default for any system with mutable state.
Fuzzing is property testing with a coverage-guided generator,
not a separate discipline.

### Mutation (test-suite quality)

| Lang | Tool | Diff-scoped mode |
|------|------|------------------|
| JS/TS/.NET/Scala | Stryker | `--since:<commit>` (Stryker.NET), incremental (StrykerJS) |
| JVM | PIT | `--mutators` selection, history file |
| Python | mutmut | `mutate_only_covered_lines` |
| Python | cosmic-ray | session-resumable |
| C/C++ | mull | LLVM IR-level via libirm |
| Rust | cargo-mutants | PR-incremental, full-branch CI |

Standard mutator catalog: Conditional Boundary, Negate
Conditionals, Math/AOR, Increments, Void Method Call, Returns
family (Empty/False/True/Null/Primitive). Run diff-scoped on
PRs, full on nightly. Document a per-package mutation-score
threshold and an equivalent-mutant suppression file with
justifications. Do not chase 100%.

### Hardware (physical devices)

| Layer | Tool | Notes |
|-------|------|-------|
| Embedded unit | Unity / Ceedling (C) | xUnit-style; CMock for mocks |
| Embedded unit | Zephyr ztest | runs via Twister |
| Device orchestration | Twister (Zephyr) | hardware-map, fixture-based |
| Device orchestration | labgrid | Resource/Driver abstraction; pairs with pytest |
| Device farm CI | LAVA (Linaro) | OS image deploy, MultiNode jobs |
| Bench/manufacturing | OpenHTF | `plug` abstraction, measurements |
| Fault injection | FAIL\* | research-oriented, bare-metal |

Honest scope: open-source HIL is thin. Proprietary stacks
(NI VeriStand, dSPACE) own real-time signal-level simulation.
Reliability-style fault injection (sensor spoofing, dropped
packets, clock skew) has no consolidated framework; it is
hand-rolled per project. Calibration uncertainty is uncovered
in OSS; cite ISO/IEC 17025 and NIST traceability for
traceable rigs.

## Decision tree (which tier?)

```
Question to verify:
├── "Does this function return correct output?" → Unit
├── "Does this UI component behave correctly?" → Component
├── "Do these services wire up correctly?" → Integration
├── "Does the user flow work?" → E2E
├── "Do these properties hold for all inputs?" → Invariant
├── "Is my test suite catching real bugs?" → Mutation
└── "Does it work on the physical device?" → Hardware
```

## Cross-tier patterns

- **Test pyramid is one shape, not the only one.** Honeycomb
  (heavy on integration) and trophy (heavy on integration plus
  E2E) are alternatives that fit microservices and frontends
  better than the classic pyramid.
- **Mutation testing exposes assertion-free tests.** Coverage
  proves a line ran; mutation proves the test would fail if
  the line were wrong. They measure different things.
- **Property tests find shrinkable counterexamples.** When a
  property fails, the framework shrinks to a minimal failing
  input. This is why property tests pay back disproportionate
  bug-finding compared to example tests.
- **Component testing is real and underused.** The mid-tier
  between unit and integration catches bugs both miss (full
  rendering with real internal state, but mocked external
  collaborators).

## Open questions

- Which tier owns contract testing? Pact-style consumer-driven
  contracts sit between integration and E2E, closer to
  integration in cost but closer to E2E in semantics.
- Mutation testing is mature on JVM, JS, Python, Rust. C/C++
  is still bumpy (mull works but has fewer adopters than the
  others). Embedded mutation testing (mutmut on micropython,
  pitest on Java ME) is mostly unexplored.
- Hardware testing's "hand-rolled per project" status is a
  durable gap. A consolidating OSS framework would unlock the
  tier; meanwhile, the labgrid, pytest, and custom-fixtures
  stack is the working pattern.

## Application

Local codebase: this taxonomy informs `update-tests` skill
recommendations, the `pensive:test-review` rubric, and the
proposed `qa-tester` plugin (issue #519).

Meta-infrastructure: a future `qa-tester` plugin would
codify each tier as its own skill, with the hub picking the
tier given a question. See plugins/parseltongue/skills/
python-testing/ for the precedent pattern.

## Lineage

Synthesized 2026-05-09 from eight parallel research agents
(seven tome:code-searcher runs plus one architectural-precedent
scout) for issue #519. Sources are listed in the frontmatter
`sources` field; full per-tier evidence references live in
issue #519.
