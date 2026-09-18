// Five reviewers over one document, each blind to the others, because
// the layers of a document fail independently.
//
// A hallucinated file path and a paragraph with no thesis are both
// defects and nothing about finding one helps find the other. Asked for
// "a review", a session returns sentence-level slop, because that is the
// layer with the most matches. The layers here are the ones the house
// rule already separates: critical patterns fail a document outright,
// document economy is structural, audience fit decides who the
// structure is for, sentence slop is local, and evidence backing is
// about claims the repository has to support.
//
// Audience is its own layer rather than part of economy because the two
// disagree usefully. A section can carry the thesis and still belong to
// a different reader, and that finding is a move, not a cut.

export const meta = {
  name: 'doc-sweep',
  description:
    'Review documents through five independent layers, from identity leaks and hallucinated paths down to sentence-level slop',
  whenToUse:
    'Run on a batch of documents before publishing, or on a large document whose problems span layers. args.docs lists the files, args.tier the declared audience tier when there is one. A .py file is accepted and is reviewed as its comments and docstrings. Returns findings by layer, critical first; it edits nothing.',
  phases: [
    { title: 'Layers', detail: 'five reviewers, five questions' },
    { title: 'Rank', detail: 'critical first, then structural, then local' },
  ],
}

const input = args || {}
const docs = input.docs || []

if (!docs.length) {
  log('doc-sweep.js started with no documents')
  return {
    started: false,
    reason: 'no-docs',
    next: 'Pass args.docs as the files to review. Markdown, or .py to review its comments and docstrings.',
  }
}

const target = docs.join(', ')
const tier = input.tier || null
const tierNote = tier
  ? `The declared audience tier is \`${tier}\`.`
  : 'No audience tier was declared. Say what each document appears to be written for, and report the missing declaration as a finding rather than picking one silently.'

const FINDINGS = {
  type: 'object',
  required: ['layer', 'findings'],
  properties: {
    layer: { type: 'string' },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        required: ['doc', 'problem'],
        properties: {
          doc: { type: 'string' },
          line: { type: 'number' },
          problem: { type: 'string' },
          rewrite: { type: 'string' },
        },
      },
    },
  },
}

const LAYERS = [
  {
    key: 'critical',
    agentType: 'scribe:slop-hunter',
    brief:
      'Find identity leaks, hallucinated identifiers and paths, and bare TODO markers with no tracked issue. Check that every backticked path and every named command actually exists. A single match here fails the document; report each one.',
  },
  {
    key: 'economy',
    agentType: 'scribe:doc-editor',
    brief:
      'Judge whether the lead states the single takeaway, whether every sentence carries or bounds or instances the thesis, and whether anything but the thesis repeats. Report throat-clears, restated headings, and sections that could be cut whole.',
  },
  {
    key: 'audience',
    agentType: 'scribe:doc-editor',
    brief:
      `Judge who each document is for and whether every section serves that reader. ${tierNote} Tiers are newcomer (has never seen this project), practitioner (knows the domain, not this repository), and expert (already familiar with the material). For each off-tier section, say which tier it actually serves and name the deep dive it should move to: modules/<topic>.md for a skill, docs/deep-dive/<topic>.md for a repo doc. Report a move, never a deletion. Content a newcomer cannot use is usually answering a question they have not asked yet, not weak writing. Skip creative output entirely: voice profiles, session-to-post narrative, and fiction.`,
  },
  {
    key: 'sentence',
    agentType: 'scribe:prose-reviewer',
    brief:
      'Find sentence-level slop: contrastive negation, participial tail-loading, hedging seesaws, significance clusters, em-dash density, and British spellings. Offer the rewrite, not just the flag. A .py document is its comments and docstrings; `scripts/slop_score.py --audit <file>` reads it that way and reports the real line numbers. Leave notation alone: an arrow in a mapping table, a plus in a formula, and a character quoted because the code matches it are code, not prose.',
  },
  {
    key: 'evidence',
    agentType: 'scribe:doc-verifier',
    brief:
      'Find quality claims with no evidence in the repository: "production-ready", "fast", "scalable", "robust". For each, say what evidence would be required and whether it exists here. No evidence means delete the claim, not soften it.',
  },
]

const swept = await parallel(
  LAYERS.map((layer) => () =>
    agent(
      `Review these documents on one layer only. ${layer.brief}\n\nDocuments: ${target}\n\nStay inside your layer. Another reviewer has the others, and a finding reported twice costs a human the same time as a finding missed.`,
      {
        label: `sweep:${layer.key}`,
        phase: 'Layers',
        agentType: layer.agentType,
        schema: FINDINGS,
      },
    ),
  ),
)

const reports = swept.filter(Boolean)
const findings = reports.flatMap((report) =>
  (report.findings || []).map((finding) => ({ ...finding, layer: report.layer })),
)

const critical = findings.filter((finding) => finding.layer === 'critical')

if (!findings.length) {
  log(`${docs.length} documents, no findings`)
  return { docs, findings: [], ranked: null }
}

const digest = findings
  .map((finding) => `[${finding.layer}] ${finding.doc}${finding.line ? `:${finding.line}` : ''} ${finding.problem}`)
  .join('\n')

const ranked = await agent(
  `These findings came from five blind reviewers. Order them for someone about to fix them.\n\n${digest}\n\nCritical findings come first and are not negotiable against style. Then structural findings, because cutting a section deletes the sentence-level findings inside it, and fixing those first wastes the work. Say explicitly where a structural fix makes a local finding moot, and where an audience finding moves a section that other findings sit inside.`,
  { label: 'rank', phase: 'Rank' },
)

log(`${findings.length} findings across ${docs.length} documents, ${critical.length} critical`)

return { docs, findings, critical, ranked }
