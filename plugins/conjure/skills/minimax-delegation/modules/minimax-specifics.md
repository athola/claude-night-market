# MiniMax-Specific Configuration

## Model Reference

| Model | Use Case | Context |
|-------|----------|---------|
| `MiniMax-M3` | Complex analysis, large context | Up to 1M tokens |
| `MiniMax-M2.7` | Fast, simple tasks | Standard context |

## CLI Options

| Flag | Purpose |
|------|---------|
| `-p "prompt"` | Specify prompt |
| `--model <name>` | Select model |
| `--output-format json` | JSON output |
| `@path` | Include file in context |

## Regional Endpoints

MiniMax serves two regions with separate base URLs. Set the one that
matches your account before delegating:

| Region | OpenAI-compatible base URL |
|--------|---------------------------|
| Global | `https://api.minimax.io/v1` |
| China | `https://api.minimaxi.com/v1` |

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
