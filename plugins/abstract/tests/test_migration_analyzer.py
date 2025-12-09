from scripts.migration_analyzer import MigrationAnalyzer


def test_detects_overlapping_functionality():
    analyzer = MigrationAnalyzer("abstract")

    overlaps = analyzer.analyze_plugin("test-skill")

    assert "test-driven-development" in overlaps
    assert overlaps["test-driven-development"]["confidence"] > 0.8
