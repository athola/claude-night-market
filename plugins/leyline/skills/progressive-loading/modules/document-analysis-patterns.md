# Document Analysis Patterns

This module covers how progressive-loading applies when the skill
processes prose documents: meeting notes, sprint summaries,
markdown specs, RFCs, or imported PDFs. The driving question is
which analysis modules to load based on document type, length,
and target output.

## When This Module Applies

Load this module when the task involves:

- Summarizing a markdown file or set of files.
- Extracting decisions, action items, or risks from prose.
- Producing a digest from meeting notes or sprint docs.
- Comparing two versions of a document for substantive change.

For git-based change summaries, load `git-catchup-patterns.md`
instead. For log files and time-series data, load
`log-analysis-patterns.md`. This module is for human-authored
prose.

## Detect Document Type Before Loading

Document type drives module selection. A short markdown spec
needs different handling than a 100-page PDF.

```python
from pathlib import Path

def classify_doc(path: Path) -> dict[str, object]:
    suffix = path.suffix.lower()
    size = path.stat().st_size
    is_markdown = suffix in {".md", ".markdown"}
    is_imported = suffix in {".pdf", ".docx", ".pptx", ".html"}
    return {
        "format": suffix,
        "bytes": size,
        "needs_conversion": is_imported,
        "long_form": size > 50_000,
        "markdown_native": is_markdown,
    }
```

The classification picks the next module: a long PDF triggers
the conversion module first, then the long-form summarization
module. A short markdown spec skips both and goes straight to
extraction.

## Loading Map

| Document Type | Load Module | Token Estimate |
|---------------|-------------|----------------|
| Short markdown (<10k bytes) | `extraction-rules.md` | 300 |
| Long markdown (>10k bytes) | `chunked-summary.md` | 500 |
| Meeting notes | `decision-extraction.md` | 400 |
| RFC or spec | `requirements-extraction.md` | 500 |
| PDF or DOCX | `document-conversion.md` then format module | 400+ |
| Two-version diff | `prose-diff.md` | 400 |

Conversion is the only module that depends on another module
afterward. The hub loads conversion, runs it, then re-classifies
the resulting markdown to pick the format module.

## Real Conversion Path

For non-markdown inputs, the
`leyline:document-conversion` skill provides a tiered fallback:
MCP markitdown first, then native tools (`pandoc`, `pdftotext`),
then a degraded text-only path. The conversion module loaded
here calls into that skill rather than reimplementing the
fallback.

```python
# Pseudo-code for conversion handoff
def convert_to_markdown(path: Path) -> Path:
    output = path.with_suffix(".md")
    # Skill handoff: leyline:document-conversion
    # owns the actual tool selection.
    return output
```

After conversion, re-run `classify_doc` on the output path so
the loader picks the right format module for the converted
content.

## Chunking for Long Documents

Long documents exceed safe per-turn token budgets. The
chunked-summary module splits the document, summarizes each
chunk, then merges the per-chunk summaries.

```python
def chunk_by_heading(text: str) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        if line.startswith("# ") and current:
            chunks.append("\n".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        chunks.append("\n".join(current))
    return chunks
```

Heading-based chunking preserves logical units. Byte-based
chunking can split a code block or a table mid-row, breaking
downstream parsing.

## Pitfalls

1. **Loading extraction rules before conversion**: For PDFs the
   bytes you see are not the prose. Convert first, classify the
   converted markdown, then load extraction rules.
2. **Treating all markdown the same**: A 100-line spec and a
   3000-line RFC need different summarization strategies. Use
   the size threshold.
3. **Re-summarizing on every turn**: If the document has not
   changed, the summary is stable. Cache by file mtime.
4. **Losing tables to byte-chunking**: Tables and code blocks
   are atomic units. Chunk by heading boundaries, not by byte
   count.
5. **Skipping decision extraction for meeting notes**: Meeting
   notes without an explicit decision pass produce a recap, not
   a useful digest. Always load `decision-extraction.md` for
   that document type.

## Cross-Reference

See `git-catchup-patterns.md` for change-based summarization,
`log-analysis-patterns.md` for time-series inputs, and the
parent `SKILL.md` for how these analysis modules plug into
the hub.
