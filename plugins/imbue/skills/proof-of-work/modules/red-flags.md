# Red Flags - Common Violations

Thought patterns that indicate you're about to violate
proof-of-work discipline.

## The "Should Work" Family

These flags share a common pattern: substituting
assumptions for evidence.

| Red Flag | Problem | Reality Check |
|----------|---------|---------------|
| "This should work" | "Should" = untested assumption | Did you TEST it? |
| "Just restart and it will work" | Restart = magic wand thinking | Did you TEST a restart? |
| "This looks correct" | Visual inspection is not functional validation | Does it PARSE, LOAD, and WORK? |

**Example recovery** ("This should work"):

```markdown
Let me verify this configuration works:

[Evidence E1] Testing cclsp startup:
$ CCLSP_CONFIG_PATH=config.json npx cclsp@latest
Error: <actual error message>

Result: FAIL - Discovered issue - config path not recognized
```

## The "Installation" Family

Installed does not mean functional.

| Red Flag | Problem | Reality Check |
|----------|---------|---------------|
| "X is installed" | Installed does not mean functional | Is it EXECUTABLE, RESPONDING, correct VERSION? |
| "Dependencies are satisfied" | requirements.txt does not reflect runtime | Check PEER deps, VERSION compat, PLATFORM issues |

**Example recovery** ("X is installed"):

```markdown
Verifying pylsp installation:

[E1] Binary exists: $ ls -la /usr/local/bin/pylsp - PASS
[E2] Responds: $ pylsp --help - PASS
[E3] Version: $ pylsp --version - PASS (v1.9.0)
[E4] Smoke test: $ echo 'print("test")' | pylsp stdin - PASS

Conclusion: pylsp is installed AND functional.
```

## The "Configuration" Family

Valid syntax does not mean correct semantics.

| Red Flag | Problem | Reality Check |
|----------|---------|---------------|
| "Environment variable is set" | Set in shell does not mean set in process | Current shell? Claude's process? Exported? |
| "Config file is valid" | Valid syntax does not mean correct semantics | Schema valid? Paths exist? Commands in PATH? |

## The "Research" Family

Documentation describes intent, not current reality.

| Red Flag | Problem | Reality Check |
|----------|---------|---------------|
| "According to the docs..." | Docs may not match current version | Which VERSION? CHANGELOG? KNOWN ISSUES? |
| "This is the recommended approach" | Recommended does not mean working here | Recommended by WHOM? Tested in THIS environment? |

**Example recovery** ("According to the docs..."):

```markdown
Documentation verification:

[E1] Docs state: "LSP tools available in Claude Code 2.0.74+"
[E2] Version check: $ claude --version - Result: 2.0.76
[E3] Known issues: Issue #14803 - LSP broken in 2.0.69-2.0.76
[E4] Changelog: No fix mentioned in 2.0.76

Conclusion: Docs correct but current version has regression.
```

## The "Completion" Family

Code written does not mean code working.

| Red Flag | Problem | Reality Check |
|----------|---------|---------------|
| "I've finished implementing X" | Code written does not mean code working | Does it COMPILE? Pass TESTS? Meet ACCEPTANCE CRITERIA? |
| "The setup is complete" | Steps followed does not mean working system | End-to-end test? Each component verified? Blockers? |

**Example recovery** ("The setup is complete"):

```markdown
Setup validation:

[E1] Components: pylsp PASS, cclsp PASS, MCP config PASS
[E2] Integration: cclsp starts PASS, servers connect PARTIAL,
     LSP tools FAIL
[E3] Blocker: Issue #14803 - LSP broken in 2.0.76

Status: BLOCKED - Setup complete but unusable due to upstream bug
Next steps: Downgrade to 2.0.67 OR wait for fix
```

## The "Documentation Exception" Family

Markdown files and config files have testable structure.

| Red Flag | Problem | Recovery |
|----------|---------|----------|
| "Skills are just documentation" | Markdown has testable structure | Test existence, required sections, module refs, hook integration |
| "It's just configuration" | Config files can break | Validate JSON, check content, test edge cases |
| "The user wanted it fast" | Speed does not override quality gates | Writing tests first REVEALS design issues early |

## The Cargo Cult Family

Using code or patterns you cannot explain.

| Red Flag | Problem | Recovery |
|----------|---------|----------|
| "The AI suggested this approach" | AI confidence does not equal correctness | Can you explain WHY? Considered simpler alternatives? |
| "This is how [big company] does it" | Different constraints, different solutions | Does your SCALE match? Same TEAM SIZE? Same PROBLEMS? |
| "It's a best practice" | "Best" without context is meaningless | Best for WHAT goal? Recommended by WHOM? In WHAT context? |
| "Just copy this snippet" | Copy-paste without understanding = debt | Can you explain EACH PART? MODIFY it? Know when it FAILS? |
| "Make it production-ready" | Not a specification | What SPECIFIC requirements? Who DEFINED ready? How VERIFIED? |

## Self-Monitoring Questions

Before ANY completion claim, ask yourself:

1. **"Did I run the actual command?"** Not "it should
   work if you run X" but "I ran X and here's the output."

2. **"Did I test in the target environment?"** Not "works
   on my machine" but "tested in user's environment."

3. **"Did I research known issues?"** Not "according to
   docs" but "docs say X, BUT issue #123 shows Y."

4. **"Can the user reproduce my validation?"** Not "I
   verified it" but "run these commands and you'll see
   [expected output]."

5. **"Am I making assumptions?"** Not "restart should fix
   it" but "tested restart, here's before/after evidence."

6. **"Would I accept this from a coworker?"** Not "I
   think this will work" but "I've proven this works."

## Recovery from Violations

If you catch yourself violating proof-of-work:

1. **STOP** -- do not send the completion claim
2. **Run the validation** -- actually test the assumption
3. **Capture evidence** -- document what you find
4. **Update your claim** -- replace assumption with proof

## The Ultimate Red Flag

**Thought:** "I don't need to test this, it's obvious it
will work."

**Reality:** Nothing is obvious. Everything must be proven.

**Recovery:** Test it anyway. Evidence beats intuition.

## Cargo Cult Summary

The fundamental cargo cult error is using code or patterns
you cannot explain. If you cannot teach it to someone else,
you do not understand it. If you do not understand it, do
not ship it.

See [anti-cargo-cult.md](anti-cargo-cult.md) for the
complete understanding verification protocol.
