"""Tests for AI Quality Validator Module."""

import pytest

from src.core.ai_quality_validator import AIQualityValidator, QualityScore


class TestQualityScore:
    """Test suite for QualityScore dataclass."""

    def test_quality_score_calculation(self):
        """Test that total score is calculated correctly."""
        score = QualityScore(
            macro_intelligence=15,
            concentration_risk=18,
            technical_analysis=12,
            risk_management=20,
            actionability=16,
            total=0,  # Will be calculated in __post_init__
        )

        assert score.total == 81
        assert score.macro_intelligence == 15
        assert score.concentration_risk == 18

    def test_quality_score_perfect(self):
        """Test perfect quality score."""
        score = QualityScore(
            macro_intelligence=20,
            concentration_risk=20,
            technical_analysis=20,
            risk_management=20,
            actionability=20,
            total=0,  # Will be calculated in __post_init__
        )

        assert score.total == 100

    def test_quality_score_minimum(self):
        """Test minimum quality score."""
        score = QualityScore(
            macro_intelligence=0,
            concentration_risk=0,
            technical_analysis=0,
            risk_management=0,
            actionability=0,
            total=0,  # Will be calculated in __post_init__
        )

        assert score.total == 0


class TestAIQualityValidator:
    """Test suite for AIQualityValidator class."""

    @pytest.fixture
    def sample_excellent_analysis(self):
        """Sample analysis text with excellent quality."""
        return """
        **MACRO FOUNDATION**: The Crypto Fear & Greed Index currently sits at 45/100 showing neutral sentiment.
        Recent institutional flows show $150M outflows from Bitcoin ETFs while Ethereum sees $75M inflows.
        Bitcoin dominance has declined to 58.2%, indicating selective altcoin season rotation.

        **PORTFOLIO RISK ASSESSMENT**: Concentration considerations – BTC allocation at 52.3% is unusually high
        relative to diversification best practices; consider gradual rebalancing using existing sell orders.

        **COMPREHENSIVE TECHNICAL ANALYSIS**: ETH showing support at $3,480 with resistance at $3,650.
        LINK in falling wedge pattern with breakout above $16.20 targeting $30. DOT consolidating near
        $3.55 support with breakout potential above $3.80. ADA oversold at $0.68 with support at $0.66.
        AVAX approaching triangle apex at $18 support. UNI needs validation above $9.50.
        XRP mixed signals with support at $2.76.

        **RISK MANAGEMENT PRIORITIES**: Address BTC overweight position first before new deployment.
        Implement stop-losses below key support levels. Maintain 30% USDT reserves.

        **STRATEGIC OPPORTUNITIES**: Conservative accumulation near technical support levels.
        Entry at ETH $3,480, LINK $15.80, with stops below $3,250 and $15.40 respectively.
        Monitor for DOT breakout above $3.80 for 25% rally potential.
        """

    @pytest.fixture
    def sample_poor_analysis(self):
        """Sample analysis text with poor quality."""
        return """
        The market looks good. Bitcoin is strong and might go up.
        Consider buying some altcoins. Ethereum could be a good choice.
        Maybe look at some other coins too.
        """

    @pytest.fixture
    def sample_portfolio_data(self):
        """Sample portfolio data for validation."""
        return {"balances": {"BTC": {"free": 0.5, "value": 50000}, "ETH": {"free": 10.0, "value": 30000}, "USDT": {"free": 20000, "value": 20000}}}

    def test_validate_analysis_excellent(self, sample_excellent_analysis, sample_portfolio_data):
        """Test validation of excellent analysis."""
        score = AIQualityValidator.validate_analysis(sample_excellent_analysis, sample_portfolio_data)

        # Should score highly across all categories
        assert score.total >= 80
        assert score.macro_intelligence >= 15  # Has Fear & Greed, flows, dominance
        assert score.concentration_risk >= 10  # Mentions concentration/overweight context
        assert score.technical_analysis >= 15  # Covers 7+ altcoins with specific levels
        assert score.risk_management >= 15  # Risk-first approach, stops, reserves
        assert score.actionability >= 10  # Specific entries and guidance

    def test_validate_analysis_poor(self, sample_poor_analysis, sample_portfolio_data):
        """Test validation of poor analysis."""
        score = AIQualityValidator.validate_analysis(sample_poor_analysis, sample_portfolio_data)

        # Should score poorly across all categories
        assert score.total <= 40
        assert score.macro_intelligence <= 5  # No macro indicators
        assert score.concentration_risk <= 5  # No risk assessment
        assert score.technical_analysis <= 10  # Minimal technical content
        assert score.risk_management <= 5  # No risk management
        assert score.actionability <= 5  # No specific guidance

    def test_score_macro_intelligence_complete(self):
        """Test macro intelligence scoring with all indicators."""
        text = """
        Fear and greed index shows 55/100 neutral sentiment.
        Institutional flows indicate $200M ETF outflows.
        Bitcoin dominance declined to 60.5% from 62%.
        Altcoin season index suggests selective rotation.
        """

        score = AIQualityValidator._score_macro_intelligence(text.lower())
        assert score == 20  # Perfect score

    def test_score_macro_intelligence_partial(self):
        """Test macro intelligence scoring with partial indicators."""
        text = "Fear and greed index at 45. Some institutional activity."

        score = AIQualityValidator._score_macro_intelligence(text.lower())
        assert score == 10  # Partial score

    def test_score_concentration_risk_complete(self):
        """Test concentration discussion scoring with full assessment."""
        text = """
        BTC overweight at 52% indicates high single-asset exposure.
        Concentration considerations suggest rebalancing attention.
        """

        score = AIQualityValidator._score_concentration_context(text.lower(), None)
        assert score >= 20

    def test_score_technical_analysis_comprehensive(self):
        """Test technical analysis scoring with comprehensive coverage."""
        analysis = """
        ETH support at $3,480 resistance $3,650. LINK falling wedge $15.40-$16.20.
        DOT consolidating $3.55 breakout $3.80. ADA oversold $0.68 support $0.66.
        AVAX triangle $18 resistance $23. UNI validation $9.50 targets $12.
        XRP support $2.76 resistance $3.14.
        """

        score = AIQualityValidator._score_technical_analysis(analysis.lower(), analysis)
        assert score >= 18  # High score for 7 altcoins + specific levels

    def test_score_risk_management_complete(self):
        """Test risk management scoring with full framework."""
        text = """
        Risk-first priority approach required. Position sizing limits 5% per asset.
        Stop-loss below key support levels. Maintain 30% USDT reserves.
        """

        score = AIQualityValidator._score_risk_management(text.lower())
        assert score == 20  # Perfect score

    def test_score_actionability_complete(self):
        """Test actionability scoring with specific guidance."""
        text = """
        Entry at $3,480 for ETH accumulation. Immediate monitoring required.
        Deploy available USDT with constraints. Follow-up priorities defined.
        """

        score = AIQualityValidator._score_actionability(text.lower(), text)
        assert score == 20  # Perfect score

    def test_get_quality_assessment_excellent(self):
        """Test quality assessment for excellent score."""
        score = QualityScore(20, 20, 20, 20, 15, 0)  # 95 total
        assessment = AIQualityValidator.get_quality_assessment(score)
        assert "EXCELLENT" in assessment

    def test_get_quality_assessment_good(self):
        """Test quality assessment for good score."""
        score = QualityScore(15, 18, 16, 17, 14, 0)  # 80 total
        assessment = AIQualityValidator.get_quality_assessment(score)
        assert "GOOD" in assessment

    def test_get_quality_assessment_poor(self):
        """Test quality assessment for poor score."""
        score = QualityScore(5, 8, 6, 7, 4, 0)  # 30 total
        assessment = AIQualityValidator.get_quality_assessment(score)
        assert "POOR" in assessment

    def test_get_improvement_suggestions_comprehensive(self):
        """Test improvement suggestions for low scores."""
        score = QualityScore(10, 8, 12, 9, 11, 0)  # 50 total, all below 15
        suggestions = AIQualityValidator.get_improvement_suggestions(score)

        assert len(suggestions) == 5  # All categories need improvement
        assert any("macro indicators" in suggestion for suggestion in suggestions)
        assert any("concentration risk" in suggestion for suggestion in suggestions)
        assert any("technical analysis" in suggestion for suggestion in suggestions)
        assert any("risk-first approach" in suggestion for suggestion in suggestions)
        assert any("specific entry levels" in suggestion for suggestion in suggestions)

    def test_get_improvement_suggestions_selective(self):
        """Test improvement suggestions for selective low scores."""
        score = QualityScore(18, 20, 10, 19, 17, 0)  # Only technical analysis low
        suggestions = AIQualityValidator.get_improvement_suggestions(score)

        assert len(suggestions) == 1
        assert "technical analysis" in suggestions[0]

    def test_altcoin_coverage_detection(self):
        """Test detection of required altcoin coverage."""
        text_with_all = "ETH LINK DOT ADA AVAX UNI XRP analysis coverage"
        text_with_few = "ETH BTC analysis only"

        score_all = AIQualityValidator._score_technical_analysis(text_with_all.lower(), text_with_all)
        score_few = AIQualityValidator._score_technical_analysis(text_with_few.lower(), text_with_few)

        assert score_all > score_few  # Should score higher with more coverage

    def test_price_level_detection(self):
        """Test detection of specific price levels."""
        text_with_levels = """
        ETH support $3,480 resistance $3,650. LINK $15.40 target $18.
        DOT 3.55 USDT breakout 3.80 USDT. Multiple price levels provided.
        """
        text_without_levels = "General discussion without specific prices"

        score_with = AIQualityValidator._score_technical_analysis(text_with_levels.lower(), text_with_levels)
        score_without = AIQualityValidator._score_technical_analysis(text_without_levels.lower(), text_without_levels)

        assert score_with > score_without  # Should score higher with specific levels

    def test_risk_keywords_detection(self):
        """Test detection of risk management keywords."""
        validator = AIQualityValidator()

        # Test various risk-related terms
        assert any(keyword in "concentration risk analysis" for keyword in validator.RISK_KEYWORDS)
        assert any(keyword in "portfolio rebalancing needed" for keyword in validator.RISK_KEYWORDS)
        assert any(keyword in "violation of guidelines" for keyword in validator.RISK_KEYWORDS)

    def test_required_altcoins_coverage(self):
        """Test coverage of required altcoins."""
        validator = AIQualityValidator()

        # Verify all required altcoins are defined
        assert "ETH" in validator.REQUIRED_ALTCOINS
        assert "LINK" in validator.REQUIRED_ALTCOINS
        assert "DOT" in validator.REQUIRED_ALTCOINS
        assert "ADA" in validator.REQUIRED_ALTCOINS
        assert "AVAX" in validator.REQUIRED_ALTCOINS
        assert "UNI" in validator.REQUIRED_ALTCOINS
        assert "XRP" in validator.REQUIRED_ALTCOINS
        assert len(validator.REQUIRED_ALTCOINS) == 7

    def test_edge_case_empty_analysis(self):
        """Test validation of empty analysis."""
        score = AIQualityValidator.validate_analysis("", None)

        assert score.total == 0
        assert all(
            category_score == 0
            for category_score in [score.macro_intelligence, score.concentration_risk, score.technical_analysis, score.risk_management, score.actionability]
        )

    def test_edge_case_very_long_analysis(self):
        """Test validation of very long analysis."""
        # Create a very long analysis with repeated good content
        base_analysis = """
        Fear greed index 55/100. Institutional flows $200M. Bitcoin dominance 60%.
        Altcoin season selective. BTC overweight 52% indicates high concentration.
        Consider rebalancing. ETH $3,480 LINK $15.40 DOT $3.55
        ADA $0.66 AVAX $18 UNI $9.30 XRP $2.76. Risk first priority approach.
        Stop loss reserves. Entry timing deploy constraints
        monitor follow priorities.
        """
        long_analysis = base_analysis * 10  # Repeat 10 times

        score = AIQualityValidator.validate_analysis(long_analysis, None)

        # Should still score well despite length
        assert score.total >= 80
        assert score.macro_intelligence >= 15
        assert score.technical_analysis >= 15
