# Governance Evidence

*For a maintainer weighing a change to `CONSTITUTION.md` or
`STEWARDSHIP.md`. A contributor following the rules does not need
this page.*

Both files state rules and principles. This page holds the sources
behind them, which keeps the files short enough to read in one sitting. Every
source below was read from the primary page on 2026-11-11 unless it is
marked secondary.

## Rule files are followed unevenly

A rule written in a file is followed more often than not, and some
rules are never followed at all. "Do They Do as They Are Told?"
([arXiv 2611.13709](https://arxiv.org/abs/2611.13709)) turned
context-file instructions into executable checks and found that
"adherence splits sharply between instructions followed consistently
and those never respected." Its authors point to "enforcement beyond
the ACF" for the second group.

This is why each rule in the constitution names the mechanism that
enforces it, or says that a reviewer is the only check. A rule with no
mechanism is a request.

Wording matters too. "Do Coding Agents Follow AGENTS.md?"
([arXiv 2611.04367](https://arxiv.org/abs/2611.04367)) tested four
wording styles across 86 tasks: "Conditional phrasing was followed
less often than Prescriptive and Explanatory." The constitution states
each rule as a requirement followed by its reason, which is the
explanatory form.

## Open-source AI policies

The constitution's disclosure and size rules sit inside a field that
has mostly settled on permitting AI with a human accountable for it.
Hora, Robbes and Zacchiroli
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

Two choices here follow from that table. Rule 1 discloses at the
repository level, because nearly every change here is agent-written,
and asks it per pull request of outside contributors only, which is
Ghostty's scope. Rule 2 keeps a line count as a signal, because LLVM's
"extractive" test, where reviewing a change costs more than it is
worth, is the cost the count approximates.

The cost is measured. "AI Slop is DDoSing Open Source"
([arXiv 2607.04003](https://arxiv.org/abs/2607.04003)) followed 294
repositories and over 2 million pull requests and issues, and found
"one-time contributors experiencing an 18.18% drop in PR merge rates
relative to the counterfactual."

## Stewardship sources

| Attribution | What the source supports |
|-------------|--------------------------|
| Peter Block, *Stewardship: Choosing Service over Self-Interest* | "the willingness to be accountable for the well-being of the larger organization by operating in service, rather than in control, of those around us" |
| Robert Baden-Powell, farewell message to Scouts, published after his death in 1941 | "Try and leave this world a little better than you found it" |
| Robert C. Martin, "The Boy Scout Rule", *97 Things Every Programmer Should Know* (2010) | Applies the Scouts' campground rule to code: check a module in cleaner than you checked it out. Paraphrased, because the chapter could not be fetched |
| [Seven generation sustainability](https://en.wikipedia.org/wiki/Seven_generation_sustainability) (secondary) | Commonly attributed to the Haudenosaunee Great Law of Peace, but "those words are not contained in written transcriptions" of it |
| [Claude's constitution](https://www.anthropic.com/constitution), Anthropic, published 2026-01-22 | The trait list and the line that Claude's character "emerged through training" without being "any less authentic" |

The campsite rule meets a limit in this repository. A pull request
should carry one coherent change, and an unrelated cleanup folded into
it makes the change harder to review and to revert. `STEWARDSHIP.md`
therefore scopes the rule to the lines a change already touches, and
sends other cleanup to its own commit.
