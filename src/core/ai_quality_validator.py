"""AI Analysis Quality Validator.

This module validates AI analysis responses against enhanced quality criteria
derived from meta-learning analysis to ensure superior strategic insights.
"""

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class QualityScore:
    """Quality score breakdown for AI analysis."""

    macro_intelligence: int  # 0-20 points
    concentration_risk: int  # 0-20 points
    technical_analysis: int  # 0-20 points
    risk_management: int  # 0-20 points
    actionability: int  # 0-20 points
    total: int  # 0-100 total

    def __post_init__(self) -> None:
        """Calculate total score."""
        self.total = self.macro_intelligence + self.concentration_risk + self.technical_analysis + self.risk_management + self.actionability


class AIQualityValidator:
    """Validates AI analysis quality against enhanced criteria."""

    # Required macro indicators
    REQUIRED_MACRO_INDICATORS = ["fear", "greed", "index", "institutional", "flow", "etf", "bitcoin", "dominance", "altcoin", "season"]

    # Required technical coverage (minimum 7)
    REQUIRED_ALTCOINS = ["ETH", "LINK", "DOT", "ADA", "AVAX", "UNI", "XRP"]

    # Risk management keywords (excluding those with dedicated checks)
    RISK_KEYWORDS = ["concentration", "violation", "rebalanc"]

    @classmethod
    def validate_analysis(cls, analysis_text: str, portfolio_data: dict[str, Any] | None = None) -> QualityScore:
        """Validate AI analysis against enhanced quality criteria.

        Args:
            analysis_text: AI analysis response to validate
            portfolio_data: Optional portfolio data for context validation

        Returns:
            QualityScore with detailed breakdown
        """
        # Normalize text for analysis
        text_lower = analysis_text.lower()

        # Score each category
        macro_score = cls._score_macro_intelligence(text_lower)
        concentration_score = cls._score_concentration_context(text_lower, portfolio_data)
        technical_score = cls._score_technical_analysis(text_lower, analysis_text)
        risk_score = cls._score_risk_management(text_lower)
        actionability_score = cls._score_actionability(text_lower, analysis_text)

        base_score = QualityScore(
            macro_intelligence=macro_score,
            concentration_risk=concentration_score,
            technical_analysis=technical_score,
            risk_management=risk_score,
            actionability=actionability_score,
            total=0,  # Calculated in __post_init__
        )

        # Gap Checklist overlay: base 100 − 5 per missing criteria
        overlay_total = 100
        # Market timing covered? infer via macro score presence
        if macro_score == 0:
            overlay_total -= 5
        # Actionable levels & stops? require actionability and presence of numeric levels
        has_levels = technical_score > 0
        if actionability_score == 0 or not has_levels:
            overlay_total -= 5
        # Risk assessment explicit?
        if risk_score == 0:
            overlay_total -= 5
        # Protection addressed? simple keyword heuristic
        if not ("stop" in text_lower or "protect" in text_lower or "oco" in text_lower):
            overlay_total -= 5

        # Final total is the minimum of category total and overlay
        base_score.total = min(base_score.total, overlay_total)
        return base_score

    @classmethod
    def _score_macro_intelligence(cls, text_lower: str) -> int:
        """Score macro intelligence inclusion (0-20 points)."""
        score = 0

        # Check for Fear & Greed Index (5 points)
        if any(indicator in text_lower for indicator in ["fear", "greed", "index"]):
            score += 5

        # Check for institutional flows (5 points)
        if any(indicator in text_lower for indicator in ["institutional", "flow", "etf"]):
            score += 5

        # Check for Bitcoin dominance (5 points)
        if "bitcoin" in text_lower and "dominance" in text_lower:
            score += 5

        # Check for altcoin season metrics (5 points)
        if "altcoin" in text_lower and ("season" in text_lower or "rotation" in text_lower):
            score += 5

        return score

    @classmethod
    def _score_concentration_context(cls, text_lower: str, portfolio_data: dict[str, Any] | None) -> int:
        """Score whether concentration considerations are addressed (0-20 points)."""
        score = 0

        # Check for concentration discussion (10 points)
        if any(keyword in text_lower for keyword in cls.RISK_KEYWORDS):
            score += 10

        # Check for overweight/large single-asset exposure identification (up to 10 points)
        if "overweight" in text_lower or "rebalanc" in text_lower:
            score += 10

        return score

    @classmethod
    def _score_technical_analysis(cls, text_lower: str, full_text: str) -> int:
        """Score technical analysis comprehensiveness (0-20 points)."""
        score = 0

        # Count covered altcoins (up to 14 points - 2 per required altcoin)
        covered_count = 0
        for altcoin in cls.REQUIRED_ALTCOINS:
            if altcoin.lower() in text_lower:
                covered_count += 1
                score += 2

        # Bonus for covering all 7+ (6 points)
        if covered_count >= 7:
            score += 6

        # Check for specific price levels (up to 6 points)
        # Deduplicate across patterns to avoid double-counting the same level
        price_patterns = [
            r"\$[\d,]+\.?\d*",  # Dollar amounts
            r"[\d,]+\.?\d*\s*usdt",  # USDT amounts
            r"support[^\n\r]*?[\d,]+\.?\d*",  # Support levels with numeric
            r"resistance[^\n\r]*?[\d,]+\.?\d*",  # Resistance levels with numeric
        ]

        def _normalize_numeric(token: str) -> str:
            # Keep digits and decimal point; drop other chars (like $, commas, words)
            cleaned = re.sub(r"[^0-9\.]", "", token)
            # Collapse multiple dots if any (defensive)
            cleaned = re.sub(r"\.+", ".", cleaned)
            return cleaned.strip(".")

        level_tokens: set[str] = set()
        for pattern in price_patterns:
            for match in re.findall(pattern, text_lower):
                # Extract numeric parts from the match and add them as tokens
                numerics = re.findall(r"[\d,]+\.?\d*", match)
                if numerics:
                    for num in numerics:
                        norm = _normalize_numeric(num)
                        if norm:
                            level_tokens.add(norm)
                else:
                    norm = _normalize_numeric(match)
                    if norm:
                        level_tokens.add(norm)

        level_count = len(level_tokens)

        # Award points based on unique specific levels provided
        if level_count >= 10:
            score += 6
        elif level_count >= 5:
            score += 3
        elif level_count >= 2:
            score += 1

        return min(score, 20)  # Cap at 20 points

    @classmethod
    def _score_risk_management(cls, text_lower: str) -> int:
        """Score risk management focus (0-20 points)."""
        score = 0

        # Check for risk-first approach (5 points)
        if "risk" in text_lower and ("first" in text_lower or "priority" in text_lower):
            score += 5

        # Check for position sizing limits (5 points)
        if any(term in text_lower for term in ["position", "sizing", "allocation", "limit"]):
            score += 5

        # Check for stop-loss mentions (5 points)
        if "stop" in text_lower and ("loss" in text_lower or "below" in text_lower):
            score += 5

        # Check for reserve requirements (5 points)
        if any(term in text_lower for term in ["reserve", "cash", "usdt", "maintain"]):
            score += 5

        return score

    @classmethod
    def _score_actionability(cls, text_lower: str, full_text: str) -> int:
        """Score actionability and specificity (0-20 points)."""
        score = 0

        # Check for specific entry levels (5 points)
        if any(term in text_lower for term in ["entry", "buy", "accumulate"]) and "$" in full_text:
            score += 5

        # Check for timeline considerations (5 points)
        if any(term in text_lower for term in ["timing", "immediate", "monitor", "watch"]):
            score += 5

        # Check for deployment constraints (5 points)
        if any(term in text_lower for term in ["deploy", "available", "constraint", "limit"]):
            score += 5

        # Check for follow-up priorities (5 points)
        if any(term in text_lower for term in ["monitor", "follow", "priority", "next"]):
            score += 5

        return score

    @classmethod
    def get_quality_assessment(cls, score: QualityScore) -> str:
        """Get qualitative assessment of analysis quality.

        Args:
            score: QualityScore object

        Returns:
            Quality assessment string
        """
        if score.total >= 90:
            return "EXCELLENT - Superior analysis meeting all enhanced criteria"
        elif score.total >= 80:
            return "GOOD - Strong analysis with minor enhancement opportunities"
        elif score.total >= 70:
            return "ADEQUATE - Analysis meets basic requirements"
        elif score.total >= 60:
            return "NEEDS IMPROVEMENT - Missing key quality elements"
        else:
            return "POOR - Significant quality issues, regeneration recommended"

    @classmethod
    def get_improvement_suggestions(cls, score: QualityScore) -> list[str]:
        """Get specific improvement suggestions based on score breakdown.

        Args:
            score: QualityScore object

        Returns:
            List of improvement suggestions
        """
        suggestions = []

        if score.macro_intelligence < 15:
            suggestions.append("Include objective macro indicators: Fear & Greed Index, institutional flows, Bitcoin dominance")

        if score.concentration_risk < 15:
            suggestions.append("Explicitly assess portfolio concentration risk and rebalancing considerations")

        if score.technical_analysis < 15:
            suggestions.append("Provide comprehensive technical analysis for 7+ major altcoins with specific price levels")

        if score.risk_management < 15:
            suggestions.append("Emphasize risk-first approach with position sizing limits and protection priorities")

        if score.actionability < 15:
            suggestions.append("Include specific entry levels, timing considerations, and deployment constraints")

        return suggestions
