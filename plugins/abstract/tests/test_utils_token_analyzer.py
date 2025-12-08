"""Tests for TokenAnalyzer class in tokens.py."""


from abstract.tokens import TokenAnalyzer


class TestTokenAnalyzerAnalyzeContent:
    """Tests for TokenAnalyzer.analyze_content method."""

    def test_analyze_content_returns_dict(self):
        """Test that analyze_content returns a dictionary."""
        result = TokenAnalyzer.analyze_content("Hello world")
        assert isinstance(result, dict)

    def test_analyze_content_has_required_keys(self):
        """Test that result contains required token breakdown keys."""
        result = TokenAnalyzer.analyze_content("Hello world")
        required_keys = {"total_tokens", "char_count", "word_count"}
        assert required_keys.issubset(result.keys())

    def test_analyze_content_empty_string(self):
        """Test analyzing empty string returns zeros."""
        result = TokenAnalyzer.analyze_content("")
        assert result["total_tokens"] == 0
        assert result["char_count"] == 0
        assert result["word_count"] == 0

    def test_analyze_content_simple_text(self):
        """Test analyzing simple text."""
        # "Hello world" = 11 chars, 2 words
        result = TokenAnalyzer.analyze_content("Hello world")
        assert result["char_count"] == 11
        assert result["word_count"] == 2
        assert result["total_tokens"] > 0

    def test_analyze_content_with_code_block(self):
        """Test analyzing content with code blocks."""
        content = """Some text

```python
def foo():
    pass
```

More text."""
        result = TokenAnalyzer.analyze_content(content)
        assert "code_tokens" in result
        assert result["code_tokens"] > 0

    def test_analyze_content_with_frontmatter(self):
        """Test analyzing content with YAML frontmatter."""
        content = """---
name: test-skill
description: A test skill
---

# Main Content

Body text here."""
        result = TokenAnalyzer.analyze_content(content)
        assert "frontmatter_tokens" in result
        assert "body_tokens" in result
        assert result["frontmatter_tokens"] > 0

    def test_analyze_content_token_estimation_uses_char_ratio(self):
        """Test that token estimation uses ~4 chars per token."""
        # 100 chars of text should be roughly 25 tokens
        text = "a" * 100
        result = TokenAnalyzer.analyze_content(text)
        # Allow some variance but should be close to 25
        assert 20 <= result["total_tokens"] <= 30


class TestTokenAnalyzerCheckEfficiency:
    """Tests for TokenAnalyzer.check_efficiency method."""

    def test_check_efficiency_returns_dict(self):
        """Test that check_efficiency returns a dictionary."""
        result = TokenAnalyzer.check_efficiency(1000)
        assert isinstance(result, dict)

    def test_check_efficiency_has_required_keys(self):
        """Test that result contains required keys."""
        result = TokenAnalyzer.check_efficiency(1000)
        required_keys = {"status", "rating", "is_efficient", "message"}
        assert required_keys.issubset(result.keys())

    def test_check_efficiency_optimal_range(self):
        """Test that tokens in optimal range return OPTIMAL status."""
        result = TokenAnalyzer.check_efficiency(1500, optimal=2000)
        assert result["status"] == "OPTIMAL"
        assert result["is_efficient"] is True
        assert result["rating"] >= 0.9

    def test_check_efficiency_good_range(self):
        """Test that tokens slightly over optimal return GOOD status."""
        result = TokenAnalyzer.check_efficiency(2500, optimal=2000, max_acceptable=4000)
        assert result["status"] == "GOOD"
        assert result["is_efficient"] is True
        assert 0.7 <= result["rating"] < 0.9

    def test_check_efficiency_warning_range(self):
        """Test that tokens near max return WARNING status."""
        result = TokenAnalyzer.check_efficiency(3500, optimal=2000, max_acceptable=4000)
        assert result["status"] == "WARNING"
        assert result["is_efficient"] is True
        assert 0.5 <= result["rating"] < 0.7

    def test_check_efficiency_exceeds_max(self):
        """Test that tokens over max return EXCESSIVE status."""
        result = TokenAnalyzer.check_efficiency(5000, optimal=2000, max_acceptable=4000)
        assert result["status"] == "EXCESSIVE"
        assert result["is_efficient"] is False
        assert result["rating"] < 0.5

    def test_check_efficiency_zero_tokens(self):
        """Test handling of zero tokens."""
        result = TokenAnalyzer.check_efficiency(0)
        assert result["status"] == "OPTIMAL"
        assert result["is_efficient"] is True

    def test_check_efficiency_custom_thresholds(self):
        """Test with custom threshold values."""
        result = TokenAnalyzer.check_efficiency(
            500, optimal=1000, max_acceptable=2000
        )
        assert result["status"] == "OPTIMAL"
        assert result["is_efficient"] is True

    def test_check_efficiency_message_describes_status(self):
        """Test that message provides useful feedback."""
        result = TokenAnalyzer.check_efficiency(
            5000, optimal=2000, max_acceptable=4000
        )
        msg = result["message"].lower()
        assert "exceed" in msg or "over" in msg

    def test_check_efficiency_includes_thresholds_in_result(self):
        """Test that result includes the thresholds used."""
        result = TokenAnalyzer.check_efficiency(1000, optimal=2000, max_acceptable=4000)
        assert result["optimal_threshold"] == 2000
        assert result["max_threshold"] == 4000
