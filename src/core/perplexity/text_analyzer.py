"""Text analysis and consistency scoring for Perplexity responses."""

from typing import Any


class TextAnalyzer:
    """Handles text analysis, consistency scoring, and discrepancy identification."""

    def calculate_consistency_score(self, recs_1: list[dict[str, Any]] | None, recs_2: list[dict[str, Any]] | None) -> float:
        """Calculate consistency score between two sets of recommendations."""
        if recs_1 is None or recs_2 is None:
            return 0.0 if (recs_1 is None) != (recs_2 is None) else 50.0

        if len(recs_1) == 0 and len(recs_2) == 0:
            return 100.0

        # Compare symbols, actions, and price ranges
        total_score = 0.0
        matches = 0

        for rec1 in recs_1:
            symbol1 = rec1.get("symbol", "")
            action1 = rec1.get("action", "")
            price1 = rec1.get("price", 0) or rec1.get("expected_current_price", 0)

            best_match_score = 0.0

            for rec2 in recs_2:
                symbol2 = rec2.get("symbol", "")
                action2 = rec2.get("action", "")
                price2 = rec2.get("price", 0) or rec2.get("expected_current_price", 0)

                # Symbol match (40 points)
                symbol_score = 40 if symbol1 == symbol2 else 0

                # Action match (40 points)
                action_score = 40 if action1 == action2 else 0

                # Price similarity (20 points)
                price_score = 0
                if price1 and price2:
                    try:
                        # Safe numeric conversion for price comparison
                        float_price1 = float(price1) if isinstance(price1, int | float | str) else 0
                        float_price2 = float(price2) if isinstance(price2, int | float | str) else 0
                        if float_price1 > 0 and float_price2 > 0:
                            price_diff_pct = abs(float_price1 - float_price2) / max(float_price1, float_price2) * 100
                        else:
                            price_diff_pct = 100  # Treat as no match if conversion fails
                    except (ValueError, TypeError):
                        price_diff_pct = 100  # Treat as no match if conversion fails
                    if price_diff_pct < 5:
                        price_score = 20
                    elif price_diff_pct < 10:
                        price_score = 15
                    elif price_diff_pct < 20:
                        price_score = 10

                match_score = symbol_score + action_score + price_score
                best_match_score = max(best_match_score, match_score)

            total_score += best_match_score
            matches += 1

        return total_score / matches if matches > 0 else 0.0

    def calculate_text_consistency_score(self, analysis_1: str, analysis_2: str) -> float:
        """
        Calculate consistency score between two text analyses based on content similarity.

        Args:
            analysis_1: First analysis text
            analysis_2: Second analysis text

        Returns:
            Consistency score between 0-100
        """
        if not analysis_1 or not analysis_2:
            return 0.0

        # Special case: identical text should return perfect score
        if analysis_1.strip() == analysis_2.strip():
            return 100.0

        # Convert to lowercase for comparison
        text_1 = analysis_1.lower()
        text_2 = analysis_2.lower()

        # Check for common key terms and sentiment indicators
        bullish_terms = ["bullish", "buy", "accumulate", "opportunity", "positive", "strong", "upward", "rally"]
        bearish_terms = ["bearish", "sell", "reduce", "risk", "negative", "weak", "downward", "decline"]
        neutral_terms = ["hold", "wait", "monitor", "sideways", "consolidation", "neutral"]

        # Count sentiment indicators in both analyses
        sentiment_1: dict[str, int] = self._get_sentiment_scores(text_1, bullish_terms, bearish_terms, neutral_terms)
        sentiment_2: dict[str, int] = self._get_sentiment_scores(text_2, bullish_terms, bearish_terms, neutral_terms)

        # Calculate sentiment alignment (higher = more consistent)
        sentiment_consistency = self._calculate_sentiment_alignment(sentiment_1, sentiment_2)

        # Check for common assets mentioned
        assets = ["btc", "bitcoin", "eth", "ethereum", "sol", "solana", "usdt"]
        asset_mentions_1 = sum(1 for asset in assets if asset in text_1)
        asset_mentions_2 = sum(1 for asset in assets if asset in text_2)

        # Asset mention consistency
        if asset_mentions_1 + asset_mentions_2 > 0:
            asset_consistency = min(asset_mentions_1, asset_mentions_2) / max(asset_mentions_1, asset_mentions_2) * 100
        else:
            asset_consistency = 50.0  # neutral if no assets mentioned

        # Check for similar strategic themes
        strategy_terms = ["accumulation", "protection", "rotation", "institutional", "sentiment", "timing"]
        strategy_overlap = sum(1 for term in strategy_terms if term in text_1 and term in text_2)
        strategy_consistency = (strategy_overlap / len(strategy_terms)) * 100

        # Weighted average of different consistency factors
        final_score = sentiment_consistency * 0.5 + asset_consistency * 0.3 + strategy_consistency * 0.2

        return min(100.0, max(0.0, final_score))

    def _get_sentiment_scores(self, text: str, bullish_terms: list[str], bearish_terms: list[str], neutral_terms: list[str]) -> dict[str, int]:
        """Get sentiment scores for a text."""
        return {
            "bullish": sum(1 for term in bullish_terms if term in text),
            "bearish": sum(1 for term in bearish_terms if term in text),
            "neutral": sum(1 for term in neutral_terms if term in text),
        }

    def _calculate_sentiment_alignment(self, sentiment_1: dict[str, int], sentiment_2: dict[str, int]) -> float:
        """Calculate alignment between two sentiment scores."""
        # Determine dominant sentiment for each analysis
        dom_1 = max(sentiment_1, key=lambda x: sentiment_1[x])
        dom_2 = max(sentiment_2, key=lambda x: sentiment_2[x])

        # If dominant sentiments match, calculate degree of alignment
        if dom_1 == dom_2:
            # Both have same dominant sentiment - high consistency
            return 80.0 + min(20.0, abs(sentiment_1[dom_1] - sentiment_2[dom_2]) * 2)
        else:
            # Different dominant sentiments - lower consistency
            total_1 = sum(sentiment_1.values())
            total_2 = sum(sentiment_2.values())

            if total_1 == 0 or total_2 == 0:
                return 50.0  # neutral if no sentiment detected

            # Calculate how strong the disagreement is
            strength_1 = sentiment_1[dom_1] / total_1 if total_1 > 0 else 0
            strength_2 = sentiment_2[dom_2] / total_2 if total_2 > 0 else 0

            # Weaker disagreement = higher consistency
            disagreement_strength = (strength_1 + strength_2) / 2
            return max(20.0, 60.0 - (disagreement_strength * 40))

    def identify_text_discrepancies(self, analysis_1: str, analysis_2: str) -> list[str]:
        """
        Identify key discrepancies between two text analyses.

        Args:
            analysis_1: First analysis text
            analysis_2: Second analysis text

        Returns:
            List of identified discrepancies
        """
        discrepancies: list[str] = []

        text_1 = analysis_1.lower()
        text_2 = analysis_2.lower()

        # Check for opposing sentiment on major assets
        assets = [("btc", "bitcoin"), ("eth", "ethereum"), ("sol", "solana")]

        for asset_short, asset_long in assets:
            if asset_short in text_1 or asset_long in text_1 or asset_short in text_2 or asset_long in text_2:
                sentiment_1 = self._get_asset_sentiment(text_1, asset_short, asset_long)
                sentiment_2 = self._get_asset_sentiment(text_2, asset_short, asset_long)

                if sentiment_1 and sentiment_2 and sentiment_1 != sentiment_2:
                    discrepancies.append(f"{asset_short.upper()} sentiment: Analysis 1 = {sentiment_1}, Analysis 2 = {sentiment_2}")

        # Check for opposing market regime assessments
        bull_indicators_1 = any(term in text_1 for term in ["bull market", "bullish trend", "upward momentum"])
        bear_indicators_1 = any(term in text_1 for term in ["bear market", "bearish trend", "downward momentum"])

        bull_indicators_2 = any(term in text_2 for term in ["bull market", "bullish trend", "upward momentum"])
        bear_indicators_2 = any(term in text_2 for term in ["bear market", "bearish trend", "downward momentum"])

        if (bull_indicators_1 and bear_indicators_2) or (bear_indicators_1 and bull_indicators_2):
            discrepancies.append("Market regime assessment: Conflicting bull/bear market identification")

        # Check for conflicting risk assessments
        high_risk_1 = any(term in text_1 for term in ["high risk", "risky environment", "caution"])
        low_risk_1 = any(term in text_1 for term in ["low risk", "safe environment", "opportunity"])

        high_risk_2 = any(term in text_2 for term in ["high risk", "risky environment", "caution"])
        low_risk_2 = any(term in text_2 for term in ["low risk", "safe environment", "opportunity"])

        if (high_risk_1 and low_risk_2) or (low_risk_1 and high_risk_2):
            discrepancies.append("Risk assessment: Conflicting risk environment evaluation")

        # Check for conflicting price direction predictions
        up_indicators_1 = any(term in text_1 for term in ["go up", "will rise", "increase", "pump", "moon"])
        down_indicators_1 = any(term in text_1 for term in ["drop", "will fall", "decrease", "dump", "crash"])

        up_indicators_2 = any(term in text_2 for term in ["go up", "will rise", "increase", "pump", "moon"])
        down_indicators_2 = any(term in text_2 for term in ["drop", "will fall", "decrease", "dump", "crash"])

        if (up_indicators_1 and down_indicators_2) or (down_indicators_1 and up_indicators_2):
            discrepancies.append("Price direction: Conflicting up/down price predictions")

        return discrepancies

    def _get_asset_sentiment(self, text: str, asset_short: str, asset_long: str) -> str | None:
        """Get sentiment for a specific asset from text."""
        words = text.split()
        sentiment_scores = {"bullish": 0.0, "bearish": 0.0, "neutral": 0.0}

        # Find asset mentions and analyze sentiment with directional and proximity weighting
        for i, word in enumerate(words):
            if asset_short in word or asset_long in word:
                # Check words after the asset mention (more likely to describe it)
                after_start = i + 1
                after_end = min(len(words), i + 6)
                after_context = words[after_start:after_end]

                # Check words before the asset mention (less weight)
                before_start = max(0, i - 3)
                before_end = i
                before_context = words[before_start:before_end]

                # Score sentiment after asset mention (higher weight)
                for j, context_word in enumerate(after_context):
                    proximity_weight = 1.0 / (j + 1)  # Closer after = higher weight
                    context_lower = context_word.lower().strip(".,!?:;")

                    if any(term in context_lower for term in ["buy", "accumulate", "bullish", "opportunity"]):
                        sentiment_scores["bullish"] += proximity_weight
                    elif any(term in context_lower for term in ["sell", "sold", "reduce", "bearish", "risk"]):
                        sentiment_scores["bearish"] += proximity_weight
                    elif any(term in context_lower for term in ["hold", "neutral", "wait"]):
                        sentiment_scores["neutral"] += proximity_weight

                # Score sentiment before asset mention (lower weight)
                for j, context_word in enumerate(reversed(before_context)):
                    proximity_weight = 0.3 / (j + 1)  # Lower weight for words before
                    context_lower = context_word.lower().strip(".,!?:;")

                    if any(term in context_lower for term in ["buy", "accumulate", "bullish", "opportunity"]):
                        sentiment_scores["bullish"] += proximity_weight
                    elif any(term in context_lower for term in ["sell", "sold", "reduce", "bearish", "risk"]):
                        sentiment_scores["bearish"] += proximity_weight
                    elif any(term in context_lower for term in ["hold", "neutral", "wait"]):
                        sentiment_scores["neutral"] += proximity_weight

        # Return sentiment with highest score, or None if no sentiment found
        if max(sentiment_scores.values()) == 0:
            return None

        return max(sentiment_scores.items(), key=lambda x: x[1])[0]

    def identify_three_way_discrepancies(self, analysis_institutional: str, analysis_sentiment: str, analysis_synthesis: str) -> list[str]:
        """
        Identify key discrepancies across three analyses: institutional, sentiment, and synthesis.

        Args:
            analysis_institutional: Institutional analysis text
            analysis_sentiment: Sentiment analysis text
            analysis_synthesis: Synthesis analysis text

        Returns:
            List of identified discrepancies across all three analyses
        """
        discrepancies: list[str] = []

        text_inst = analysis_institutional.lower()
        text_sent = analysis_sentiment.lower()
        text_synth = analysis_synthesis.lower()

        # Check for opposing sentiment on major assets across all three analyses
        assets = [("btc", "bitcoin"), ("eth", "ethereum"), ("sol", "solana")]

        for asset_short, asset_long in assets:
            if any(asset_short in text or asset_long in text for text in [text_inst, text_sent, text_synth]):
                sentiment_inst = self._get_asset_sentiment(text_inst, asset_short, asset_long)
                sentiment_sent = self._get_asset_sentiment(text_sent, asset_short, asset_long)
                sentiment_synth = self._get_asset_sentiment(text_synth, asset_short, asset_long)

                sentiments = [sentiment_inst, sentiment_sent, sentiment_synth]
                valid_sentiments = [s for s in sentiments if s is not None]

                if len(set(valid_sentiments)) > 1:  # Multiple different sentiments
                    labels = ["Institutional", "Sentiment", "Synthesis"]
                    sentiment_summary: list[str] = []
                    for i, sentiment in enumerate(sentiments):
                        if sentiment:
                            sentiment_summary.append(f"{labels[i]}={sentiment}")
                    if sentiment_summary:
                        discrepancies.append(f"{asset_short.upper()} sentiment divergence: {', '.join(sentiment_summary)}")

        # Check for conflicting market regime assessments
        bull_indicators = ["bull market", "bullish trend", "upward momentum", "risk-on"]
        bear_indicators = ["bear market", "bearish trend", "downward momentum", "risk-off"]

        regime_assessments: list[tuple[str, str]] = []
        for _i, (text, label) in enumerate([(text_inst, "Institutional"), (text_sent, "Sentiment"), (text_synth, "Synthesis")]):
            if any(term in text for term in bull_indicators):
                regime_assessments.append((label, "bullish"))
            elif any(term in text for term in bear_indicators):
                regime_assessments.append((label, "bearish"))
            else:
                regime_assessments.append((label, "neutral"))

        # Check for regime conflicts
        regimes = {regime for _, regime in regime_assessments}
        if len(regimes) > 1 and "neutral" not in regimes:  # Conflicting non-neutral regimes
            regime_summary = [f"{label}={regime}" for label, regime in regime_assessments]
            discrepancies.append(f"Market regime conflict: {', '.join(regime_summary)}")

        # Check for conflicting risk assessments
        risk_assessments: list[tuple[str, str]] = []
        high_risk_terms = ["high risk", "risky environment", "caution", "defensive"]
        low_risk_terms = ["low risk", "safe environment", "opportunity", "aggressive"]

        for _i, (text, label) in enumerate([(text_inst, "Institutional"), (text_sent, "Sentiment"), (text_synth, "Synthesis")]):
            if any(term in text for term in high_risk_terms):
                risk_assessments.append((label, "high"))
            elif any(term in text for term in low_risk_terms):
                risk_assessments.append((label, "low"))
            else:
                risk_assessments.append((label, "moderate"))

        # Check for risk conflicts
        risks = {risk for _, risk in risk_assessments}
        if "high" in risks and "low" in risks:  # Direct conflict
            risk_summary = [f"{label}={risk}" for label, risk in risk_assessments]
            discrepancies.append(f"Risk assessment conflict: {', '.join(risk_summary)}")

        # Check if synthesis successfully resolves conflicts or introduces new ones
        inst_sent_conflicts = len(self.identify_text_discrepancies(analysis_institutional, analysis_sentiment))
        if inst_sent_conflicts > 0:
            synth_inst_conflicts = len(self.identify_text_discrepancies(analysis_synthesis, analysis_institutional))
            synth_sent_conflicts = len(self.identify_text_discrepancies(analysis_synthesis, analysis_sentiment))

            if synth_inst_conflicts + synth_sent_conflicts > inst_sent_conflicts:
                discrepancies.append("Synthesis analysis introduced new conflicts rather than resolving existing ones")
            elif synth_inst_conflicts + synth_sent_conflicts == 0:
                discrepancies.append("Synthesis successfully resolved all institutional-sentiment conflicts")

        return discrepancies
