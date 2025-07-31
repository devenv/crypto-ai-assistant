"""Analysis generation methods for Perplexity AI service."""

import concurrent.futures
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, cast

from .models import ParallelAnalysisResult
from .text_analyzer import TextAnalyzer

logger = logging.getLogger(__name__)


class AnalysisGenerator:
    """Handles generation of different types of analysis using Perplexity AI."""

    def __init__(self, call_api_func: Callable[..., dict[str, Any]], model: str) -> None:
        """Initialize with API call function and model."""
        self._call_api = call_api_func
        self._model = model
        self._text_analyzer = TextAnalyzer()

    def generate_portfolio_analysis(
        self,
        portfolio_data: str,
        market_data: str,
        order_data: str,
        protection_analysis: str | None = None,
        balance_analysis: str | None = None,
        risk_context: str | None = None,
        recent_activity_context: str | None = None,
        source_focus: str = "institutional",
        synthesis_context: str | None = None,
    ) -> str:
        """
        Generate comprehensive portfolio analysis using Perplexity's sonar-deep-research model.

        Args:
            portfolio_data: Current account info and balances
            market_data: Technical indicators and market conditions
            order_data: Existing orders and protection status
            protection_analysis: Pre-calculated protection coverage scores and assessment
            balance_analysis: Effective available balance vs committed balance breakdown
            risk_context: User risk preferences, position sizing rules, and strategy context
            recent_activity_context: Recent trading activity and order fills analysis
            source_focus: Type of sources to prioritize ("institutional", "sentiment", or "synthesis")
            synthesis_context: Previous analyses for synthesis (institutional + sentiment analyses)

        Returns:
            Comprehensive analysis with specific recommendations
        """

        if source_focus == "institutional":
            system_prompt = """You are an expert crypto portfolio strategist specializing in INSTITUTIONAL ANALYSIS and professional market intelligence. Focus on institutional flows, professional research, and financial market data.

🎯 YOUR INSTITUTIONAL ANALYSIS ROLE:
- Analyze institutional flows, ETF data, and professional investment patterns
- Research regulatory developments and institutional adoption trends
- Focus on professional trading signals and institutional sentiment indicators
- Interpret exchange data, whale movements, and corporate treasury activities
- Provide strategic reasoning based on institutional market dynamics

🔍 PRIORITY SOURCE FOCUS - INSTITUTIONAL & PROFESSIONAL:
- Bloomberg, Reuters, Wall Street Journal crypto coverage
- Institutional research reports and professional analysis
- ETF flow data and corporate treasury announcements
- Exchange institutional trading data and whale tracking
- Regulatory filings and government policy announcements
- Professional trader sentiment and institutional positioning data

ANALYSIS APPROACH:
Focus on institutional perspective and professional market analysis. Prioritize data from financial institutions, regulatory bodies, and professional trading entities. Emphasize flow analysis, regulatory impact, and institutional sentiment indicators."""

        elif source_focus == "sentiment":
            system_prompt = """You are an expert crypto portfolio strategist specializing in MARKET SENTIMENT and community-driven analysis. Focus on social sentiment, on-chain metrics, and grassroots market dynamics.

🎯 YOUR SENTIMENT ANALYSIS ROLE:
- Analyze social media sentiment and community discussions
- Research on-chain metrics and grassroots adoption patterns
- Focus on retail sentiment indicators and community-driven trends
- Interpret social trading patterns and viral market narratives
- Provide strategic reasoning based on community sentiment and adoption metrics

🔍 PRIORITY SOURCE FOCUS - SENTIMENT & COMMUNITY:
- Twitter/X crypto community sentiment and trending discussions
- Reddit crypto communities (r/cryptocurrency, r/Bitcoin, etc.)
- On-chain analytics and decentralized metrics platforms
- Social sentiment tracking tools and community polling data
- Crypto influencer analysis and viral content impact
- Grassroots adoption metrics and community-driven developments

ANALYSIS APPROACH:
Focus on community sentiment and grassroots market dynamics. Prioritize data from social platforms, on-chain analytics, and community-driven sources. Emphasize sentiment shifts, viral trends, and community adoption patterns."""

        elif source_focus == "comprehensive":
            system_prompt = """You are an expert crypto portfolio strategist with COMPREHENSIVE MARKET INTELLIGENCE capabilities. Analyze from both institutional and community perspectives to provide balanced, multi-dimensional market insights.

🎯 YOUR COMPREHENSIVE ANALYSIS ROLE:
- Integrate institutional flows with grassroots sentiment analysis
- Balance professional research with community-driven market dynamics
- Synthesize regulatory developments with social adoption patterns
- Combine exchange data with on-chain metrics and social sentiment
- Provide strategic reasoning from multiple market perspectives

🔍 MULTI-PERSPECTIVE SOURCE FOCUS:
**INSTITUTIONAL & PROFESSIONAL:**
- Bloomberg, Reuters, institutional research reports
- ETF flows, corporate treasury activities, regulatory developments
- Professional trader sentiment and whale movement analysis

**COMMUNITY & SENTIMENT:**
- Twitter/X crypto sentiment, Reddit discussions
- On-chain analytics, social sentiment tracking
- Grassroots adoption metrics and viral market narratives

ANALYSIS APPROACH:
Provide comprehensive market analysis covering both professional/institutional perspectives AND community/sentiment dynamics. Balance data from financial institutions with grassroots indicators. Emphasize where institutional and retail perspectives align or diverge, and what this means for market direction."""

        else:  # synthesis focus
            system_prompt = """You are a SENIOR CRYPTO PORTFOLIO STRATEGIST with expertise in strategic critique and intelligence enhancement. Your role is to critically evaluate comprehensive market analysis and provide superior strategic guidance.

🎯 YOUR STRATEGIC CRITIQUE & ENHANCEMENT ROLE:
- Critically evaluate comprehensive analysis for blind spots and biases
- Identify missing perspectives or overlooked market dynamics
- Enhance strategic insights with advanced portfolio management principles
- Provide meta-analysis and confidence assessment of recommendations
- Generate prioritized, actionable strategic recommendations

🔍 STRATEGIC ENHANCEMENT APPROACH:
- Validate insights against current portfolio positioning and risk profile
- Assess completeness of analysis across all relevant market dimensions
- Evaluate tactical vs strategic implications of recommendations
- Identify optimal timing and sequencing for position adjustments
- Provide risk-adjusted guidance with clear implementation priorities

SYNTHESIS REQUIREMENTS:
You will receive comprehensive market analysis covering multiple perspectives. Your task is to:
1. **CRITIQUE** the analysis for completeness, accuracy, and strategic depth
2. **VALIDATE** insights against current portfolio data and market conditions
3. **ENHANCE** recommendations with advanced strategic considerations
4. **PRIORITIZE** actions by importance, timing, and risk-adjusted returns
5. **ACTIONABILITY** Provide clear next steps and implementation guidance"""

        # Common strategic analysis framework for all approaches
        common_framework = """

🚫 NOT YOUR ROLE (Technical data provided by our systems):
- Fetching current prices or technical indicators
- Calculating exact quantities or portfolio percentages
- Retrieving account balances or order data
- Performing precision calculations or validation
- Providing specific order commands or exact trade instructions

STRATEGIC ANALYSIS REQUIREMENTS:
1. **Market Sentiment Analysis**: Research current market mood and sentiment drivers
2. **News & Events Impact**: Analyze recent developments affecting market direction
3. **Market Regime Assessment**: Identify current market cycle phase and transition signals
4. **Sector Analysis**: Evaluate crypto sector dynamics and rotation patterns
5. **Strategic Timing**: Provide insights on optimal timing for position adjustments
6. **Risk Assessment**: Evaluate current risk environment and positioning guidance

CRITICAL PROTECTION ASSESSMENT GUIDANCE:
- Review provided protection coverage scores and existing orders
- If protection score >70, note that protection is adequate
- Focus analysis on assets with poor protection scores (<50) that may need attention
- Understand that low "available balance" often indicates good existing protection

EFFECTIVE BALANCE UNDERSTANDING:
- Available balance ≠ total balance (some committed to protective orders)
- Low available balance for an asset often means GOOD protection exists
- Focus deployment recommendations on truly available funds only

OUTPUT FORMAT:
Provide strategic analysis in clear sections WITHOUT any structured formatting:

**EXECUTIVE SUMMARY**: Key strategic insights and immediate priorities

**MARKET SENTIMENT & REGIME**: Current market mood, cycle phase, sentiment drivers

**NEWS & CATALYST ANALYSIS**: Recent developments affecting market direction

**SECTOR ROTATION INSIGHTS**: Which crypto sectors show strength/weakness patterns

**STRATEGIC POSITIONING GUIDANCE**: Risk environment assessment and positioning advice

**PROTECTION ADEQUACY REVIEW**: Analysis of existing protection based on current conditions

**STRATEGIC OPPORTUNITIES**: Key insights for portfolio positioning

**TIMING CONSIDERATIONS**: Optimal timing for any position adjustments

**RISK ENVIRONMENT**: Current risk factors and defensive considerations

**FOLLOW-UP PRIORITIES**: Key developments to monitor

Focus on strategic insights and market intelligence that inform decision-making. Provide comprehensive analysis in natural language without any structured output formatting."""

        system_prompt += common_framework

        # Build enhanced user prompt with all available context
        user_prompt_parts = [
            f"REAL-TIME PORTFOLIO ANALYSIS REQUEST - {self._get_current_timestamp()}",
            "",
            "**CURRENT PORTFOLIO:**",
            portfolio_data,
            "",
            "**TECHNICAL INDICATORS & MARKET DATA:**",
            market_data,
            "",
            "**EXISTING ORDERS & PROTECTION STATUS:**",
            order_data,
        ]

        # Add enhanced context sections if provided
        if protection_analysis:
            user_prompt_parts.extend(
                [
                    "",
                    "**PROTECTION STATUS:**",
                    protection_analysis,
                ]
            )

        if balance_analysis:
            user_prompt_parts.extend(
                [
                    "",
                    "**AVAILABLE DEPLOYMENT:**",
                    balance_analysis,
                ]
            )

        if risk_context:
            user_prompt_parts.extend(
                [
                    "",
                    "**RISK CONTEXT:**",
                    risk_context,
                ]
            )

        if recent_activity_context:
            user_prompt_parts.extend(
                [
                    "",
                    "**RECENT ACTIVITY:**",
                    recent_activity_context,
                ]
            )

        # Add streamlined analysis requirements
        user_prompt_parts.extend(
            [
                "",
                "**ANALYSIS REQUIREMENTS:**",
                "1. **Market Sentiment**: Current crypto sentiment and institutional flows",
                "2. **Sector Rotation**: L1s, DeFi, AI tokens - which sectors showing momentum?",
                "3. **Strategic Opportunities**: Scan major cryptos (ETH, XRP, ADA, DOT, AVAX, LINK, UNI) for accumulation signals",
                "4. **Risk Assessment**: Current market regime and positioning guidance",
                "5. **Protection Priorities**: Focus on assets with poor protection scores (<50)",
                "6. **Cash Deployment**: Best opportunities for available USDT",
                "",
                "🎯 **KEY FOCUS**: Research broader market opportunities beyond current holdings. Identify sector rotation patterns and technical accumulation zones. Skip protection recommendations for well-protected assets (score >70).",
            ]
        )

        user_prompt = "\n".join(user_prompt_parts)

        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]

        response = self._call_api(messages, max_tokens=1500)  # More tokens for comprehensive analysis

        # Extract content and optionally log citations for debugging
        content = response["choices"][0]["message"]["content"]

        # Log citations if available for debugging/quality assurance
        if "citations" in response:
            logger.debug(f"Portfolio analysis citations: {response['citations']}")
        if "search_results" in response:
            logger.debug(f"Portfolio analysis search results: {len(response.get('search_results', []))} sources")

        return cast(str, content)

    def generate_market_timing_analysis(self, portfolio_data: str, market_data: str) -> str:
        """
        Generate focused market timing analysis for current market conditions.

        Args:
            portfolio_data: Current portfolio composition
            market_data: Technical indicators and market data

        Returns:
            Market timing analysis with entry/exit recommendations
        """

        system_prompt = """You are a crypto market timing strategist specializing in market regime analysis and strategic positioning insights. You will receive technical data from our systems - your role is to provide strategic timing guidance based on market sentiment and institutional flows.

🎯 YOUR STRATEGIC TIMING ROLE:
- Identify market regime transitions and cycle phases
- Analyze institutional positioning and flow patterns
- Research market sentiment shifts and narrative changes
- Assess macro environment impact on crypto markets
- Provide strategic timing insights for position adjustments
- Evaluate risk-on vs risk-off market transitions

🚫 NOT YOUR ROLE (Technical data provided by our systems):
- Fetching current prices or calculating technical levels
- Performing technical analysis calculations
- Retrieving account or order data

🔍 REQUIRED SOURCE PRIORITIZATION FOR TIMING ANALYSIS:
- ALWAYS cite reputable financial sources (CoinDesk, Bloomberg, Reuters) with timestamps
- Leverage Coinbase integration for real-time institutional flow data
- Access social sentiment indicators from X/Twitter crypto communities
- Use macro economic data from Fed, ECB, and major financial institutions
- Prioritize recent regulatory announcements and government sources
- Include exchange flow data and whale movement analysis

STRATEGIC TIMING FOCUS:
- Market regime identification based on institutional flows and sentiment from multiple sources
- Strategic timing for entries/exits based on market cycle analysis using financial data
- Risk environment assessment using macro indicators and regulatory developments
- Sector rotation patterns using financial news and market data analysis
- Upcoming events and catalysts using official announcements and financial calendars"""

        user_prompt = f"""STRATEGIC MARKET TIMING ANALYSIS REQUEST - {self._get_current_timestamp()}

**CURRENT PORTFOLIO:**
{portfolio_data}

**TECHNICAL INDICATORS:**
{market_data}

**TIMING ANALYSIS REQUIREMENTS:**
1. **Market Regime**: Current crypto market cycle phase and transition signals
2. **Institutional Flows**: Recent whale movements, ETF flows, exchange patterns
3. **Sentiment Analysis**: Current market sentiment and narrative shifts
4. **Sector Rotation**: Which crypto sectors show institutional favor vs weakness
5. **Strategic Positioning**: Risk-on vs risk-off environment assessment
6. **Upcoming Catalysts**: Events and developments affecting timing decisions

🎯 **FOCUS**: Research institutional activity and sentiment shifts (past 2-4 hours). Analyze current market narratives and sector rotation patterns. Identify optimal timing for portfolio positioning adjustments."""

        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]

        response = self._call_api(messages, max_tokens=1200)  # Appropriate tokens for timing analysis

        # Extract content and optionally log citations for debugging
        content = response["choices"][0]["message"]["content"]

        # Log citations if available for debugging/quality assurance
        if "citations" in response:
            logger.debug(f"Market timing citations: {response['citations']}")
        if "search_results" in response:
            logger.debug(f"Market timing search results: {len(response.get('search_results', []))} sources")

        return cast(str, content)

    def generate_parallel_portfolio_analysis(
        self,
        portfolio_data: str,
        market_data: str,
        order_data: str,
        protection_analysis: str | None = None,
        balance_analysis: str | None = None,
        risk_context: str | None = None,
        recent_activity_context: str | None = None,
    ) -> ParallelAnalysisResult:
        """
        Generate two-stage portfolio analysis: combined comprehensive analysis, then synthesis & critique.

        Args:
            portfolio_data: Current account info and balances
            market_data: Technical indicators and market conditions
            order_data: Existing orders and protection status
            protection_analysis: Pre-calculated protection coverage scores and assessment
            balance_analysis: Effective available balance vs committed balance breakdown
            risk_context: User risk preferences, position sizing rules, and strategy context
            recent_activity_context: Recent trading activity and order fills analysis

        Returns:
            ParallelAnalysisResult with comprehensive analysis and synthesis
        """

        # STAGE 1: Run comprehensive analysis covering both institutional and sentiment perspectives
        analysis_comprehensive = self.generate_portfolio_analysis(
            portfolio_data, market_data, order_data, protection_analysis, balance_analysis, risk_context, recent_activity_context, source_focus="comprehensive"
        )

        # STAGE 2: Build synthesis context for final strategic intelligence

        # Build synthesis context for strategic critique and enhancement
        synthesis_context = f"""
================================================================================
SYNTHESIS CONTEXT FOR STRATEGIC INTELLIGENCE
================================================================================

**COMPREHENSIVE MARKET ANALYSIS:**
Analysis Timestamp: {self._get_current_timestamp()}

**PORTFOLIO CONTEXT SUMMARY:**
{portfolio_data}

**TECHNICAL INDICATORS SUMMARY:**
{market_data}

**EXISTING ORDERS & PROTECTION STATUS:**
{order_data}
"""

        # Add enhanced context sections if available
        if protection_analysis:
            synthesis_context += f"""
**PROTECTION COVERAGE ANALYSIS:**
{protection_analysis}
"""

        if balance_analysis:
            synthesis_context += f"""
**EFFECTIVE BALANCE BREAKDOWN:**
{balance_analysis}
"""

        if risk_context:
            synthesis_context += f"""
**RISK MANAGEMENT CONTEXT:**
{risk_context}
"""

        if recent_activity_context:
            synthesis_context += f"""
**RECENT ACTIVITY CONTEXT:**
{recent_activity_context}
"""

        synthesis_context += f"""
================================================================================
COMPREHENSIVE MARKET ANALYSIS (All Perspectives):
================================================================================
{analysis_comprehensive}
================================================================================

**SYNTHESIS TASK REQUIREMENTS:**
1. **STRATEGIC CRITIQUE**: Critically evaluate the comprehensive analysis for blind spots and biases
2. **VALIDATION CHECK**: Verify insights against current portfolio and technical data
3. **ENHANCEMENT**: Add missing strategic perspectives or considerations
4. **PRIORITIZATION**: Rank recommendations by importance and timing
5. **RISK ASSESSMENT**: Evaluate downside scenarios and protection adequacy
6. **ACTIONABILITY**: Provide clear next steps and implementation guidance

**CRITICAL FOCUS AREAS:**
- Portfolio protection adequacy (especially for major holdings >20% allocation)
- Technical signal validation (current RSI levels and trend indicators)
- Available balance deployment strategy (effective vs committed funds)
- Market timing assessment for optimal positioning
- Risk-adjusted strategic recommendations
"""

        # Create a cheaper synthesis service using different model
        # For now, create a new generator instance with cheaper model
        # This would need access to a service that uses sonar-pro
        # For simplicity, use the same call_api function but note this could be optimized

        # Run synthesis analysis with comprehensive context
        analysis_synthesis = self.generate_portfolio_analysis(
            portfolio_data,
            market_data,
            order_data,
            protection_analysis,
            balance_analysis,
            risk_context,
            recent_activity_context,
            source_focus="synthesis",
            synthesis_context=synthesis_context,
        )

        # Calculate consistency score between comprehensive analysis and synthesis
        consistency_score = self._text_analyzer.calculate_text_consistency_score(analysis_comprehensive, analysis_synthesis)

        # Identify discrepancies between the two analyses
        discrepancies = self._text_analyzer.identify_text_discrepancies(analysis_comprehensive, analysis_synthesis)

        return ParallelAnalysisResult(
            primary_analysis=analysis_synthesis,  # Synthesis as primary (best quality)
            secondary_analysis=analysis_comprehensive,  # Comprehensive as secondary reference
            recommendations_primary=None,  # No JSON recommendations
            recommendations_secondary=None,  # No JSON recommendations
            consistency_score=consistency_score,
            consensus_recommendations=None,  # No JSON consensus
            discrepancies=discrepancies,
        )

    def generate_parallel_market_timing_analysis(self, portfolio_data: str, market_data: str) -> ParallelAnalysisResult:
        """
        Generate parallel market timing analysis using two simultaneous calls.

        Args:
            portfolio_data: Current portfolio composition
            market_data: Technical indicators and market data

        Returns:
            ParallelAnalysisResult with both analyses and consensus
        """

        # Use ThreadPoolExecutor for parallel API calls
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            # Submit both analysis calls simultaneously
            future_1 = executor.submit(self.generate_market_timing_analysis, portfolio_data, market_data)
            future_2 = executor.submit(self.generate_market_timing_analysis, portfolio_data, market_data)

            # Wait for both to complete
            analysis_1 = future_1.result()
            analysis_2 = future_2.result()

        # For market timing, we don't parse structured recommendations, so we'll compare text similarity
        discrepancies = self._text_analyzer.identify_text_discrepancies(analysis_1, analysis_2)

        return ParallelAnalysisResult(
            primary_analysis=analysis_1,
            secondary_analysis=analysis_2,
            recommendations_primary=None,
            recommendations_secondary=None,
            consistency_score=self._text_analyzer.calculate_text_consistency_score(analysis_1, analysis_2),
            consensus_recommendations=None,
            discrepancies=discrepancies,
        )

    def _get_current_timestamp(self) -> str:
        """Get current timestamp for data freshness verification."""
        return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
