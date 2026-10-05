import { expect, test } from 'claude-code/testing'
import type { On } from 'claude-code'
import type { Engine } from 'claude-code/testing'

// What Claude Code passes to an AbovePrompt render hook, apart from the surface.
const BAND = {
  plugin: 'conserve',
  component: 'AbovePrompt',
  requestId: 'above',
  viewport: { columns: 100, rows: 30 },
  props: { hasSurvey: false, isWorking: false, maxRows: 5, bodyColumns: 80, scroll: { offset: 0, bodyRows: 5 }, view: {} },
} as const

const ENGINE_TEXT = 'drawn by Claude Code'

// Every stub the module can reach. A missing stub makes the kit skip the
// whole hook silently, which reads as a wrong assertion rather than a gap.
function stubs(on: On, statuses: Array<string | undefined> = []) {
  on('session.measure', ($, e) => ({ changed: e.changed }))
  on('ui.render', () => ({ type: 'Text', props: {}, children: [ENGINE_TEXT] }))
  on('ui.status', ($, e) => {
    statuses.push(e.text)
    return { value: undefined }
  })
  on('classic.SessionStart', () => ({}))
  on('turn.step', async function* ($, e) {
    return {
      turnId: e.turnId,
      index: e.index,
      answer: 'ok',
      toolUses: [],
      stopReason: 'end_turn',
      usage: e.agentId
        ? { input_tokens: 0, output_tokens: 1, cache_read_input_tokens: 0, cache_creation_input_tokens: 1000, model: 'm' }
        : { input_tokens: 0, output_tokens: 1, cache_read_input_tokens: 900, cache_creation_input_tokens: 100, model: 'm' },
    }
  })
}

function measure($: Engine, percent: number) {
  return $.session.measure({
    context: { window: 200000, tokens: percent * 2000, percent },
    rateLimits: [],
    changed: ['context'],
  })
}

async function step($: Engine, agentId?: string) {
  const stream = $.turn.step({ turnId: 't', index: 0, model: 'm', messageCount: 1, ...(agentId ? { agentId } : {}) })
  let next = await stream.next()
  while (next.done !== true) next = await stream.next()
  return next.value
}

test('band shows the context percent after a measurement', async ($, on) => {
  stubs(on)
  await measure($, 42)
  const ui = await $.ui.mount({ ...BAND, surface: 'terminal' })
  expect(await ui.find({ type: 'Text', text: /context 42%/ })).toBeDefined()
})

test('band draws only the engine element before any reading', async ($, on) => {
  stubs(on)
  const ui = await $.ui.mount({ ...BAND, surface: 'terminal' })
  expect(await ui.find({ type: 'Text', text: ENGINE_TEXT })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: /context|cache/ })).toBeUndefined()
})

test('band draws nothing of its own while a survey is showing', async ($, on) => {
  stubs(on)
  await measure($, 42)
  const ui = await $.ui.mount({ ...BAND, surface: 'terminal', props: { ...BAND.props, hasSurvey: true } })
  expect(await ui.find({ type: 'Text', text: /context/ })).toBeUndefined()
  expect(await ui.find({ type: 'Text', text: ENGINE_TEXT })).toBeDefined()
})

test('status line is set at the critical threshold and cleared below it', async ($, on) => {
  const statuses: Array<string | undefined> = []
  stubs(on, statuses)
  await measure($, 42)
  expect(statuses).toEqual([])
  await measure($, 55)
  expect(statuses.length).toBe(1)
  expect(statuses[0]).toMatch(/context 55%/)
  await measure($, 30)
  expect(statuses.length).toBe(2)
  expect(statuses[1]).toBeUndefined()
})

test('band shows the prompt-cache read share of the main loop only', async ($, on) => {
  stubs(on)
  await step($)
  const ui = await $.ui.mount({ ...BAND, surface: 'terminal' })
  expect(await ui.find({ type: 'Text', text: /cache 90%/ })).toBeDefined()
  await step($, 'agent-1')
  expect(await ui.find({ type: 'Text', text: /cache 90%/ })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: /cache 0%/ })).toBeUndefined()
})

test('a /clear returns the band to the no-reading state', async ($, on) => {
  stubs(on)
  await measure($, 42)
  await step($)
  await $.classic.SessionStart({ source: 'clear' })
  const ui = await $.ui.mount({ ...BAND, surface: 'terminal' })
  expect(await ui.find({ type: 'Text', text: /context|cache/ })).toBeUndefined()
})

test('desktop draws the same band line as the terminal', async ($, on) => {
  stubs(on)
  await measure($, 42)
  await step($)
  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({ ...BAND, surface })
    expect(await ui.find({ type: 'Text', text: /context 42% .* cache 90%/ })).toBeDefined()
    await ui.unmount()
  }
})
