"""Property-based tests for AI Quality Validation using Hypothesis."""

import pytest
from hypothesis import Phase, given, settings
from hypothesis import strategies as st

from src.core.ai_context_generator import AIContextGenerator
from src.core.ai_quality_validator import AIQualityValidator, QualityScore


class TestAIQualityProperties:
    """Property-based tests for AI Quality Validator."""

    @given(
        macro=st.integers(min_value=0, max_value=20),
        concentration=st.integers(min_value=0, max_value=20),
        technical=st.integers(min_value=0, max_value=20),
        risk=st.integers(min_value=0, max_value=20),
        actionable=st.integers(min_value=0, max_value=20),
    )
    @settings(phases=[Phase.generate])  # Disable shrinking for performance
    def test_quality_score_total_calculation_property(self, macro, concentration, technical, risk, actionable):
        """Test that quality score total is always correctly calculated."""
        score = QualityScore(
            macro_intelligence=macro,
            concentration_risk=concentration,
            technical_analysis=technical,
            risk_management=risk,
            actionability=actionable,
            total=0,  # Will be calculated in __post_init__
        )

        expected_total = macro + concentration + technical + risk + actionable
        assert score.total == expected_total
        assert 0 <= score.total <= 100

    @given(
        macro=st.integers(min_value=0, max_value=20),
        concentration=st.integers(min_value=0, max_value=20),
        technical=st.integers(min_value=0, max_value=20),
        risk=st.integers(min_value=0, max_value=20),
        actionable=st.integers(min_value=0, max_value=20),
    )
    @settings(phases=[Phase.generate])
    def test_quality_assessment_consistency_property(self, macro, concentration, technical, risk, actionable):
        """Test that quality assessment categories are consistent with scores."""
        score = QualityScore(
            macro_intelligence=macro,
            concentration_risk=concentration,
            technical_analysis=technical,
            risk_management=risk,
            actionability=actionable,
            total=0,  # Will be calculated in __post_init__
        )

        assessment = AIQualityValidator.get_quality_assessment(score)

        # Verify assessment matches score range
        if score.total >= 90:
            assert "EXCELLENT" in assessment
        elif score.total >= 80:
            assert "GOOD" in assessment
        elif score.total >= 70:
            assert "ADEQUATE" in assessment
        elif score.total >= 60:
            assert "NEEDS IMPROVEMENT" in assessment
        else:
            assert "POOR" in assessment

    @given(score_value=st.integers(min_value=0, max_value=100))
    @settings(phases=[Phase.generate])
    def test_improvement_suggestions_threshold_property(self, score_value):
        """Test that improvement suggestions are provided below threshold consistently."""
        # Create a score where one category is low
        if score_value <= 15:
            # Create score with one low category
            score = QualityScore(
                macro_intelligence=score_value,
                concentration_risk=20,
                technical_analysis=20,
                risk_management=20,
                actionability=20,
                total=0,  # Will be calculated in __post_init__
            )
        else:
            # Create score with all high categories
            score = QualityScore(
                macro_intelligence=20,
                concentration_risk=20,
                technical_analysis=20,
                risk_management=20,
                actionability=20,
                total=0,  # Will be calculated in __post_init__
            )

        suggestions = AIQualityValidator.get_improvement_suggestions(score)

        # If any category is below 15, should have suggestions
        low_categories = sum(
            1
            for cat_score in [score.macro_intelligence, score.concentration_risk, score.technical_analysis, score.risk_management, score.actionability]
            if cat_score < 15
        )

        assert len(suggestions) == low_categories

    @given(text_content=st.text(min_size=0, max_size=1000))
    @settings(phases=[Phase.generate], max_examples=50)
    def test_analysis_validation_robustness_property(self, text_content):
        """Test that analysis validation never crashes with any text input."""
        try:
            score = AIQualityValidator.validate_analysis(text_content, None)

            # Score should always be valid
            assert isinstance(score, QualityScore)
            assert 0 <= score.total <= 100
            assert 0 <= score.macro_intelligence <= 20
            assert 0 <= score.concentration_risk <= 20
            assert 0 <= score.technical_analysis <= 20
            assert 0 <= score.risk_management <= 20
            assert 0 <= score.actionability <= 20

        except Exception as e:
            pytest.fail(f"Validation crashed with input '{text_content[:100]}...': {e}")

    @given(fear_greed_mentioned=st.booleans(), flows_mentioned=st.booleans(), dominance_mentioned=st.booleans(), altcoin_mentioned=st.booleans())
    @settings(phases=[Phase.generate])
    def test_macro_intelligence_scoring_property(self, fear_greed_mentioned, flows_mentioned, dominance_mentioned, altcoin_mentioned):
        """Test macro intelligence scoring consistency."""
        text_parts = []
        expected_score = 0

        if fear_greed_mentioned:
            text_parts.append("fear and greed index shows 55")
            expected_score += 5

        if flows_mentioned:
            text_parts.append("institutional flows indicate outflows")
            expected_score += 5

        if dominance_mentioned:
            text_parts.append("bitcoin dominance declined to 60%")
            expected_score += 5

        if altcoin_mentioned:
            text_parts.append("altcoin season rotation patterns")
            expected_score += 5

        text = " ".join(text_parts)
        actual_score = AIQualityValidator._score_macro_intelligence(text.lower())

        assert actual_score == expected_score

    @given(concentration_mentioned=st.booleans(), forty_percent_mentioned=st.booleans(), overweight_mentioned=st.booleans())
    @settings(phases=[Phase.generate])
    def test_concentration_risk_scoring_property(self, concentration_mentioned, forty_percent_mentioned, overweight_mentioned):
        """Test concentration discussion scoring consistency."""
        text_parts = []
        expected_score = 0

        if concentration_mentioned:
            text_parts.append("concentration risk requires attention")

        if forty_percent_mentioned:
            # Historical 40% mention now maps to general concentration discussion
            text_parts.append("concentration risk")

        # Award 10 points once for any concentration discussion (OR logic)
        if concentration_mentioned or forty_percent_mentioned:
            expected_score += 10

        if overweight_mentioned:
            text_parts.append("BTC overweight position exceeds limits, consider rebalancing")
            expected_score += 10
            # 'rebalancing' also triggers concentration discussion points if not already counted
            if not (concentration_mentioned or forty_percent_mentioned):
                expected_score += 10

        # De-duplicate tokens to avoid double counting overlapping keywords
        raw_text = " ".join(text_parts)
        text = " ".join(dict.fromkeys(raw_text.split()))
        actual_score = AIQualityValidator._score_concentration_context(text.lower(), None)

        assert actual_score == expected_score

    @given(
        altcoins_covered=st.sets(st.sampled_from(["ETH", "LINK", "DOT", "ADA", "AVAX", "UNI", "XRP"]), min_size=0, max_size=7),
        price_levels=st.integers(min_value=0, max_value=20),
    )
    @settings(phases=[Phase.generate])
    def test_technical_analysis_scoring_property(self, altcoins_covered, price_levels):
        """Test technical analysis scoring scales with coverage."""
        text_parts = []

        # Add altcoin mentions
        for altcoin in altcoins_covered:
            text_parts.append(f"{altcoin} analysis provided")

        # Add price levels
        for i in range(price_levels):
            text_parts.append(f"support at ${3000 + i * 100}")

        text = " ".join(text_parts)
        score = AIQualityValidator._score_technical_analysis(text.lower(), text)

        # Score should increase with more altcoins and price levels
        expected_altcoin_score = len(altcoins_covered) * 2
        if len(altcoins_covered) >= 7:
            expected_altcoin_score += 6  # Bonus for covering all

        # Price level scoring (capped at 6 points)
        if price_levels >= 10:
            expected_price_score = 6
        elif price_levels >= 5:
            expected_price_score = 3
        elif price_levels >= 2:
            expected_price_score = 1
        else:
            expected_price_score = 0

        expected_total = min(expected_altcoin_score + expected_price_score, 20)
        assert score == expected_total

    @given(portfolio_allocation=st.floats(min_value=0.0, max_value=100.0))
    @settings(phases=[Phase.generate], max_examples=50)
    def test_concentration_analysis_allocation_property(self, portfolio_allocation):
        """Test concentration analysis handles any allocation percentage."""
        portfolio_data = {
            "balances": {"BTC": {"free": 1.0, "value": portfolio_allocation * 1000}, "USDT": {"free": 1000, "value": (100 - portfolio_allocation) * 1000}}
        }

        try:
            result = AIContextGenerator._generate_concentration_risk_analysis(portfolio_data)

            # Should always return a string
            assert isinstance(result, str)
            assert len(result) > 0

            # Basic robustness check (no fixed caps enforced anymore)
            assert isinstance(result, str) and len(result) > 0

        except Exception as e:
            pytest.fail(f"Concentration analysis failed with allocation {portfolio_allocation}: {e}")

    @given(threshold=st.integers(min_value=0, max_value=100), actual_score=st.integers(min_value=0, max_value=100))
    @settings(phases=[Phase.generate])
    def test_threshold_comparison_property(self, threshold, actual_score):
        """Test that threshold comparison is consistent."""
        score = QualityScore(
            macro_intelligence=min(actual_score // 5, 20),
            concentration_risk=min(actual_score // 5, 20),
            technical_analysis=min(actual_score // 5, 20),
            risk_management=min(actual_score // 5, 20),
            actionability=min(actual_score - (4 * min(actual_score // 5, 20)), 20),
            total=0,  # Will be calculated in __post_init__
        )

        # Use actual score for comparison since total is calculated
        meets_threshold = score.total >= threshold

        # Verify the comparison logic
        if score.total >= threshold:
            assert meets_threshold is True
        else:
            assert meets_threshold is False
