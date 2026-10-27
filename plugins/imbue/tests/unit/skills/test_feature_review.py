"""Contract tests for the feature-review skill.

The skill is markdown that a session follows, so its behavior is what the
files say. These tests pin the formulas, weights, thresholds, scales and
guardrails in SKILL.md and its modules, and check that the files which
repeat a value agree with each other. Arithmetic runs on numbers parsed
out of the markdown, so a changed weight or threshold changes the result.

The worked example's value, cost and band are pinned by
test_feature_review_doc_math.py and are not repeated here.
"""

from __future__ import annotations

import fnmatch
import re
import runpy
import tempfile
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[3] / "skills" / "feature-review"
MODULES = SKILL_DIR / "modules"
SKILL = (SKILL_DIR / "SKILL.md").read_text()
FRAMEWORK = (MODULES / "scoring-framework.md").read_text()
CLASSIFICATION = (MODULES / "classification-system.md").read_text()
TRADEOFFS = (MODULES / "tradeoff-dimensions.md").read_text()
RESEARCH = (MODULES / "research-enrichment.md").read_text()
CONFIG = (MODULES / "configuration.md").read_text()
METHODOLOGY = (MODULES / "multi-metric-evaluation-methodology.md").read_text()

VALUE_FACTORS = ("reach", "impact", "business_value", "time_criticality")
COST_FACTORS = ("effort", "risk", "complexity")


def _between(text: str, start: str, end: str) -> str:
    """Return text from the first ``start`` up to the next ``end``."""
    begin = text.index(start)
    return text[begin : text.index(end, begin + len(start))]


def _yaml_block_after(text: str, marker: str) -> str:
    """Return the first fenced block that follows ``marker``."""
    after = text[text.index(marker) :]
    return _between(after, "```", "\n```\n")


def _weights(block: str, keys: tuple[str, ...]) -> dict[str, float]:
    """Read ``key: number`` pairs for ``keys`` from a YAML-ish block."""
    found = {}
    for key in keys:
        match = re.search(rf"^\s+{key}: ([\d.]+)", block, re.M)
        assert match, f"{key} missing"
        found[key] = float(match.group(1))
    return found


def _skill_config_block() -> str:
    return _yaml_block_after(SKILL, "Create `.feature-review.yaml` in project root:")


def _config_schema_block() -> str:
    return _yaml_block_after(CONFIG, "## Full Configuration Schema")


def _framework_example_value(name: str) -> float:
    example = _between(FRAMEWORK, "## Calculation Example", "## Interpreting Scores")
    match = re.search(rf"^{name}: ([\d.]+)", example, re.M)
    assert match, name
    return float(match.group(1))


def _framework_printed(label: str) -> float:
    example = _between(FRAMEWORK, "## Calculation Example", "## Interpreting Scores")
    match = re.search(rf"^{label} = .* = ([\d.]+)$", example, re.M)
    assert match, label
    return float(match.group(1))


def _thresholds() -> dict[str, float]:
    block = _config_schema_block()
    return {
        key: float(re.search(rf"^\s+{key}: ([\d.]+)", block, re.M).group(1))
        for key in ("high_priority", "medium_priority", "confidence_warning")
    }


def _code_block_function(text: str, name: str, init: dict | None = None) -> dict:
    """Run the fenced python block that defines ``name``; return its globals."""
    for block in re.findall(r"```python\n(.*?)```", text, re.S):
        if f"def {name}(" in block:
            with tempfile.TemporaryDirectory() as scratch:
                script = Path(scratch) / "doc_block.py"
                script.write_text(block)
                return runpy.run_path(str(script), init_globals=init)
    raise AssertionError(f"no python block defines {name}")


def _research_namespace() -> dict:
    # The max_delta_clamp block reads FIBONACCI from the block before it,
    # as a reader following the module top to bottom would.
    namespace = _code_block_function(RESEARCH, "clamp_to_fibonacci")
    return _code_block_function(RESEARCH, "max_delta_clamp", init=namespace)


def _channel_weights() -> dict[str, float]:
    table = _between(RESEARCH, "### Channel Weight", "### Evidence Strength Sources")
    return {
        name: float(weight)
        for name, weight in re.findall(r"^\| ([\w-]+) \| ([\d.]+) \|", table, re.M)
    }


def _channel_factors() -> dict[str, tuple[str, str]]:
    table = _between(RESEARCH, "## Channel-to-Factor Mapping", "## Score Delta")
    return {
        channel: (primary, secondary)
        for channel, primary, secondary in re.findall(
            r"^\| ([\w-]+) \| ([\w ]+?) \| ([\w ]+?) \|", table, re.M
        )
        if channel != "Channel"
    }


def _tradeoff_default_weights() -> dict[str, float]:
    table = _between(TRADEOFFS, "### Default Weights", "### Guardrail")
    return {
        name.lower().replace(" ", "_"): float(weight)
        for name, weight in re.findall(
            r"^\| ([A-Z][\w ]+?) \| ([\d.]+) \|", table, re.M
        )
    }


def _tradeoff_score(scores: dict[str, float], weights: dict[str, float]) -> float:
    """Tradeoff Score = sum(score * weight) / sum(weights), as the module states."""
    total_weight = sum(weights[d] for d in scores)
    return sum(scores[d] * weights[d] for d in scores) / total_weight


def _example_names(text: str, heading: str, end: str) -> list[str]:
    table = _between(text, heading, end)
    rows = re.findall(r"^\| ([A-Z][\w -]+?) \| ", table, re.M)
    return [row for row in rows if row not in {"Feature", "Pro", "Model"}]


class TestScoringFramework:
    """Feature: RICE+WSJF hybrid scoring produces accurate prioritization."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_value_score_calculation(self) -> None:
        """Scenario: Value score is calculated from value factors.

        Given the skill's scoring formula
        When the value score is defined
        Then it is the weighted average of the four value factors, each of
            which the framework module defines on the Fibonacci scale.
        """
        assert (
            "Value Score = weighted_avg(Reach, Impact, Business Value, Time Criticality)"
            in SKILL
        )
        for heading in (
            "### Reach (R)",
            "### Impact (I)",
            "### Business Value (BV)",
            "### Time Criticality (TC)",
        ):
            section = FRAMEWORK[FRAMEWORK.index(heading) :]
            scores = re.findall(r"^\| (\d+) \|", section, re.M)[:6]
            assert scores == ["1", "2", "3", "5", "8", "13"], heading

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_cost_score_calculation(self) -> None:
        """Scenario: Cost score is calculated from cost factors.

        Given the skill's scoring formula
        When the cost score is defined
        Then it is the weighted average of Effort, Risk and Complexity.
        """
        assert "Cost Score = weighted_avg(Effort, Risk, Complexity)" in SKILL
        assert "Cost Score = weighted_avg(Effort, Risk, Complexity)" in FRAMEWORK
        for heading in ("### Effort (E)", "### Risk (Rk)", "### Complexity (Cx)"):
            assert heading in FRAMEWORK

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_feature_score_calculation(self) -> None:
        """Scenario: Feature score combines value, cost, and confidence.

        Given the worked example's printed value, cost and confidence
        When (value / cost) * confidence is computed
        Then it equals the printed Feature Score.
        """
        assert "Feature Score = (Value Score / Cost Score) * Confidence" in FRAMEWORK
        assert "Adjusted Score = Feature Score * Confidence" in SKILL
        value = _framework_printed("Value Score")
        cost = _framework_printed("Cost Score")
        confidence = _framework_example_value("Confidence")
        assert _framework_printed("Feature Score") == pytest.approx(
            value / cost * confidence, abs=0.005
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_weighted_value_score(self) -> None:
        """Scenario: Weighted value score applies configured weights.

        Given the default weights stated in SKILL.md's prose
        When they weight the worked example's value factors
        Then the result is the framework's printed Value Score, so the
            two files state the same weights.
        """
        prose = _between(SKILL, "Default weights (value:", "and how to override")
        weights = {
            "reach": float(re.search(r"reach ([\d.]+)", prose)[1]),
            "impact": float(re.search(r"impact ([\d.]+)", prose)[1]),
            "business_value": float(re.search(r"business value ([\d.]+)", prose)[1]),
            "time_criticality": float(
                re.search(r"time criticality ([\d.]+)", prose)[1]
            ),
        }
        value = sum(
            _framework_example_value(name) * weights[key]
            for name, key in (
                ("Reach", "reach"),
                ("Impact", "impact"),
                ("Business Value", "business_value"),
                ("Time Criticality", "time_criticality"),
            )
        )
        assert value == pytest.approx(_framework_printed("Value Score"), abs=0.005)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_priority_thresholds(self) -> None:
        """Scenario: Feature scores map to priority levels.

        Given the thresholds in configuration.md, SKILL.md and the framework
        When the cut points are read from each
        Then High starts above 2.5, Medium at 1.5, Low at 1.0, and the
            three files state the same numbers.
        """
        limits = _thresholds()
        assert (limits["high_priority"], limits["medium_priority"]) == (2.5, 1.5)
        assert "| 1.0 - 1.5 | Low |" in FRAMEWORK
        assert f"**> {limits['high_priority']}**: High priority." in SKILL
        assert (
            f"**{limits['medium_priority']} - {limits['high_priority']}**: "
            "Medium priority." in SKILL
        )
        assert f"| > {limits['high_priority']} | High |" in FRAMEWORK

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_confidence_adjustment(self) -> None:
        """Scenario: Low confidence features are flagged for research.

        Given the confidence guardrail
        When the three files state the cut-off
        Then each says confidence below 0.5 is flagged for research.
        """
        assert _thresholds()["confidence_warning"] == 0.5
        assert "Confidence < 0.5: Require research before commitment" in FRAMEWORK
        assert (
            "Features with confidence < 0.5 should be flagged for research" in FRAMEWORK
        )
        assert "Review scores below 50% confidence." in SKILL

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_weight_normalization(self) -> None:
        """Scenario: Weights must sum to 1.0 within each category.

        Given the default weights in SKILL.md, configuration.md and the
            framework's Custom Weights block
        When each category is summed
        Then value and cost each sum to 1.0, and the files agree.
        """
        framework_block = _yaml_block_after(FRAMEWORK, "## Custom Weights")
        sources = [_skill_config_block(), _config_schema_block(), framework_block]
        parsed = [
            (_weights(b, VALUE_FACTORS), _weights(b, COST_FACTORS)) for b in sources
        ]
        for value, cost in parsed:
            assert sum(value.values()) == pytest.approx(1.0)
            assert sum(cost.values()) == pytest.approx(1.0)
        assert parsed[0] == parsed[1] == parsed[2]
        assert "Weights within each category must sum to 1.0" in FRAMEWORK
        assert "Weight sum | Weights within each category must sum to 1.0" in CONFIG

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_zero_weight_handling(self) -> None:
        """Scenario: Zero weights effectively disable factors.

        Given SKILL.md's "0.0 to disable" tradeoff weights and the module's
            composite formula
        When one dimension's weight is set to 0.0
        Then the composite equals the score over the remaining dimensions.
        """
        assert "# Tradeoff dimension weights (0.0 to disable)" in SKILL
        assert (
            "Tradeoff Score = Σ(dimension_score * dimension_weight) / Σ(weights)"
            in TRADEOFFS
        )
        weights = _tradeoff_default_weights()
        scores = dict.fromkeys(weights, 3.0)
        scores["latency"] = 1.0
        disabled = {**weights, "latency": 0.0}
        without_latency = {d: s for d, s in scores.items() if d != "latency"}
        assert _tradeoff_score(scores, disabled) == pytest.approx(
            _tradeoff_score(without_latency, weights)
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_missing_dimension_handling(self) -> None:
        """Scenario: Missing dimensions use default values.

        Given the configuration schema
        When a project omits a key
        Then the documented default applies, as the schema's header says.
        """
        assert (
            "# All values shown are defaults - only specify what you want to change"
            in CONFIG
        )
        minimal = _yaml_block_after(CONFIG, "### Startup (Move Fast)")
        assert "weights:" not in minimal
        assert "high_priority: 2.0" in minimal


class TestClassificationSystem:
    """Feature: Features are classified along two orthogonal axes."""

    @staticmethod
    def _patterns(key: str) -> list[str]:
        match = re.search(rf"{key}: \[(.*?)\]", _config_schema_block())
        assert match, key
        return [p.strip().strip('"') for p in match.group(1).split(",")]

    @staticmethod
    def _matches(name: str, patterns: list[str]) -> bool:
        return any(fnmatch.fnmatch(name.lower(), p) for p in patterns)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_proactive_classification(self) -> None:
        """Scenario: Proactive features anticipate user needs.

        Given the classification definition and the proactive name patterns
        When the documented proactive examples are matched
        Then both files define proactive as anticipating needs, and the
            configured patterns catch the examples.
        """
        assert (
            "| **Proactive** | Anticipates user needs. | Suggestions, prefetching. |"
            in SKILL
        )
        assert (
            "Anticipates user needs and acts before explicit request." in CLASSIFICATION
        )
        patterns = self._patterns("proactive_patterns")
        for example in ("Auto-save", "Prefetching", "Suggestions"):
            assert self._matches(example, patterns), example

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_reactive_classification(self) -> None:
        """Scenario: Reactive features respond to explicit input.

        Given the module's reactive examples
        When matched against the proactive patterns
        Then none is misread as proactive, and the definition is stated.
        """
        assert "Responds to explicit user input or system events." in CLASSIFICATION
        assert "default_type: reactive" in _config_schema_block()
        reactive = _example_names(
            CLASSIFICATION, "| Feature | How It's Reactive |", "**Tradeoffs:**"
        )
        assert reactive == [
            "Form submission",
            "Search",
            "Navigation",
            "Validation",
            "Commands",
        ]
        patterns = self._patterns("proactive_patterns")
        assert not [r for r in reactive if self._matches(r, patterns)]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_static_classification(self) -> None:
        """Scenario: Static features have incremental data updates.

        Given the module's static examples
        When matched against the dynamic patterns
        Then none is misread as dynamic, and static is the default.
        """
        assert "Data changes incrementally through explicit updates." in CLASSIFICATION
        assert "| **Static** | Incremental, versioned. | File-based, cached. |" in SKILL
        assert "default_data: static" in _config_schema_block()
        static = _example_names(
            CLASSIFICATION, "| Feature | Why It's Static |", "**Tradeoffs:**"
        )
        patterns = self._patterns("dynamic_patterns")
        assert "Skill definitions" in static
        assert not [s for s in static if self._matches(s, patterns)]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_dynamic_classification(self) -> None:
        """Scenario: Dynamic features have continuous data changes.

        Given the dynamic definition and its name patterns
        When the module's "User sessions" example is matched
        Then a dynamic pattern catches it.
        """
        assert "Data changes continuously through ongoing operations." in CLASSIFICATION
        assert (
            "| **Dynamic** | Continuous, streaming. | Database, real-time. |" in SKILL
        )
        dynamic = _example_names(
            CLASSIFICATION, "| Feature | Why It's Dynamic |", "**Tradeoffs:**"
        )
        assert "User sessions" in dynamic
        assert self._matches("User sessions", self._patterns("dynamic_patterns"))

    @pytest.mark.bdd
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "axis_1,axis_2,archetype",
        [
            ("Proactive", "Static", "Predictive Cache"),
            ("Proactive", "Dynamic", "Smart Assistant"),
            ("Reactive", "Static", "Reference Lookup"),
            ("Reactive", "Dynamic", "Interactive Query"),
        ],
        ids=["predictive-cache", "smart-assistant", "reference-lookup", "query"],
    )
    def test_2x2_matrix_classification(self, axis_1, axis_2, archetype) -> None:
        """Scenario: Features map to one of four archetypes.

        Given the 2x2 matrix
        When each axis pair is looked up
        Then the module names exactly one archetype for it.
        """
        heading = f"#### {archetype} ({axis_1} and {axis_2})"
        others = re.findall(
            rf"^#### .* \({axis_1} and {axis_2}\)$", CLASSIFICATION, re.M
        )
        assert others == [heading]


class TestKanoClassification:
    """Feature: Kano categories guide prioritization."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_performance_features_scale_linearly(self) -> None:
        """Scenario: Performance features have linear satisfaction.

        Given the framework and the methodology module
        When each describes the Performance category
        Then both say satisfaction scales linearly.
        """
        assert "### Performance (Linear)" in FRAMEWORK
        assert "More is better; satisfaction scales with quality" in FRAMEWORK
        assert (
            "| Performance | Linear satisfaction | Linear dissatisfaction |"
            in METHODOLOGY
        )


class TestTradeoffDimensions:
    """Feature: Tradeoffs are scored across quality dimensions."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_minimum_dimensions_required(self) -> None:
        """Scenario: At least 5 tradeoff dimensions must be evaluated.

        Given the guardrail in three files
        When each states the minimum
        Then all say 5, out of the nine dimensions SKILL.md lists.
        """
        assert (
            "**Minimum dimensions**: Evaluate at least 5 tradeoff dimensions." in SKILL
        )
        assert "**Minimum 5 dimensions must be evaluated.**" in TRADEOFFS
        assert "At least 5 tradeoff dimensions must have non-zero weight" in CONFIG
        table = _between(SKILL, "| Dimension | Question | Scale |", "See [tradeoff")
        assert len(re.findall(r"^\| \*\*", table, re.M)) == 9
        assert "structured evaluation across nine dimensions" in TRADEOFFS

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_dimension_scale_validation(self) -> None:
        """Scenario: All dimensions use 1-5 scale.

        Given SKILL.md's dimension table and the module's scale
        When each row's scale is read
        Then every dimension is scored 1-5.
        """
        table = _between(SKILL, "| Dimension | Question | Scale |", "See [tradeoff")
        scales = re.findall(r"\| ([\d-]+) \|$", table, re.M)
        assert scales == ["1-5"] * 9
        assert "**Scoring Scale:** 1-5 for each dimension" in TRADEOFFS

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_weighted_tradeoff_score(self) -> None:
        """Scenario: Tradeoff scores can be weighted.

        Given the module's default weights
        When the composite formula weights a set of scores
        Then the low-weight dimension moves the result less, and the module,
            SKILL.md and configuration.md state the same weights.
        """
        weights = _tradeoff_default_weights()
        skill = _weights(_skill_config_block(), tuple(weights))
        config = _weights(_config_schema_block(), tuple(weights))
        assert weights == skill == config
        base = dict.fromkeys(weights, 3.0)
        low_redundancy = {**base, "redundancy": 1.0}
        low_quality = {**base, "quality": 1.0}
        assert weights["redundancy"] < weights["quality"]
        assert _tradeoff_score(low_redundancy, weights) > _tradeoff_score(
            low_quality, weights
        )


class TestIntegration:
    """Feature: Accepted suggestions become GitHub issues."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_issue_title_comes_from_the_suggestion(self) -> None:
        """Scenario: Generated issues take their title from the suggestion.

        Renamed from test_issue_title_format: the skill states no title
        format (the old test asserted a conventional-commit title nothing
        documents). It does state where the title comes from, and the
        deferred-capture command carries the same title.
        """
        assert "1. Generate issue title and body from suggestions." in SKILL
        assert '--title "<suggestion title>"' in SKILL
        assert "--source feature-review" in SKILL

    @pytest.mark.bdd
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "band,expected_label",
        [
            ("high", "priority/high"),
            ("medium", "priority/medium"),
            ("low", "priority/low"),
        ],
    )
    def test_suggestion_labels(self, band, expected_label) -> None:
        """Scenario: Suggestions get appropriate labels based on priority.

        Given configuration.md's priority_labels and label_prefix
        When the label for a priority band is read
        Then it is the configured one for that band, under the
            ``priority/`` prefix SKILL.md names.
        """
        block = _config_schema_block()
        prefix = re.search(r'label_prefix: "(.*?)"', block)[1]
        label = re.search(rf'^\s+{band}: "(.*?)"', block, re.M)[1]
        assert label == expected_label
        assert label.startswith(prefix)
        assert "(enhancement, feature-review, priority/*)" in SKILL

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_default_labels_agree_between_skill_and_configuration(self) -> None:
        """SKILL.md and configuration.md name the same non-priority labels."""
        default = re.search(r"default_labels: \[(.*?)\]", _config_schema_block())[1]
        configured = {label.strip() for label in default.split(",")}
        stated = re.search(r"Apply labels \((.*?), priority/\*\)", SKILL)[1]
        assert configured == {label.strip() for label in stated.split(",")}

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_backlog_limit_guardrail(self) -> None:
        """Scenario: Backlog is limited to prevent suggestion overload.

        Given the backlog guardrail
        When each file states the limit
        Then all say 25, and no example configuration exceeds it.
        """
        assert "**Backlog limit**: Limit suggestion queue to 25 items." in SKILL
        assert (
            "max_items: 25              # Maximum items (guardrail, cannot exceed 25)"
            in CONFIG
        )
        assert "| Backlog limit | Maximum 25 items" in CONFIG
        limits = [int(n) for n in re.findall(r"max_items: (\d+)", CONFIG)]
        assert limits
        assert max(limits) <= 25


class TestResearchEnrichment:
    """Feature: tome research adjusts scores with external evidence."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_delta_calculation(self) -> None:
        """Scenario: Research delta adjusts scores correctly.

        Given the delta formula and the code-search channel weight
        When strong positive findings are scored
        Then the applied delta is consensus * strength * channel weight and
            clears the configured evidence threshold.
        """
        assert "research_delta = findings_consensus * evidence_strength" in RESEARCH
        assert "applied_delta = research_delta * channel_weight" in RESEARCH
        weight = _channel_weights()["code-search"]
        assert weight == 0.8
        applied = 1.5 * 0.8 * weight
        threshold = float(re.search(r"evidence_threshold: ([\d.]+)", CONFIG)[1])
        assert applied > threshold

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_evidence_threshold_discard(self) -> None:
        """Scenario: Low-evidence deltas are discarded.

        Given the discard rule and the configured threshold
        When sparse findings through the weakest channel are scored
        Then the delta falls under the threshold and the doc sets it to 0.
        """
        assert "If abs(applied_delta) < evidence_threshold:" in RESEARCH
        assert "applied_delta = 0  (insufficient evidence, discard)" in RESEARCH
        assert "| 1-5 findings | 0.3-0.5 |" in RESEARCH
        threshold = float(re.search(r"evidence_threshold: ([\d.]+)", CONFIG)[1])
        weakest = min(_channel_weights().values())
        sparse_strength = 0.3  # lower bound of the "1-5 findings" row
        assert abs(1 * sparse_strength * weakest) < threshold

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_fibonacci_clamping(self) -> None:
        """Scenario: Adjusted scores clamp to nearest Fibonacci.

        Given the module's clamp_to_fibonacci
        When it runs on the module's own example
        Then 7 clamps to 8, on the skill's 1-13 Fibonacci scale.
        """
        namespace = _research_namespace()
        assert namespace["FIBONACCI"] == [1, 2, 3, 5, 8, 13]
        assert "**Scoring Scale:** Fibonacci (1, 2, 3, 5, 8, 13)." in SKILL
        assert "Initial: 5, raw_adjusted: 7 -> clamp: 8" in RESEARCH
        assert namespace["clamp_to_fibonacci"](7) == 8

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_max_delta_constraint(self) -> None:
        """Scenario: Adjustments capped at max_delta Fibonacci steps.

        Given max_delta_clamp and the configured max_delta
        When 2 is pushed to 13 (four steps)
        Then it stops at 5, the value the module's example concludes.
        """
        max_delta = int(re.search(r"max_delta: (\d+)", CONFIG)[1])
        namespace = _research_namespace()
        assert "exceeds max_delta -> use 5 (2 steps away from 2)" in RESEARCH
        assert namespace["max_delta_clamp"](2, 13, max_delta) == 5
        assert namespace["max_delta_clamp"](3, 13, max_delta) == 8
        assert namespace["max_delta_clamp"](5, 8, max_delta) == 8

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_graceful_degradation(self) -> None:
        """Scenario: Scores unchanged when research unavailable.

        Given tome is not installed
        When --research runs
        Then all three files say it warns and keeps initial scores.
        """
        assert (
            "**Graceful degradation**: If tome is not installed, prints\n"
            "a warning and proceeds with initial scores unchanged." in SKILL
        )
        assert "Initial scores stand unchanged." in RESEARCH
        assert "a warning and proceeds with initial scores unchanged." in CONFIG

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_channel_factor_mapping(self) -> None:
        """Scenario: Research channels map to correct scoring factors.

        Given the channel-to-factor table
        When each channel's primary factor is read
        Then it matches the factors SKILL.md's research example adjusts.
        """
        mapping = _channel_factors()
        assert mapping["code-search"][0] == "Reach"
        assert mapping["discourse"][0] == "Impact"
        assert mapping["papers"][0] == "Impact"
        assert mapping["triz"][0] == "Business Value"
        example = _between(SKILL, "### Code Search (GitHub)", "### Suggestion Report")
        code_search, discourse = example.split("### Discourse")
        assert "**Reach**: +1" in code_search
        assert "**Impact**: +1" in discourse

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_adjusted_score_with_research(self) -> None:
        """Scenario: Research enriches a feature's score.

        Given the clamping rules
        When an initial 3 gets a +2 delta
        Then raw 5 is already on the scale and is kept.
        """
        namespace = _research_namespace()
        assert "1. Calculate `raw_adjusted = initial_score + applied_delta`" in RESEARCH
        adjusted = namespace["clamp_to_fibonacci"](3 + 2)
        assert adjusted == 5
        assert namespace["max_delta_clamp"](3, adjusted) == 5

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_score_adjustment_example_follows_the_clamp_rule(self) -> None:
        """Every row in the example table equals clamp(initial + delta)."""
        namespace = _research_namespace()
        table = _between(RESEARCH, "### Score Adjustments", "```\n")
        rows = re.findall(
            r"^\| \w+ +\| \w+ +\| (\d+) +\| ([+-]?\d+) +\| (\d+) ", table, re.M
        )
        assert rows
        for initial, delta, adjusted in rows:
            assert namespace["clamp_to_fibonacci"](int(initial) + int(delta)) == int(
                adjusted
            )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_research_does_not_reduce_below_minimum(self) -> None:
        """Scenario: Research cannot reduce score below 1.

        Given a large negative delta on a low score
        When the module's clamp runs
        Then the result is 1, the bottom of the Fibonacci scale.
        """
        namespace = _research_namespace()
        assert "findings_consensus: -2 to +2" in RESEARCH
        assert namespace["clamp_to_fibonacci"](2 - 5) == 1
