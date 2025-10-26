# AI in Trading: From Agents to Execution

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](CONTRIBUTING.md)

A comprehensive repository demonstrating how to build and deploy sophisticated algorithmic trading solutions using modern AI, from multi-agent systems to production-ready execution frameworks.
---

## 🎯 Objective

The primary objective of this repository is to provide a concrete, end-to-end example of using modern AI agents for trading. It connects the theoretical application of LLMs to a practical, executable trading bot.

The project demonstrates the following workflow:

1.  **Learn**: Discover the landscape of modern AI tools for trading.
2.  **Build**: Follow tutorials to construct AI agent systems for market analysis.
3.  **Integrate**: Plug AI-driven logic into a professional-grade trading framework.
4.  **Deploy**: Run a fully automated, AI-powered trading bot.

This project will be updated with new implementations and tutorials to reflect advancements in the field.

---

## 📂 Repository Structure & Key Components

This repository is organized into modules based on the AI tools and platforms they demonstrate. We will continue to expand this structure as we incorporate new technologies.

### 1. Gemini CLI
- **Location**: [gemini_cli/](https://github.com/QuantInsti/AI-in-Trading-Workflow/tree/main/gemini_cli)
- **Description**: This section contains the core end-to-end implementation and related guides.
    - **Production Trading Framework (`ib_stock_setup`)**: A professional Python framework for automated stock trading via the Interactive Brokers (IB) API.
    - **AI-Powered Strategy (`AI_strategy.py`)**: A pluggable multi-agent strategy using Gemini that trades based on news sentiment and volatility analysis.
    - **Developer Guides**: Practical examples for using the Gemini CLI for development tasks.

### 2. Gemini FullStack LangChain
- **Location**: [gemini_full_stack_langchain/](https://github.com/QuantInsti/AI-in-Trading-Workflow/tree/main/gemini_fullstack_langchain)
- **Description**: A detailed, step-by-step tutorial on coding the multi-agent news analysis system from scratch, which provides the foundation for the `AI_strategy.py` file in our setups to trade live with LLMs!

### 3. LLMs
- **Location**: [LLMs/](https://github.com/QuantInsti/AI-in-Trading-Workflow/tree/main/LLMs)
- **Description**: Detailed examples on how to create an agentic-based portfolio manager and an MCP server using the Interactive Brokers API with LLMs!
  
### 4. More Curated List of AI Trading Tools coming soon!
- We're currently engaged in creating more use cases of AI tools and platforms. Stay tuned!

---

## 🚀 Featured Implementation: AI News-Sentiment Trader

The main example in this repository demonstrates the integration of the AI strategy with the trading framework. By combining the `ib_stock_setup` and the `AI_strategy.py`, you can deploy a bot that:
1.  Connects to Interactive Brokers.
2.  Fetches the latest financial news for a target stock.
3.  Uses a multi-agent system to analyze sentiment and volatility.
4.  Makes autonomous `BUY`/`SELL` decisions based on the AI's analysis.
5.  Executes and manages the trade according to pre-set risk parameters.

This demonstrates a complete workflow, from AI-driven analysis to automated trade execution.

---

## 🌱 Future Implementations

This repository is actively maintained and will be expanded with more implementations, including but not limited to:
-   Advanced quantitative strategies using AI.
-   Integrations with other brokerages and data sources.
-   Tutorials on new and emerging agentic frameworks.
-   Alternative asset classes like crypto and forex.

Stay tuned for updates!

---

## 🤝 How to Contribute

Contributions are welcome! Whether it's reporting a bug, suggesting a new feature, improving documentation, or submitting a new implementation, your help is appreciated. Please refer to the `CONTRIBUTING.md` guide within the `ib_stock_setup` directory for initial guidelines.

## 📄 License

This project is licensed under the Apache License 2.0. See the `LICENSE.txt` file in the `ib_stock_setup` directory for details.
