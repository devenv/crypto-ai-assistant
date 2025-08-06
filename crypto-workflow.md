# AI Trading Workflow - Strategic Development (v5.0)

This workflow uses **comprehensive deep research** for developing new trading strategies and executing complex market analysis.

**🔄 ALL COINS ANALYSIS PRINCIPLE:**
- **NEVER analyze only "major holdings"** - include ALL portfolio positions above $1.00 (currently: BTC, SOL, TAO, FET, RAY)
- **Small positions matter**: Even positions under $50 can signal market shifts or need strategic analysis
- **Complete strategic coherence**: Entire portfolio should align with developed strategy, not just large positions
- **Comprehensive protection**: All positions should be evaluated for protective measures regardless of size

---

## ⚠️ **CRITICAL SAFETY & SETUP**

**🚨 Before ANY trading:**
- **Backup private keys** securely
- **Never share API keys** or credentials
- **Start with small amounts** until confident
- **Double-check all commands** - financial mistakes are costly

**💻 Command Format:**
- **Windows:** `.\main.ps1` instead of `python main.py`
- **Unix/Linux/Mac:** `./main.sh` (or `python main.py`)
- **Examples:** `.\main.ps1 account info` or `./main.sh account info`

---

## 🎯 **QUICK START BY EXPERIENCE LEVEL**

<details>
<summary>📚 <strong>BEGINNER:</strong> Essential commands only</summary>

```bash
python main.py account info                    # Check portfolio
python main.py ai analyze-portfolio --mode strategy  # Get AI analysis
python main.py order place-limit SYMBOL SIDE QTY PRICE  # Place orders
```

**Safety First:** Use small amounts, verify prices with `analysis indicators` before trading.

</details>

<details>
<summary>🔧 <strong>INTERMEDIATE:</strong> Advanced features</summary>

- Order validation and simulation (`validate order-simulation`)
- OCO protective orders (`order place-oco`)
- Technical analysis integration (`analysis indicators`)
- Automated plan synchronization

</details>

<details>
<summary>⚙️ <strong>ADVANCED:</strong> System optimization</summary>

- Custom validation workflows (`validate ai-recommendations`)
- Error recovery automation
- Performance optimization
- Strategic framework evolution

</details>

---

## 🤖 **WORKFLOW PURPOSE & AI MODEL USAGE**

| Feature | This Workflow (Strategy Development) | Monitoring Workflow |
|---------|--------------------------------------|---------------------|
| **Purpose** | **New Strategy Development** | **Daily Portfolio Monitoring** |
| **AI Model** | **External AI (prompts provided)** | **sonar** (quick check) |
| **Command** | `ai analyze-portfolio --mode strategy` | `ai analyze-portfolio --mode monitoring` |
| **Use When** | Planning new strategies | Daily/weekly monitoring |
| **Time** | Generates prompts for external AI | Quick automated check |

---

## 📋 **CORE WORKFLOW: 8-STEP PROCESS**

### **🧠 ENHANCED AI ANALYSIS FRAMEWORK: ITERATIVE TWO-STAGE APPROACH**

**🎯 STRATEGIC ANALYSIS EVOLUTION:**
Strategic analysis now provides comprehensive prompts for external AI services, allowing you to use ChatGPT, Claude, or any preferred AI service for deep market research.

**Stage 1: External AI Analysis (Prompt Generation)**
- System generates comprehensive prompts with portfolio context
- Integrated institutional + sentiment analysis framework provided
- Technical indicators + portfolio data + market intelligence included
- **Output**: Copy-paste prompts for external AI services
- **Usage**: Paste prompts into ChatGPT, Claude, or preferred AI service

**Stage 2: Analysis Evaluation & Enhancement (Optional)**
- Evaluate external AI analysis quality and completeness
- Identify gaps or areas needing additional research
- Use additional prompts or manual analysis for missing elements
- Combine insights from multiple AI services if needed
- **Threshold**: Analysis quality >75 = proceed, <75 = additional research

**⚠️ CRITICAL RULE: Always use the generated prompts with external AI, then evaluate quality**

**Enhanced Benefits:**
- **Flexibility**: Use any AI service (ChatGPT, Claude, Perplexity, etc.)
- **Cost Control**: No automatic API costs, use your preferred service
- **Quality Control**: Review and iterate with external AI as needed
- **Transparency**: Full visibility into prompts and responses

### **Step 1: Enhanced Strategic Analysis (Iterative Two-Stage Process)**

**🎯 EXTERNAL AI STRATEGIC ANALYSIS PRINCIPLE (CRITICAL):**
- **Stage 1**: Generate comprehensive prompts with portfolio context for external AI
- **Stage 2**: Evaluate external AI analysis quality and iterate if needed
- **Prompt Quality**: System provides institutional + sentiment analysis framework
- **External Analysis**: Use generated prompts with ChatGPT, Claude, or preferred AI service
- **Our System Role**: Exact prices, technical indicators, portfolio calculations, order data, balances, validation, execution

**🔍 STAGE 1: PROMPT GENERATION FOR EXTERNAL AI**
```bash
# Generate comprehensive AI prompts for copy-paste to external services:
python main.py ai analyze-portfolio --mode strategy
```

**📋 PROMPT OUTPUT**: The system automatically generates comprehensive system and user prompts that you can copy and paste into any external AI service (ChatGPT, Claude, Perplexity, etc.) for deep strategic analysis.

**Stage 1 Prompt Generation Includes:**
- 💰 Complete portfolio status with allocations and values
- 📋 All active orders with IDs, types, and current status
- 📊 Technical indicators (RSI, EMA, MACD) for ALL portfolio positions
- 🏛️ **Institutional Intelligence Framework**: Guidance for ETF flows, regulatory analysis
- 📱 **Sentiment Intelligence Framework**: Instructions for social trends, community sentiment
- 🔗 **Market Context Framework**: Guidelines for regime analysis, timing considerations
- 📝 **Strategic Requirements**: Specific analysis requirements and output format

**📊 STAGE 1 EXTERNAL AI USAGE:**
Use generated prompts with your preferred external AI service:

**AI Service Options:**
- ✅ **ChatGPT**: Copy system prompt to custom instructions, user prompt to chat
- ✅ **Claude**: Use prompts in conversation for comprehensive analysis
- ✅ **Perplexity**: Paste prompts for research-backed strategic insights
- ✅ **Other AI Services**: Any service that accepts system + user prompts

**🔍 EXTERNAL AI ANALYSIS EVALUATION:**
After receiving analysis from external AI, evaluate quality and completeness:

| Analysis Quality | External AI Response | Next Action |
|------------------|---------------------|-------------|
| **Market Timing** | Vague timing guidance | Ask follow-up questions for precise entry/exit timing |
| **Risk Assessment** | Generic risk mentions | Request specific portfolio risk quantification |
| **Conflicting Signals** | Technical vs sentiment discord | Ask AI to resolve and prioritize recommendations |
| **Actionability** | Abstract recommendations | Request concrete order specifications and levels |
| **Regime Clarity** | Unclear market phase | Ask for explicit regime identification |
| **Protection Gaps** | Missing protection analysis | Request targeted protection recommendations |

**🎯 STAGE 2: EXTERNAL AI REFINEMENT (When Needed)**
If initial analysis lacks quality, use follow-up prompts with external AI:

**Follow-up Prompt Examples:**
- "Provide specific entry and exit levels for the opportunities you mentioned"
- "Quantify the portfolio concentration risk you identified with specific percentages"
- "Resolve the conflicting signals between technical and sentiment analysis"
- "Give concrete order specifications (price levels, quantities) for your recommendations"

**Stage 2 External AI Refinement Focus:**
- 🎯 **Targeted Gap Resolution**: Address specific gaps identified from initial analysis
- ⏰ **Market Timing Precision**: Request enhanced timing analysis for optimal entry/exit
- 🔍 **Reality Validation**: Ask AI to validate insights against current portfolio state
- ⚖️ **Priority Ranking**: Request clear prioritization of competing recommendations
- 📈 **Regime Analysis**: Ask for explicit market regime identification and implications
- 🛡️ **Protection Strategy**: Request targeted protection recommendations with specifics

**🔄 EXTERNAL AI ANALYSIS INTEGRATION:**
After receiving comprehensive analysis from external AI:

1. **Quality Assessment**: Evaluate analysis completeness and actionability (>75 = good)
2. **Gap Resolution**: Use follow-up prompts if key areas are missing or unclear
3. **Cross-Validation**: Optionally use multiple AI services for comparison
4. **Final Analysis**: Combine insights from all interactions for complete picture
5. **Decision Readiness**: Ensure analysis provides clear, actionable guidance

**📊 FINAL ANALYSIS PACKAGE:**
- **Primary Analysis**: Main strategic insights from external AI
- **Refinements**: Any follow-up clarifications or additional details
- **Quality Score**: Self-assessed completeness and actionability rating
- **Action Plan**: Clear next steps derived from AI analysis

### **Step 2: External AI Analysis Evaluation & Enhancement Decision**

**📊 EXTERNAL AI ANALYSIS EVALUATION**
Review external AI analysis results systematically:

1. **Data Integration**: Verify AI used provided portfolio, orders, and technical data effectively
2. **Strategic Clarity**: Assess clarity of market regime and timing guidance
3. **Actionability**: Evaluate specificity of recommendations and execution guidance
4. **Gap Identification**: Identify areas needing follow-up questions or clarification
5. **Quality Score**: Assess overall analysis quality and confidence level

**🔍 EXTERNAL AI QUALITY ASSESSMENT PROTOCOL:**
- ✅ **75-100**: High quality - proceed directly to Step 2.5 (Protection Assessment)
- 🟡 **60-74**: Good with gaps - **USE FOLLOW-UP PROMPTS** for targeted enhancement
- 🚨 **<60**: Insufficient - **TRY DIFFERENT AI SERVICE** or use manual analysis

**📋 GAP ANALYSIS BEFORE STAGE 2:**
When Stage 1 scores <75, identify specific improvement areas:

**Market Timing Gaps:**
- [ ] Entry/exit timing too vague or generic
- [ ] Conflicting timing signals not resolved
- [ ] Market regime unclear or not explicitly stated

**Actionability Gaps:**
- [ ] Recommendations too abstract for execution
- [ ] Missing specific price levels or quantities
- [ ] Protection strategy insufficient or unclear

**Risk Assessment Gaps:**
- [ ] Portfolio risk not quantified or contextualized
- [ ] Position sizing guidance missing or generic
- [ ] Risk/reward ratios not calculated

**Reality Alignment Gaps:**
- [ ] Recommendations don't account for existing orders
- [ ] Available balance not properly considered
- [ ] Current technical levels not integrated

**🎯 STAGE 2 ENHANCEMENT EXECUTION**
When Stage 2 is triggered, run enhanced analysis:

```bash
# Enhanced analysis targeting identified gaps:
python main.py ai market-timing
```

**Stage 2 Call Instructions:**
- Focus on specific gaps identified from Stage 1
- Request precise timing and entry/exit guidance
- Validate recommendations against current portfolio reality
- Provide concrete actionable recommendations with specifics

**📊 INTEGRATED ANALYSIS ASSESSMENT**
After Stage 2 completion, integrate both analyses:

**Integration Decision Matrix:**
- **Stage Alignment**: Do Stage 1 and Stage 2 agree on direction?
- **Conflict Resolution**: When stages disagree, prioritize Stage 2 (more targeted)
- **Complementary Insights**: Combine Stage 1 breadth with Stage 2 precision
- **Final Confidence**: Assess combined quality score

**Combined Analysis Quality Scoring:**
- ✅ **80-100**: Excellent - high confidence execution
- 🟡 **65-79**: Good - proceed with minor adjustments
- 🟠 **50-64**: Adequate - careful execution with enhanced validation
- 🚨 **<50**: Insufficient - manual analysis fallback required

**📝 STRATEGIC INSIGHTS INTEGRATION**
Extract actionable intelligence from integrated analysis:

**Key Integration Questions:**
- **Market Direction**: What's the primary strategic direction (accumulate/protect/hold)?
- **Timing Precision**: When should actions be taken (immediate/on dips/on breaks)?
- **Risk Quantification**: What's the specific risk level of recommended actions?
- **Protection Strategy**: How should current positions be protected?
- **Cash Deployment**: How much and when should available USDT be deployed?

**Action Translation Examples:**
- 🔍 **"BTC accumulation opportunity"** → Validate with `analysis indicators --coins BTC`
- 🛡️ **"SOL protection inadequate"** → Check with `account orders --symbol SOLUSDT`
- ⚖️ **"ETH profit-taking at $3,800"** → Simulate with `validate order-simulation`
- 💰 **"Deploy 30% cash on 5% dip"** → Check with `validate balance-check USDT`

### **Step 2.5: Existing Protection Assessment** *(CRITICAL)*

🛡️ **BEFORE acting on AI recommendations, evaluate existing protection:**

**Quick Protection Check:**
```bash
# Check existing orders for ALL portfolio positions mentioned in AI analysis
python main.py account orders --symbol SOLUSDT
python main.py account orders --symbol ETHUSDT
python main.py account orders --symbol BTCUSDT
python main.py account orders --symbol TAOUSDT
python main.py account orders --symbol FETUSDT
python main.py account orders --symbol RAYUSDT
```

**Protection Adequacy Decision Matrix:**

| Condition | Action | Rationale |
|-----------|--------|-----------|
| **Sell orders within 5% of current price** | ✅ SKIP protective recommendations | Already protected |
| **Sell orders cover >50% of position** | ✅ SKIP or minimal adjustment | Adequate coverage |
| **Multiple protective price levels exist** | 🔍 EVALUATE incremental benefit | May be sufficient |
| **No protective orders within 10%** | ✅ EXECUTE AI protection recommendations | Needs protection |

**Real Example from Our Session:**
- **SOL**: AI recommended OCO, but existing 5.0 SOL sell at $185 (current $183.83) = **EXCELLENT PROTECTION**
- **ETH**: AI recommended stop-loss, but existing sells at $3,750/$3,700 (current $3,647) = **GOOD PROTECTION**
- **Decision**: Skip protective orders, focus on BTC repositioning instead

**Protection Coverage Score (Quick Calculation):**
- Protective orders within 5% of current price: **+50 points**
- Orders cover majority of position: **+30 points**
- Multiple price levels protected: **+20 points**
- **Score >70**: Skip new protection orders
- **Score <70**: Implement AI recommendations

### **Step 3: Manual Analysis Fallback (When Both AI Stages Insufficient)**

```bash
# When integrated analysis scores <50 or AI systems fail:
python main.py account history ETHUSDT --limit 5    # Recent transaction patterns
python main.py account history BTCUSDT --limit 5    # Recent transaction patterns
python main.py account history SOLUSDT --limit 5    # Recent transaction patterns
python main.py account history TAOUSDT --limit 5    # Recent transaction patterns
python main.py account history FETUSDT --limit 5    # Recent transaction patterns
python main.py account history RAYUSDT --limit 5    # Recent transaction patterns
python main.py analysis indicators --coins BTC,SOL,TAO,FET,RAY  # Current technical state - ALL portfolio positions
```

**Manual Analysis Triggers:**
- **Combined analysis score <50** after both Stage 1 and Stage 2
- **Both AI stages fail** to provide adequate strategic guidance
- **AI systems unavailable** or malfunctioning during critical decisions
- **Extremely contradictory signals** that both stages cannot resolve
- **Time-sensitive protection issues** when AI analysis incomplete

**🔍 Manual Analysis Protocol:**
1. **Protection Priority**: Identify any major positions (>20%) without protection <10%
2. **Technical Assessment**: Review RSI extremes (>80 or <20) requiring immediate action
3. **Balance Reality**: Confirm available USDT vs committed orders for new positions
4. **Risk Containment**: Focus on conservative actions that reduce portfolio risk
5. **Documentation**: Record all manual decisions for future AI training

**📊 Conservative Manual Decision Framework:**
- **Immediate Protection**: Place basic stop-losses for unprotected major positions
- **Order Cleanup**: Cancel obviously stale or conflicting orders
- **Cash Preservation**: Avoid new large deployments without clear technical signals
- **Plan Documentation**: Update plan with all manual actions and rationale

⚠️ **Manual Analysis Safety Rules:**
- **Use full trading pairs**: ETHUSDT, BTCUSDT, SOLUSDT (not abbreviated)
- **Conservative position sizing**: <10% portfolio for any new positions
- **Protection first**: Always prioritize risk management over opportunity
- **Document everything**: Essential for improving future AI analysis

### **Step 4: Strategic Action Plan Development**

📋 **STRATEGIC INSIGHTS TO ACTION PLAN**
Convert AI strategic analysis into specific, validated actions:

**Action Plan Development Process:**
1. **Extract Key Insights**: Identify specific opportunities/risks from AI analysis
2. **Technical Validation**: Verify with current indicators and market data
3. **Protection Review**: Assess adequacy using existing orders
4. **Balance Validation**: Confirm available funds for any new positions
5. **Risk Assessment**: Ensure alignment with risk tolerance

**Example Action Plan Creation:**

**From AI Insight**: *"BTC showing strong accumulation opportunity with RSI at 42, institutional flows positive"*

**Validation Steps:**
```bash
# 1. Verify current technical state
python main.py analysis indicators --coins BTC

# 2. Check available USDT for accumulation
python main.py validate balance-check USDT

# 3. Review existing BTC orders
python main.py account orders --symbol BTCUSDT

# 4. Simulate potential accumulation order
python main.py validate order-simulation BTCUSDT BUY LIMIT 0.004 --price 115000
```

**Documented Plan:**
```markdown
BTC ACCUMULATION OPPORTUNITY
- Rationale: AI identifies RSI 42 + institutional flows
- Technical Validation: ✅ RSI confirmed at 42.2 (Strong Buy signal)
- Available Funds: ✅ $877 USDT available
- Existing Protection: ✅ Sell order at $130K provides upside protection
- Proposed Action: BUY 0.004 BTC at $115,000 (~$460 USDT)
- Risk Level: LOW (position stays <25% portfolio)
```

**FINALIZATION CHECKLIST**
- [ ] Strategic insights align with risk tolerance
- [ ] Technical indicators support AI analysis
- [ ] Protective orders adequate for new positions
- [ ] Available balance confirmed for all planned actions
- [ ] No conflicts with existing orders identified

### **Step 5: Pre-Execution Validation (Advanced)**

🛡️ **AUTOMATED VALIDATION TOOLS**
```bash
# Validate AI recommendations before execution:
python main.py validate ai-recommendations '[JSON_RECOMMENDATIONS]'

# Check available balance:
python main.py validate balance-check ETH

# Simulate order before placing:
python main.py validate order-simulation ETHUSDT SELL LIMIT 0.0439 --price 3650
```

### **Step 6: Systematic Execution**

🎯 **EXECUTION PROTOCOL**
Execute actions one by one with immediate documentation:

```bash
# 1. Execute command
python main.py order place-limit ETHUSDT SELL 0.2409 3800

# 2. IMMEDIATELY update current_plan.md with Order ID
# 3. Only then proceed to next action
```

⚠️ **CRITICAL RULE:** Update `current_plan.md` immediately after each command.

### **Step 7: Post-Execution Verification**

🔍 **POST-EXECUTION VERIFICATION PROTOCOL**

**A. Verify Orders Exist:**
```bash
python main.py account orders
```

**B. Check for Unexpected Fills:**
```bash
python main.py account info
python main.py account history ETHUSDT --limit 3
```

**C. Plan Reconciliation:**
Ensure `current_plan.md` accurately reflects live portfolio state.

### **Step 8: Transition to Monitoring**

Switch to **crypto-monitoring-workflow.md** for ongoing daily oversight.

---

## 🚀 **ENHANCED WORKFLOW BENEFITS: UX, SAFETY & PRECISION**

### **🎯 USER EXPERIENCE IMPROVEMENTS**

**✅ Iterative Refinement:**
- **Transparency**: Clear visibility into what Stage 1 identified and what gaps need addressing
- **Control**: User can see specific improvement areas before triggering Stage 2
- **Efficiency**: Stage 2 only when needed, targeted analysis reduces noise
- **Predictability**: Clear progression rules and decision thresholds

**✅ Enhanced Safety:**
- **Dual Validation**: Two independent analyses reduce single-point-of-failure risk
- **Gap Identification**: Explicit documentation of what needs improvement
- **Reality Alignment**: Stage 2 specifically validates against current portfolio state
- **Conservative Fallback**: Manual analysis protocol for when AI stages insufficient

**✅ Improved Actionability:**
- **Targeted Enhancement**: Stage 2 focuses specifically on actionability gaps
- **Concrete Guidance**: Enhanced analysis provides specific price levels and quantities
- **Integrated Insights**: Combined analysis leverages breadth + precision
- **Clear Execution Path**: Unambiguous next steps with confidence levels

### **🛡️ SAFETY ENHANCEMENTS**

**🔒 Multi-Layer Validation:**
1. **Stage 1**: Comprehensive analysis with quality assessment
2. **Gap Analysis**: Explicit identification of improvement areas
3. **Stage 2**: Targeted enhancement addressing specific gaps
4. **Integration**: Combined analysis with conflict resolution
5. **Manual Fallback**: Conservative protocol when AI insufficient

**🔒 Risk Management Integration:**
- **Protection Assessment**: Mandatory evaluation of existing protection before new orders
- **Balance Reality**: Stage 2 validates against actual available funds
- **Position Sizing**: Enhanced analysis includes specific risk quantification
- **Conservative Bias**: Manual fallback prioritizes protection over opportunity

**🔒 Error Prevention:**
- **Conflicting Signals**: Stage 2 explicitly resolves contradictions from Stage 1
- **Order Conflicts**: Enhanced validation against existing order state
- **Market Timing**: Precise timing guidance reduces premature execution risk
- **Documentation**: All decisions tracked for learning and improvement

### **📊 PRECISION IMPROVEMENTS**

**🎯 Market Timing Precision:**
- **Stage 1**: Broad market context and general timing guidance
- **Stage 2**: Specific entry/exit levels with precise timing conditions
- **Integration**: Combined timing strategy with confidence levels
- **Validation**: Reality check against current technical levels

**🎯 Actionability Enhancement:**
- **Stage 1**: Strategic direction and general recommendations
- **Stage 2**: Concrete order specifications with price levels
- **Integration**: Prioritized action plan with execution sequence
- **Validation**: Pre-execution simulation for all recommendations

**🎯 Risk Quantification:**
- **Stage 1**: General risk environment assessment
- **Stage 2**: Specific portfolio risk quantification and mitigation
- **Integration**: Risk-adjusted recommendations with position sizing
- **Validation**: Protection adequacy assessment before execution

---

## 🚀 **ADVANCED FEATURES & AUTOMATION**

### **Validation Commands**

```bash
# AI recommendation validation (100-point scoring):
python main.py validate ai-recommendations '[JSON]'

# Order simulation (prevent critical errors):
python main.py validate order-simulation SYMBOL SIDE TYPE QTY [--price PRICE]

# Balance verification (prevent insufficient balance):
python main.py validate balance-check ASSET
```

### **Protective Order Strategy Guide**

**⚠️ CRITICAL: Understand Order Types for Protection**

| Order Type | Purpose | When Price Executes | Example Use Case |
|------------|---------|-------------------|------------------|
| **LIMIT SELL** | Take profit | When market reaches or exceeds your price | Profit-taking: SELL LIMIT at $110 (current $100) |
| **OCO SELL** | Dual protection | Either take-profit OR stop-loss hits | Protection: Take-profit $110, Stop-loss $90 |

**Protective Order Examples:**
```bash
# ✅ CORRECT: OCO for downside protection + upside capture
python main.py validate order-simulation ETHUSDT SELL OCO 0.5 --price 3800 --stop-price 3400
# Result: Sells at $3800 (profit) OR $3400 (protection)

# ❌ WRONG: LIMIT SELL below market (executes immediately)
python main.py validate order-simulation ETHUSDT SELL LIMIT 0.5 --price 3400  # Current: $3600
# Result: Immediate execution, no protection

# ✅ CORRECT: LIMIT SELL above market (profit-taking only)
python main.py validate order-simulation ETHUSDT SELL LIMIT 0.5 --price 3800  # Current: $3600
# Result: Waits for $3800, no downside protection
```

**Protection Strategy Decision Matrix:**
- **Need downside protection?** → Use OCO orders
- **Only profit-taking?** → Use LIMIT SELL above market
- **Small position (<1% portfolio)?** → Consider if protection overhead is worthwhile

### **Plan Synchronization Protocol**

**🚨 GOLDEN RULE:** `current_plan.md` = Single Source of Truth

**Update Triggers:**
- ✅ Every order placement → Document Order ID immediately
- ✅ Every order cancellation → Mark CANCELED with timestamp
- ✅ Every order fill → Update position, mark FILLED
- ✅ Portfolio value changes → Update totals

**Active Order Registry Template:**
```markdown
| Asset | Order ID | Type | Side | Price | Quantity | Status | Entry Time | Notes |
|-------|----------|------|------|-------|----------|---------|------------|-------|
| ETH   | 32643068755 | LIMIT | SELL | 3550 | 0.012 | ACTIVE | 20:59 | Profit ladder |
| BTC   | 46167771039 | LIMIT | BUY | 112000 | 0.00267 | ACTIVE | 20:59 | Support buy |
```

---

## 🔧 **TECHNICAL REFERENCE**

### **Essential Commands Quick Reference**

| Command | Purpose | Example |
|---------|---------|---------|
| `account info` | Check portfolio | `python main.py account info` |
| `account orders` | List active orders | `python main.py account orders` |
| `ai analyze-portfolio` | Get AI analysis | `python main.py ai analyze-portfolio --mode strategy` |
| `order place-limit` | Place limit order | `python main.py order place-limit ETHUSDT SELL 0.24 3800` |
| `order place-oco` | Place OCO order | `python main.py order place-oco ETHUSDT 0.24 3650 3300` |
| `order cancel` | Cancel order | `python main.py order cancel order ETHUSDT 12345` |

### **Error Recovery & Troubleshooting**

**Common Issues:**

| Error | Cause | Solution | Prevention |
|-------|-------|----------|------------|
| Insufficient balance | Assets in orders | Check existing orders | Use `validate balance-check` |
| Immediate fill | Wrong price side | Verify current market price | Use `validate order-simulation` |
| OCO rejection | Conflicting levels | Check existing orders | Review order conflicts |

**Recovery Steps:**
1. **Stop execution** immediately
2. **Check account status** and order history
3. **Document actual state** in plan
4. **Adjust strategy** based on new information

### **Strategic Work Troubleshooting**

**Two-Stage AI Analysis Issue Resolution:**

| Issue Type | Immediate Action | Strategic Response |
|------------|------------------|-------------------|
| **Stage 1 quality <75** | Proceed to Stage 2 synthesis | Analyze comprehensive perspective gaps |
| **Stage 2 fails to enhance analysis** | Trigger enhanced analysis | Focus on critical decisions only |
| **Both AI stages insufficient** | Use manual analysis fallback | Conservative decisions with available data |
| **Conflicting market signals** | Document specific conflicts | Use enhanced analysis to explicitly resolve |
| **Market regime uncertainty** | Enhanced timing analysis | Targeted research on regime transitions |
| **API errors in analysis** | Re-run failed stage | Fall back to previous successful stage |
| **Multiple order conflicts** | List all orders first | Cancel conflicting orders before new placements |
| **Market volatility during execution** | Pause execution | Re-analyze with current prices |
| **Plan synchronization errors** | Check recent fills | Update plan with actual positions |

**Strategic Recovery Protocol:**
```bash
# Step 1: Assess current state
python main.py account info
python main.py account orders

# Step 2: Check recent activity
python main.py account history ETHUSDT --limit 10
python main.py account history BTCUSDT --limit 10

# Step 3: Re-analyze if needed
python main.py ai analyze-portfolio --mode strategy

# Step 4: Validate any new plans
python main.py validate ai-recommendations '[JSON]'
```

### **Safety Validation for External AI**

**Quick Validation Checklist:**
```
□ Current prices confirmed (run: analysis indicators)
□ SELL orders: Price > Current Market ✅
□ BUY orders: Price < Current Market ✅
□ OCO orders: Both limits on correct sides ✅
□ No immediate fill risk ✅
□ Existing order conflicts checked ✅
□ Risk tolerance maintained (<40% single asset) ✅
```

**Critical Red Flags (Auto-Reject):**
```
❌ Orders filling immediately (wrong side of market)
❌ Recommendations >50% portfolio in single trade
❌ Stop-losses >15% for major assets
❌ Cash deployment >90% of available
❌ Price targets ignoring existing protective orders
```

**Quick Quality Score Calculation:**
```
Rate each category 1-5, multiply by weight:

Data Fresh (×5):     ___ /25 points
Technical Valid (×5): ___ /25 points
Risk Appropriate (×4): ___ /20 points
Executable (×3):     ___ /15 points
Portfolio Fit (×3):   ___ /15 points

TOTAL: ___/100 points

>90: Execute with confidence
75-89: Minor adjustments needed
60-74: Major modifications required
<60: Reject - request new analysis
```

---

## 🔄 **TRANSITION TO MONITORING MODE**

### **When Strategic Work is Complete**

**After completing Step 8 (Post-Execution Verification), transition to ongoing monitoring:**

**Final Strategic Session Tasks:**
1. **Complete Plan Update:** Ensure `current_plan.md` reflects all executed trades
2. **Document Strategy:** Note key decisions and rationale for future reference
3. **Set Monitoring Schedule:** Based on market volatility and position sizes
4. **Establish Triggers:** Define when to return to strategic mode

**Monitoring Setup Checklist:**
```bash
# Verify all orders are properly tracked
python main.py account orders

# Confirm positions are protected
# (All major positions should have stop-losses or planned exits)

# Test monitoring command
python main.py ai analyze-portfolio --mode monitoring

# Set next strategic review date (typically 1-2 weeks)
```

### **Monitoring Mode Guidelines**

**For ongoing oversight after strategic execution:**

**Daily Monitoring Approach:**
- **Command:** `python main.py ai analyze-portfolio --mode monitoring`
- **Focus:** Health checks, order fills, actionable issues only
- **Time:** Quick monitoring check
- **Action Threshold:** Actionable score <60 requires attention

**Return to Strategic Mode When:**
- Portfolio changes >10% from plan
- Major market regime change detected
- Multiple monitoring issues persist
- New strategic opportunities identified
- Planned strategic review date reached

**Emergency Strategic Re-entry:**
- If monitoring tools fail repeatedly
- If multiple unexpected order fills occur
- If market volatility requires position adjustments
- If external events impact strategy assumptions

---

## 🎯 **STRATEGIC SESSION SUCCESS CRITERIA**

### **Session Completion Checklist**

**Strategic analysis session is successful when:**
- ✅ Comprehensive AI analysis completed (score >75) for ALL portfolio positions
- ✅ All recommendations validated and reviewed across entire portfolio
- ✅ Execution plan documented with specific actions for every relevant position
- ✅ Risk assessment completed and approved for complete portfolio
- ✅ Conflict checks performed for all planned orders across all positions

**Execution session is successful when:**
- ✅ All planned orders placed successfully
- ✅ Order IDs documented in plan immediately
- ✅ Post-execution verification completed
- ✅ Unexpected fills addressed appropriately
- ✅ Plan synchronization confirmed accurate

**Transition to monitoring is successful when:**
- ✅ ALL portfolio positions have appropriate protection (BTC,SOL,TAO,FET,RAY)
- ✅ Monitoring command tested and working for complete portfolio
- ✅ Next strategic review scheduled with ALL positions considerations
- ✅ Emergency escalation triggers defined for every position
- ✅ Plan documentation complete and current for entire portfolio

### **Quality Metrics for Strategic Work**

**Target Performance Standards:**
- **Analysis Quality:** AI validation scores >80 consistently
- **Execution Accuracy:** Orders placed correctly >99% of time
- **Plan Synchronization:** Plan accuracy >98% after execution
- **Risk Management:** ALL portfolio positions protected appropriately (major positions >20% within 10%, smaller positions evaluated for protection needs)
- **Documentation Quality:** Plan reflects reality within 2% variance

**Monthly Strategic Review Questions:**
1. **Effectiveness:** Are strategic decisions improving portfolio performance?
2. **Process:** Is the 8-step workflow being followed consistently?
3. **Risk Management:** Are protective measures working as intended?
4. **Integration:** Is transition to monitoring working smoothly?
5. **Evolution:** What workflow improvements have been identified?

---

## 🧠 **META-THINKING & CONTINUOUS IMPROVEMENT**

### **Workflow Evolution Protocol**

**When workflow improvements are identified:**

1. **Document the Issue:**
   ```markdown
   Date: [YYYY-MM-DD]
   Issue: [Description of problem/opportunity]
   Impact: [Effect on workflow efficiency/accuracy]
   Solution: [Proposed improvement]
   Status: [Proposed/Testing/Implemented]
   ```

2. **Test & Validate:** Run through improved process without breaking existing functionality

3. **Update Documentation:** Modify this document and related sections

4. **Integration Check:** Ensure alignment with monitoring workflow and development guidelines

### **Quality Assessment Questions**

**Regularly evaluate:**
1. **Efficiency:** Repetitive manual steps that could be automated?
2. **Accuracy:** Steps that frequently lead to errors?
3. **Completeness:** Scenarios this workflow doesn't handle well?
4. **Clarity:** Instructions needing better explanation?
5. **Integration:** How well does this integrate with monitoring processes?

---

## 📚 **COMPLETE COMMAND REFERENCE**

### **Account Management**
```bash
python main.py account info                           # Portfolio overview
python main.py account orders [--symbol SYMBOL]      # Active orders
python main.py account history SYMBOL [--limit N]    # Trade history
```

### **Order Management**
```bash
python main.py order place-limit SYMBOL SIDE QTY PRICE    # Limit order
python main.py order place-market SYMBOL SIDE QTY         # Market order
python main.py order place-oco SYMBOL QTY PRICE STOP      # OCO order (SELL only)
python main.py order cancel order SYMBOL ID               # Cancel single order
python main.py order cancel oco SYMBOL LIST_ID            # Cancel OCO order
```

### **Analysis & AI**
```bash
python main.py analysis indicators --coins COIN_LIST      # Technical indicators
python main.py ai analyze-portfolio --mode strategy       # Generate prompts for external AI
python main.py ai analyze-portfolio --mode monitoring     # Quick monitoring analysis
python main.py ai market-timing                          # Market timing analysis
```

### **Validation & Safety**
```bash
python main.py validate ai-recommendations '[JSON]'       # Validate AI suggestions
python main.py validate order-simulation ARGS             # Simulate order placement
python main.py validate balance-check ASSET               # Check available balance
```

---

**🎯 KEY PRINCIPLE:** This workflow prioritizes systematic strategy development with comprehensive analysis of ALL portfolio positions above $1.00. Strategy mode now generates comprehensive prompts for external AI services (ChatGPT, Claude, Perplexity, etc.) rather than making automatic API calls. This provides cost control, service flexibility, and complete transparency. For daily monitoring, use `crypto-monitoring-workflow.md` which focuses on quick health checks and actionable issues only.

**🔄 RESILIENCE:** If any command fails or gets interrupted, retry the command as needed to complete each workflow step fully before proceeding to the next step. Complete workflow integrity is essential for strategic success.
