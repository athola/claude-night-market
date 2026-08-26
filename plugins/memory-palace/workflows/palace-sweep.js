// One question asked of every palace at once, because a memory search
// that stops at the first hit finds the palace you thought of first.
//
// Knowledge here is spread across palaces by domain, and the domain a
// fact was filed under is not always the domain you would look in. A
// sequential search returns the first plausible match and stops, which
// is the retrieval failure that makes a memory system feel empty when
// it is not. Asking every palace the same question surfaces the match
// filed somewhere unexpected, and the ranking stage is what turns
// several partial answers into one.

export const meta = {
  name: 'palace-sweep',
  description:
    'Ask one question of every memory palace in parallel and rank the answers, including the ones filed under an unexpected domain',
  whenToUse:
    'Run when a search of the obvious palace came back empty or thin. args.question is what to look for; args.palaces narrows the set. Returns ranked findings with their palace of origin; it writes nothing.',
  phases: [
    { title: 'Search', detail: 'one agent per palace' },
    { title: 'Rank', detail: 'merge partial answers into one' },
  ],
}

const input = args || {}
const question = input.question

if (!question) {
  log('palace-sweep.js started with no question')
  return {
    started: false,
    reason: 'no-question',
    next: 'Pass args.question. A sweep with no question reads every palace and returns their tables of contents.',
  }
}

const palaces = input.palaces || []

if (!palaces.length) {
  return {
    started: false,
    reason: 'no-palaces',
    next: 'Pass args.palaces as a list of palace names. Run /memory-palace:navigate to enumerate them; a workflow script cannot read the filesystem.',
  }
}

const HITS = {
  type: 'object',
  required: ['palace', 'hits'],
  properties: {
    palace: { type: 'string' },
    hits: {
      type: 'array',
      items: {
        type: 'object',
        required: ['note', 'relevance', 'excerpt'],
        properties: {
          note: { type: 'string' },
          relevance: { type: 'number' },
          excerpt: { type: 'string' },
          storedWhen: { type: 'string' },
        },
      },
    },
  },
}

const searched = await parallel(
  palaces.map((palace) => () =>
    agent(
      `Search the ${palace} palace for anything bearing on this question, following Skill(memory-palace:knowledge-locator).\n\nQuestion: ${question}\n\nSearch by meaning, not only by keyword: a note answering this question may not use its words. Report an excerpt with each hit so the ranking stage can judge without re-reading. Report when the note was stored, because a stored fact reflects what was true when it was written. An empty result is a valid answer and more useful than a stretch.`,
      {
        label: `search:${palace}`,
        phase: 'Search',
        agentType: 'memory-palace:knowledge-navigator',
        schema: HITS,
      },
    ),
  ),
)

const results = searched.filter(Boolean)
const hits = results.flatMap((result) =>
  (result.hits || []).map((hit) => ({ ...hit, palace: result.palace })),
)

if (!hits.length) {
  log(`no palace held anything on: ${question}`)
  return { question, hits: [], answer: null }
}

const digest = hits
  .map((hit) => `[${hit.palace}] ${hit.note} (${hit.relevance}): ${hit.excerpt}`)
  .join('\n')

const answer = await agent(
  `These palaces were searched independently for one question. Merge what they found into a single answer.\n\nQuestion: ${question}\n\n${digest}\n\nWhere two palaces hold the same fact, say so once. Where they disagree, report the disagreement with both dates rather than picking the newer one, because the older note may be the one that recorded why. Say plainly which parts of the question nothing here answers.`,
  { label: 'rank', phase: 'Rank' },
)

log(`${hits.length} hits across ${results.length} palaces`)

return { question, hits, answer }
