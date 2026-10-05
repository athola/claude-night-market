declare module 'claude-code' {
  interface PluginState {
    conserve: {
      contextPercent: number | null
      cacheReadShare: number | null
    }
  }
}
