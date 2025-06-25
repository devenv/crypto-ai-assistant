# 🤖 AI Trading Assistant

A command-line interface (CLI) for interacting with the Binance API, designed to be used with a structured trading workflow.

[![CI/CD](https://img.shields.io/badge/CI/CD-passing-brightgreen)](https://github.com/your-username/your-repo/actions)
[![Coverage](https://img.shields.io/badge/Coverage-100%25-brightgreen)](https://github.com/your-username/your-repo/actions)
[![Language](https://img.shields.io/badge/Language-Python-blue)](https://www.python.org/)

---

This project provides a CLI for crypto trading and a set of **workflows** to guide the process. The main idea is to separate active trading from routine monitoring, using the CLI as a tool to execute a well-defined plan.

---

## 📈 AI-Powered Workflows

This project is built around two key workflows that are executed by an AI assistant. The AI uses the provided CLI commands to systematically manage your crypto portfolio, turning high-level strategy into concrete actions.

### 1. Active Trading Workflow

This workflow is used when you want to analyze the market and execute new trades. The AI will:

1.  **Gather Intelligence**: It runs a full analysis of your account, open orders, and relevant market indicators using the `account` and `analysis` commands.
2.  **Consult an External Strategist**: The AI prepares a comprehensive prompt based on its analysis. The user then manually sends this to an external research provider (e.g., Perplexity, ChatGPT) and pastes the resulting trading plan back. The AI then formalizes this into `current_plan.md` for the user's final review.
3.  **Execute Precisely**: Before placing any trades, the AI verifies the correct order size precision using the `exchange lotsize` command to prevent rejections. It then executes the trades defined in the plan.
4.  **Manage Risk**: As soon as a buy order is filled, the AI automatically executes the "Post-Fill Drill": it confirms your new asset balance and immediately places a corresponding OCO (One-Cancels-the-Other) order to protect your new position with a stop-loss and a take-profit.

To initiate this workflow, you can instruct the AI:
> "Let's start a new trading session. Please follow the steps in @crypto-workflow.md"

### 2. Portfolio Monitoring Workflow

This is a routine checklist the AI runs to ensure all your active positions are safe and aligned with your plan. The AI will:

1.  **Get a Snapshot**: It fetches the current state of your portfolio and all open orders.
2.  **Verify and Reconcile**: The AI cross-references this information with your `current_plan.md` to ensure every asset is protected by an OCO order.
3.  **Take Corrective Action**: If an unprotected asset is found (e.g., a buy order was filled but the protective OCO was not placed), the AI automatically executes the **Post-Fill Drill** to secure the position. It will also handle other discrepancies, like canceling duplicate orders or updating incorrect ones.
4.  **Report Findings**: The AI provides a concise summary of its findings and any actions taken.

To run this check, you can tell the AI:
> "Time for a portfolio check. Let's run the @crypto-monitoring-workflow.md"

---

## 🚀 Getting Started

Follow these steps to get the project up and running.

### Prerequisites

-   Python 3.10
-   A Binance Account with API Key and Secret

### Installation & Configuration

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/crypto-ai-assistant.git
    cd crypto-ai-assistant
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install all dependencies:**
    ```bash
    pip install -e .[dev,test]
    ```

4.  **Configure API Keys**:
    -   Create a file named `.env` in the project root.
    -   Add your Binance API key and secret:
        ```env
        BINANCE_API_KEY="your_api_key_here"
        BINANCE_API_SECRET="your_api_secret_here"
        ```

5.  **Review Application Settings**:
    -   Customize behavior in `src/config.toml`. A default configuration is provided, but you can adjust parameters for analysis and display values.

---

## 🛠️ Command Reference

These are the low-level commands used to execute the steps defined in the workflows.

### General Help
`crypto-ai-assistant --help`

### Account Commands
-   **Info**: `crypto-ai-assistant account info [--min-value <VALUE>]`
-   **Orders**: `crypto-ai-assistant account orders [--symbol <SYMBOL>]`
-   **History**: `crypto-ai-assistant account history <SYMBOL> [--limit <NUMBER>]`

### Exchange Commands
- **Lot Size**: `crypto-ai-assistant exchange lotsize <SYMBOL>`

### Analysis Commands
-   **Indicators**: `crypto-ai-assistant analysis indicators --coins "BTC,ETH,SOL"`

### Order Commands
-   **Place Market**: `crypto-ai-assistant order place-market <SYMBOL> <SIDE> <QUANTITY>`
-   **Place Limit**: `crypto-ai-assistant order place-limit <SYMBOL> <SIDE> <QUANTITY> <PRICE>`
-   **Place OCO**: `crypto-ai-assistant order place-oco <SYMBOL> <QUANTITY> <PRICE> <STOP_PRICE>`
-   **Cancel**: `crypto-ai-assistant order cancel <order|oco> <SYMBOL> <ORDER_ID>`

---

## 👨‍💻 Development Workflow

For contributing to this project, please follow the structured development workflow. This ensures code quality, consistency, and maintainability.

### How to Use the Development Workflow
To start a development session with the AI, you can reference the developer guide directly.

-   **To begin a development task**, you might say:
    > "I want to work on a new feature. Please follow the process in @dev/ai-developer.md"

This will guide the AI to follow the established procedures for branching, coding, testing, and quality checks. For full details on the process, please read the [Developer Workflow](./dev/ai-developer.md) document.

---

## 📂 Project Structure
```
.
├── docs/               # Workflow and planning documents
├── src/
│   ├── api/            # Binance API client and models
│   ├── core/           # Core business logic
│   └── main.py         # Main CLI application
├── tests/              # Unit and integration tests
├── .env                # API keys (not committed)
├── config.toml         # Application configuration
└── pyproject.toml      # Project metadata and dependencies
```
---

## ⚠️ Disclaimer

Trading cryptocurrencies involves significant risk. This tool is for educational and informational purposes only. The author is not responsible for any financial losses incurred through the use of this software. Always do your own research and trade responsibly.
