// The read-only half of /sanctum:fix-workflow: recreate, analyse, plan.
//
// It stops before the implementer on purpose. A workflow's subagents run in
// acceptEdits whatever the session's permission mode, so an implementer stage
// here would apply edits the operator never saw proposed. Implementation and
// validation stay in the session, where the diff is visible and where a
// command can actually be run: this script has no shell, so it could not
// verify its own work anyway.
//
// What it returns is a plan. Nothing in it is evidence.

export const meta = {
  name: 'fix-workflow-analysis',
  description:
    'Recreate a workflow slice, generate improvement options with trade-offs, and converge on one plan with acceptance criteria',
  whenToUse:
    'Run from /sanctum:fix-workflow when a slice needs the full three-stage analysis. Requires an explicit request: a workflow never starts unasked. args carry slice (what happened), scope (sanctum|repo) and focus (skills|agents|commands|hooks|all). Returns a plan for the session to implement; it never edits files.',
  phases: [
    { title: 'Recreate', detail: 'restate the slice and surface friction' },
    { title: 'Analyse', detail: 'candidate improvements with trade-offs' },
    { title: 'Plan', detail: 'converge on one approach with acceptance criteria' },
  ],
}

const input = args || {}

if (!input.slice) {
  log('fix-workflow-analysis started with no slice to analyse')
  return {
    started: false,
    reason: 'no-slice',
    next: 'This workflow needs the slice it should analyse. Run /sanctum:fix-workflow, which collects the recent command or session slice and passes it as args.slice. Do not re-invoke this workflow directly and do not improvise a slice.',
  }
}

const scope = input.scope === 'repo' ? 'the whole repository' : 'the sanctum plugin'
const focus = input.focus || 'all'

const RECREATION = {
  type: 'object',
  required: ['steps', 'friction', 'components'],
  properties: {
    steps: { type: 'array', items: { type: 'string' } },
    friction: { type: 'array', items: { type: 'string' } },
    components: {
      type: 'array',
      items: {
        type: 'object',
        required: ['path', 'kind'],
        properties: {
          path: { type: 'string' },
          kind: { type: 'string', enum: ['skill', 'agent', 'command', 'hook', 'rule', 'other'] },
        },
      },
    },
  },
}

const OPTIONS = {
  type: 'object',
  required: ['options'],
  properties: {
    options: {
      type: 'array',
      items: {
        type: 'object',
        required: ['approach', 'changes', 'sacrifices', 'confidence'],
        properties: {
          approach: { type: 'string' },
          changes: { type: 'array', items: { type: 'string' } },
          sacrifices: { type: 'string' },
          confidence: { type: 'number' },
        },
      },
    },
  },
}

const PLAN = {
  type: 'object',
  required: ['chosen', 'why', 'edits', 'acceptance', 'rejected'],
  properties: {
    chosen: { type: 'string' },
    why: { type: 'string' },
    edits: {
      type: 'array',
      items: {
        type: 'object',
        required: ['path', 'change'],
        properties: { path: { type: 'string' }, change: { type: 'string' } },
      },
    },
    acceptance: { type: 'array', items: { type: 'string' } },
    rejected: { type: 'array', items: { type: 'string' } },
  },
}

phase('Recreate')

const recreation = await agent(
  `Recreate this workflow slice and surface its friction. Scope: ${scope}. Focus: ${focus}.\n\nSlice:\n${input.slice}\n\nRead only. Name every skill, agent, command, hook or rule the slice touched, with its repository path.`,
  { label: 'recreate', phase: 'Recreate', agentType: 'sanctum:workflow-recreate-agent', schema: RECREATION },
)

if (!recreation) {
  return { started: true, failed: 'recreate', next: 'The recreation stage returned nothing. Re-run, or do the retrospective in the session.' }
}

phase('Analyse')

const analysis = await agent(
  `Generate improvement approaches for this slice, each with what it gives up.\n\nSteps:\n${recreation.steps.join('\n')}\n\nFriction:\n${recreation.friction.join('\n')}\n\nComponents:\n${recreation.components.map((c) => `${c.kind}: ${c.path}`).join('\n')}\n\nPrefer deleting a component over adding one. An approach whose only benefit is future flexibility is not an approach.`,
  { label: 'analyse', phase: 'Analyse', agentType: 'sanctum:workflow-improvement-analysis-agent', schema: OPTIONS },
)

if (!analysis || !analysis.options.length) {
  return { started: true, recreation, failed: 'analyse', next: 'No improvement options were produced. The slice may not need one.' }
}

phase('Plan')

const plan = await agent(
  `Converge on one approach and state what it must satisfy to count as done.\n\nOptions:\n${analysis.options.map((o, i) => `${i + 1}. ${o.approach} (confidence ${o.confidence}) -- sacrifices: ${o.sacrifices}`).join('\n')}\n\nComponents in play:\n${recreation.components.map((c) => c.path).join('\n')}\n\nEvery acceptance criterion must be checkable from outside the conversation: a test that fails without the change, a command whose output shows it, or a file that exists. Say which options you rejected and why.`,
  { label: 'plan', phase: 'Plan', agentType: 'sanctum:workflow-improvement-planner-agent', schema: PLAN },
)

if (!plan) {
  return { started: true, recreation, analysis, failed: 'plan', next: 'Planning returned nothing. Choose among the analysis options in the session.' }
}

log(`plan: ${plan.chosen} (${plan.edits.length} edits, ${plan.acceptance.length} acceptance criteria)`)

return {
  started: true,
  recreation,
  options: analysis.options,
  plan,
  next: 'Implement in the session, not here. This workflow has no shell, so no acceptance criterion above has been checked. Apply the edits, run the criteria, and paste their output.',
}
