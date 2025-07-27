# 🤖 AI Trading Assistant

A command-line interface (CLI) for interacting with the Binance API, designed to be used with a structured trading workflow.

[![CI/CD](https://img.shields.io/badge/CI/CD-in_progress-yellow)](https://github.com/crypto-ai-assistant/crypto-ai-assistant/actions)
[![Coverage](https://img.shields.io/badge/Coverage-34%25-red)](https://github.com/crypto-ai-assistant/crypto-ai-assistant/actions)
[![Language](https://img.shields.io/badge/Language-Python-blue)](https://www.python.org/)

---

This project provides a CLI for crypto trading and a set of **workflows** to guide the process. The main idea is to separate active trading from routine monitoring, using the CLI as a tool to execute a well-defined plan.

---

## 📈 AI-Powered Workflows

This project is built around two key workflows that are executed by an AI assistant. The AI uses the provided CLI commands to systematically manage your crypto portfolio, turning high-level strategy into concrete actions.

### 1. Active Trading Workflow (`crypto-workflow.md`)

This workflow is used when you want to analyze the market and execute new trades. The AI will:

1.  **Gather Intelligence**: It runs a full analysis of your account, open orders, and relevant market indicators using the `account` and `analysis` commands.
2.  **AI-Powered Analysis**: The AI uses the integrated Perplexity AI service to generate comprehensive portfolio analysis with protection assessment and balance analysis.
3.  **Validate Recommendations**: Before placing any trades, the AI validates recommendations using automated scoring and order simulation to prevent errors.
4.  **Execute Precisely**: The AI verifies the correct order size precision using the `exchange lotsize` command and validates orders using `validate order-simulation`.
5.  **Manage Risk**: As soon as a buy order is filled, the AI automatically executes the "Post-Fill Drill": it confirms your new asset balance and immediately places a corresponding OCO (One-Cancels-the-Other) order to protect your new position.

To initiate this workflow, you can instruct the AI:
> "Let's start a new trading session. Please follow the steps in @crypto-workflow.md"

### 2. Portfolio Monitoring Workflow (`crypto-monitoring-workflow.md`)

This is a routine checklist the AI runs to ensure all your active positions are safe and aligned with your plan. The AI will:

1.  **Get a Snapshot**: It fetches the current state of your portfolio and all open orders.
2.  **AI-Powered Monitoring**: Uses `ai analyze-portfolio --mode monitoring` for quick portfolio health checks.
3.  **Protection Analysis**: Automatically analyzes protection coverage using the built-in protection analyzer.
4.  **Take Corrective Action**: If an unprotected asset is found, the AI automatically executes protective measures.
5.  **Report Findings**: The AI provides a concise summary of its findings and any actions taken.

To run this check, you can tell the AI:
> "Time for a portfolio check. Let's run the @crypto-monitoring-workflow.md"

---

## 🚀 Getting Started

Follow these steps to get the project up and running.

### Prerequisites

-   Python 3.10+
-   A Binance Account with API Key and Secret
-   Perplexity API Key (for AI analysis features)

### Installation & Configuration

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/crypto-ai-assistant/crypto-ai-assistant.git
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
    -   Add your API keys:
        ```env
        BINANCE_API_KEY="your_api_key_here"
        BINANCE_API_SECRET="your_api_secret_here"
        PERPLEXITY_API_KEY="your_perplexity_api_key_here"
        ```

5.  **Review Application Settings**:
    -   Customize behavior in `src/core/config.toml`. A default configuration is provided for analysis parameters and display values.

---

## 🛠️ Command Reference

These are the low-level commands used to execute the steps defined in the workflows.

### General Help
`crypto-ai-assistant --help`

### Account Commands
-   **Info**: `crypto-ai-assistant account info [--min-value <VALUE>]`
-   **Orders**: `crypto-ai-assistant account orders [--symbol <SYMBOL>]`
-   **History**: `crypto-ai-assistant account history <SYMBOL> [--limit <NUMBER>]`

### Order Commands
-   **Place Market**: `crypto-ai-assistant order place-market <SYMBOL> <SIDE> <QUANTITY>`
-   **Place Limit**: `crypto-ai-assistant order place-limit <SYMBOL> <SIDE> <QUANTITY> <PRICE>`
-   **Place OCO**: `crypto-ai-assistant order place-oco <SYMBOL> <QUANTITY> <PRICE> <STOP_PRICE>`
-   **Cancel**: `crypto-ai-assistant order cancel <order|oco> <SYMBOL> <ORDER_ID>`

### Exchange Commands
- **Lot Size**: `crypto-ai-assistant exchange lotsize <SYMBOL>`
- **Exchange Info**: `crypto-ai-assistant exchange info <SYMBOL>`

### Analysis Commands
-   **Indicators**: `crypto-ai-assistant analysis indicators --coins "BTC,ETH,SOL"`

### AI Commands (New Features)
-   **Portfolio Analysis**: `crypto-ai-assistant ai analyze-portfolio [--mode strategy|monitoring] [--parallel]`
-   **Market Timing**: `crypto-ai-assistant ai market-timing`
-   **Update Plan**: `crypto-ai-assistant ai update-plan <ANALYSIS_TEXT> [--execute]`

### Validation Commands (New Features)
-   **AI Recommendations**: `crypto-ai-assistant validate ai-recommendations <JSON_RECOMMENDATIONS>`
-   **Order Simulation**: `crypto-ai-assistant validate order-simulation <SYMBOL> <SIDE> <TYPE> <QUANTITY> [--price] [--stop-price]`
-   **Balance Check**: `crypto-ai-assistant validate balance-check <ASSET>`

---

## 🛠️ Development Setup

### Quick Start

```bash
# One-command setup
python scripts/setup-dev.py

# Activate virtual environment (Windows)
.\venv\Scripts\Activate.ps1

# Run quality checks
make check
```

### Development Commands

```bash
# Setup and environment
make setup          # Complete development environment setup
make install        # Install dependencies only

# Quality checks (recommended workflow)
make fix            # Auto-fix formatting and linting issues
make check          # Run all staged quality checks
make test           # Run tests with coverage

# Individual checks
make lint           # Run linting only
make type           # Run type checking only
make test-fast      # Fast test run

# Maintenance
make clean          # Clean build artifacts
make help           # Show all available commands
```

### Advanced Usage

```bash
# Staged quality pipeline (recommended)
python scripts/staged-check.py                    # Run all stages
python scripts/staged-check.py --stage env        # Environment check only
python scripts/staged-check.py --stage format --fix  # Format with auto-fix
python scripts/staged-check.py --help             # See all options

# Development shortcuts
python scripts/dev.py test-fast    # Fast tests
python scripts/dev.py cov          # Coverage report
python scripts/dev.py clean        # Clean caches
```

For complete development workflow guidance, see the project's development rules in `.cursorrules`.

---

## 🧪 **Development Pipeline Status**

**Latest Update**: Work In Progress ⚠️ (2024-01)

### **Current Pipeline Health**
```
Stage 1: Environment Verification  ✅ PASSING (100%)
  ├─ Python 3.12.6                ✅ OK
  ├─ Core imports                  ✅ OK
  └─ Dev tools available           ✅ OK

Stage 2: Code Formatting & Linting ⚠️  NEEDS ATTENTION
  ├─ Auto-formatting               ❌ 4 files need reformatting
  └─ Linting                       ⚠️  See format output

Stage 3: Type Checking             🔄 NOT TESTED
  ├─ MyPy analysis                 ⏳ Pending format fixes
  └─ Type stub resolution          ⏳ Pending format fixes

Stage 4: Tests & Coverage           ❌ REQUIRES ATTENTION
  ├─ Test execution                ❌ 1 failing test
  └─ Coverage at 34% vs 85% target ❌ Coverage recovery needed
```

### **🚨 Active Issues**
- **Formatting**: 4 files require reformatting (`src/core/protection_analyzer.py`, `tests/core/test_ai_integration.py`, `tests/core/test_perplexity_service.py`, `tests/core/test_protection_analyzer.py`)
- **Tests**: 1 failing test in `test_ai_integration.py` (string format assertion issue)
- **Coverage**: Recovery needed from 34% to target 85%

### **🚀 Quick Development Commands**
```bash
# Fix formatting issues
python scripts/staged-check.py --stage format --fix

# Individual stages
python scripts/staged-check.py --stage env      # Environment check
python scripts/staged-check.py --stage format  # Formatting + linting
python scripts/staged-check.py --stage types   # Type checking
python scripts/staged-check.py --stage tests   # Tests + coverage
```

---

##  Project Structure
```
.
├── crypto-workflow.md          # Strategic trading workflow
├── crypto-monitoring-workflow.md  # Portfolio monitoring workflow
├── current_plan.md            # AI-generated trading plans
├── src/
│   ├── api/                   # Binance API client and models
│   │   ├── client.py          # Core Binance API client
│   │   ├── enums.py           # Order types, sides, etc.
│   │   ├── exceptions.py      # API-specific exceptions
│   │   └── models.py          # TypedDict models
│   ├── core/                  # Core business logic
│   │   ├── account.py         # Account management
│   │   ├── ai_context_generator.py  # AI context generation
│   │   ├── ai_integration.py  # AI integration utilities
│   │   ├── config.py          # Configuration loading
│   │   ├── config.toml        # Application configuration
│   │   ├── exchange.py        # Exchange information
│   │   ├── history.py         # Trade history
│   │   ├── indicators.py      # Technical indicators
│   │   ├── orders.py          # Order management
│   │   ├── order_validator.py # Order validation
│   │   ├── perplexity_service.py  # Perplexity AI integration
│   │   ├── precision_formatter.py  # Price/quantity formatting
│   │   ├── protection_analyzer.py  # Portfolio protection analysis
│   │   └── validation_service.py   # AI recommendation validation
├── tests/                     # Unit and integration tests
├── scripts/                   # Development tools
│   ├── setup-dev.py          # Environment setup
│   └── staged-check.py        # Quality pipeline
├── .env                       # API keys (not committed)
└── pyproject.toml            # Project metadata and dependencies
```

---

## 🆕 **Key Features**

### **AI-Powered Analysis**
- **Portfolio Analysis**: Comprehensive AI-driven portfolio assessment using Perplexity
- **Protection Coverage**: Automated analysis of position protection adequacy
- **Balance Analysis**: Smart balance utilization with commitment tracking
- **Market Timing**: AI-powered entry/exit timing recommendations

### **Advanced Validation**
- **Order Simulation**: Test orders before execution to prevent errors
- **AI Recommendation Scoring**: 100-point automated validation system
- **Balance Checking**: Effective balance analysis accounting for existing orders
- **Exchange Compliance**: Automatic lot size and precision validation

### **Risk Management**
- **OCO Order Integration**: Automated protective order placement
- **Position Protection**: Real-time protection coverage assessment
- **Immediate Fill Prevention**: Validation to prevent catastrophic pricing errors
- **Commitment Tracking**: Understand true available vs committed balance

---

## ⚠️ Disclaimer

Trading cryptocurrencies involves significant risk. This tool is for educational and informational purposes only. The author is not responsible for any financial losses incurred through the use of this software. Always do your own research and trade responsibly.
