// Multi-lens review as a pipeline: each dimension's findings verify as soon
// as that dimension returns, instead of waiting for the slowest lens.
//
// Two choices are load-bearing.
//
//   1. Dedup happens in plain JavaScript, not in an agent. A barrier is
//      justified only where a stage needs cross-item context, and merging
//      findings across lenses is that case. Everything before it pipelines.
//
//   2. This replaces the prose barrier in SKILL.md, and serves its purpose
//      better. That rule exists so one lens cannot colour how the next is
//      read. A script is not a reasoning entity, so it cannot be anchored by
//      reading stage one before stage two, and results pass between stages
//      without entering anyone's context.
//
// What it cannot do, by construction: run the test suite, read a diff, or
// prove a finding reproduces. A workflow script has no filesystem and no
// shell. Its return value feeds a gate; it is not one.

export const meta = {
  name: 'unified-review',
  description:
    'Review changed code across dimensions, adversarially verify each finding, and return one ranked list',
  whenToUse:
    'Run when a change needs more than one review lens and the findings must survive a skeptic. Requires an explicit request: this repository never starts a workflow on its own. Subagents run in acceptEdits mode, so scope the prompts to reading rather than editing.',
  phases: [
    { title: 'Review', detail: 'one agent per review dimension' },
    { title: 'Verify', detail: 'three adversarial lenses per finding' },
  ],
}

// Agent types come from plugins/pensive/agents/. The mapping mirrors the table
// at plugins/pensive/skills/unified-review/SKILL.md:138-165, including its rule
// that a skill name is never an agent type: dimensions without a dedicated
// agent use general-purpose and invoke the skill themselves.
const DIMENSIONS = [
  {
    key: 'bugs',
    agentType: 'pensive:code-reviewer',
    prompt: 'Hunt correctness defects in the changed code. Report only what you can point at with a file and line.',
  },
  {
    key: 'architecture',
    agentType: 'pensive:architecture-reviewer',
    prompt: 'Assess the changed code against the ADRs in docs/adr/ and the invariants in .claude/rules/. Report coupling that the change introduces.',
  },
  {
    key: 'tests',
    agentType: 'pensive:code-reviewer',
    prompt: 'Assess test coverage of the change. A branch with no test that fails when it breaks is a finding.',
  },
  {
    key: 'security',
    agentType: 'general-purpose',
    prompt: 'Invoke Skill(pensive:harden) and apply it to the changed code. Report findings with their CWE where one applies.',
  },
]

const FINDINGS = {
  type: 'object',
  required: ['findings'],
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        required: ['title', 'file', 'line', 'severity', 'why'],
        properties: {
          title: { type: 'string' },
          file: { type: 'string' },
          line: { type: 'integer' },
          severity: { type: 'string', enum: ['blocking', 'important', 'minor'] },
          why: { type: 'string' },
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

// Distinct lenses rather than three identical skeptics: redundancy catches one
// failure mode, diversity catches three.
const LENSES = [
  'correctness: does the described defect actually follow from the code as written',
  'reproduction: can you state concrete inputs and the wrong output they produce',
  'prior art: is this already guarded by a test, a rule, or an ADR in this repo',
]

// Bounds, so a demo run cannot become a full review spend by accident.
// The tool's own guidance is that a bounded run must say what it dropped
// rather than reading as full coverage, which is what the log lines below
// are for.
const input = args || {}
const target = input.target || 'the current working diff'
const wanted = Array.isArray(input.dimensions) ? input.dimensions : null
const selected = wanted
  ? DIMENSIONS.filter((d) => wanted.includes(d.key))
  : DIMENSIONS
const maxFindings = typeof input.maxFindings === 'number' ? input.maxFindings : 0
const lenses = typeof input.lenses === 'number' ? LENSES.slice(0, input.lenses) : LENSES

if (selected.length < DIMENSIONS.length) {
  const dropped = DIMENSIONS.filter((d) => !selected.includes(d)).map((d) => d.key)
  log(`bounded run: skipping dimensions ${dropped.join(', ')}`)
}
if (lenses.length < LENSES.length) {
  log(`bounded run: verifying with ${lenses.length} of ${LENSES.length} lenses`)
}

phase('Review')

const perDimension = await pipeline(
  selected,
  (d) =>
    agent(`${d.prompt}\n\nReview target: ${target}.`, {
      label: `review:${d.key}`,
      phase: 'Review',
      agentType: d.agentType,
      schema: FINDINGS,
    }),
  (review, dimension) => {
    if (!review || !review.findings || review.findings.length === 0) return []
    let toVerify = review.findings
    if (maxFindings > 0 && toVerify.length > maxFindings) {
      log(
        `bounded run: ${dimension.key} reported ${toVerify.length} findings, verifying the first ${maxFindings}`,
      )
      toVerify = toVerify.slice(0, maxFindings)
    }
    return parallel(
      toVerify.map((f) => () =>
        parallel(
          lenses.map((lens) => () =>
            agent(
              `Try to refute this review finding through one lens.\n\nLens: ${lens}\n\nFinding: ${f.title}\nAt: ${f.file}:${f.line}\nClaim: ${f.why}\n\nDefault to refuted: true when the evidence is not there.`,
              { label: `verify:${f.file}`, phase: 'Verify', schema: VERDICT },
            ),
          ),
        ).then((votes) => {
          const heard = votes.filter(Boolean)
          const standing = heard.filter((v) => !v.refuted).length
          return { ...f, dimension: dimension.key, standing, heard: heard.length }
        }),
      ),
    )
  },
)

// The one barrier that earns its place: deduplication needs every finding at
// once, and it is arithmetic, so no agent is spawned for it.
const survived = perDimension
  .flat(2)
  .filter(Boolean)
  .filter((f) => f.heard > 0 && f.standing * 2 > f.heard)

const byLocation = new Map()
for (const f of survived) {
  const key = `${f.file}:${f.line}:${f.title.toLowerCase()}`
  const seen = byLocation.get(key)
  if (!seen) {
    byLocation.set(key, { ...f, dimensions: [f.dimension] })
  } else if (!seen.dimensions.includes(f.dimension)) {
    seen.dimensions.push(f.dimension)
  }
}

const RANK = { blocking: 0, important: 1, minor: 2 }
const confirmed = [...byLocation.values()].sort(
  (a, b) => RANK[a.severity] - RANK[b.severity] || b.dimensions.length - a.dimensions.length,
)

log(`${confirmed.length} findings survived adversarial verification`)

return {
  target,
  dimensions: selected.map((d) => d.key),
  bounded: { maxFindings, lenses: lenses.length },
  confirmed,
  note:
    'Findings are agent claims that survived refutation. No command was run inside this workflow, so nothing here is proof-of-work evidence. Reproduce before acting.',
}
