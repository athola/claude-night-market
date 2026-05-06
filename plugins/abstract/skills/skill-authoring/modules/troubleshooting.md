# Skill-Authoring Troubleshooting

Common failures when authoring skills, with diagnosis steps and
fixes. Use this module when a skill you wrote does not behave
the way the test corpus says it should. Each section names a
symptom, lists the likely causes in order of frequency, and
gives the fix.

## Symptom: skill does not appear in `/skills`

The skill is on disk but the harness does not list it.

### Likely causes

1. **Frontmatter syntax error**. YAML is strict about colons
   and quoting. A description containing an unquoted colon
   (`description: Use when: X`) fails to parse on Claude Code
   before 2.1.69.
2. **Missing `description:` field**. Before 2.1.69, skills
   without a description were silently excluded from the list.
3. **Wrong filename**. The file must be named exactly
   `SKILL.md` (case-sensitive). `Skill.md` or `skill.md` will
   not load.
4. **Plugin not installed**. The skill is in a plugin that has
   not been loaded into the harness.

### Diagnosis

```bash
# Verify the file exists with the exact name
ls plugins/<plugin>/skills/<skill>/SKILL.md

# Validate the frontmatter parses
python plugins/abstract/scripts/skill_validator.py \
  plugins/<plugin>/skills/<skill>/SKILL.md

# Check the harness sees the plugin
ls ~/.claude/plugins/ 2>/dev/null
```

### Fix

If the description contains a colon, quote the value:

```yaml
description: 'Audit hooks. Use when: reviewing PRs.'
```

If the field is missing, add one. If the filename is wrong,
rename to `SKILL.md` exactly.

## Symptom: skill appears but never activates

The skill shows in `/skills` but Claude never loads it for
relevant prompts.

### Likely causes

1. **Description too generic**. "Helps with development"
   matches everything and ranks below skills with specific
   triggers.
2. **Description missing the trigger phrase**. The user says
   "review my PR" but the description says "evaluates code
   changes." Semantic match is weaker than verbatim match.
3. **Competing skill outranks it**. Another skill has a more
   specific description for the same trigger.
4. **`paths:` glob excludes the conversation**. If the skill
   has a path filter, it only activates when the conversation
   touches matching files.

### Diagnosis

In a fresh session, type the prompt that should activate the
skill, then run `/skills` to see which skills loaded and in
what rank order. If the target skill is absent or low-ranked,
the description does not match the prompt.

```bash
# Compare the description to the prompt
head -5 plugins/<plugin>/skills/<skill>/SKILL.md
```

### Fix

Rewrite the description to lead with the action and the
trigger phrase the user would actually use:

```yaml
description: 'Review pull requests with line comments and
  scope checks. Use when reviewing PRs or MRs.'
```

If a competing skill outranks it, either narrow the competing
skill's description or merge the two skills if they overlap
substantively. See `description-writing.md` for the formula.

## Symptom: skill loads but Claude ignores its content

The skill activates but the response does not follow the
skill's guidance.

### Likely causes

1. **Skill is too long**. SKILL.md over 500 lines forces
   Claude to summarize, dropping requirements.
2. **Requirements buried**. Critical requirements appear
   below 200 lines of preamble.
3. **Hedging language**. "You might want to consider X"
   reads as optional. Claude treats it as optional.
4. **Rationalizations not blocked**. The user prompt invites
   a shortcut and the skill has no explicit counter.

### Diagnosis

Check the line count and the placement of the most important
requirement:

```bash
wc -l plugins/<plugin>/skills/<skill>/SKILL.md
rg -n '^## ' plugins/<plugin>/skills/<skill>/SKILL.md
```

If the requirement is below line 200, move it up. If
SKILL.md exceeds 500 lines, move detail to modules.

### Fix

Tighten the language. Replace "consider," "should," and
"might" with "must" and "required." See
`anti-rationalization.md` for the language hierarchy and
`persuasion-principles.md` for the directive forms that
work best.

If the skill is too long, split using the patterns in
`progressive-disclosure.md`.

## Symptom: skill works in tests, fails in production

Test scenarios pass but real users report the skill misfires
or gets bypassed.

### Likely causes

1. **Test scenarios were sanitized**. The author tested with
   "create a user endpoint" but real users say "quick login
   for the prototype." The pressure phrasing matters.
2. **Test ran on a different model**. RED on Sonnet, GREEN
   on Opus. The model difference, not the skill, fixed the
   failure.
3. **Test ran in the same conversation**. Priming bias.
4. **Real prompts mix domains**. A request that combines
   security and refactoring activates two skills with
   conflicting advice.

### Diagnosis

Pull a real user transcript where the skill failed. Run that
exact prompt through a fresh subagent on the same model the
user was using. If the skill fails, the test corpus is not
representative.

### Fix

Add the real prompt to the test corpus. If multiple skills
conflict, see `advanced-patterns.md` for the multi-skill
coordination pattern. If model dependence is the cause,
re-run RED/GREEN/REFACTOR on the production model.

## Symptom: module references broken

`SKILL.md` links to `modules/<example>.md` but the link does
not resolve when the user follows it.

### Likely causes

1. **Path typo**. `modules/<name>.md` vs `Modules/<name>.md`
   vs `module/<name>.md`.
2. **File not committed**. Module exists locally but not in
   the branch the user installed.
3. **Cross-skill reference uses wrong syntax**. The skill
   uses `../other-skill/modules/x.md` and the consuming
   harness does not support relative paths.

### Diagnosis

```bash
# List declared modules from frontmatter and verify each exists
rg '^- modules/' plugins/<plugin>/skills/<skill>/SKILL.md

for m in $(rg '^- modules/' \
  plugins/<plugin>/skills/<skill>/SKILL.md | \
  awk '{print $2}'); do
  ls plugins/<plugin>/skills/<skill>/$m \
    || echo "MISSING: $m"
done
```

### Fix

Correct the path. For cross-skill references, use the
`Skill(plugin:skill)` form rather than relative file paths.
The form resolves through the harness regardless of install
location.

## Symptom: skill produces hallucinated content

The skill instructs Claude to cite a file or run a command,
but Claude makes up plausible-looking outputs.

### Likely causes

1. **Skill cites paths that no longer exist**. The author
   wrote against an old codebase layout.
2. **Skill instructs Claude to run a command without
   capturing output**. Claude infers what the output would
   have been.
3. **No verification step**. The skill produces an artifact
   without checking it.

### Diagnosis

Verify every `Read`, `Bash`, and `rg` command in the skill
points at a real file or runs against real state:

```bash
rg -n '`[A-Za-z0-9_./-]+\.(py|md|sh|json)`' \
  plugins/<plugin>/skills/<skill>/SKILL.md \
  plugins/<plugin>/skills/<skill>/modules/*.md
```

For each cited path, run `ls` to confirm it exists.

### Fix

Replace stale paths with current ones. Add a verification
step at the end of the skill that runs the cited commands
and checks their output. See `error-handling.md` for the
"surface, stop, ask" pattern.

## Symptom: skill is very large and slow to maintain

Every edit to the skill requires reading the whole file, and
small changes regress unrelated sections.

### Likely causes

1. SKILL.md grew past 500 lines.
2. A single module covers multiple topics.
3. Examples were appended over time without restructure.

### Fix

Split. The `progressive-disclosure.md` module specifies the
rule: SKILL.md under 500 lines, modules 200-400 lines,
references one level deep. Run the analyzer:

```bash
python plugins/abstract/scripts/skill_analyzer.py \
  plugins/<plugin>/skills/<skill>/SKILL.md
```

The analyzer produces split recommendations.

## Anti-patterns

| Anti-pattern | Better approach |
|--------------|-----------------|
| Adding a "troubleshooting" section to every module | Centralize here |
| Asking the user to debug the skill themselves | Diagnose first |
| Bumping the version on every fix without a test | Add a test, then bump |
| Catching all skill bugs with a "see also" link | Diagnose the cause |

## Verification

Most of the symptoms above can be caught before merge:

```bash
# Run the full skill audit
python plugins/abstract/scripts/skills_auditor.py \
  --skill plugins/<plugin>/skills/<skill>/SKILL.md

# Check compliance
python plugins/abstract/scripts/compliance_checker.py \
  --skill plugins/<plugin>/skills/<skill>/SKILL.md

# Estimate tokens
python plugins/abstract/scripts/skill_analyzer.py \
  plugins/<plugin>/skills/<skill>/SKILL.md
```

If any check fails, fix before merging. The deployment
checklist (`deployment-checklist.md`) gates merge on these
results.

Cross-reference: see `Skill(abstract:skills-eval)` for the
auditing framework that detects most of these issues at scale,
and `validation.md` in this skill for pre-merge structural
checks.
