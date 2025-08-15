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

#### Prompt Handling Protocol (single source)
- Copy in this exact order each time (do not repeat elsewhere; link back here):
  1) SYSTEM PROMPT → copy first
  2) USER PROMPT → copy second
  3) Paste AI response back to the app

1. **Agent Generates Prompts:**

   * Agent runs `python main.py ai analyze-portfolio --mode strategy` to produce a detailed system prompt and user prompt.
   * **Agent displays both prompts in separate code blocks with clear headers for easy copy-paste**
   * Agent waits for user to complete external AI consultation

2. **User External AI Interaction:**

   * **User copies the SYSTEM PROMPT** and pastes it into preferred AI service (ChatGPT, Claude, Perplexity, etc.)
   * **User copies the USER PROMPT** and pastes it as the question to the AI service
   * **User copies the AI response** and provides it back to the agent

3. **Agent Evaluates Quality:**

   * Base score = 100. Gap Checklist (mechanical):
     - Market timing covered? If no: −5
     - Actionable levels & stops? If no: −5
     - Risk assessment explicit? If no: −5
     - Protection addressed? If no: −5
   * Proceed thresholds: ≥75 proceed; 60–74 request clarification; <60 re-run or switch provider

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