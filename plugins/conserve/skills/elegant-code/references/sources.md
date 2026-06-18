# Sources

Evidence behind the `elegant-code` skill. Gathered via `tome:research`
(code, discourse, and academic channels) while porting the beneficial
ideas from [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail).

## Additive bias has a mechanism

- Adams et al., "People systematically overlook subtractive changes,"
  *Nature* 2021. https://www.nature.com/articles/s41586-021-03380-y
- "More is More: Addition Bias in Large Language Models," arXiv
  2409.02569. https://arxiv.org/abs/2409.02569
- "Loose lips sink ships: Mitigating Length Bias in RLHF," arXiv
  2310.05199 (reward models over-reward length).
  https://arxiv.org/abs/2310.05199

## Iteration is not free

- "Security Degradation in Iterative AI Code Generation," arXiv
  2506.11022 (+37.6% critical vulnerabilities after five refinement
  rounds). https://arxiv.org/abs/2506.11022

## Rung 4: package hallucination and slopsquatting

- "We Have a Package for You! ... Package Hallucinations by Code
  Generating LLMs," USENIX Security 2025, arXiv 2406.10279
  (5.2% commercial to 21.7% open-source fabricated imports).
  https://arxiv.org/abs/2406.10279
- "Importing Phantoms: Measuring LLM Package Hallucination
  Vulnerabilities," arXiv 2501.19012.
  https://arxiv.org/abs/2501.19012

## The negligence floor (omission is the real failure mode)

- Veracode 2025 GenAI Code Security Report (~45% of AI code carries a
  flaw). https://www.veracode.com/resources/analyst-reports/2025-genai-code-security-report/
- AI code ~2.74x vulnerability rate versus human code.
  https://www.softwareseni.com/ai-generated-code-security-risks-why-vulnerabilities-increase-2-74x-and-how-to-prevent-them/
- CVE-2025-48757: generated schemas shipped without row-level
  security policies (missing-by-default authorization).
- "Investigating The Smells of LLM Generated Code," arXiv 2510.03029
  (~63% more code smells than human reference solutions).
  https://arxiv.org/abs/2510.03029

## Why not "fewer lines means fewer bugs" (honest disclaimer)

The complexity-to-defect law is contested. The skill argues from
attack surface and review cost instead.

- "An Empirical Investigation of Correlation between Code Complexity
  and Bugs," arXiv 1912.01142 (no strong correlation).
  https://arxiv.org/abs/1912.01142
- "Defect patterns and software metric correlations in a mature
  ubiquitous system," arXiv 1912.04014 (no support for the folklore).
  https://arxiv.org/abs/1912.04014

## Elegance is clarity, not terseness

- "Beyond Correctness: Benchmarking Multi-dimensional Code
  Generation" (RACE), arXiv 2407.11470 (correctness-only evaluation
  misses readability, maintainability, and efficiency cost).
  https://arxiv.org/abs/2407.11470

## Dependency minimalism is "right-size," not "fewer always"

- Russ Cox, "Our Software Dependency Problem" (expected-cost framing
  for adopting a dependency). https://research.swtch.com/deps
- Tim Bray, "0 dependencies" discussion (zero-dep code relocates bug
  surface into `internal/`).
  https://lobste.rs/s/fc516s/0_dependencies
- "We should all be using dependency cooldowns" (delay adopting new
  versions as a supply-chain control).
  https://lobste.rs/s/rygog1/we_should_all_be_using_dependency

## Prior art and adjacent tooling

- ponytail (seed). https://github.com/DietrichGebert/ponytail
- knip (JS/TS unused files, exports, deps). https://knip.dev/
- vulture (Python dead code). https://github.com/jendrikseipp/vulture
- deadcode (Python, with autoremoval).
  https://github.com/albertas/deadcode
- You-Dont-Need-Lodash-Underscore (native-over-dependency catalog).
  https://github.com/you-dont-need/You-Dont-Need-Lodash-Underscore
