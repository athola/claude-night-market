// Find where platform clients that ship independently have drifted apart.
//
// A team that avoids synchronization meetings lets each platform ship as
// fast as it can, then finds the divergence after the fact (ADR-0029).
// This is the finding half. Three stages:
//
//   1. Inventory: one agent per platform root lists the features a user
//      can reach, each with the files that implement it. Agents never see
//      each other's inventory, so one platform cannot set the vocabulary.
//   2. Align: one agent reads every inventory and proposes mismatches. It
//      is the barrier, because naming the same feature across platforms
//      needs all of them at once.
//   3. Verify: each proposed mismatch goes to its own agent, which reads
//      the code on every named platform before confirming it. Alignment
//      guesses from summaries, and a guess is not a finding.
//
// It reports. It changes no code and does not decide which platform is
// right. At most four platforms and five verified mismatches keep a run
// under ten agents.

export const meta = {
  name: 'parity-sweep',
  description:
    'Find features that one platform client has and another lacks, or that behave differently, and confirm each with file evidence',
  whenToUse:
    'Run after platform clients have shipped independently, to find where they diverge. args.platforms lists each client as {name, root}. args.focus narrows the sweep to one feature area. Returns confirmed mismatches. It changes no code.',
  phases: [
    { title: 'Inventory', detail: 'one agent per platform root' },
    { title: 'Align', detail: 'one agent proposes mismatches across inventories' },
    { title: 'Verify', detail: 'one agent per proposed mismatch' },
  ],
}

const MAX_PLATFORMS = 4
const MAX_VERIFIED = 5

const input = args || {}
const platforms = input.platforms
if (!Array.isArray(platforms) || platforms.length < 2) {
  return {
    started: false,
    reason: 'need-two-platforms',
    next: 'Pass args.platforms as a list of at least two {name, root} entries.',
  }
}
const malformed = platforms.filter((p) => !p || typeof p.name !== 'string' || typeof p.root !== 'string')
if (malformed.length) {
  return {
    started: false,
    reason: 'platform-without-name-or-root',
    next: 'Give every entry in args.platforms a name and a root path.',
  }
}
// Dropping a platform silently would read as parity on the ones left out.
const swept = platforms.slice(0, MAX_PLATFORMS)
const dropped = platforms.slice(MAX_PLATFORMS).map((p) => p.name)
if (dropped.length) log(`swept the first ${MAX_PLATFORMS} platforms. Not swept: ${dropped.join(', ')}`)

const focus = typeof input.focus === 'string' && input.focus ? input.focus : null
const scope = focus ? `Cover only features in this area: ${focus}.` : 'Cover every feature a user can reach.'

const INVENTORY = {
  type: 'object',
  required: ['platform', 'features'],
  properties: {
    platform: { type: 'string' },
    features: {
      type: 'array',
      items: {
        type: 'object',
        required: ['key', 'summary', 'files'],
        properties: {
          key: { type: 'string' },
          summary: { type: 'string' },
          files: { type: 'array', items: { type: 'string' } },
        },
      },
    },
  },
}

const ALIGNMENT = {
  type: 'object',
  required: ['mismatches'],
  properties: {
    mismatches: {
      type: 'array',
      items: {
        type: 'object',
        required: ['feature', 'kind', 'detail'],
        properties: {
          feature: { type: 'string' },
          kind: { type: 'string', enum: ['missing', 'divergent'] },
          present_on: { type: 'array', items: { type: 'string' } },
          absent_on: { type: 'array', items: { type: 'string' } },
          detail: { type: 'string' },
        },
      },
    },
  },
}

const VERDICT = {
  type: 'object',
  required: ['feature', 'confirmed', 'evidence'],
  properties: {
    feature: { type: 'string' },
    confirmed: { type: 'boolean' },
    evidence: { type: 'string' },
  },
}

const inventories = await parallel(
  swept.map((platform) => () =>
    agent(
      `List the user-facing features of the ${platform.name} client under ${platform.root}. ${scope} Give each feature a short key, a one-line summary of its behavior, and the files that implement it. Read code, not only names. Report only features you found in the code.`,
      { label: `inventory:${platform.name}`, phase: 'Inventory', schema: INVENTORY },
    ),
  ),
)

const found = inventories.filter(Boolean)
const missing = swept.filter((_, index) => !inventories[index]).map((p) => p.name)
// A platform with no inventory would look like it lacks every feature.
if (found.length < 2) {
  log(`no inventory for ${missing.join(', ')}. Too few platforms to compare`)
  return {
    started: true,
    reason: 'fewer-than-two-inventories',
    next: 'Check the platform roots and run the sweep again.',
    missing,
  }
}
if (missing.length) log(`no inventory for ${missing.join(', ')}. Those platforms are unswept, not empty`)

const alignment = await agent(
  `Compare these platform inventories and list the mismatches. A missing mismatch is a feature some platforms have and others lack. A divergent mismatch is a feature every platform has with different behavior. Match features by behavior, not by key. Inventories: ${JSON.stringify(found)}`,
  { label: 'align', phase: 'Align', schema: ALIGNMENT },
)

const proposed = alignment ? alignment.mismatches : []
const toVerify = proposed.slice(0, MAX_VERIFIED)
const unverified = proposed.slice(MAX_VERIFIED).map((m) => m.feature)
if (unverified.length) log(`${unverified.length} proposed mismatches left unverified`)

const roots = found
  .map((inv) => swept.find((p) => p.name === inv.platform))
  .filter(Boolean)
  .map((p) => `${p.name} at ${p.root}`)
  .join(', ')

const verdicts = await parallel(
  toVerify.map((mismatch) => () =>
    agent(
      `Confirm or refute one proposed platform mismatch. Feature: ${mismatch.feature}. Kind: ${mismatch.kind}. Claim: ${mismatch.detail}. Platforms: ${roots}. Read the code on every platform before you decide. Quote the file and line that settles it. Change no code.`,
      { label: `verify:${mismatch.feature}`, phase: 'Verify', schema: VERDICT },
    ),
  ),
)

const checked = verdicts.filter(Boolean)
// A verifier that died left no verdict: that mismatch is unchecked, not refuted.
const unchecked = toVerify.filter((_, index) => !verdicts[index]).map((m) => m.feature)
const confirmed = checked.filter((v) => v.confirmed)
const refuted = checked.filter((v) => !v.confirmed)
log(`${confirmed.length} confirmed, ${refuted.length} refuted, ${unchecked.length} unchecked, ${unverified.length} unverified`)

return {
  started: true,
  confirmed,
  refuted,
  proposed: proposed.length,
  unverified,
  unchecked,
  missing,
  dropped,
}
