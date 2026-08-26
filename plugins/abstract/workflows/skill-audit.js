// One agent per quality dimension over a named set of skills, then an
// adversarial pass on what they claim to have found.
//
// The dimensions are blind to each other on purpose. A single reviewer
// asked for "quality" reliably returns frontmatter problems, because
// those are the cheapest to see, and stops. Splitting the ask is what
// surfaces the expensive findings: a description that will not fire, a
// skill with no way to tell when it is done.
//
// This does not replace Skill(abstract:skills-eval), which scores one
// skill and owns the rubric. This owns the dispatch when the set is
// large enough that reading them in sequence loses the thread.

export const meta = {
  name: 'skill-audit',
  description:
    'Audit a set of skills across four independent quality dimensions, then verify each finding before reporting it',
  whenToUse:
    'Run when auditing more than a handful of skills at once. args.skills is a list of plugin:name or paths; args.strict raises the reporting bar. Returns findings for a human to act on; it writes nothing.',
  phases: [
    { title: 'Dimensions', detail: 'four blind reviewers over the same set' },
    { title: 'Verify', detail: 'try to refute each finding' },
  ],
}

const input = args || {}
const targets = input.skills || []

if (!targets.length) {
  log('skill-audit.js started with no skills')
  return {
    started: false,
    reason: 'no-targets',
    next: 'Pass args.skills as a list of plugin:name identifiers or SKILL.md paths.',
  }
}

const FINDINGS = {
  type: 'object',
  required: ['findings'],
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        required: ['skill', 'claim', 'evidence'],
        properties: {
          skill: { type: 'string' },
          claim: { type: 'string' },
          evidence: { type: 'string' },
          severity: { type: 'string', enum: ['high', 'medium', 'low'] },
        },
      },
    },
  },
}

const VERDICT = {
  type: 'object',
  required: ['refuted', 'reason'],
  properties: {
    refuted: { type: 'boolean' },
    reason: { type: 'string' },
  },
}

const DIMENSIONS = [
  {
    key: 'discovery',
    brief:
      'Read each skill\'s description only. Decide whether a session searching for this capability would find it, and whether a session that should skip it would skip it. Report descriptions that state what the skill is without stating when to reach for it.',
  },
  {
    key: 'exit-criteria',
    brief:
      'Find skills with no Exit Criteria section, and skills whose criteria are not checkable from outside the conversation. "The skill feels complete" is not a criterion; "the file exists and parses" is.',
  },
  {
    key: 'instruction-strength',
    brief:
      'Find statements phrased as invariants that are really defaults or context. An invariant needs a trust boundary, a safety contract, or a recorded failure with a link. Report the ones with none.',
  },
  {
    key: 'length-and-shape',
    brief:
      'Find skills that narrate a procedure where they should describe a map, and skills that have bundled several skills into one file. Report the line count with the reason it is high.',
  },
]

const list = targets.join(', ')

const reviewed = await pipeline(
  DIMENSIONS,
  (dimension) =>
    agent(
      `Audit these skills on one dimension only: ${dimension.brief}\n\nSkills: ${list}\n\nRead each skill. Report only what you can point at. An empty findings list is a valid answer.`,
      {
        label: `audit:${dimension.key}`,
        phase: 'Dimensions',
        agentType: 'abstract:skill-auditor',
        schema: FINDINGS,
      },
    ),
  (review) =>
    parallel(
      (review?.findings || []).map((finding) => () =>
        agent(
          `Try to refute this audit finding. Read the skill and look for the reading that makes the finding wrong. Default to refuted=true when the evidence does not hold up.\n\nSkill: ${finding.skill}\nClaim: ${finding.claim}\nEvidence offered: ${finding.evidence}`,
          { label: `verify:${finding.skill}`, phase: 'Verify', schema: VERDICT },
        ).then((verdict) => ({ ...finding, verdict })),
      ),
    ),
)

const surviving = reviewed
  .flat()
  .filter(Boolean)
  .filter((finding) => finding.verdict && !finding.verdict.refuted)

log(`${surviving.length} findings survived refutation across ${targets.length} skills`)

return { audited: targets, findings: surviving }
