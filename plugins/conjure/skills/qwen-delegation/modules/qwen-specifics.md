# Qwen-Specific Configuration

## Model Reference

`coder-model` is the selection for every requirement. The service
authenticates through Qwen OAuth, and qwen-code accepts only
`coder-model` there: any other `--model` prints a warning and runs
`coder-model` anyway
([source](https://github.com/QwenLM/qwen-code/blob/main/packages/core/src/models/modelConfigResolver.ts)).

| Model | Auth | Context |
|-------|------|---------|
| `coder-model` | Qwen OAuth (this service) | Qwen 3.7 Max |
| `qwen3.8-max` | Model Studio API key | 1M tokens |
| `qwen3.8-flash` | Model Studio API key | 1M tokens |

The Model Studio ids apply only after configuring qwen-code for API-key
auth and overriding the service's `default_model` to match.

## CLI Options

| Flag | Purpose |
|------|---------|
| `-p "prompt"` | Specify prompt |
| `--model <name>` | Select model |
| `-o, --output-format <type>` | Output format |
| `@path` | Include file in context |

## Context Inclusion Patterns
- Use `@path` to include file contents
- Use `@directory/**/*` for recursive inclusion

## Cost Reference

Qwen OAuth carries no per-token price. For API-key auth, use the
[Model Studio pricing page](https://www.alibabacloud.com/help/en/model-studio/model-pricing):
`qwen3.8-max` is $2 input and $6 output per 1M tokens, and
`qwen3.8-flash` is $0.15 and $0.47 (international, checked 2026-10-26).

## Qwen-Specific Troubleshooting

### Rate Limits
- Check with: `uv run python scripts/delegation_executor.py --verify qwen`
- Space requests out. Every OAuth request runs the same `coder-model`

### Installation Issues
- Install: `npm install -g @qwen-code/qwen-code`
- PATH issues: validate `~/.local/bin` is in PATH
- Verify: `which qwen` and `qwen --version`

### Model Access
- Check available models: `qwen --help | grep -A 10 "model"`
- Version updates may add new models
