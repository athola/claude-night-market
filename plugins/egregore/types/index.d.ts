export type LoopView = {
  id: string
  stage: string
  step: string
  attempts: number
  maxAttempts: number
  remaining: number
}

declare module 'claude-code' {
  interface PluginState {
    egregore: { loop: LoopView | null }
  }
}
