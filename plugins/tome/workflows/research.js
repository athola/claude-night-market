// Tome's channel fan-out as one barrier, then a synthesis.
//
// The barrier is deliberate here, unlike most fan-outs. Synthesis needs every
// channel at once: it deduplicates findings that several channels returned,
// and it has to report which channels came back empty, which is only knowable
// once they all have.
//
// This does not replace Skill(tome:research). The skill owns domain
// classification, channel weights, session state, citation formatting and the
// memory-palace export. This script owns the part that is only dispatch.
//
// The harness also bundles /deep-research over a similar channel set. Prefer
// it for a one-off question. Prefer this when the result has to land in a tome
// session with weights, TRIZ and an export path.

export const meta = {
  name: 'research',
  description:
    'Fan out one research question across tome channels and merge the findings into a ranked, per-channel report',
  whenToUse:
    'Run from /tome:research once the topic is classified and the channel plan exists. Requires an explicit request: a workflow never starts unasked. args carry topic, channels (code|discourse|academic|triz), domain and trizDepth. Returns findings for the skill to rank, cite and store; it writes nothing.',
  phases: [
    { title: 'Channels', detail: 'one agent per selected channel' },
    { title: 'Synthesis', detail: 'merge, dedupe, and say which channels were empty' },
  ],
}

const input = args || {}

if (!input.topic) {
  log('research.js started with no topic')
  return {
    started: false,
    reason: 'no-topic',
    next: 'This workflow needs a classified topic and a channel plan. Run /tome:research, which classifies the domain and picks channels before dispatching. Do not improvise a plan here.',
  }
}

const CHANNELS = [
  { key: 'code', agentType: 'tome:code-searcher', brief: 'Search GitHub for real implementations, libraries and prior art. Report repositories with what each one actually does.' },
  { key: 'discourse', agentType: 'tome:discourse-scanner', brief: 'Scan Hacker News, Lobsters, Reddit and practitioner blogs for experience reports. Keep contrarian views rather than smoothing them.' },
  { key: 'academic', agentType: 'tome:literature-reviewer', brief: 'Search arXiv and Semantic Scholar. Prefer papers whose abstract states a measured result over ones that survey.' },
  { key: 'triz', agentType: 'tome:triz-analyst', brief: 'Find the technical contradiction, then look for how an adjacent field resolved the same shape. State the bridge mapping explicitly.' },
]

const wanted = Array.isArray(input.channels) ? input.channels : ['code', 'discourse']
const selected = CHANNELS.filter((c) => wanted.includes(c.key))

if (!selected.length) {
  return { started: false, reason: 'no-channels', next: 'No known channel was requested. Known channels: code, discourse, academic, triz.' }
}

const skipped = CHANNELS.filter((c) => !selected.includes(c)).map((c) => c.key)
if (skipped.length) log(`not searching: ${skipped.join(', ')}`)

const FINDINGS = {
  type: 'object',
  required: ['searched', 'findings'],
  properties: {
    searched: { type: 'string' },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        required: ['title', 'url', 'why'],
        properties: {
          title: { type: 'string' },
          url: { type: 'string' },
          why: { type: 'string' },
        },
      },
    },
  },
}

phase('Channels')

const domain = input.domain ? ` Domain: ${input.domain}.` : ''
const depth = input.trizDepth ? ` TRIZ depth: ${input.trizDepth}.` : ''

const returned = await parallel(
  selected.map((c) => () =>
    agent(`${c.brief}\n\nTopic: ${input.topic}.${domain}${depth}\n\nRecord what you searched for, even when you find nothing. An empty channel and a broken channel must not look alike.`, {
      label: `channel:${c.key}`,
      phase: 'Channels',
      agentType: c.agentType,
      schema: FINDINGS,
    }).then((r) => ({ channel: c.key, result: r })),
  ),
)

phase('Synthesis')

const answered = returned.filter((r) => r && r.result)
const failed = selected
  .map((c) => c.key)
  .filter((key) => !answered.some((r) => r.channel === key))
const empty = answered.filter((r) => r.result.findings.length === 0).map((r) => r.channel)

// Dedupe by URL across channels, in plain code: this is arithmetic, and a
// finding corroborated by two channels is stronger than one that is not.
const byUrl = new Map()
for (const { channel, result } of answered) {
  for (const f of result.findings) {
    const seen = byUrl.get(f.url)
    if (seen) {
      if (!seen.channels.includes(channel)) seen.channels.push(channel)
    } else {
      byUrl.set(f.url, { ...f, channels: [channel] })
    }
  }
}

const findings = [...byUrl.values()].sort((a, b) => b.channels.length - a.channels.length)

log(`${findings.length} findings from ${answered.length} of ${selected.length} channels`)

return {
  topic: input.topic,
  findings,
  coverage: {
    searched: answered.map((r) => ({ channel: r.channel, query: r.result.searched })),
    empty,
    failed,
    skipped,
  },
  next: 'Rank, cite and store these through Skill(tome:research). An empty channel is reported above with what it searched for, so a thin topic and a broken channel stay distinguishable.',
}
