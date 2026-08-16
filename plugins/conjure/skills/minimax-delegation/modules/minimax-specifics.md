# MiniMax-Specific Configuration

## Model Reference

`MiniMax-M3` is the default model.

| Model | Use Case | Context | Input | Thinking |
|-------|----------|---------|-------|----------|
| `MiniMax-M3` | Complex analysis, large context | 1,000,000 tokens | Text, image, video | Adaptive or disabled |
| `MiniMax-M2.7` | Fast, simple tasks | 204,800 tokens | Text | Always on |

## Cost Reference (USD per 1M tokens)

| Model | Input | Output | Cache Read | Cache Write |
|-------|-------|--------|------------|-------------|
| `MiniMax-M3` | $0.60 | $2.40 | $0.12 | Not available |
| `MiniMax-M2.7` | $0.30 | $1.20 | $0.06 | $0.375 |

## CLI Options

| Flag | Purpose |
|------|---------|
| `-p "prompt"` | Specify prompt |
| `--model <name>` | Select model |
| `--output-format json` | JSON output |
| `@path` | Include file in context |

## Regional Endpoints

MiniMax serves two regions with separate OpenAI- and
Anthropic-compatible base URLs. Set the compatibility and region that
match your client and account before delegating:

| Region | OpenAI-compatible | Anthropic-compatible | Documentation |
|--------|-------------------|----------------------|---------------|
| Global | `https://api.minimax.io/v1` | `https://api.minimax.io/anthropic` | `https://platform.minimax.io/docs` |
| China | `https://api.minimaxi.com/v1` | `https://api.minimaxi.com/anthropic` | `https://platform.minimaxi.com/docs` |

Both regions authenticate with the `MINIMAX_API_KEY` environment
variable, sent as a bearer token by the `minimax` CLI.

## Context Inclusion Patterns

- Use `@path` to include file contents.
- Use `@directory/**/*` for recursive inclusion.
- MiniMax-M3 handles large contexts well (1M tokens).

## MiniMax-Specific Troubleshooting

### Rate Limit (HTTP 429)

- Consider `MiniMax-M2.7` to reduce request volume.
- Check quota with `make quota-status`.

### Region Issues

- A 404 or auth error on one endpoint usually means the account is
  registered in the other region. Switch the base URL between
  `api.minimax.io` and `api.minimaxi.com` and retry.
