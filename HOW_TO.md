# A Practical Workflow for AI in Trading

Integrating Large Language Models (LLMs) and agentic systems into a trading workflow can be a complex and fragmented process. This guide provides a structured, opinionated path that connects the self-contained examples in this repository into a single, coherent workflow.

Following this guide provides several key benefits:

*   **From Concept to Code, Faster:** Learn how to use AI as a development partner to rapidly prototype a trading idea and generate a complete, backtestable Python script, significantly reducing initial development time.
*   **Build Confidence Through Backtesting:** Understand how to use the generated code in a practical backtesting environment to validate your strategy's logic and performance before risking capital.
*   **Choose Your Deployment Path:** Gain clarity on the different ways to deploy an AI strategy. This guide illuminates two powerful options: integrating your logic into a robust, pre-built trading framework or building a fully autonomous, standalone trading bot from the ground up.

To get started, first clone the repository:

```bash
git clone https://github.com/QuantInsti/AI-in-Trading-Workflow.git
```

This workflow empowers you to systematically build, test, and deploy AI-driven trading strategies with confidence.

---

## The Trader's Workflow

This guide breaks down the process into three logical steps, from initial idea to final deployment.

### 1. From Idea to Code

The first challenge in algorithmic trading is translating a conceptual trading idea into a functional, testable script. This repository offers two distinct approaches to accelerate this process:

*   **For a Low-Code, Visual Approach:** Start with the [**Dify Agent Builder**](./Dify/example_01_create_code_builder/). This example guides you through using a visual interface to chain multiple AI agents together. The final result is a system that takes a simple English description of a strategy and automatically generates a complete Python backtesting script, including advanced considerations like risk management and transaction costs.

*   **For a Developer-Centric, CLI Approach:** If you prefer working in a terminal, use the [**Gemini CLI Backtesting Example**](./gemini_cli/example_01_create_backtesting_code/). This `how_to.md` file shows you the exact prompts to use with the Gemini CLI to generate a Python script for a moving average crossover strategy, complete with data downloading, parameter optimization, and PDF reporting.

### 2. Backtesting the Strategy

With a strategy script in hand, the next critical step is to validate its performance on historical data.

*   **Validate Your Generated Script:** The [**Gemini CLI Backtesting Example**](./gemini_cli/example_01_create_backtesting_code/) provides a complete, runnable backtesting environment. You can use the generated script as a template to test your own strategies, analyze performance metrics like the Sortino Ratio and Maximum Drawdown, and visualize the results before moving forward.

### 3. Deploying the Strategy: Two Paths

Once you have a backtested and validated strategy, the next step is to deploy it. This repository offers two distinct paths for deploying your AI-driven strategies into a trading environment:

*   **Path A (Framework Integration):** For users who prefer integrating their AI logic into a robust, pre-existing trading engine, this path demonstrates how to connect an AI-generated strategy to **QuantInsti's `ib_stock_setup` framework**. This approach is ideal for those who want to leverage a battle-tested system for order management, data handling, and risk controls, allowing them to focus purely on the strategy's logic. You can find this implementation in the [**AI Strategy Integration Example**](./gemini_cli/example_02_run_multi_agent_system_on_IB_stock_setup/).

*   **Path B (Standalone Autonomous Systems):** For users who want to build a more advanced, fully autonomous agentic system from scratch, without relying on a pre-existing trading framework, this path showcases examples of complete, self-contained trading bots. This approach offers maximum flexibility and is suited for developing sophisticated, end-to-end systems. We feature two distinct styles of standalone bots:
    *   The Fully Autonomous Bot: The **Agentic Portfolio Manager** (./LLMs/example_02_Agentic_AI_based_Portfolio_manager_using_Alpaca_API/) is a "set-it-and-forget-it" system. It runs continuously, performs its own analysis, allocates capital, and executes trades without human intervention. This is ideal for traders who want to fully automate a strategy.
    *   The Interactive Trading Assistant: The **Natural Language Trading Server** (./LLMs/example_01_create_ib_mcp_server_in_python/) acts as a powerful assistant that you control. It allows you to execute complex trades and query your Interactive Brokers account using plain English commands. This is perfect for traders who want to leverage AI for execution and analysis while maintaining direct, command-by-command control over their trading activity.
