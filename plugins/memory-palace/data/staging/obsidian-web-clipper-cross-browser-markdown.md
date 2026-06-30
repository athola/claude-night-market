---
title: 'Obsidian Web Clipper: cross-browser Markdown capture extension'
source:
  type: web_fetch
  identifier: https://github.com/obsidianmd/obsidian-clipper
author: drain-workflow
date_captured: '2026-06-30'
palace: Tacit Knowledge Capture
district: Research 2026-06-29
maturity: probation
tags:
- web-clipper
- markdown-conversion
- browser-extension
- content-capture
- obsidian
---

# Obsidian Web Clipper: cross-browser Markdown capture extension

## Marginal Value Summary

- **Integration Decision**: standalone
- **Confidence**: 90%
- **Novelty Tags**: web-clipper, markdown-conversion, browser-extension, content-capture, obsidian

## Intake Content

# Obsidian Web Clipper: cross-browser Markdown capture extension

Official Obsidian browser extension that captures web content as durable Markdown. Multi-browser WebExtension codebase, defuddle-based extraction, variable/filter templating, local image storage and offline persistence. Reference for building multi-browser clipping with Markdown output without rebuilding browser-compat layers.

## Key points

- Cross-browser via WebExtension polyfill (Chrome/Firefox/Safari/Edge), single codebase
- Converts pages to Markdown using the defuddle extraction library
- Template system with variables, filters, planned conditional logic
- Local image storage (Obsidian 1.8.0+), offline-capable persistence
- TypeScript + SCSS; webpack bundling, vitest tests, lz-string template compression

Source: https://github.com/obsidianmd/obsidian-clipper
