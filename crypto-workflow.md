# AI Trading Workflow - Version 3.0

This document outlines a refined workflow for using the Crypto AI Assistant to analyze markets, develop a trading plan, and execute it on Binance, all through a unified command-line interface.

---

## Phase 1: Data Gathering & Analysis

**1. Get Account & Order Status:**
   - Run the `account` commands to get a clear picture of your current holdings and any pending orders.
     ```bash
     python main.py account info
     python main.py account orders
     ```

**2. Identify Coins for Analysis:**
   - Based on your account holdings (from `account info`), select coins for analysis.

**3. Get Technical Indicators:**
   - Run the `analysis indicators` command for your selected coins to get the latest data.
     ```bash
     python main.py analysis indicators --coins ETH,SOL,BNB
     ```

**4. Review Past Activity:**
   - Check `current_plan.md` for the context of the last active strategy.
   - Run the `account history` command for your selected coins to understand recent trades.
   - **⚠️ IMPORTANT:** Use the full trading pair symbol (e.g., `ETHUSDT`, `BTCUSDT`, `SOLUSDT`), not just the coin name.
     ```bash
     python main.py account history ETHUSDT
     python main.py account history BTCUSDT
     python main.py account history SOLUSDT
     ```

**5. Generate a "Deepsearch" Prompt for an External LLM:**
   - Instruct the AI assistant to synthesize all the data gathered in the previous steps.
   - The assistant will generate a comprehensive, copy-paste-ready prompt designed for a powerful external AI (e.g., GPT-4, Claude 3).
   - The user's role is to take this generated prompt and use it in the external tool to get a detailed, actionable trading plan.

---

## Phase 2: Plan Execution & Risk Management

**6. Develop and Save the Final Trading Plan:**
   - Review the AI's suggestions and finalize your plan in `current_plan.md`.

**7. Pre-Execution Verification (Critical Step):**
   - **A. Verify Order Precision (LOT_SIZE):** For every coin in your plan, use the `exchange lotsize` command to find the required quantity precision.
     ```bash
     python main.py exchange lotsize BNBUSDT
     # Expected Output: INFO: Symbol: BNBUSDT, LOT_SIZE Step Size: 0.00100000
     ```
   - **B. Adjust Quantities in Plan:** Round all order quantities in `current_plan.md` down to the correct number of decimal places.

**8. Execute Plan Actions & Update Status:**
   - Execute each action specified in `current_plan.md` one by one.
   - **🚨 CRITICAL:** **IMMEDIATELY** after each successful command, update `current_plan.md` to reflect the change. This is **MANDATORY** for maintaining an accurate state.
     - If you place an order, update its status to `OPEN` or `PLACED`.
     - If you cancel an order, update its status to `CANCELED`.
     ```bash
     # Example Execution Flow:
     # 1. Execute the command from the plan
     python main.py order cancel order ETHUSDT <ID>
     # 2. Immediately update current_plan.md to mark that order as CANCELED.

     # 3. Execute the next command from the plan
     python main.py order place ETHUSDT BUY LIMIT 0.2409 --price 2380
     # 4. Immediately update current_plan.md to add the new order with status OPEN.
     ```

**9. Manage Filled Orders (The Post-Fill Drill):**
   - As soon as a buy order is filled, you must immediately place its corresponding OCO risk management order.
   - **A. Confirm Exact Balance:** Run `python main.py account info --min-value 0` to see *all* asset balances, including small ones, and get the exact quantity.
   - **B. Round Quantity for OCO Precision (Critical):** Before placing the OCO order, you **must** round the quantity from your balance **down** to the precision required by the symbol's `LOT_SIZE` filter. Failure to do so will cause the order to be rejected.
   - **C. Place a Single OCO Order:** Place one OCO order for the **entire** new position to set a stop-loss and a take-profit.
     ```bash
     # OCO Syntax Example (for a position of 6.368 SOL, rounded to 6.36 if step size is 0.01):
     python main.py order place-oco SOLUSDT SELL_OCO 6.36 --price 180 --stop_price 139.80
     ```
   - **D. Update `current_plan.md`:** **IMMEDIATELY** mark the entry order as `FILLED` and the OCO order as `PLACED`.
   - **🚨 MANDATORY:** This step is not optional. Every filled order must be documented immediately to prevent confusion and double-trading.

**10. Monitor and Reevaluate:**
    - Continuously monitor your open orders and market conditions.
    - Always keep `current_plan.md` synchronized with your portfolio.

---

## 🚨 **CRITICAL: Plan Synchronization Protocol**

**GOLDEN RULE:** `current_plan.md` is your single source of truth. It must **ALWAYS** match your live portfolio state.

**Plan Update Trigger Events:**
- ✅ **Every order placement** - Document order ID, status, and parameters
- ✅ **Every order cancellation** - Mark as `CANCELED` with timestamp
- ✅ **Every order fill** - Update position size, mark as `FILLED`
- ✅ **Every OCO placement** - Document protective order details
- ✅ **Every position exit** - Mark as `SOLD` or `EXITED`, update cash
- ✅ **Portfolio value changes** - Update total value regularly

**The Update-First Rule:**
1. **Execute the trade command**
2. **IMMEDIATELY update current_plan.md**
3. **Only then proceed to the next action**

**Plan Maintenance Best Practices:**
- 📝 **Use timestamps** for all updates
- 📝 **Be specific** about order IDs and quantities
- 📝 **Mark status clearly** (OPEN, FILLED, CANCELED, PLACED)
- 📝 **Update portfolio value** after major changes
- 📝 **Review plan before each trading session**

---

## Appendix: Command Reference

### **`account`**: Manage portfolio data
- **`info`**: Get current portfolio balances and total value.
  - `python main.py account info`
- **`orders`**: List all open orders for one or all symbols.
  - `python main.py account orders [--symbol <SYMBOL>]`
- **`history`**: Fetch recent trade history for a specific symbol.
  - `python main.py account history <SYMBOL> [--limit <LIMIT>]`
  - **⚠️ SYMBOL Format:** Use full trading pair (e.g., `ETHUSDT`, `BTCUSDT`, `SOLUSDT`), not just coin name

### **`order`**: Place and cancel trading orders
- **`place-limit`**: Place a new limit order.
  - `python main.py order place-limit <SYMBOL> <SIDE> <QUANTITY> <PRICE>`
- **`place-market`**: Place a new market order.
  - `python main.py order place-market <SYMBOL> <SIDE> <QUANTITY>`
- **`place-oco`**: Place a new OCO (One-Cancels-the-Other) order. This is for the SELL side only to set a take-profit and a stop-loss.
  - `python main.py order place-oco <SYMBOL> <QUANTITY> <PRICE> <STOP_PRICE>`
- **`cancel`**: Cancel an open single order or an entire OCO order.
  - `python main.py order cancel order <SYMBOL> <ID>`
  - `python main.py order cancel oco <SYMBOL> <LIST_ID>`

### **`exchange`**: Get market and exchange information
- **`lotsize`**: Check symbol's LOT_SIZE filter for correct quantity precision.
  - `python main.py exchange lotsize <SYMBOL>`

### **`analysis`**: Run technical analysis
- **`indicators`**: Get key technical indicators (RSI, MAs) for specified coins.
  - `python main.py analysis indicators --coins <COIN_LIST>`
