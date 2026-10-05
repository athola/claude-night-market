// Shows the running egregore loop above the prompt and answers /egregore-loop
// without a model turn. The Python hooks drive the loop; this module reads
// .egregore/manifest.json and writes nothing. It observes and draws only:
// it never answers tool.call, hooks tool.check, or rewrites tool input.
import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register, Timer } from 'claude-code'

import type { LoopView } from '../types'

// Relative paths resolve against the session cwd. _manifest_utils.py also
// walks up the parents; the band covers the common case, cwd at the root.
const MANIFEST = '.egregore/manifest.json'
const REFRESH_MS = 30_000
// Same set as ACTIVE_STATUSES in _manifest_utils.py: work still to do.
const UNFINISHED = new Set(['active', 'paused', 'pending'])

const loop = atom({ plugin: 'egregore', key: 'loop' } as const, null)

type Reading = { kind: 'missing' } | { kind: 'malformed' } | { kind: 'read'; view: LoopView | null }

type Item = Record<string, unknown>

function viewOf(manifest: Record<string, unknown>): LoopView | null {
  const listed = manifest.work_items || manifest.items
  const items: Item[] = Array.isArray(listed) ? listed : []
  const unfinished = items.filter(i => UNFINISHED.has(String(i.status)))
  const current = unfinished.find(i => i.status === 'active') ?? unfinished[0]
  if (current === undefined) return null
  return {
    id: String(current.id),
    stage: String(current.pipeline_stage),
    step: String(current.pipeline_step),
    attempts: Number(current.attempts ?? 0),
    maxAttempts: Number(current.max_attempts ?? 0),
    remaining: unfinished.length,
  }
}

async function readManifest($: EngineInterface): Promise<Reading> {
  let text: string
  try {
    text = await $.fs.read(MANIFEST)
  } catch {
    // A refused read is how a missing manifest arrives: no loop here.
    return { kind: 'missing' }
  }
  try {
    const parsed: unknown = JSON.parse(text)
    if (typeof parsed !== 'object' || parsed === null) return { kind: 'malformed' }
    return { kind: 'read', view: viewOf(parsed as Record<string, unknown>) }
  } catch {
    // JSON.parse throws SyntaxError on a half-written file; report it, never throw.
    return { kind: 'malformed' }
  }
}

// Re-reads the manifest when its mtime differs from `seenMtimeMs`, and
// answers the mtime now on disk (undefined once the file is gone).
async function refreshIfChanged($: EngineInterface, seenMtimeMs: number | undefined) {
  let mtimeMs: number | undefined
  try {
    mtimeMs = (await $.fs.stat(MANIFEST)).mtimeMs
  } catch {
    // A refused stat means the manifest is gone; the band then goes empty.
    mtimeMs = undefined
  }
  if (mtimeMs !== seenMtimeMs) {
    const reading = await readManifest($)
    await update($, loop, () => (reading.kind === 'read' ? reading.view : null))
  }
  return mtimeMs
}

function describe(view: LoopView) {
  return `egregore: ${view.id} · ${view.stage}/${view.step} · attempt ${view.attempts}/${view.maxAttempts} · ${view.remaining} remaining`
}

export const register: Register = on => {
  let seenMtimeMs: number | undefined
  let timer: Timer | undefined

  on('session.start', async ($, e, next) => {
    seenMtimeMs = await refreshIfChanged($, seenMtimeMs)
    timer?.cancel()
    timer = $.clock.every(REFRESH_MS, async () => {
      seenMtimeMs = await refreshIfChanged($, seenMtimeMs)
    })
    // Registered last: a taken name throws, and the band must still refresh.
    try {
      await $.command.register({
        name: 'egregore-loop',
        description: 'Show the running egregore loop without a model turn',
        immediate: true,
      })
    } catch (error) {
      await $.ui.log(`egregore: /egregore-loop not registered: ${String(error)}`)
    }
    return next(e)
  })

  // /clear, /resume and /branch reset $.state, and session.start does not
  // fire again after them.
  on('classic.SessionStart', { source: ['clear', 'resume', 'fork'] }, async ($, e, next) => {
    seenMtimeMs = await refreshIfChanged($, undefined)
    return next(e)
  })

  on('command.run', { command: 'egregore-loop' }, async $ => {
    const reading = await readManifest($)
    if (reading.kind === 'missing') return { text: `No egregore loop: ${MANIFEST} not found in this directory.` }
    if (reading.kind === 'malformed') return { text: `No egregore loop: ${MANIFEST} is not valid JSON.` }
    if (reading.view === null) return { text: 'No egregore loop: every work item is finished.' }
    return { text: describe(reading.view) }
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const view = await read($, loop)
    if (e.props.hasSurvey || view === null) return next(e)
    const { Box, Text } = $.ui.resolve(e)
    const theirs = await next(e)
    return (
      <Box flexDirection="column">
        {theirs}
        <Text dimColor>{describe(view)}</Text>
      </Box>
    )
  })
}
