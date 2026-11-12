# ADR-0030: Constitution Rules Name Their Check and Disclose at Repo Level

**Date**: 2026-11-11
**Status**: Accepted
**Deciders**: Claude Night Market maintainers

## Context

`CONSTITUTION.md` and `STEWARDSHIP.md` were revised on 2026-11-11
after a `tome:research` pass. The arXiv abstracts, the Wikipedia
article and Claude's constitution were read that day. The project
policies were read by research agents in the same session. The Block
and Baden-Powell wording comes from search results that reproduce it.

### Rule files are followed unevenly

A rule written in a file is followed more often than not, and some
rules are never followed at all. "Do They Do as They Are Told?"
([arXiv 2611.13709](https://arxiv.org/abs/2611.13709)) turned
context-file instructions into executable checks and found that
"adherence splits sharply between instructions followed consistently
and those never respected." Its authors point to "enforcement beyond
the ACF" for the second group.

Wording matters too. "Do Coding Agents Follow AGENTS.md?"
([arXiv 2611.04367](https://arxiv.org/abs/2611.04367)) tested four
wording styles across 86 tasks: "Conditional phrasing was followed
less often than Prescriptive and Explanatory."

### Open-source AI policies

The field has mostly settled on permitting AI with a human accountable
for it. Hora, Robbes and Zacchiroli
([arXiv 2609.07542](https://arxiv.org/abs/2609.07542)) analyzed 281
policies: 83.3% permit or encourage AI in code contributions, 67.3%
require a high level of human involvement, and 48.8% require
disclosure.

| Project | Disclosure | Limit on AI work |
|---------|------------|------------------|
| [LLVM](https://llvm.org/docs/AIToolPolicy.html) | Should note tool use, e.g. an `Assisted-by:` trailer | A human reads all generated code before asking for review |
| [Linux kernel](https://docs.kernel.org/process/coding-assistants.html) | Agents must not add `Signed-off-by`. Only a human certifies the DCO | A human reviews all output |
| [curl](https://curl.se/dev/contribute.html) | Required in security and other reports | Fabricated AI reports get the reporter banned |
| [Ghostty](https://github.com/ghostty-org/ghostty/blob/main/AI_POLICY.md) | All AI use, naming the tool and its extent | Outside contributions only. No AI-generated media |
| [Gentoo](https://wiki.gentoo.org/wiki/Project:Council/AI_policy) | Not applicable | Contributions made with AI tools are forbidden |
| [QEMU proposal](https://patchew.org/QEMU/20260528073412.551117-1-pbonzini@redhat.com/) | `AI-used-for:` trailer | Small fixes of 20 lines or fewer without asking first; posted, not merged |

The cost of unaccountable AI work is measured. "AI Slop is DDoSing
Open Source" ([arXiv 2607.04003](https://arxiv.org/abs/2607.04003))
followed 294 repositories and over 2 million pull requests and issues,
and found "one-time contributors experiencing an 18.18% drop in PR
merge rates relative to the counterfactual."

## Decision

Each rule in the constitution names the mechanism that checks it, or
says that a reviewer is the only check. A rule with no mechanism is a
request, and the first paper above says some requests are never
honored. Each rule is stated as a requirement followed by its reason,
which is the explanatory form the second paper found followed more
often than conditional phrasing.

Rule 1 discloses AI involvement at the repository level, because
nearly every change here is agent-written. It asks for disclosure per
pull request from outside contributors only, which is Ghostty's scope.

Rule 2 keeps a line count as a signal. LLVM's "extractive" test, where
reviewing a change costs more than it is worth, is the cost the count
approximates.

The campsite rule in `STEWARDSHIP.md` is bounded to the lines a change
already touches. A pull request carries one coherent change, and an
unrelated cleanup folded into it makes the change harder to review and
to revert. Other cleanup goes in its own commit. The attributions
behind each stewardship principle, with what could and could not be
verified, are in that file's **Origin** notes.

## Consequences

- A new rule needs a named check before it is added, or an explicit
  statement that review is its only check.
- Per-PR disclosure is not required of maintainers. Outside
  contributors carry it, and nobody may deny AI involvement.
- A large AI change names its plan in the PR rather than being
  refused on size.
- Amending a rule follows the process in `CONSTITUTION.md`.
