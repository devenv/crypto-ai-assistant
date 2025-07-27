"""Quality validation for Perplexity AI responses."""

from typing import Any


class QualityValidator:
    """Validates the quality of Perplexity AI responses for strategic analysis."""

    def validate_perplexity_response_quality(self, analysis_text: str, recommendations: list[dict[str, Any]] | None = None) -> tuple[bool, str]:
        """
        Validate that Perplexity response meets minimum quality requirements for strategic analysis.

        Args:
            analysis_text: The raw analysis text from Perplexity
            recommendations: Legacy parameter, ignored in new text-based approach

        Returns:
            Tuple of (is_valid, failure_reason)
        """
        # Check minimum analysis length for comprehensive strategic analysis
        if not analysis_text or len(analysis_text) < 500:
            return False, f"Analysis text too short ({len(analysis_text) if analysis_text else 0} < 500 characters)"

        # Check for required strategic analysis sections
        required_sections = [
            ("executive summary", "EXECUTIVE SUMMARY"),
            ("market sentiment", "MARKET SENTIMENT"),
            ("market regime", "MARKET REGIME"),
            ("strategic", "STRATEGIC"),
            ("timing", "TIMING"),
            ("risk", "RISK"),
        ]

        found_sections: list[str] = []
        analysis_lower = analysis_text.lower()

        for section_keyword, section_name in required_sections:
            if section_keyword in analysis_lower:
                found_sections.append(section_name)

        if len(found_sections) < 3:  # Relaxed from 4 to 3
            missing = [name for _, name in required_sections if name not in found_sections]
            return False, f"Missing key strategic sections. Found {len(found_sections)}/6. Missing: {', '.join(missing[:3])}"

        # Check for market data integration (should reference current data)
        market_indicators = ["rsi", "price", "volume", "sentiment", "institutional", "whale", "market", "crypto", "bitcoin", "ethereum"]
        market_references = sum(1 for indicator in market_indicators if indicator in analysis_lower)

        if market_references < 2:  # Relaxed from 3 to 2
            return False, f"Insufficient market data integration. Found {market_references}/10 market indicators"

        # Check for actionable insights (should provide strategic guidance)
        actionable_keywords = [
            "consider",
            "recommend",
            "suggest",
            "opportunity",
            "risk",
            "timing",
            "position",
            "strategy",
            "focus",
            "monitor",
            "should",
            "could",
            "would",
        ]

        actionable_count = sum(1 for keyword in actionable_keywords if keyword in analysis_lower)
        if actionable_count < 2:  # Relaxed from 3 to 2
            return False, f"Insufficient actionable insights. Found {actionable_count}/12 actionable terms"

        # Enhanced validation for synthesis analysis (meta-analysis focus)
        synthesis_indicators = [
            "analysis",
            "compare",
            "contrast",
            "synthesis",
            "meta",
            "critique",
            "perspective",
            "institutional",
            "sentiment",
            "consistency",
            "conflict",
        ]
        synthesis_count = sum(1 for indicator in synthesis_indicators if indicator in analysis_lower)

        # More flexible source validation for two-stage system
        if synthesis_count >= 3:  # This appears to be synthesis analysis (relaxed from 5 to 3)
            # For synthesis: look for strategic critique and enhancement indicators
            critique_indicators = [
                "analysis",
                "assessment",
                "evaluation",
                "review",
                "critique",
                "strategic",
                "recommendations",
                "insights",
                "perspective",
                "approach",
                "considerations",
                "priorities",
                "guidance",
                "strategy",
                "positioning",
                "timing",
                "risk",
            ]
            critique_count = sum(1 for indicator in critique_indicators if indicator in analysis_lower)

            if critique_count < 3:  # Relaxed requirement for strategic content
                return False, f"Insufficient strategic analysis content for synthesis. Found {critique_count}/17 strategic indicators"
        else:
            # For direct analysis: more flexible evidence of market research or strategic thinking
            citation_indicators = [
                "source",
                "according",
                "data shows",
                "reports",
                "analysis indicates",
                "current",
                "recent",
                "today",
                "this week",
                "market data",
                "price action",
                "institutional",
                "whale",
                "flow",
                "trend",
                "momentum",
                "signals",
            ]
            citation_count = sum(1 for indicator in citation_indicators if indicator in analysis_lower)

            if citation_count < 2:  # Relaxed requirement and more flexible indicators
                return False, f"Insufficient market research evidence. Found {citation_count}/16 research indicators"

        return (
            True,
            f"Strategic analysis meets quality requirements ({len(analysis_text)} chars, {len(found_sections)} sections, {market_references} market refs)",
        )
