# AI Trading Portfolio Monitoring Workflow - Version 3.0

This document outlines a systematic workflow for monitoring your active cryptocurrency portfolio on Binance using the unified `main.py` CLI.

---

## The Monitoring Loop (Run Daily or During Volatility)

### **Phase 1: Get the Current State**

**1. Check Portfolio & Open Orders:**
   - Get a complete snapshot of what you hold and what orders are pending.
     ```bash
     python main.py account info --min-value 0
     python main.py account orders
     ```

### **Phase 2: Verify Against Your Plan**

**2. Compare with `current_plan.md`:**
   - Open your `current_plan.md` file.
   - **A. Check for Filled Orders:** Have any of your `OPEN` orders been filled?
   - **B. Verify Stop-Losses:** For **every asset you hold**, is there a corresponding `OCO` order active? If a position is unprotected, proceed to Phase 3.

### **Phase 3: Take Action on Discrepancies**

This phase covers actions to take when your live portfolio state diverges from `current_plan.md`.

**A. The Post-Fill Drill (For Newly Acquired Assets):**
   - If you discover a filled buy order with no corresponding protection, execute these steps:
   - **1. Confirm Exact Balance:** Run `python main.py account info --min-value 0` again to get the *precise* quantity of the new asset.
   - **2. Check Lot Size:** Run `python main.py exchange lotsize <SYMBOL>` to confirm quantity precision. Round your balance *down* to the correct number of decimal places.
   - **3. Place a Single OCO Order:** Place one OCO order to protect the entire new position as defined in your plan.
     ```bash
     # Example: Placing a protective OCO for a new SOL position of 3.868
     python main.py order place-oco SOLUSDT 3.868 180 155.50
     ```
   - **4. Update `current_plan.md`:** After the OCO is successfully placed, immediately update the plan. Mark the buy order as `FILLED` and the new OCO order as `PLACED`.

**B. General Discrepancy Resolution:**
   - For other discrepancies (e.g., a missing asset, duplicate orders, incorrect stop-loss levels), the process is:
   - **1. Identify the Action:** Determine what needs to be done. If an asset from the plan is missing, investigate its history to see if it was sold.
     ```bash
     python main.py account history <SYMBOL>
     ```
   - **2. Execute the Command:** Run the appropriate command (e.g., `order cancel`).
   - **3. Update `current_plan.md`:** Immediately after, update the plan to reflect the change (e.g., mark a position `SOLD` or an order `CANCELED`).

**4. Get Fresh Market Context (Optional but Recommended):**
   - If the market is volatile, get updated technical indicators.
     ```bash
     python main.py analysis indicators --coins ETH,SOL,BNB
     ```

### **Phase 4: Report**

**5. Generate a Status Report:**
   - Based on your findings, generate a concise report.
   - **If no action is needed:** "All positions are aligned with the plan and protected. Monitoring continues."
   - **If action is required:** "Action Needed: The `ETH` buy order has filled. Proceeding with the Post-Fill Drill."
   - **If there's a warning:** "Warning: `BNB` price is approaching the stop-loss. Monitor closely."

---

## Appendix: Command Reference

### **`account`**: Manage portfolio data
- **`info`**: Get current portfolio balances and total value.
  - `python main.py account info --min-value 0`
- **`orders`**: List all open orders for one or all symbols.
  - `python main.py account orders`
- **`history`**: Fetch recent trade history for a specific symbol.
  - `python main.py account history <SYMBOL> [--limit <LIMIT>]`

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
