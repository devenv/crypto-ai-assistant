# AI Trading Workflow - Version 3.0

This document outlines a refined workflow for using the Crypto AI Assistant to analyze markets, develop a trading plan, and execute it on Binance, all through a unified command-line interface.

## Command Format

**Windows PowerShell:** Use `.\main.ps1` instead of `python main.py`
**Unix/Linux/Mac:** Use `./main.sh` (or `python main.py`)

Examples:
- Windows: `.\main.ps1 account info`
- Unix: `./main.sh account info`
- Manual: `python main.py account info`

---

## Phase 1: Data Gathering & Analysis

**1. Get Account & Order Status:**
   - Run the `account` commands to get a clear picture of your current holdings and any pending orders.
     ```bash
     # Windows PowerShell:
     .\main.ps1 account info
     .\main.ps1 account orders

     # Unix/Linux/Mac:
     ./main.sh account info
     ./main.sh account orders

     # Manual (any system):
     python main.py account info
     python main.py account orders
     ```

**2. Identify Coins for Analysis:**
   - Based on your account holdings (from `account info`), select coins for analysis.

**3. Get Technical Indicators:**
   - Run the `analysis indicators` command for your selected coins to get the latest data.
     ```bash
     # Windows PowerShell:
     .\main.ps1 analysis indicators --coins ETH,SOL,BNB

     # Unix/Linux/Mac:
     ./main.sh analysis indicators --coins ETH,SOL,BNB

     # Manual (any system):
     python main.py analysis indicators --coins ETH,SOL,BNB
     ```

**4. Review Past Activity:**
   - Check `current_plan.md` for the context of the last active strategy.
   - Run the `account history` command for your selected coins to understand recent trades.
   - **⚠️ IMPORTANT:** Use the full trading pair symbol (e.g., `ETHUSDT`, `BTCUSDT`, `SOLUSDT`), not just the coin name.
     ```bash
     # Windows PowerShell:
     .\main.ps1 account history ETHUSDT
     .\main.ps1 account history BTCUSDT
     .\main.ps1 account history SOLUSDT

     # Unix/Linux/Mac:
     ./main.sh account history ETHUSDT
     ./main.sh account history BTCUSDT
     ./main.sh account history SOLUSDT

     # Manual (any system):
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
     # Windows PowerShell:
     .\main.ps1 exchange lotsize BNBUSDT

     # Unix/Linux/Mac:
     ./main.sh exchange lotsize BNBUSDT

     # Manual (any system):
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

     # Windows PowerShell:
     # 1. Execute the command from the plan
     .\main.ps1 order cancel order ETHUSDT <ID>
     # 2. Immediately update current_plan.md to mark that order as CANCELED.

     # 3. Execute the next command from the plan
     .\main.ps1 order place ETHUSDT BUY LIMIT 0.2409 --price 2380
     # 4. Immediately update current_plan.md to add the new order with status OPEN.

     # Unix/Linux/Mac:
     # 1. Execute the command from the plan
     ./main.sh order cancel order ETHUSDT <ID>
     # 2. Immediately update current_plan.md to mark that order as CANCELED.

     # 3. Execute the next command from the plan
     ./main.sh order place ETHUSDT BUY LIMIT 0.2409 --price 2380
     # 4. Immediately update current_plan.md to add the new order with status OPEN.

     # Manual (any system):
     # 1. Execute the command from the plan
     python main.py order cancel order ETHUSDT <ID>
     # 2. Immediately update current_plan.md to mark that order as CANCELED.

     # 3. Execute the next command from the plan
     python main.py order place ETHUSDT BUY LIMIT 0.2409 --price 2380
     # 4. Immediately update current_plan.md to add the new order with status OPEN.
     ```

**9. Manage Filled Orders (The Post-Fill Drill):**
   - As soon as a buy order is filled, you must immediately place its corresponding OCO risk management order.
   - **A. Confirm Exact Balance:** Run the account info command to see *all* asset balances, including small ones, and get the exact quantity.
     ```bash
     # Windows PowerShell:
     .\main.ps1 account info --min-value 0

     # Unix/Linux/Mac:
     ./main.sh account info --min-value 0

     # Manual (any system):
     python main.py account info --min-value 0
     ```
   - **B. Round Quantity for OCO Precision (Critical):** Before placing the OCO order, you **must** round the quantity from your balance **down** to the precision required by the symbol's `LOT_SIZE` filter. Failure to do so will cause the order to be rejected.
   - **C. Place a Single OCO Order:** Place one OCO order for the **entire** new position to set a stop-loss and a take-profit.
     ```bash
     # OCO Syntax Example (for a position of 6.368 SOL, rounded to 6.36 if step size is 0.01):

     # Windows PowerShell:
     .\main.ps1 order place-oco SOLUSDT SELL_OCO 6.36 --price 180 --stop_price 139.80

     # Unix/Linux/Mac:
     ./main.sh order place-oco SOLUSDT SELL_OCO 6.36 --price 180 --stop_price 139.80

     # Manual (any system):
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
  - Windows: `.\main.ps1 account info`
  - Unix: `./main.sh account info`
  - Manual: `python main.py account info`
- **`orders`**: List all open orders for one or all symbols.
  - Windows: `.\main.ps1 account orders [--symbol <SYMBOL>]`
  - Unix: `./main.sh account orders [--symbol <SYMBOL>]`
  - Manual: `python main.py account orders [--symbol <SYMBOL>]`
- **`history`**: Fetch recent trade history for a specific symbol.
  - Windows: `.\main.ps1 account history <SYMBOL> [--limit <LIMIT>]`
  - Unix: `./main.sh account history <SYMBOL> [--limit <LIMIT>]`
  - Manual: `python main.py account history <SYMBOL> [--limit <LIMIT>]`
  - **⚠️ SYMBOL Format:** Use full trading pair (e.g., `ETHUSDT`, `BTCUSDT`, `SOLUSDT`), not just coin name

### **`order`**: Place and cancel trading orders
- **`place-limit`**: Place a new limit order.
  - Windows: `.\main.ps1 order place-limit <SYMBOL> <SIDE> <QUANTITY> <PRICE>`
  - Unix: `./main.sh order place-limit <SYMBOL> <SIDE> <QUANTITY> <PRICE>`
  - Manual: `python main.py order place-limit <SYMBOL> <SIDE> <QUANTITY> <PRICE>`
- **`place-market`**: Place a new market order.
  - Windows: `.\main.ps1 order place-market <SYMBOL> <SIDE> <QUANTITY>`
  - Unix: `./main.sh order place-market <SYMBOL> <SIDE> <QUANTITY>`
  - Manual: `python main.py order place-market <SYMBOL> <SIDE> <QUANTITY>`
- **`place-oco`**: Place a new OCO (One-Cancels-the-Other) order. This is for the SELL side only to set a take-profit and a stop-loss.
  - Windows: `.\main.ps1 order place-oco <SYMBOL> <QUANTITY> <PRICE> <STOP_PRICE>`
  - Unix: `./main.sh order place-oco <SYMBOL> <QUANTITY> <PRICE> <STOP_PRICE>`
  - Manual: `python main.py order place-oco <SYMBOL> <QUANTITY> <PRICE> <STOP_PRICE>`
- **`cancel`**: Cancel an open single order or an entire OCO order.
  - Windows: `.\main.ps1 order cancel order <SYMBOL> <ID>`
  - Windows: `.\main.ps1 order cancel oco <SYMBOL> <LIST_ID>`
  - Unix: `./main.sh order cancel order <SYMBOL> <ID>`
  - Unix: `./main.sh order cancel oco <SYMBOL> <LIST_ID>`
  - Manual: `python main.py order cancel order <SYMBOL> <ID>`
  - Manual: `python main.py order cancel oco <SYMBOL> <LIST_ID>`

### **`exchange`**: Get market and exchange information
- **`lotsize`**: Check symbol's LOT_SIZE filter for correct quantity precision.
  - Windows: `.\main.ps1 exchange lotsize <SYMBOL>`
  - Unix: `./main.sh exchange lotsize <SYMBOL>`
  - Manual: `python main.py exchange lotsize <SYMBOL>`

### **`analysis`**: Run technical analysis
- **`indicators`**: Get key technical indicators (RSI, MAs) for specified coins.
  - Windows: `.\main.ps1 analysis indicators --coins <COIN_LIST>`
  - Unix: `./main.sh analysis indicators --coins <COIN_LIST>`
  - Manual: `python main.py analysis indicators --coins <COIN_LIST>`
