// Every rule in the catalog, checked against the repository it claims to
// govern, one agent per category.
//
// A rule file is a claim about what this codebase does. Rules rot the
// way documentation rots, and worse, because a stale rule is read,
// believed and acted on. The check is per-rule and independent: read the
// rule, look for what it describes, report whether it is still true.
//
// The categories run in parallel and the report is per-category, because
// a security rule that has gone stale is a different urgency from a
// style rule that has.

export const meta = {
  name: 'rule-sweep',
  description:
    'Check each catalog rule against the codebase it governs and report the ones that no longer describe it',
  whenToUse:
    'Run after a refactor that moved files a rule names, or periodically. args.categories narrows the sweep; args.root is the repository to check against. Returns stale rules with what changed under them.',
  phases: [{ title: 'Sweep', detail: 'one agent per rule category' }],
}

const input = args || {}
const root = input.root || '.'

const ALL_CATEGORIES = ['security', 'workflow', 'python', 'performance', 'stewardship']
const categories = input.categories || ALL_CATEGORIES

const STALENESS = {
  type: 'object',
  required: ['category', 'stale'],
  properties: {
    category: { type: 'string' },
    stale: {
      type: 'array',
      items: {
        type: 'object',
        required: ['rule', 'claim', 'reality'],
        properties: {
          rule: { type: 'string' },
          claim: { type: 'string' },
          reality: { type: 'string' },
          severity: { type: 'string', enum: ['high', 'medium', 'low'] },
        },
      },
    },
  },
}

const swept = await parallel(
  categories.map((category) => () =>
    agent(
      `Read every rule under plugins/hookify/skills/rule-catalog/rules/${category}/ and check each against ${root}.\n\nA rule names paths, commands, or patterns. For each, look for what it names. Report a rule as stale when what it describes is not there any more, when the path it guards has moved, or when the pattern it blocks no longer appears in a form the rule would match.\n\nDo not report a rule as stale because you disagree with it. Stale means the world moved, not that the rule is wrong.`,
      { label: `sweep:${category}`, phase: 'Sweep', schema: STALENESS },
    ),
  ),
)

const reports = swept.filter(Boolean)
const stale = reports.flatMap((report) =>
  (report.stale || []).map((entry) => ({ ...entry, category: report.category })),
)

log(`${stale.length} stale rules across ${reports.length} categories`)

return { root, categories, stale }
