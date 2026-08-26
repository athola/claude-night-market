// Every diagram of one codebase at once, because they share a read.
//
// Each cartograph diagram skill walks the same source tree and answers a
// different question of it. Run one at a time and the tree is read four
// times by four sessions that cannot see each other's conclusions. Run
// them together and the structural pass is paid once per lens, in
// parallel, and the inconsistencies between lenses become visible: a
// module the dependency graph shows as central and the architecture
// diagram omits is a finding, and neither lens produces it alone.

export const meta = {
  name: 'atlas',
  description:
    'Generate the architecture, dependency, data-flow and community diagrams of one codebase in parallel and report where they disagree',
  whenToUse:
    'Run when onboarding to an unfamiliar codebase or documenting one for others. args.root is the directory to map; args.lenses narrows the set. Returns Mermaid sources plus the disagreements between lenses.',
  phases: [
    { title: 'Lenses', detail: 'one agent per diagram type' },
    { title: 'Reconcile', detail: 'report what the lenses disagree about' },
  ],
}

const input = args || {}
const root = input.root || '.'

const DIAGRAM = {
  type: 'object',
  required: ['lens', 'mermaid', 'nodes'],
  properties: {
    lens: { type: 'string' },
    mermaid: { type: 'string' },
    nodes: { type: 'array', items: { type: 'string' } },
    omitted: { type: 'array', items: { type: 'string' } },
  },
}

const LENSES = [
  { key: 'architecture', skill: 'cartograph:architecture-diagram', asks: 'how the top-level components relate' },
  { key: 'dependency', skill: 'cartograph:dependency-graph', asks: 'which modules import which' },
  { key: 'data-flow', skill: 'cartograph:data-flow', asks: 'how data moves between components' },
  { key: 'communities', skill: 'cartograph:code-communities', asks: 'which modules cluster, and where the coupling boundaries fall' },
]

const lenses = input.lenses
  ? LENSES.filter((lens) => input.lenses.includes(lens.key))
  : LENSES

const drawn = await parallel(
  lenses.map((lens) => () =>
    agent(
      `Map ${root} through one lens: ${lens.asks}. Follow Skill(${lens.skill}).\n\nReturn the Mermaid source and the list of nodes you included. Also list anything you deliberately left out and why, because the omission is what another lens will disagree with.`,
      {
        label: `map:${lens.key}`,
        phase: 'Lenses',
        agentType: 'cartograph:codebase-explorer',
        schema: DIAGRAM,
      },
    ),
  ),
)

const produced = drawn.filter(Boolean)

if (produced.length < 2) {
  log(`only ${produced.length} lens produced a diagram; nothing to reconcile`)
  return { root, diagrams: produced, disagreements: null }
}

const inventory = produced
  .map((diagram) => `${diagram.lens}: included ${diagram.nodes.join(', ')}${diagram.omitted?.length ? ` | omitted ${diagram.omitted.join(', ')}` : ''}`)
  .join('\n')

const disagreements = await agent(
  `These lenses mapped the same codebase and included different things. Report where they disagree and what each disagreement means.\n\n${inventory}\n\nA module one lens treats as central and another omits is the finding worth reporting. A module absent from every lens is probably dead. Do not smooth the differences into a summary; name them.`,
  { label: 'reconcile', phase: 'Reconcile' },
)

log(`${produced.length} lenses drawn over ${root}`)

return { root, diagrams: produced, disagreements }
