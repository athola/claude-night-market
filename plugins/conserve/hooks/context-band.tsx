// Draws context fill and prompt-cache reuse above the prompt, for the user.
// context_warning.py stays the part Claude reads: mods can be switched off
// remotely or by policy, so this module observes and draws only. It never
// answers tool.call, hooks tool.check, or rewrites tool input.
import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

// Mirrors CRITICAL_THRESHOLD in context_warning.py (0.50), so the status
// line and the Python warning agree on when context is critical.
const CRITICAL_PERCENT = 50

const contextPercent = atom({ plugin: 'conserve', key: 'contextPercent' } as const, null)
const cacheReadShare = atom({ plugin: 'conserve', key: 'cacheReadShare' } as const, null)

const isCritical = (percent: number | null) => percent !== null && percent >= CRITICAL_PERCENT

async function reset($: EngineInterface) {
  await update($, contextPercent, () => null)
  await update($, cacheReadShare, () => null)
  await $.ui.status(undefined)
}

export const register: Register = on => {
  on('session.measure', async ($, e, next) => {
    const percent = e.context.percent
    if (percent !== undefined) {
      const previous = await read($, contextPercent)
      await update($, contextPercent, () => percent)
      if (isCritical(percent)) {
        await $.ui.status(`conserve: context ${percent}% (critical at ${CRITICAL_PERCENT}%)`)
      } else if (isCritical(previous)) {
        await $.ui.status(undefined)
      }
    }
    return next(e)
  })

  on('turn.step', async function* ($, e, next) {
    const result = yield* next(e)
    const usage = result.usage
    if (e.agentId === undefined && usage !== null) {
      const prompt = usage.input_tokens + usage.cache_read_input_tokens + usage.cache_creation_input_tokens
      if (prompt > 0) {
        await update($, cacheReadShare, () => Math.round((usage.cache_read_input_tokens / prompt) * 100))
      }
    }
    return result
  })

  // /clear, /resume and /branch reset $.state but leave the status line up.
  on('classic.SessionStart', { source: ['clear', 'resume', 'fork'] }, async ($, e, next) => {
    await reset($)
    return next(e)
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const percent = await read($, contextPercent)
    const share = await read($, cacheReadShare)
    if (e.props.hasSurvey || (percent === null && share === null)) return next(e)
    const parts: string[] = []
    if (percent !== null) parts.push(`context ${percent}%`)
    if (share !== null) parts.push(`cache ${share}%`)
    const { Box, Text } = $.ui.resolve(e)
    const theirs = await next(e)
    return (
      <Box flexDirection="column">
        {theirs}
        <Text dimColor>{parts.join(' · ')}</Text>
      </Box>
    )
  })
}
