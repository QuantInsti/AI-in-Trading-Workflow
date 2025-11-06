# Multi-Agent System for an IB Stock Setup

**For Educational and Paper Trading Purposes Only**

The content, code, and strategies provided in this repository are for educational and informational purposes only. They are not intended as financial advice, investment recommendations, or a solicitation to buy or sell any securities.

**Trading financial markets involves substantial risk, and you are solely responsible for any decisions you make. The authors and contributors of this repository assume no liability for any financial losses you may incur.**

Always conduct your own thorough research and risk assessment before deploying any trading strategy in a live environment. You should start by using these examples with paper trading accounts.

---

This project demonstrates the use of a multi-agent AI system to generate trading signals for an Interactive Brokers (IB) stock trading setup framework.

The system uses a team of specialized AI agents to analyze a stock by combining real-time news sentiment with market data to produce a trading recommendation.

## Core Components

*   **`ibkr-stock/`**: A Python package that represents a trading setup framework. It is designed to handle the mechanics of trading, such as fetching data, managing positions, and executing orders with Interactive Brokers. The strategy logic is defined in `ibkr-stock/user_config/AI_strategy.py`. This trading setup can be found in our repository called [QuantInsti-Live-Algo-Trading-Setups](https://github.com/QuantInsti/QuantInsti-Live-Algo-Trading-Setups/tree/master/ibkr-stock)

*   **`client_example.py`**: A standalone Python script that showcases the core multi-agent logic. It demonstrates how the agents collaborate to produce a trading signal. This script serves as the blueprint for the logic that is integrated into the `ibkr-stock` framework. This Python file comes from our another example on [gemini_fullstack_langchain/example_01_create_multi_agent_system](https://github.com/QuantInsti/AI-in-Trading-Workflow/tree/main/gemini_fullstack_langgraph/example_01_create_multi_agent_system)

*   **`how_to.md`**: A guide that explains how to use a tool like the Gemini CLI to integrate the logic from `client_example.py` into the `AI_strategy.py` file within the trading framework.

## Agent Workflow

The system follows a three-step process to generate a trading signal:

1.  **News Gathering**: The first agent scans for the latest news related to a specific stock.

2.  **Sentiment Analysis**: The second agent analyzes the news summaries and assigns a sentiment score, ranging from -1 (very bearish) to +1 (very bullish).

3.  **Strategy Generation**: The final agent takes the sentiment score and the CBOE Volatility Index (VIX) as input. It then generates a structured JSON recommendation with three keys:
    *   `action`: 'BUY', 'SELL', or 'HOLD'
    *   `confidence`: A score from 0.0 to 1.0
    *   `reasoning`: An explanation for the decision.

This workflow is orchestrated within the `get_signal` function in `ibkr-stock/user_config/AI_strategy.py`.

## Getting Started

Before you proceed, don't forget to check the gemini folder's [README](https://github.com/QuantInsti/AI-in-Trading-Workflow/blob/main/gemini_cli/README.md) file.

### Prerequisites

*   Python 3.12
*   Git
*   An Interactive Brokers (IB) account and TWS/IB Gateway running (for live trading).
*   A Gemini API Key

### Step 1: Clone the Repository

First, clone this repository to your local machine:

```bash
git clone https://github.com/QuantInsti/AI-in-Trading-Workflow.git
```

### Step 2: Navigate to the Directory

Change to the example's directory in your Anaconda Prompt or terminal.

For Windows users:
```bash
cd \path_to\AI-in-Trading-Workflow\gemini_cli\example_02_run_multi_agent_system_on_IB_stock_setup
```

For Mac/Linux users:
```bash
cd /path_to/AI-in-Trading-Workflow/gemini_cli/example_02_run_multi_agent_system_on_IB_stock_setup
```

Where "path_to" is the address that corresponds to the PC location of your downloaded cloned repository

### Step 3: Set up the Environment

We recommend using a Conda environment for these examples.

**1. Activate the environment:**
From your terminal (or Anaconda Prompt on Windows), run:
```bash
conda activate gemini_cli_env
```

### Step 4: Set up the Environment as per the stock setup

You should follow the instructions of the stock setup located in the [README]() file of the setup repository.

### Step 5: Set up Your Gemini API Key

Set your Gemini API Key as an environment variable.

**For Windows (in Anaconda Prompt):**

```bash
set GEMINI_API_KEY="YOUR_ACTUAL_GEMINI_API_KEY"
```

**For macOS and Linux (in a terminal with an activated Anaconda environment):**

```bash
export GEMINI_API_KEY="YOUR_ACTUAL_GEMINI_API_KEY"
```

### Step 6: Create the AI Strategy File

The trading logic is defined in `ibkr-stock/user_config/AI_strategy.py`. To create this file, follow the instructions in `how_to.md`, which explains how to adapt the logic from `client_example.py` into the required format for the trading framework.

### Step 7: Run the Trading System

Once `AI_strategy.py` has been created and is in the `user_config` directory, you will need to run the main application within the `ibkr-stock` package. This typically involves navigating to the `ibkr-stock` directory and executing its main script (e.g., `python main.py` or similar, depending on the framework's entry point). The framework will then call the `get_signal` function to get trading signals from the multi-agent system and execute trades.

This modular design separates the AI-driven analysis from the trading mechanics.

*Note: This README provides an overview of the multi-agent system. To understand how the `AI_strategy.py` file was created from `client_example.py`, please refer to the `how_to.md` file.*

---

### Next Steps and Experimentation

This project is a blueprint for integrating an AI agent into a trading framework. To deepen your understanding, we strongly recommend the following activities:

*   **Tweak the Prompts:**
    *   Modify the prompts in `AI_strategy.py`. For example, change the `TradingStrategyAgent`'s prompt to be more risk-averse when the VIX is high.
    *   Change the `SentimentAnalyzerAgent`'s prompt to output the score on a different scale (e.g., 1-10) and adjust the code to handle the new format.

*   **Extend the Project:**
    *   **Add a New Agent:** This is a key learning exercise. Create a `TechnicalAnalysisAgent` that calculates an indicator (like RSI or MACD) using a library like `ta`. Pass this new data point to the `TradingStrategyAgent` and modify its prompt to include this technical indicator in its decision-making process.
    *   **Improve State Management:** The current example is stateless (it makes a decision based only on current data). Modify the `get_signal` function to remember the previous recommendation and include that information in the prompt for the current decision.
