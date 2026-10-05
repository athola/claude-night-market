import { expect, mock, test } from 'claude-code/testing'
import type { On } from 'claude-code'
import type { Engine } from 'claude-code/testing'

// What Claude Code passes to an AbovePrompt render hook, apart from the surface.
const BAND = {
  plugin: 'egregore',
  component: 'AbovePrompt',
  requestId: 'above',
  viewport: { columns: 100, rows: 30 },
  props: { hasSurvey: false, isWorking: false, maxRows: 5, bodyColumns: 80, scroll: { offset: 0, bodyRows: 5 }, view: {} },
} as const

const ENGINE_TEXT = 'drawn by Claude Code'

function item(id: string, status: string, step = 'brainstorm', stage = 'intake') {
  return { id, pipeline_stage: stage, pipeline_step: step, attempts: 1, max_attempts: 3, status }
}

// The manifest on disk, as the fs stubs answer it. A test changes these to
// simulate the orchestrator writing a new manifest.
type Disk = { manifest: string | null; mtimeMs: number; registerDenies?: boolean; logs?: string[]; reads?: number; stats?: number; registrations?: number }

// Every stub the module can reach. A missing stub makes the kit skip the
// whole hook silently, which reads as a wrong assertion rather than a gap.
function stubs(on: On, disk: Disk) {
  const clock = mock.clock(on)
  on('session.start', () => ({ cwd: '/work' }))
  on('classic.SessionStart', () => ({}))
  on('ui.render', () => ({ type: 'Text', props: {}, children: [ENGINE_TEXT] }))
  on('command.register', () => {
    disk.registrations = (disk.registrations ?? 0) + 1
    return disk.registerDenies ? { deny: 'name taken' } : { value: undefined }
  })
  on('ui.log', ($, e) => {
    disk.logs?.push(e.text)
    return { value: undefined }
  })
  on('fs.read', ($, e) => {
    disk.reads = (disk.reads ?? 0) + 1
    return disk.manifest !== null && e.path.endsWith('.egregore/manifest.json')
      ? { value: disk.manifest }
      : { deny: 'ENOENT' }
  })
  on('fs.stat', ($, e) => {
    disk.stats = (disk.stats ?? 0) + 1
    return disk.manifest !== null && e.path.endsWith('.egregore/manifest.json')
      ? { value: { kind: 'file', size: disk.manifest.length, mtimeMs: disk.mtimeMs, isLink: false } }
      : { deny: 'ENOENT' }
  })
  return clock
}

function start($: Engine) {
  return $.session.start({ surface: 'terminal', isInteractive: true, cwd: '/work' })
}

async function bandText($: Engine) {
  const ui = await $.ui.mount({ ...BAND, surface: 'terminal' })
  return ui.find({ type: 'Text', text: /egregore/ })
}

const RUNNING = JSON.stringify({
  project_dir: '/work',
  work_items: [item('wrk-1', 'completed'), item('wrk-2', 'active', 'execute', 'build'), item('wrk-3', 'pending')],
})

test('/egregore-loop names the active item, stage, step and what remains', async ($, on) => {
  stubs(on, { manifest: RUNNING, mtimeMs: 1 })
  await start($)
  const answer = await $.command.run({ command: 'egregore-loop', args: '' })
  expect(answer.text).toMatch(/wrk-2/)
  expect(answer.text).toMatch(/build\/execute/)
  expect(answer.text).toMatch(/attempt 1\/3/)
  expect(answer.text).toMatch(/2 remaining/)
  expect(await bandText($)).toBeDefined()
})

test('without a manifest the command says no loop and the band stays empty', async ($, on) => {
  stubs(on, { manifest: null, mtimeMs: 0 })
  await start($)
  const answer = await $.command.run({ command: 'egregore-loop', args: '' })
  expect(answer.text).toMatch(/no egregore loop/i)
  expect(await bandText($)).toBeUndefined()
})

test('a manifest whose items are all finished draws nothing of its own', async ($, on) => {
  const done = JSON.stringify({ work_items: [item('wrk-1', 'completed'), item('wrk-2', 'failed')] })
  stubs(on, { manifest: done, mtimeMs: 1 })
  await start($)
  expect(await bandText($)).toBeUndefined()
  const answer = await $.command.run({ command: 'egregore-loop', args: '' })
  expect(answer.text).toMatch(/finished/)
})

test('a manifest using the legacy items key is read', async ($, on) => {
  const legacy = JSON.stringify({ items: [item('old-1', 'active', 'review', 'quality')] })
  stubs(on, { manifest: legacy, mtimeMs: 1 })
  await start($)
  const found = await bandText($)
  expect(found).toBeDefined()
  const answer = await $.command.run({ command: 'egregore-loop', args: '' })
  expect(answer.text).toMatch(/old-1/)
  expect(answer.text).toMatch(/quality\/review/)
})

test('malformed JSON is reported by the command and breaks no hook', async ($, on) => {
  stubs(on, { manifest: '{ not json', mtimeMs: 1 })
  await start($)
  const answer = await $.command.run({ command: 'egregore-loop', args: '' })
  expect(answer.text).toMatch(/not valid JSON/)
  expect(await bandText($)).toBeUndefined()
})

test('the timer picks up a manifest the orchestrator rewrote', async ($, on) => {
  const disk: Disk = { manifest: RUNNING, mtimeMs: 1 }
  const clock = stubs(on, disk)
  await start($)
  disk.manifest = JSON.stringify({ work_items: [item('wrk-2', 'active', 'pr-prep', 'ship')] })
  disk.mtimeMs = 2
  await clock.advance(30_000)
  const ui = await $.ui.mount({ ...BAND, surface: 'terminal' })
  expect(await ui.find({ type: 'Text', text: /ship\/pr-prep/ })).toBeDefined()
})

test('a refused command registration still leaves the band refreshing', async ($, on) => {
  const disk: Disk = { manifest: RUNNING, mtimeMs: 1, registerDenies: true, logs: [] }
  const clock = stubs(on, disk)
  await start($)
  disk.manifest = JSON.stringify({ work_items: [item('wrk-9', 'active', 'review', 'quality')] })
  disk.mtimeMs = 2
  await clock.advance(30_000)
  const ui = await $.ui.mount({ ...BAND, surface: 'terminal' })
  expect(await ui.find({ type: 'Text', text: /wrk-9/ })).toBeDefined()
  expect(disk.logs?.join('\n')).toMatch(/egregore-loop not registered/)
})

test('after /clear the band reads the manifest again', async ($, on) => {
  stubs(on, { manifest: RUNNING, mtimeMs: 1 })
  await $.classic.SessionStart({ source: 'clear' })
  expect(await bandText($)).toBeDefined()
})

test('the timer skips the read while the manifest mtime is unchanged', async ($, on) => {
  const disk: Disk = { manifest: RUNNING, mtimeMs: 1 }
  const clock = stubs(on, disk)
  await start($)
  const readsAfterStart = disk.reads
  await clock.advance(90_000)
  expect(disk.reads).toBe(readsAfterStart)
})

test('a JSON value that is not an object is reported as malformed', async ($, on) => {
  stubs(on, { manifest: '42', mtimeMs: 1 })
  await start($)
  const answer = await $.command.run({ command: 'egregore-loop', args: '' })
  expect(answer.text).toMatch(/not valid JSON/)
})

test('band draws nothing of its own while a survey is showing', async ($, on) => {
  stubs(on, { manifest: RUNNING, mtimeMs: 1 })
  await start($)
  const ui = await $.ui.mount({ ...BAND, surface: 'terminal', props: { ...BAND.props, hasSurvey: true } })
  expect(await ui.find({ type: 'Text', text: /egregore/ })).toBeUndefined()
  expect(await ui.find({ type: 'Text', text: ENGINE_TEXT })).toBeDefined()
})

test('a second session.start replaces the timer instead of stacking one', async ($, on) => {
  const disk: Disk = { manifest: RUNNING, mtimeMs: 1 }
  const clock = stubs(on, disk)
  await start($)
  await start($)
  expect(disk.registrations).toBe(2)
  const statsBefore = disk.stats ?? 0
  await clock.advance(30_000)
  expect(disk.stats).toBe(statsBefore + 1)
})
