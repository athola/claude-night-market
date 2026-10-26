# MiniMax-Specific Configuration

## Model Reference

`MiniMax-M3.1-Flash` is the default and fast-response selection.
`MiniMax-M3` remains the large-context selection. Explicit model options
and saved service overrides remain authoritative, including legacy IDs.

| Model | Use Case | Context | Input | Thinking |
|-------|----------|---------|-------|----------|
| `MiniMax-M3.1-Flash` | Default delegation | 1,000,000 tokens | Text, image, video | Adaptive only |
| `MiniMax-M3` | Large-context selection | 1,000,000 tokens | Text, image, video | Adaptive or disabled |

The executor exposes no thinking or effort flags. It leaves these to
`mmx` and the API defaults; it does not request disabled thinking for
Flash or inject a service tier.

## Cost Reference

Use the [official pricing table](https://platform.minimax.io/docs/pricing/overview)
for the selected model, service tier and input-length band. The former
$0.60/$2.40 M3 example describes a short-context rate, not a universal
standard rate. No price estimate is applied by the delegation executor.

## CLI Options

Text generation lives behind the `mmx text chat` subcommand.

| Flag | Purpose |
|------|---------|
| `--message "prompt"` | Specify the prompt. Repeat for multi-turn input |
| `--model <name>` | Select model |
| `--system "text"` | Set a system prompt |
| `--output json` | JSON output instead of text |
| `--stream` | Stream the response |
| `--messages-file -` | Read a JSON message array from stdin |

There is no `@path` file-reference syntax. The service contract supports
`--temperature` when explicitly requested. `delegation_executor.py` reads
requested files and inlines their contents into `--message`.

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `MINIMAX_REGION` | `global` or `cn` |
| `MINIMAX_BASE_URL` | Override the API base URL |
| `MINIMAX_OUTPUT` | `text` or `json` |
| `MINIMAX_TIMEOUT` | Request timeout in seconds |
| `MMX_CONFIG_DIR` | Directory holding `config.json` (default `~/.mmx`) |

`mmx` reads no `MINIMAX_API_KEY`. Pass a key with `mmx auth login
--api-key` or the per-command `--api-key` flag.

Set `MMX_CONFIG_DIR` when `mmx` runs from a subprocess or CI job whose
home directory differs from where the login happened. Without it, a
delegation that works in a terminal reports itself unauthenticated.

## Regional Endpoints

| Region | OpenAI-compatible | Anthropic-compatible | Documentation |
|--------|-------------------|----------------------|---------------|
| Global | `https://api.minimax.io/v1` | `https://api.minimax.io/anthropic` | `https://platform.minimax.io/docs` |
| China | `https://api.minimaxi.com/v1` | `https://api.minimaxi.com/anthropic` | `https://platform.minimaxi.com/docs` |

Keys are issued per region and do not work across regions. API-key login
probes both regions and saves the one that accepts the key, so the base
URL rarely needs setting by hand.

## Context Inclusion Patterns

- Pass file contents inside `--message`. The CLI resolves no file paths.
- `delegation_executor.py` inlines up to 96 KiB of file context, which
  keeps the prompt under the operating system limit on a single argument.
- For larger corpora, split the work across several delegations rather
  than raising the cap.

## MiniMax-Specific Troubleshooting

### Command Not Found

Install the official CLI with `npm install -g mmx-cli`. The binary is
`mmx`. A binary named `minimax` comes from an unrelated third-party
package and is not used here.

### Authentication Failures

Run `mmx auth status`. If it fails inside automation but passes in a
terminal, set `MMX_CONFIG_DIR` to the directory holding the credentials.

### Rate Limit (HTTP 429)

- Reduce request concurrency or wait before retrying.
- Check remaining quota with `mmx quota`.

### Wrong Region

An authentication error right after a successful login usually means the
account belongs to the other region. Set it explicitly with `mmx config
set --key region --value cn` (or `global`). Re-sending the same key to
the other region's host does not work, because keys are region-bound.
