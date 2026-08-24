// Discover, author in parallel, review adversarially. The fixer stays out.
//
// No worktree isolation, deliberately. The tool offers it for agents that
// mutate the same files in parallel, and it costs a worktree each. Authoring
// agents here write one new directory per skill under .claude/skills/, which
// is disjoint by construction, so `.claude/rules/plan-before-large-dispatch.md`
// says to skip it. The write fence in each prompt is what keeps that true.
//
// Authoring writes; reviewing and fixing do not. Subagents in a workflow run
// in acceptEdits whatever the session's permission mode, so the only writes
// this script permits are new files at paths that did not exist. Applying
// review findings edits files that already exist, and that stays in the
// session where the diff is visible.

export const meta = {
  name: 'skill-library',
  description:
    'Discover what a project knows, author one skill per topic in parallel, and review each adversarially',
  whenToUse:
    'Run from /attune:skill-library once the discovery brief exists. Requires an explicit request: a workflow never starts unasked. args carry topics (array of {name, brief}) and libraryRoot. Authoring agents create new skill directories; the review findings come back for the session to apply.',
  phases: [
    { title: 'Author', detail: 'one agent per skill, writing only new files' },
    { title: 'Review', detail: 'two lenses per skill, reading only' },
  ],
}

const input = args || {}
const topics = Array.isArray(input.topics) ? input.topics : []
const libraryRoot = input.libraryRoot || '.claude/skills'

if (!topics.length) {
  log('skill-library started with no topics')
  return {
    started: false,
    reason: 'no-topics',
    next: 'This workflow authors skills from a discovery brief it does not produce. Run /attune:skill-library, which discovers the topics first and passes them as args.topics. Do not invent a topic list here.',
  }
}

const WRITTEN = {
  type: 'object',
  required: ['path', 'summary'],
  properties: {
    path: { type: 'string' },
    summary: { type: 'string' },
  },
}

const REVIEW = {
  type: 'object',
  required: ['verdict', 'findings'],
  properties: {
    verdict: { type: 'string', enum: ['ship', 'fix-required'] },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        required: ['severity', 'what'],
        properties: {
          severity: { type: 'string', enum: ['blocking', 'important', 'minor'] },
          what: { type: 'string' },
        },
      },
    },
  },
}

// Two lenses, because an author cannot see its own contradiction and a second
// reader with the same brief tends to repeat the first one's blind spot.
const LENSES = [
  {
    key: 'accuracy',
    brief:
      'Check every claim against the repository. A cited path that does not resolve, a command that does not exist, or a described behavior the code does not have is blocking.',
  },
  {
    key: 'economy',
    brief:
      'Check whether this earns a reader\'s time. A skill restating a general practice, or one whose exit criteria cannot be checked from outside a conversation, is important rather than blocking.',
  },
]

phase('Author')

const reviewed = await pipeline(
  topics,
  (topic) =>
    agent(
      `Author one skill for this project's library.\n\nTopic: ${topic.name}\nBrief: ${topic.brief || 'see the discovery notes in the repository'}\n\nWrite fence: create files only under ${libraryRoot}/${topic.name}/. Do not modify any file that already exists, anywhere. Every claim must cite a path that resolves. Include an Exit Criteria section whose items can be checked from outside a conversation.`,
      { label: `author:${topic.name}`, phase: 'Author', schema: WRITTEN },
    ),
  (written, topic) => {
    if (!written) return null
    return parallel(
      LENSES.map((lens) => () =>
        agent(
          `Review one authored skill through one lens, reading only. Change nothing.\n\nLens: ${lens.brief}\n\nSkill: ${written.path}\nWhat the author says it covers: ${written.summary}`,
          { label: `review:${topic.name}:${lens.key}`, phase: 'Review', schema: REVIEW },
        ),
      ),
    ).then((reviews) => ({
      skill: topic.name,
      path: written.path,
      reviews: reviews.filter(Boolean),
    }))
  },
)

const authored = reviewed.filter(Boolean)
const failed = topics.filter((t) => !authored.some((a) => a.skill === t.name)).map((t) => t.name)

const needFixes = authored.filter((a) =>
  a.reviews.some((r) => r.verdict === 'fix-required'),
)

log(`${authored.length} of ${topics.length} skills authored, ${needFixes.length} need fixes`)

return {
  libraryRoot,
  authored: authored.map((a) => ({
    skill: a.skill,
    path: a.path,
    blocking: a.reviews.flatMap((r) => r.findings.filter((f) => f.severity === 'blocking')),
    other: a.reviews.flatMap((r) => r.findings.filter((f) => f.severity !== 'blocking')),
  })),
  failed,
  next: 'Apply the findings in the session, not here. Fixing edits files that already exist, which is the write this script deliberately does not make. Nothing above was verified by running anything.',
}
