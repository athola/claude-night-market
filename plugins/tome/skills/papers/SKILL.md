---
name: papers
description: >-
  Search academic literature via arXiv, Semantic Scholar,
  and open-access discovery chains. Fetches and parses
  PDFs for key findings. Use when the user needs academic
  papers, citations, or formal research on a topic.
category: research
tags:
  - arxiv
  - semantic-scholar
  - academic
  - papers
  - pdf
estimated_tokens: 200
---

# Academic Papers Search

Search arXiv, Semantic Scholar, and open-access sources.

## Sources (Priority Order)

1. arXiv API (free, unlimited metadata)
2. Semantic Scholar API (100 req/5min, citation graphs)
3. Unpaywall (legal free version discovery)
4. CORE.ac.uk (open-access aggregator)
5. PubMed Central (biomedical)
6. Author preprint pages (WebSearch fallback)

## PDF Processing

- Fetch via WebFetch
- Read via Read tool (20 pages max per request)
- Chunk longer papers with page ranges
- Extract: abstract, key findings, methodology

## Fallback Guidance

When a paper is paywalled and no open version exists:
- Public library JSTOR/ProQuest access via library card
- DeepDyve article rental
- Inter-library loan request
- Direct author email template
