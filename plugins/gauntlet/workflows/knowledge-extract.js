// Knowledge extraction fanned out by subsystem, because the enrichment
// pass is the expensive half and it is per-subsystem independent.
//
// The AST walk is cheap. What costs is deciding what a module is for,
// which needs a session that has read it. Running that sequentially over
// a large codebase means the last subsystem is enriched by a session
// carrying eleven subsystems of unrelated context, and quality falls off
// along the way. One agent per subsystem is what keeps the last one as
// good as the first.

export const meta = {
  name: 'knowledge-extract',
  description:
    'Extract and enrich the gauntlet knowledge base one subsystem per agent, then merge into a single corpus',
  whenToUse:
    'Run when initializing the knowledge base or after a large refactor. args.subsystems lists the directories; args.depth selects how much rationale to capture. Returns the merged corpus for the skill to write.',
  phases: [
    { title: 'Extract', detail: 'one agent per subsystem' },
    { title: 'Merge', detail: 'reconcile overlapping concepts' },
  ],
}

const input = args || {}
const subsystems = input.subsystems || []

if (!subsystems.length) {
  log('knowledge-extract.js started with no subsystems')
  return {
    started: false,
    reason: 'no-subsystems',
    next: 'Pass args.subsystems as a list of directories. Extracting a whole repository in one agent is the failure this workflow exists to avoid.',
  }
}

const CORPUS = {
  type: 'object',
  required: ['subsystem', 'entries'],
  properties: {
    subsystem: { type: 'string' },
    entries: {
      type: 'array',
      items: {
        type: 'object',
        required: ['concept', 'whatItDoes', 'whyItExists'],
        properties: {
          concept: { type: 'string' },
          whatItDoes: { type: 'string' },
          whyItExists: { type: 'string' },
          gotcha: { type: 'string' },
        },
      },
    },
  },
}

const extracted = await parallel(
  subsystems.map((subsystem) => () =>
    agent(
      `Extract the knowledge a new contributor needs about ${subsystem}, following Skill(gauntlet:extract).\n\nFor each concept, record what it does and why it exists. The second is the one worth the read: what it does is visible in the code, and why it exists usually is not. Where a comment or a commit message explains a decision, capture the decision rather than the comment. Where you cannot tell why something exists, say so instead of inventing a rationale.`,
      {
        label: `extract:${subsystem}`,
        phase: 'Extract',
        agentType: 'gauntlet:extractor',
        schema: CORPUS,
      },
    ),
  ),
)

const corpora = extracted.filter(Boolean)
const entries = corpora.flatMap((corpus) => corpus.entries || [])

if (corpora.length < 2) {
  log(`${entries.length} entries from ${corpora.length} subsystem`)
  return { subsystems, entries, merged: null }
}

const concepts = entries.map((entry) => `${entry.concept}: ${entry.whatItDoes}`).join('\n')

const merged = await agent(
  `These entries came from separate subsystem extractions that could not see each other. Reconcile them.\n\n${concepts}\n\nWhere two subsystems described the same concept differently, that difference is either a real boundary or a misunderstanding, and you should say which. Where a concept appears in one subsystem and is used by another, link them. Do not merge two concepts that share a name and nothing else.`,
  { label: 'merge', phase: 'Merge' },
)

log(`${entries.length} entries across ${corpora.length} subsystems`)

return { subsystems, entries, merged }
