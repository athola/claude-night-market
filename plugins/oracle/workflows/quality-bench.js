// Score many skills through the oracle at once, because each inference
// is independent and the daemon is the only shared resource.
//
// oracle exists to put a number on skill quality without a human reading
// every file. One at a time that is a loop with a model call in it. The
// fan-out is what makes a whole-plugin sweep practical, and the
// calibration stage at the end is the part that matters: a score is only
// meaningful against the distribution it sits in, and a single score
// tells a reader nothing about whether 0.6 is good here.

export const meta = {
  name: 'quality-bench',
  description:
    'Score a set of skills through the oracle in parallel and report each score against the distribution rather than alone',
  whenToUse:
    'Run when triaging a plugin\'s skills by quality, or to track drift across releases. args.skills lists what to score. Returns scores with their calibration. It edits nothing.',
  phases: [
    { title: 'Score', detail: 'one inference per skill' },
    { title: 'Calibrate', detail: 'place each score in the distribution' },
  ],
}

const input = args || {}
const skills = input.skills || []

if (!skills.length) {
  log('quality-bench.js started with no skills')
  return {
    started: false,
    reason: 'no-skills',
    next: 'Pass args.skills as a list of SKILL.md paths. Run /oracle:oracle-setup first if the daemon is not provisioned.',
  }
}

const SCORE = {
  type: 'object',
  required: ['skill', 'source', 'basis'],
  properties: {
    skill: { type: 'string' },
    // A daemon that is down has no score to give. With score required, the
    // schema forced the agent to invent one to return at all.
    source: { type: 'string', enum: ['oracle', 'unavailable'] },
    score: { type: 'number' },
    basis: { type: 'string' },
    weakest: { type: 'string' },
  },
}

const scored = await parallel(
  skills.map((skill) => () =>
    agent(
      `Score ${skill} for quality using the oracle inference daemon. Read Skill(oracle:setup) for how to reach it. If the daemon is not running, set source to unavailable and omit the score. Do not present your own judgment as an oracle score.\n\nReturn the score, what it was based on, and the single weakest dimension. Do not compare this skill to any other. The calibration stage does that with all of them.`,
      { label: `score:${skill.split('/').slice(-2)[0]}`, phase: 'Score', schema: SCORE },
    ),
  ),
)

// A skill whose scorer returned nothing is unscored. Leaving it out of
// the distribution shifts the calibration it was meant to be read against.
// A score the oracle did not produce is unscored too. It would rank a
// guess inside the distribution.
const isOracleScore = (entry) => entry.source === 'oracle' && typeof entry.score === 'number'
const scores = scored.filter((entry) => entry && isOracleScore(entry))
// Derived from scores. The two lists then partition the skills.
const unscored = skills.filter((skill, index) => !scores.includes(scored[index]))
// Two causes need different fixes. A dead scorer agent needs a re-run.
// A scorer that found the daemon down needs the daemon provisioned.
const dropped = skills.filter((skill, index) => !scored[index])
const unavailable = skills.filter((skill, index) => scored[index] && scored[index].source === 'unavailable')

if (unscored.length) log(`no score for ${unscored.join(', ')}`)
if (dropped.length) log(`no reply from the scorer for ${dropped.join(', ')}. Re-run these skills`)
if (unavailable.length) {
  log(`daemon unavailable for ${unavailable.join(', ')}. Check whether the oracle daemon is provisioned`)
}

if (!scores.length) {
  log('no skill scored')
  return { skills, scores: [], calibration: null, unscored, unavailable, dropped }
}

const ordered = [...scores].sort((left, right) => left.score - right.score)
const digest = ordered.map((entry) => `${entry.score}  ${entry.skill}  (weakest: ${entry.weakest || 'unstated'})`).join('\n')

const calibration = await agent(
  `These skills were scored independently. Place the scores in their distribution.\n\n${digest}\n\nReport the spread, and say which scores are low relative to this set rather than to an absolute bar. A set where every score is 0.8 has no low outliers, and saying so is more useful than ranking them. Name the weakness that recurs across the bottom of the distribution, which is the one worth a systematic fix.`,
  { label: 'calibrate', phase: 'Calibrate' },
)
// A dead calibrate agent returns the same null as the skip path above.
const failed = calibration ? null : 'calibrate'
if (failed) log('no result from the calibrate stage. The scores are uncalibrated')

log(`${scores.length} skills scored, range ${ordered[0].score} to ${ordered[ordered.length - 1].score}`)

return { skills, scores: ordered, calibration, unscored, unavailable, dropped, failed }
