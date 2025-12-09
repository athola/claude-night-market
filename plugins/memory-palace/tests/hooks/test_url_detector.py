"""Tests for url_detector hook."""

from __future__ import annotations

import os
import sys

# Add hooks to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../hooks"))

from url_detector import extract_urls


class TestExtractUrls:
    """Tests for URL extraction."""

    def test_no_urls(self) -> None:
        """Text without URLs should return empty list."""
        assert extract_urls("Hello world, no URLs here.") == []

    def test_http_url(self) -> None:
        """HTTP URLs should be extracted."""
        urls = extract_urls("Check out http://example.com for more.")
        assert "http://example.com" in urls

    def test_https_url(self) -> None:
        """HTTPS URLs should be extracted."""
        urls = extract_urls("See https://example.com/article for details.")
        assert len(urls) == 1
        assert "https://example.com/article" in urls[0]

    def test_multiple_urls(self) -> None:
        """Multiple URLs should be extracted."""
        text = "Visit https://one.com and https://two.com for info."
        urls = extract_urls(text)
        assert len(urls) == 2

    def test_localhost_skipped(self) -> None:
        """Localhost URLs should be skipped."""
        urls = extract_urls("API at http://localhost:3000/api")
        assert len(urls) == 0

    def test_127_0_0_1_skipped(self) -> None:
        """127.0.0.1 URLs should be skipped."""
        urls = extract_urls("Server at http://127.0.0.1:8080")
        assert len(urls) == 0

    def test_image_urls_skipped(self) -> None:
        """Image URLs should be skipped."""
        urls = extract_urls("Image at https://example.com/photo.png")
        assert len(urls) == 0

    def test_video_urls_skipped(self) -> None:
        """Video URLs should be skipped."""
        urls = extract_urls("Video at https://example.com/video.mp4")
        assert len(urls) == 0

    def test_archive_urls_skipped(self) -> None:
        """Archive URLs should be skipped."""
        urls = extract_urls("Download https://example.com/file.zip")
        assert len(urls) == 0

    def test_pdf_urls_skipped(self) -> None:
        """PDF URLs should be skipped (special handling needed)."""
        urls = extract_urls("Paper at https://example.com/paper.pdf")
        assert len(urls) == 0

    def test_article_urls_extracted(self) -> None:
        """Article URLs should be extracted."""
        urls = extract_urls("Read https://blog.example.com/article-title")
        assert len(urls) == 1

    def test_fast_path_no_protocol(self) -> None:
        """Fast path: text without :// should return immediately."""
        # This should be very fast since no URLs possible
        urls = extract_urls("No protocol indicators here at all")
        assert urls == []

    def test_urls_in_markdown(self) -> None:
        """URLs in markdown links should be extracted."""
        text = "Check [this article](https://example.com/article) for more."
        urls = extract_urls(text)
        # Should extract but might include trailing )
        assert any("example.com/article" in url for url in urls)

    def test_complex_url_path(self) -> None:
        """Complex URL paths should be handled."""
        text = "See https://docs.example.com/v2/api/reference#section"
        urls = extract_urls(text)
        assert len(urls) == 1
        assert "docs.example.com" in urls[0]
