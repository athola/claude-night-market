# Spec Register

Load this when the spec describes a system that already exists, such
as a runtime contract, an API reference, or a spec set kept beside the
code. A pre-build feature spec stays free of implementation details,
per the hub, and skips the status and identifier rules below.

How a specification reads sentence by sentence. The structure module
says which sections a spec has. This one says how each statement in
them is written. The goal is a reader who can tell what the system
does today from what it is meant to do.

The model is the zombie-ant spec set (19 files, about 12,000
words). The repo's slop detector found 22 findings in it. Twelve are
semicolons, several inside table cells. It tags status 145 times and
uses "will" nowhere.

## Rules

**Define terms once, in a table.** A `## Terms` table near the top
gives each term one meaning. Use the same word for the same thing
everywhere after it.

```markdown
| Term | Meaning |
|------|---------|
| Target | Managed edge system addressed by CLI or API commands. |
| Pathway | Planned runtime implementation selected from config. |
```

**Tag every statement with its status.** Write what exists in the
present tense. Mark what does not exist yet as Planned, either on the
statement or by grouping it under a "Planned" list. "Model upload is
not implemented." is a status, and keeps a reader from building on a
route that returns a stub.

```markdown
Implemented daemon responsibilities:

- `config.toml` validation
- HTTP command API

Planned daemon responsibilities:

- model upload, conversion, activation, and delete execution
```

**Do not write "will".** Future tense hides status. "The runtime will
retry" might be built, planned, or a wish. Write "The runtime retries"
or "Planned: the runtime retries".

**One fact per sentence.** "Runtime config controls permission.
Inventory controls reachability." Rationale belongs in an ADR the spec
links to.

**Normative keywords follow RFC 8174.** MUST, SHOULD, MAY and the rest
carry their defined meaning only in capitals, and only in a document
that adopts them with the BCP 14 boilerplate. Pick one:

- Adopt them. Put the boilerplate at the top and write every
  requirement in capitals. A lowercase "must" in that document is
  ambiguous.
- Do not adopt them. Leave out the boilerplate and write requirements
  as plain present-tense statements.

A spec that declares RFC 2119 and then writes "must" in lowercase has
promised a convention it does not use. The zombie-ant README declares
RFC 2119, yet the set contains one capital keyword against 8 lowercase
"must", 6 "should", and 22 "may". Check with
`rg -c '\b(MUST|SHOULD|MAY)\b'` before claiming the convention.

**Name what code a statement covers.** Write identifiers, routes, and
file names in backticks: `zombie-ant-runtime`, `POST /models`.

## Sources

- RFC 8174, <https://www.rfc-editor.org/rfc/rfc8174>
- RFC 7322 (RFC Style Guide), <https://www.rfc-editor.org/rfc/rfc7322>
- zombie-ant spec set, read 2026-11-10 at master `4b72abbb`,
  <https://gitlab.com/iris-core/pubsec/zombie-ant/-/tree/master/docs/spec>
  (private repository)
