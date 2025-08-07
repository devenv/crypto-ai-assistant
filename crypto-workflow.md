# AI Trading Workflow – Strategic Development (v5.0)

This workflow supports comprehensive research and strategy creation for crypto trading. It is designed to work alongside daily monitoring and is intended for discrete planning sessions rather than day‑to‑day oversight.

## Guiding Principles

* **All Coins Matter** – analyse every portfolio position above $1.00, not just the largest holdings. Smaller positions can signal market shifts and must be protected.
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

1. **Agent Generates Prompts:**

   * Agent runs `python main.py ai analyze-portfolio --mode strategy` to produce a detailed system prompt and user prompt.
   * **Agent displays both prompts in separate code blocks with clear headers for easy copy-paste**
   * Agent waits for user to complete external AI consultation

2. **User External AI Interaction:**

   * **User copies the SYSTEM PROMPT** and pastes it into preferred AI service (ChatGPT, Claude, Perplexity, etc.)
   * **User copies the USER PROMPT** and pastes it as the question to the AI service
   * **User copies the AI response** and provides it back to the agent

3. **Agent Evaluates Quality:**

   * Agent scores the AI response (>75 = proceed; 60–74 = request clarification; <60 = try another service or manual analysis)
   * Agent identifies gaps in market timing, actionability, risk assessment or protection
   * If analysis is insufficient, agent requests specific follow-up questions or suggests alternative AI services

**📋 Agent Formatting Requirements:**
- Display each prompt in separate code blocks with clear markdown headers
- Use `**SYSTEM PROMPT (Copy this first):**` followed by a code block
- Use `**USER PROMPT (Copy this second):**` followed by a code block
- Include clear instructions for copy-paste workflow
- Wait for user to provide external AI response before proceeding

**🔄 Interactive Flow Example:**
```
Agent: "Here are your AI prompts - copy these to your external AI service:"

**SYSTEM PROMPT (Copy this first):**
```[system prompt in code block]```

**USER PROMPT (Copy this second):**
```[user prompt in code block]```

Agent: "Please paste the AI response here when ready..."
User: [Pastes AI analysis response]
Agent: "Analysis received. Quality score: 82/100. Proceeding to Module B..."
```

### Module B – Protection & Validation

Before executing any recommendation:

1. **Check Existing Orders:** `python main.py account orders --symbol SYMBOL` for each holding.
2. **Assess Coverage:** ensure sell orders and stop levels adequately protect each position. If there's no stop within 10 % of current price, plan to add protection.
3. **Validate Actions:** simulate proposed orders (`python main.py validate order-simulation ...`) and verify balances (`python main.py validate balance-check ASSET`).

### Module C – Action Plan Development

Convert validated AI insights into a practical plan:

1. Summarise the rationale and risk/reward for each trade.
2. Confirm available funds and conflict with existing orders.
3. Draft specific orders (side, price, size) and document them in your plan.

### Module D – Execution & Verification

1. Execute orders one at a time using `python main.py order ...`.
2. Immediately log each order ID and update your plan.
3. After execution, verify orders and positions (`python main.py account orders` and `python main.py account info`).

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
* **Sell Orders Within 5 % of current price and covering >50 % of the position** count as good protection. Otherwise, add or adjust protective orders.

### Common Commands

* **Portfolio & Orders:** `account info`, `account orders`, `account history SYMBOL --limit N`
* **Trading:** `order place-limit SYMBOL SIDE QTY PRICE`, `order place-market`, `order place-oco`, `order cancel`
* **Analysis & AI:** `analysis indicators --coins COIN_LIST`, `ai analyze-portfolio --mode strategy|monitoring`, `validate ai-recommendations`, `validate order-simulation`, `validate balance-check`

For additional details on troubleshooting, error recovery, and manual fallback procedures, consult the full reference section of your original workflow document.

---

This rewrite condenses repeated instructions, groups related tasks into clear modules and references, and clarifies which tools and steps apply at each stage of your strategic process.