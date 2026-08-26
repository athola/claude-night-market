// Every plugin's contract checked at once, because 24 sequential checks
// is a coffee break and the checks share nothing.
//
// leyline owns the cross-plugin contracts: manifest consistency, hook
// registration, dependency declarations, the shared helpers each plugin
// vendors. Verifying one plugin needs a read of that plugin and the
// contract, and nothing about plugin A informs the check of plugin B.
// The only stage that needs everything is the last one, where a
// contract that no plugin satisfies is a finding about the contract.

export const meta = {
  name: 'plugin-health',
  description:
    'Check every plugin against the shared leyline contracts in parallel, then report contracts that no plugin satisfies',
  whenToUse:
    'Run before a release, or after changing a shared contract. args.plugins narrows the set. Returns per-plugin violations plus contracts that may have gone stale; it repairs nothing.',
  phases: [
    { title: 'Check', detail: 'one agent per plugin' },
    { title: 'Contracts', detail: 'find the contract nobody satisfies' },
  ],
}

const input = args || {}
const plugins = input.plugins || []

if (!plugins.length) {
  log('plugin-health.js started with no plugin list')
  return {
    started: false,
    reason: 'no-plugins',
    next: 'Pass args.plugins as a list of plugin names. Enumerating plugins/ is a filesystem read, which a workflow script cannot do; the caller supplies the list.',
  }
}

const HEALTH = {
  type: 'object',
  required: ['plugin', 'violations'],
  properties: {
    plugin: { type: 'string' },
    violations: {
      type: 'array',
      items: {
        type: 'object',
        required: ['contract', 'detail'],
        properties: {
          contract: { type: 'string' },
          detail: { type: 'string' },
          severity: { type: 'string', enum: ['high', 'medium', 'low'] },
        },
      },
    },
    satisfied: { type: 'array', items: { type: 'string' } },
  },
}

const checked = await parallel(
  plugins.map((plugin) => () =>
    agent(
      `Check plugins/${plugin} against the shared contracts. Read Skill(leyline:stewardship) and Skill(leyline:pytest-config) for what they are.\n\nCheck: plugin.json registers every skill, command and agent on disk and nothing that is not; declared dependencies exist; hooks named in hooks.json exist and are executable; vendored shared helpers match the canonical copy; every SKILL.md has a description and exit criteria.\n\nList what you checked and found satisfied as well as what you found violated. The satisfied list is what the next stage needs to tell a stale contract from a broken plugin.`,
      { label: `check:${plugin}`, phase: 'Check', schema: HEALTH },
    ),
  ),
)

const reports = checked.filter(Boolean)
const violations = reports.flatMap((report) =>
  (report.violations || []).map((entry) => ({ ...entry, plugin: report.plugin })),
)

if (reports.length < 2) {
  log(`${violations.length} violations from ${reports.length} plugin`)
  return { plugins, violations, staleContracts: null }
}

const coverage = reports
  .map((report) => `${report.plugin}: satisfied ${(report.satisfied || []).join(', ') || 'none'}`)
  .join('\n')

const staleContracts = await agent(
  `These per-plugin checks ran independently. Report any contract that no plugin satisfies.\n\n${coverage}\n\nA contract every plugin violates is more likely a contract that moved than 24 independent mistakes, and it should be reported as a question about the contract rather than as 24 findings. Say which of these is which.`,
  { label: 'contracts', phase: 'Contracts' },
)

log(`${violations.length} violations across ${reports.length} plugins`)

return { plugins, violations, staleContracts }
