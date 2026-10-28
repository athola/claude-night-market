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
    'Run after a refactor that moved files a rule names, or periodically. args.categories narrows the sweep. args.root is the repository to check against. Returns stale rules with what changed under them.',
  phases: [{ title: 'Sweep', detail: 'one agent per rule category' }],
}

const input = args || {}
const root = input.root || '.'

// One entry per directory under plugins/hookify/skills/rule-catalog/rules/.
// A test compares the two.
const ALL_CATEGORIES = ['documentation', 'git', 'performance', 'python', 'security', 'stewardship', 'workflow']
const KNOWN = ALL_CATEGORIES.join(', ')
const selection = input.categories ?? null
// A string would pass `.includes` as a substring match, so only a list
// is a selection.
if (selection !== null && !Array.isArray(selection)) {
  return {
    started: false,
    reason: 'categories-not-a-list',
    next: 'Pass args.categories as a list of category names. Omit it to run every category.',
  }
}
const categories = selection ? ALL_CATEGORIES.filter((name) => selection.includes(name)) : ALL_CATEGORIES
// A misspelled category must not dispatch an agent at nothing.
const unknown = (selection || []).filter((name) => !ALL_CATEGORIES.includes(name))
if (unknown.length) log(`unknown category ${unknown.join(', ')}. Known categories: ${KNOWN}`)
if (!categories.length) {
  return {
    started: false,
    reason: 'no-categories-selected',
    next: `Name one or more known categories in args.categories: ${KNOWN}. Omit it to run every category.`,
    unknown,
  }
}

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
      `Read every rule under plugins/hookify/skills/rule-catalog/rules/${category}/ and check each against ${root}.\n\nA rule names paths, commands, or patterns. For each, look for what it names. Report a rule as stale in three cases. What it describes is not there any more. The path it guards has moved. The pattern it blocks no longer appears in a form the rule would match.\n\nDo not report a rule as stale because you disagree with it. Stale means the world moved, not that the rule is wrong.`,
      { label: `sweep:${category}`, phase: 'Sweep', schema: STALENESS },
    ),
  ),
)

// A category whose sweeper returned nothing is unswept; "no stale rules
// there" would be the wrong reading.
const missing = categories.filter((category, index) => !swept[index])
// The category comes from the roster, not from the agent's own report.
const reports = swept
  .map((report, index) => report && { ...report, category: categories[index] })
  .filter(Boolean)
const stale = reports.flatMap((report) =>
  (report.stale || []).map((entry) => ({ ...entry, category: report.category })),
)

log(`${stale.length} stale rules across ${reports.length} of ${categories.length} categories`)
if (missing.length) log(`no sweep from ${missing.join(', ')}. Those categories are unswept, not clean`)

return { root, categories, stale, coverage: { swept: reports.map((r) => r.category), missing } }
