# Network and Data

Three parts of the marketplace reach off your machine, and each can be
turned off. This page names every one, what it sends, under whose
credentials, and the switch that disables it. It is for a practitioner
deciding whether to install, and for an operator auditing what a
session can reach. The README carries the one-paragraph summary.

Two hooks use your existing GitHub credentials, and both fail
silently when `gh` is unauthenticated or the network is
unavailable.

- **Star prompt** (`leyline`,
  `plugins/leyline/hooks/auto-star-repo.sh`). On session start it
  checks whether you have starred `athola/claude-night-market`,
  using your `gh` CLI auth or a `GITHUB_TOKEN` / `GH_TOKEN` env
  var. It only reads star status and asks once per session. It
never stars or unstars without your consent. Opt out by setting
  `CLAUDE_NIGHT_MARKET_NO_STAR_PROMPT=1`.
- **Learnings and insights posting** (`abstract`,
  `plugins/abstract/hooks/post_learnings_stop.py`). On session
  stop, if `~/.claude/skills/LEARNINGS.md` has content, it posts a
  skill-usage summary (and may promote high-severity items to
  issues) via your authenticated `gh` CLI. The target is detected
  at runtime: a `target_repo` override in
  `~/.claude/skills/discussions/config.json`, otherwise the
  current repo from `gh repo view`. Posting defaults to on. Opt
out by setting `auto_post_learnings` to `false` in that config
  file.

The third sends the contents of your files. **Delegation**
(`conjure`, also reached by `attune` missions and `egregore`
pipeline steps) hands execution work to whichever external model
CLI answers first, in the order Gemini, Qwen, MiniMax, GLM, Muse,
Codex, OpenCode. The prompt and the file contents it carries go to
that provider, under the credentials you configured for it. This
runs by default. Decline it for one run with
`CONJURE_DELEGATION=off`, or for one machine by setting
`"enabled": false` in
`~/.claude/hooks/delegation/config.json`. When no provider
answers, the work stays on your machine.
