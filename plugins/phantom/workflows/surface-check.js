// Each desktop control surface verified by its own agent, because a
// failure in one must not stop the others from being checked.
//
// Desktop automation fails in ways that are specific to the surface:
// the screenshot path is a permission problem, the keyboard path is a
// focus problem, the window path is a compositor problem. Checked in
// sequence, the first failure ends the run and the operator learns
// about one of three problems. Checked in parallel, they learn about
// all three and fix them in one pass.

export const meta = {
  name: 'surface-check',
  description:
    'Verify each desktop control surface independently so one failing surface does not hide the state of the others',
  whenToUse:
    'Run before relying on desktop control, or when a control action failed and the cause is unclear. args.surfaces narrows the set. Returns a per-surface verdict with its remedy; it changes no system setting.',
  phases: [{ title: 'Surfaces', detail: 'one agent per control surface' }],
}

const input = args || {}

const ALL_SURFACES = [
  { key: 'screenshot', brief: 'Capture a screenshot and confirm the file exists and is non-empty. On macOS this is a screen-recording permission, and the failure is silent: the capture succeeds and the image is blank or missing.' },
  { key: 'pointer', brief: 'Confirm the pointer can be located and moved. Report whether the move was observed or only requested.' },
  { key: 'keyboard', brief: 'Confirm a keystroke reaches the focused window. Focus is the usual failure: the key is sent and nothing has it.' },
  { key: 'windows', brief: 'Confirm windows can be enumerated with their titles and bounds. An empty list is a permission failure, not an empty desktop.' },
]

const surfaces = input.surfaces
  ? ALL_SURFACES.filter((surface) => input.surfaces.includes(surface.key))
  : ALL_SURFACES

const VERDICT = {
  type: 'object',
  required: ['surface', 'working', 'evidence'],
  properties: {
    surface: { type: 'string' },
    working: { type: 'boolean' },
    evidence: { type: 'string' },
    remedy: { type: 'string' },
  },
}

const checked = await parallel(
  surfaces.map((surface) => () =>
    agent(
      `Verify one desktop control surface: ${surface.brief}\n\nReport what you actually observed. A command that exited 0 is not evidence that the surface works, and several of these exit 0 while doing nothing. When it does not work, name the permission or setting that would fix it. Change no system setting.`,
      { label: `check:${surface.key}`, phase: 'Surfaces', schema: VERDICT },
    ),
  ),
)

const verdicts = checked.filter(Boolean)
const broken = verdicts.filter((verdict) => !verdict.working)

log(
  broken.length
    ? `${broken.length} of ${verdicts.length} surfaces not working`
    : `all ${verdicts.length} surfaces working`,
)

return { verdicts, broken }
