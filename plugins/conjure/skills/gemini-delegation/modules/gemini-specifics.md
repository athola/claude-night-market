# Gemini-Specific Configuration

## Model Reference

`gemini-3.8-flash` is the default and fast-response selection.
`gemini-3.1-pro-preview` is the large-context selection. It is a preview
model, so check the
[deprecations page](https://ai.google.dev/gemini-api/docs/deprecations)
for its shutdown date. Explicit model options and saved service
overrides remain authoritative.

| Model | Use Case | Input context | Status |
|-------|----------|---------------|--------|
| `gemini-3.8-flash` | Default delegation | 1,048,576 tokens | Stable |
| `gemini-3.1-pro-preview` | Large-context selection | 1,048,576 tokens | Preview |

## CLI Options

| Flag | Purpose |
|------|---------|
| `-p "prompt"` | Specify prompt |
| `--model <name>` | Select model |
| `--output-format json` | JSON output |
| `-s` | Sandbox mode |
| `@path` | Include file in context |

## Context Inclusion Patterns
- Use `@path` to include file contents
- Use `@directory/**/*` for recursive inclusion
- Gemini handles large contexts well (1M+ tokens)

## Cost Reference (USD per 1M tokens)

From the [pricing page](https://ai.google.dev/gemini-api/docs/pricing),
checked 2026-10-26.

| Model | Input | Output |
|-------|-------|--------|
| `gemini-3.8-flash` | $0.75 until 2026-12-31, then $1.50 | $3.75, then $7.50 |
| `gemini-3.1-pro-preview` | $2.00 up to 200K, $4.00 above | $12.00 up to 200K, $18.00 above |

## Gemini-Specific Troubleshooting

### Rate Limit (HTTP 429)
- Free tier: ~60 RPM, ~1000 requests/day
- Consider `gemini-3.8-flash` to reduce RPM usage
- Use `~/conjure/hooks/gemini/status.sh` for quick check

### Context Too Large
- Use selective globbing: `src/**/*.py` instead of `src/**/*`
- Pre-process: `rg -v "^\s*#" file.py` to remove comments (or `grep -v`)

### Region Issues
- Some models available only in certain regions
- Check API documentation for availability
