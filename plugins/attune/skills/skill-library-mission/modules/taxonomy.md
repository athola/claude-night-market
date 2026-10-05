# Skill Library Taxonomy

Sixteen categories, adapted to what Phase 1 discovery found. Merge
categories that are thin in the target repo, split ones that are
deep, and add domain categories the taxonomy does not imagine. Aim
for 10 to 16 skills total. Placeholders: `<project>` is the repo's
short name, `<domain>` is its technical field.

## Categories

The sixteen categories are listed once, in Phase 2 of
`references/mission-prompt.md`: twelve core categories (1 to 12) that
every project has, and four advanced ones (13 to 16). The prompt is
pasted whole into a fresh session and must carry the full list. This
module adds only the rules for adapting it.

## Adaptation Rules

- Merge when discovery finds a category thin: the first run in this
  repo folded run-and-operate, build tooling, and release steps into
  one `operations` skill because they shared a Makefile.
- Split when a category is deep enough to exceed one skill's token
  budget; prefer a hub skill plus modules over two overlapping
  skills.
- Add a `collective-memory` category when the project keeps memory in
  discussions, ADRs, or journals: searching memory before
  re-investigating is its own discipline.
- One home per fact. When two categories want the same fact, pick
  the owner and cross-reference from the other.
