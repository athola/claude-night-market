"""Academic literature channel: arXiv, Semantic Scholar, and open-access
helpers.

These functions do NOT make HTTP calls. They prepare query strings and
URLs for WebSearch/WebFetch tool calls, and parse the results those
tools return into Finding objects.
"""

from __future__ import annotations

import html
import re
from typing import Any
from urllib.parse import quote, quote_plus

from tome.models import Finding

# ---------------------------------------------------------------------------
# arXiv
# ---------------------------------------------------------------------------

_ARXIV_API_BASE = "https://export.arxiv.org/api/query"
_ARXIV_BASE_RELEVANCE = 0.7


def build_arxiv_search_url(topic: str, max_results: int = 10) -> str:
    """Build arXiv API search URL.

    Args:
        topic: Free-text research topic.
        max_results: Maximum number of results to request (default 10).

    Returns:
        URL string for the arXiv Atom API, sorted by relevance.
    """
    encoded = quote_plus(topic)
    return (
        f"{_ARXIV_API_BASE}?search_query=all:{encoded}"
        f"&max_results={max_results}&sortBy=relevance"
    )


def _extract_tag_text(xml: str, tag: str) -> str | None:
    """Return the text content of the first occurrence of ``tag``."""
    pattern = rf"<{tag}[^>]*>(.*?)</{tag}>"
    match = re.search(pattern, xml, re.DOTALL)
    if match:
        return html.unescape(match.group(1).strip())
    return None


def _extract_arxiv_id(id_url: str) -> str:
    """Extract the bare arXiv ID (without version) from an abs URL."""
    # Matches patterns like arxiv.org/abs/2301.12345v1 or abs/2301.12345
    match = re.search(r"abs/([^v]+?)(?:v\d+)?$", id_url.strip())
    if match:
        return match.group(1)
    return id_url


def _extract_pdf_link(entry_xml: str) -> str:
    """Extract href from <link title="pdf" ...> within an entry block."""
    match = re.search(
        r'<link[^>]+title=["\']pdf["\'][^>]+href=["\']([^"\']+)["\']',
        entry_xml,
        re.DOTALL,
    )
    if match:
        return match.group(1)
    # Also handle reversed attribute order: href before title
    match = re.search(
        r'<link[^>]+href=["\']([^"\']+)["\'][^>]+title=["\']pdf["\']',
        entry_xml,
        re.DOTALL,
    )
    if match:
        return match.group(1)
    return ""


def parse_arxiv_response(xml_text: str) -> list[Finding]:
    """Parse arXiv Atom XML response into Finding objects.

    Uses regex/string parsing only — no lxml or xml.etree dependency.

    Args:
        xml_text: Raw Atom XML string from the arXiv API.

    Returns:
        List of Findings with ``source="arxiv"`` and
        ``channel="academic"``.
    """
    findings: list[Finding] = []

    # Split by <entry> blocks
    entry_blocks = re.findall(r"<entry>(.*?)</entry>", xml_text, re.DOTALL)

    for block in entry_blocks:
        # Title — strip leading/trailing whitespace and normalise inner spaces
        title_raw = _extract_tag_text(block, "title") or ""
        title = " ".join(title_raw.split())

        # ID URL
        id_url = _extract_tag_text(block, "id") or ""
        arxiv_id = _extract_arxiv_id(id_url)
        url = id_url  # canonical URL is the abs page

        # Abstract / summary
        summary = _extract_tag_text(block, "summary") or ""
        summary = " ".join(summary.split())

        # Authors
        author_blocks = re.findall(r"<author>(.*?)</author>", block, re.DOTALL)
        authors: list[str] = []
        for ab in author_blocks:
            name = _extract_tag_text(ab, "name")
            if name:
                authors.append(name)

        # Published year
        published = _extract_tag_text(block, "published") or ""
        year: int | None = None
        year_match = re.match(r"(\d{4})", published)
        if year_match:
            year = int(year_match.group(1))

        # Categories
        categories = re.findall(r'<category[^>]+term=["\']([^"\']+)["\']', block)

        # PDF link
        pdf_url = _extract_pdf_link(block)

        metadata: dict[str, Any] = {
            "authors": authors,
            "year": year,
            "categories": categories,
            "pdf_url": pdf_url,
            "arxiv_id": arxiv_id,
        }

        findings.append(
            Finding(
                source="arxiv",
                channel="academic",
                title=title or arxiv_id,
                url=url,
                relevance=_ARXIV_BASE_RELEVANCE,
                summary=summary,
                metadata=metadata,
            )
        )

    return findings


# ---------------------------------------------------------------------------
# Semantic Scholar
# ---------------------------------------------------------------------------

_SS_API_BASE = "https://api.semanticscholar.org/graph/v1/paper/search"
_SS_FIELDS = (
    "title,abstract,year,citationCount,influentialCitationCount,"
    "isOpenAccess,openAccessPdf,authors,venue,externalIds"
)


def build_semantic_scholar_url(topic: str, limit: int = 10) -> str:
    """Build Semantic Scholar search URL.

    Args:
        topic: Free-text research topic.
        limit: Maximum number of results (default 10).

    Returns:
        URL string for the Semantic Scholar paper search endpoint.
    """
    encoded = quote_plus(topic)
    return f"{_SS_API_BASE}?query={encoded}&limit={limit}&fields={_SS_FIELDS}"


def _citation_relevance(citations: int) -> float:
    """Map citation count to a relevance score on the configured tiers."""
    if citations >= 500:
        return 0.9
    if citations >= 100:
        return 0.8
    if citations >= 50:
        return 0.7
    if citations >= 10:
        return 0.6
    return 0.5


def parse_semantic_scholar_response(data: dict[str, Any]) -> list[Finding]:
    """Parse Semantic Scholar JSON response into Findings.

    Args:
        data: Parsed JSON from the Semantic Scholar API.

    Returns:
        List of Findings with ``source="semantic_scholar"`` and
        ``channel="academic"``.
    """
    findings: list[Finding] = []
    papers = data.get("data", [])
    if not isinstance(papers, list):
        return findings

    for paper in papers:
        if not isinstance(paper, dict):
            continue

        title: str = paper.get("title") or ""
        abstract: str = paper.get("abstract") or ""
        year: int | None = paper.get("year")
        citations: int = paper.get("citationCount") or 0
        is_open_access: bool = paper.get("isOpenAccess") or False
        venue: str | None = paper.get("venue") or None
        paper_id: str = paper.get("paperId") or ""

        # PDF URL
        pdf_url: str | None = None
        oa_pdf = paper.get("openAccessPdf")
        if isinstance(oa_pdf, dict):
            pdf_url = oa_pdf.get("url")

        # Authors
        raw_authors = paper.get("authors") or []
        authors: list[str] = [
            a["name"] for a in raw_authors if isinstance(a, dict) and a.get("name")
        ]

        # External IDs
        ext_ids = paper.get("externalIds") or {}
        doi: str | None = ext_ids.get("DOI")

        # URL: prefer arXiv abs page if available, else S2 paper page
        arxiv_id = ext_ids.get("ArXiv")
        if arxiv_id:
            url = f"https://arxiv.org/abs/{arxiv_id}"
        elif paper_id:
            url = f"https://www.semanticscholar.org/paper/{paper_id}"
        else:
            url = ""

        relevance = _citation_relevance(citations)

        metadata: dict[str, Any] = {
            "authors": authors,
            "year": year,
            "citations": citations,
            "venue": venue,
            "doi": doi,
            "is_open_access": is_open_access,
            "pdf_url": pdf_url,
            "paper_id": paper_id,
        }

        findings.append(
            Finding(
                source="semantic_scholar",
                channel="academic",
                title=title or paper_id,
                url=url,
                relevance=relevance,
                summary=abstract,
                metadata=metadata,
            )
        )

    return findings


# ---------------------------------------------------------------------------
# Open Access Discovery
# ---------------------------------------------------------------------------

_UNPAYWALL_BASE = "https://api.unpaywall.org/v2"
_CORE_BASE = "https://api.core.ac.uk/v3/search/works"
_OPENALEX_BASE = "https://api.openalex.org/works"


def build_unpaywall_url(doi: str, email: str = "research@example.com") -> str:
    """Build Unpaywall API URL for a DOI.

    Args:
        doi: Digital Object Identifier string.
        email: Contact email required by Unpaywall's polite pool policy.

    Returns:
        URL string for the Unpaywall v2 API.
    """
    return f"{_UNPAYWALL_BASE}/{quote(doi, safe='')}?email={quote(email, safe='@.')}"


def parse_unpaywall_response(data: dict[str, Any]) -> str | None:
    """Extract the best open access URL from an Unpaywall response.

    Checks in order:
    1. ``data["best_oa_location"]["url_for_pdf"]``
    2. ``data["best_oa_location"]["url"]``
    3. ``None`` if no open access location is present.

    Args:
        data: Parsed JSON from the Unpaywall API.

    Returns:
        URL string or None.
    """
    location = data.get("best_oa_location")
    if not isinstance(location, dict):
        return None
    pdf = location.get("url_for_pdf")
    if pdf:
        return str(pdf)
    url = location.get("url")
    return str(url) if url else None


def build_core_search_url(topic: str, limit: int = 5) -> str:
    """Build CORE.ac.uk API search URL.

    Args:
        topic: Free-text research topic.
        limit: Maximum number of results (default 5).

    Returns:
        URL string for the CORE v3 works search endpoint.
    """
    encoded = quote_plus(topic)
    return f"{_CORE_BASE}?q={encoded}&limit={limit}"


def build_openalex_search_url(topic: str, per_page: int = 5) -> str:
    """Build OpenAlex search URL.

    Args:
        topic: Free-text research topic.
        per_page: Results per page (default 5).

    Returns:
        URL string for the OpenAlex works search endpoint.
    """
    encoded = quote_plus(topic)
    return f"{_OPENALEX_BASE}?search={encoded}&per_page={per_page}"


def generate_access_fallback_guidance(title: str, doi: str | None = None) -> str:
    """Generate human-readable guidance for accessing a paywalled paper.

    Args:
        title: Paper title.
        doi: Optional DOI for generating service-specific links.

    Returns:
        Formatted markdown string with access strategies.
    """
    lines: list[str] = [
        f"## Accessing: {title}",
        "",
        "### 1. Public Library Access",
        "",
        "Many public library systems provide free access to academic",
        "databases such as JSTOR and ProQuest. Check your library card",
        "holder benefits at your local or university library.",
        "",
        "### 2. Inter-Library Loan (ILL)",
        "",
        "Submit an ILL request through your library's online portal.",
        "Most libraries can obtain articles within a few business days",
        "at no cost.",
        "",
    ]

    if doi:
        lines += [
            "### 3. DeepDyve Rental",
            "",
            "Rent this article short-term via DeepDyve:",
            f"https://www.deepdyve.com/lp/doi/{quote(doi, safe='')}",
            "",
        ]

    lines += [
        "### 4. Author Copy Request",
        "",
        "Email the corresponding author directly to request a preprint",
        "or accepted manuscript. A polite template:",
        "",
        "```",
        f'Subject: Request for copy of "{title}"',
        "",
        "Dear [Author],",
        "",
        "I came across your paper and would be grateful if you could",
        "share a copy for research purposes.",
        "",
        "Thank you,",
        "[Your name]",
        "```",
        "",
        "### 5. Google Scholar",
        "",
        f'Search Google Scholar for "{title}" — author-uploaded PDFs',
        "often appear in search results:",
        f"https://scholar.google.com/scholar?q={quote_plus(title)}",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# PDF Processing Helpers
# ---------------------------------------------------------------------------


def estimate_page_chunks(total_pages: int, chunk_size: int = 20) -> list[str]:
    """Generate page range strings for chunked PDF reading.

    Args:
        total_pages: Total number of pages in the document.
        chunk_size: Pages per chunk (default 20).

    Returns:
        List of range strings, e.g. ``["1-20", "21-40", "41-55"]``.
    """
    ranges: list[str] = []
    start = 1
    while start <= total_pages:
        end = min(start + chunk_size - 1, total_pages)
        ranges.append(f"{start}-{end}")
        start = end + 1
    return ranges


def build_paper_summary_prompt(title: str, abstract: str) -> str:
    """Build a prompt for extracting key findings from a paper.

    Args:
        title: Paper title.
        abstract: Paper abstract text.

    Returns:
        Structured prompt string asking for findings, methodology,
        limitations, and relevance.
    """
    return (
        f"You are summarising the academic paper: {title}\n\n"
        f"Abstract:\n{abstract}\n\n"
        "Please extract the following from the full paper text:\n\n"
        "1. **Key findings** (3-5 bullet points): What are the main "
        "results and contributions?\n"
        "2. **Methodology summary**: What methods, datasets, or "
        "experimental approaches were used?\n"
        "3. **Limitations**: What limitations do the authors "
        "acknowledge, or do you observe?\n"
        "4. **Relevance**: How does this paper relate to the broader "
        "research topic under investigation?\n"
    )
