# AI Trading Workflow – Strategic Development (v6.0)

This workflow supports comprehensive research and strategy creation for crypto trading. It is designed to work alongside daily monitoring and is intended for discrete planning sessions rather than day‑to‑day oversight.

## Guiding Principles

* **All Coins Matter** – analyse every portfolio position meeting scope: value > $1.00 OR allocation > 1% (ignore true dust).
* **Risk First** – ensure every position has a protective strategy before seeking new opportunities.
* **Safety Always** – back up private keys, never share credentials, and start small when testing new strategies.

## Setup & Safety

Use `./main.sh` (Unix/Mac) or `.\main.ps1` (Windows) to run commands. Always verify your environment and practice with small amounts before executing larger trades.

## Experience‑Level Quick Start

* **Beginner:**

  * View your portfolio: `python main.py account info`
  * Generate a strategy prompt: `python main.py ai analyze-portfolio --mode strategy`
  * Place a limit order: `python main.py order place-limit SYMBOL SIDE QTY PRICE`

* **Intermediate:** access order validation, OCO orders, technical indicator checks and plan synchronization tools.

* **Advanced:** customize validation workflows, automate error recovery and optimize system performance.

---

## Core Workflow Overview

The strategic workflow follows eight modular steps. Each module can be referenced independently, avoiding the need to re-read the entire document during subsequent sessions.

### Module A – External AI Analysis (Interactive Two‑Stage)

#### Prompt Handling Protocol (Optimized for Perplexity Space)
- **SYSTEM PROMPT**: Now permanently set in Perplexity Space (displayed below for transparency)
- **USER PROMPT**: Generated dynamically based on current portfolio state
- **WORKFLOW**: Copy user prompt → Paste into Perplexity Space → Paste response back to app

1. **Agent Generates User Prompt:**

   * Agent runs `python main.py ai analyze-portfolio --mode strategy` to produce a dynamic user prompt.
   * **Agent displays the permanently set system prompt for transparency**
   * **Agent displays the generated user prompt for copy-paste**
   * Agent waits for user to complete external AI consultation

2. **User External AI Interaction:**

   * **User copies the USER PROMPT** and pastes it into Perplexity Space (system prompt already set)
   * **User copies the AI response** and provides it back to the agent

3. **Agent Evaluates Quality:**

   * Base score = 100. Gap Checklist (mechanical):
     - Market timing covered? If no: −5
     - Actionable levels & stops? If no: −5
     - Risk assessment explicit? If no: −5
     - Protection addressed? If no: −5
   * Proceed thresholds: ≥75 proceed; 60–74 request clarification; <60 re-run or switch provider

**📋 Agent Formatting Requirements:**
- Display the permanently set system prompt for transparency (already configured in Perplexity Space)
- Display the dynamically generated user prompt in a clear code block
- Use `**PERMANENTLY SET SYSTEM PROMPT (For Reference):**` followed by a code block
- Use `**USER PROMPT (Copy this to Perplexity Space):**` followed by a code block
- Include clear instructions for Perplexity Space workflow
- Wait for user to provide external AI response before proceeding

**🔄 Interactive Flow Example:**
```
Agent: "Here's your user prompt for Perplexity Space (system prompt already set):"

**PERMANENTLY SET SYSTEM PROMPT (For Reference):**
```[optimized system prompt in code block]```

**USER PROMPT (Copy this to Perplexity Space):**
```[dynamic user prompt in code block]```

Agent: "Please paste the AI response here when ready..."
User: [Pastes AI analysis response]
Agent: "Analysis received. Quality score: 82/100. Proceeding to Module B..."
```

**🔧 PERMANENTLY SET SYSTEM PROMPT (Optimized for Perplexity Space):**
```
You are an expert crypto portfolio strategist with COMPREHENSIVE MARKET INTELLIGENCE capabilities. Analyze from both institutional and community perspectives to provide balanced, multi-dimensional market insights.

🎯 YOUR COMPREHENSIVE ANALYSIS ROLE:
- Integrate institutional flows with grassroots sentiment analysis
- Balance professional research with community-driven market dynamics
- Synthesize regulatory developments with social adoption patterns
- Combine exchange data with on-chain metrics and social sentiment
- Provide strategic reasoning from multiple market perspectives

🔍 MANDATORY MULTI-SOURCE ANALYSIS:
**INSTITUTIONAL & PROFESSIONAL SOURCES:**
- Bloomberg, Reuters, institutional research reports
- ETF flows, corporate treasury activities, regulatory developments
- Professional trader sentiment and whale movement analysis
- Fund positioning and macro trend analysis

**COMMUNITY & SENTIMENT SOURCES:**
- Twitter/X crypto sentiment, Reddit discussions
- On-chain analytics, social sentiment tracking
- Grassroots adoption metrics and viral market narratives
- Meme trends and retail FOMO/FUD patterns

📊 REQUIRED OUTPUT STRUCTURE:
Present findings in parallel sections with clear attribution:
- "Institutional Consensus" vs "Community Sentiment" tables
- Direct quotes and source citations for all key claims
- Cross-verification requirements (minimum 2 independent sources)
- Mark speculative or low-confidence predictions explicitly

🎯 COMPREHENSIVE TECHNICAL ANALYSIS REQUIREMENTS:
- **MINIMUM COVERAGE**: Analyze at least 7 major altcoins (ETH, LINK, DOT, ADA, AVAX, UNI, XRP)
- **CONFLUENCE FACTORS**: Support/resistance levels with volume, MA crossover, orderbook activity
- **BREAKOUT TRIGGERS**: Specific price + volume thresholds or external catalysts
- **MULTI-TIMEFRAME**: Daily, 4h, and weekly analysis with most significant levels highlighted
- **RISK MANAGEMENT**: Stop loss guidance and risk/reward ratios for each opportunity

🚨 MANDATORY MACRO INTELLIGENCE (CRITICAL FOUNDATION):
1. **Fear & Greed Index**: Current level with interpretation and trend analysis
2. **Institutional Flows**: Recent fund flows, ETF activity, whale movements with data sources
3. **Bitcoin Dominance**: Current percentage, trend implications, and sector rotation signals
4. **Market Structure**: Altcoin Season Index, sector performance, capital flow patterns

📈 SECTOR ROTATION ANALYSIS REQUIREMENTS:
- Evaluate AI tokens, DeFi, L1, meme coins performance over last quarter
- Identify catalysts, capital flows, and cross-sector performance relative to BTC
- Present historical sector performance timeline with upcoming event triggers
- Flag leading/lagging sectors with specific data points

🎯 ACTIONABLE TRADING RECOMMENDATIONS FORMAT:
For each opportunity, provide:
- Entry zone (support/resistance levels)
- Trigger condition (price/volume/on-chain catalyst)
- Risk management (stop loss, position sizing guideline)
- Risk/reward ratio calculation
- Rationale (referenced from both analyst and community inputs)
- Scenario planning (breakdown/breakout adjustments)

📊 QUALITY REQUIREMENTS:
- All key levels must be substantiated with at least 2 independent sources
- Attribute all claims to specific institutional/community sources
- Highlight data conflicts or uncovered risks
- Mark speculative predictions as low-confidence
- Include limitations and data gaps disclosure
- Present in well-labeled tables and parallel sections

🚫 NOT YOUR ROLE (Technical data provided by our systems):
- Fetching current prices or technical indicators
- Calculating exact quantities or portfolio percentages
- Retrieving account balances or order data
- Performing precision calculations or validation
- Providing specific order commands or exact trade instructions

Focus on risk-first strategic insights that prioritize portfolio protection with comprehensive, multi-source analysis and actionable recommendations.
```

### Module B – Protection & Validation (Now before deeper AI)

Run this immediately after Module A prompts are prepared (can feed gaps back to AI):

1. **Check Existing Orders:** `python main.py account orders --symbol SYMBOL` for each holding.
2. **Assess Coverage:** ensure sell orders and stop levels adequately protect each position. If no stop within 10% or inadequate TP coverage, log the gap.
3. **Validate Actions:** simulate proposed orders (`python main.py validate order-simulation ...`) and verify balances (`python main.py validate balance-check ASSET`).
4. Feed gaps to AI: “Update protection for [symbols with gaps]; skip [symbols protected].”

### Module C – Execution Module (Merged: Plan + Execute)

Single loop for efficiency:
1. Validate recommendation → Place order(s) → Log order IDs → Verify positions and protection
2. Commands: `order place-*`, `account orders`, `account info`, plus `validate *`

### Module E – Transition to Monitoring

Once all strategic actions are complete:

1. Ensure every position has appropriate protection.
2. Test the monitoring command: `python main.py ai analyze-portfolio --mode monitoring`.
3. Schedule the next strategic review or set thresholds that trigger a return to strategy mode.

---

## Reference & Tools

### Protection Strategies

* **OCO (One‑Cancels‑Other)**: combines a take‑profit and stop‑loss order. Suitable when you need downside protection and upside capture simultaneously.
* **Limit Sell Above Market:** for profit taking when you already have sufficient downside protection.
* **Protection adequacy guide**: stop within 10% OR diversified TP coverage covering ≥50% of position earns “GOOD”. Below that: flag as gap.

### Macro & Risk Triggers (Action-Oriented)
- Call out shifts that should trigger strategy adjustment:
  - Fear & Greed Index > 80 (overheated), < 20 (capitulation)
  - BTC Dominance < 59% (alt season risk-on), > 55% (BTC-led risk-off)
  - ETF/institutional flow inflections (notable in/out flows)

### Tactical Snapshot (post-AI)
- One-page sheet to drive action:
  - Macro Summary (with triggers)
  - Risk Flags (🔴/🟠/🟢 by severity)
  - Top 3 Actions with entry/stop/size

### Common Commands

* **Portfolio & Orders:** `account info`, `account orders`, `account history SYMBOL --limit N`
* **Trading:** `order place-limit SYMBOL SIDE QTY PRICE`, `order place-market`, `order place-oco`, `order cancel`
* **Analysis & AI:** `analysis indicators --coins COIN_LIST`, `ai analyze-portfolio --mode strategy|monitoring`, `validate ai-recommendations`, `validate order-simulation`, `validate balance-check`
* **Tactical Snapshot:** `ai analyze-portfolio --mode strategy --snapshot`

For additional details on troubleshooting, error recovery, and manual fallback procedures, consult the full reference section of your original workflow document.

---

This v6.0 update consolidates prompt handling, makes quality scoring mechanical via a Gap Checklist, moves protection assessment earlier, merges execution into one module, adds macro/risk triggers, introduces color-coded risk states, and provides a tactical snapshot to accelerate decisions.