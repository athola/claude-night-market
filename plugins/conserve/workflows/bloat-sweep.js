// Tier 2 of the bloat audit, fanned out by area instead of by scan.
//
// The tiered audit runs cheap signals first and escalates only what they
// flag. Tier 2 is where the cost lands, because each flagged area needs
// a real read. Those reads are independent, so they run together, and
// each area's dedupe happens inside its own stage instead of behind a
// barrier that makes every area wait for the slowest.
//
// The consolidation at the end is a barrier and needs to be: a duplicate
// block spanning two areas is only visible once both have reported.

export const meta = {
  name: 'bloat-sweep',
  description:
    'Run the deep bloat scan across several code areas at once and consolidate the findings that span more than one',
  whenToUse:
    'Run after a tier-1 scan flags areas, or before a release. args.areas lists the directories to scan; args.tier selects the depth. Returns findings ranked by what deleting them would save; it deletes nothing.',
  phases: [
    { title: 'Scan', detail: 'one agent per flagged area' },
    { title: 'Consolidate', detail: 'find the duplication that spans areas' },
  ],
}

const input = args || {}
const areas = input.areas || []

if (!areas.length) {
  log('bloat-sweep.js started with no areas')
  return {
    started: false,
    reason: 'no-areas',
    next: 'Run /conserve:bloat-scan first. Its tier-1 pass names the areas worth the deep read; scanning everything is the cost this workflow exists to avoid.',
  }
}

const FINDINGS = {
  type: 'object',
  required: ['area', 'findings'],
  properties: {
    area: { type: 'string' },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        required: ['kind', 'location', 'evidence'],
        properties: {
          kind: {
            type: 'string',
            enum: ['dead-code', 'duplication', 'god-object', 'doc-bloat', 'unused-dep'],
          },
          location: { type: 'string' },
          evidence: { type: 'string' },
          lines: { type: 'number' },
        },
      },
    },
  },
}

const scanned = await parallel(
  areas.map((area) => () =>
    agent(
      `Scan ${area} for bloat, following Skill(conserve:bloat-detector).\n\nReport only what you can point at with a location and evidence. A symbol with no reference is dead code; a symbol you did not find a reference for is a symbol you did not search hard enough for, and the difference matters. Say which you have. Delete nothing.`,
      {
        label: `scan:${area}`,
        phase: 'Scan',
        agentType: 'conserve:bloat-auditor',
        schema: FINDINGS,
      },
    ),
  ),
)

const reports = scanned.filter(Boolean)
const all = reports.flatMap((report) => report.findings || [])

if (all.length < 2) {
  log(`${all.length} findings; nothing to consolidate across areas`)
  return { areas, findings: all, crossArea: null }
}

const digest = all
  .map((finding) => `${finding.kind} @ ${finding.location}: ${finding.evidence}`)
  .join('\n')

const crossArea = await agent(
  `These findings came from separate area scans that could not see each other. Report the duplication that spans more than one area, which no single scan could have found.\n\n${digest}\n\nRank what remains by the lines deleting it would save, and say for each whether deletion or integration is the better move. The repository prefers integration over deletion where integration is possible.`,
  { label: 'consolidate', phase: 'Consolidate' },
)

log(`${all.length} findings across ${reports.length} areas`)

return { areas, findings: all, crossArea }
