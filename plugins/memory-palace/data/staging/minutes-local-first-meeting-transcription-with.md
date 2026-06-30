---
title: 'Minutes: local-first meeting transcription with MCP agent integration'
source:
  type: web_fetch
  identifier: https://github.com/silverstein/minutes
author: drain-workflow
date_captured: '2026-06-30'
palace: Tacit Knowledge Capture
district: Research 2026-06-29
maturity: probation
tags:
- speech-to-text
- meeting-notes
- privacy-first
- mcp
- rust
---

# Minutes: local-first meeting transcription with MCP agent integration

## Marginal Value Summary

- **Integration Decision**: standalone
- **Confidence**: 90%
- **Novelty Tags**: speech-to-text, meeting-notes, privacy-first, mcp, rust

## Intake Content

# Minutes: local-first meeting transcription with MCP agent integration

Minutes is a local-first meeting transcription tool: on-device whisper.cpp transcription, native diarization, structured Markdown with decisions/action-items, a cross-meeting SQLite relationship graph, and 31 MCP tools for agent integration. Reference for embedding local transcription and structured metadata extraction without cloud infra.

## Key points

- Local audio transcription via whisper.cpp (Metal/CUDA/Vulkan), on-device
- Structured Markdown + YAML frontmatter: decisions, action items, speakers
- Native diarization (pyannote-rs); SQLite relationship graph across meetings
- 31 MCP tools + 7 resources for Claude Code/Codex/Gemini; no API keys
- CLI + Tauri menubar + MCP server share one minutes-core Rust library

Source: https://github.com/silverstein/minutes
