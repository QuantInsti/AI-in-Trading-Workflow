# Multi-Agent Sentiment Analysis System for Trading

**For Educational and Paper Trading Purposes Only**

This repository provides content, code, and strategies for educational and informational purposes only. We do not intend for them to be financial advice, investment recommendations, or a solicitation to buy or sell any securities.

**Trading financial markets involves substantial risk, and you are solely responsible for any decisions you make. The authors and contributors of this repository assume no liability for any financial losses you may incur.**

Always conduct your own thorough research and risk assessment before deploying any trading strategy in a live environment. You should start by using these examples with paper trading accounts.

---

This project demonstrates a multi-agent system built with LangChain and powered by Gemini. It uses a group of AI agents that work together to gather news, analyze market sentiment, and produce a final trading recommendation.

A key feature of this example is its ability to generate a detailed **PDF report** after each analysis. This report provides a complete audit trail of the agent's decision-making process, summarizing the inputs, agent contributions, and the final output.

## Agent Workflow

The system operates as a pipeline, where each agent completes a specific task before passing its results to the next.

1.  **News Gatherer Agent**: Finds the latest news for the target stock.
2.  **Sentiment Analyzer Agent**: Reads the news and assigns a sentiment score from -1 (very bearish) to +1 (very bullish).
3.  **Market Data Fetcher**: Fetches the CBOE Volatility Index (VIX) to measure market volatility.
4.  **Trading Strategy Agent**: The final agent in the chain. It takes the sentiment score and VIX value and produces a structured JSON recommendation.
5.  **PDF Report Generation**: After the analysis is complete, the script generates a PDF file (e.g., `TSLA_trading_report_YYYYMMDD_HHMMSS.pdf`) that contains a full summary of the workflow.

## Directory Contents

*   **`client_example.py`**: The main script that defines and runs the multi-agent workflow and generates the PDF report.
*   **`how_to.md`**: A guide that explains how to use an AI assistant like the Gemini CLI to generate a similar agent-based system.
*   **`requirements.txt`**: A list of Python dependencies required to run the script.

## Getting Started

### 1. Prerequisites

Before running this example, you must set up the `gemini-fullstack-langgraph-quickstart` environment. Please follow all the installation and setup instructions provided at the official repository: [https://github.com/google-gemini/gemini-fullstack-langgraph-quickstart](https://github.com/google-gemini/gemini-fullstack-langgraph-quickstart).

Once the environment is fully configured, you can use the Gemini CLI with the library to generate the `client_example.py` file, as described in the `how_to.md` guide.

### 2. Install Dependencies

Install the required Python libraries using the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

### 3. Run the Example

Once the prerequisites are met, first, export your Gemini API Key:

```bash
export GEMINI_API_KEY="YOUR_ACTUAL_GEMINI_API_KEY"
```

Then, run the example from your terminal:

```bash
python client_example.py
```

The script will execute the agent workflow, print the final trading recommendation to the console, and save a detailed PDF report in the same directory.

### 4. Building Your Own

The `how_to.md` file contains a tutorial on how to use conversational AI to build a similar system. It provides example prompts and instructions for guiding an AI assistant to write the agent code.

*Note: This README provides an overview of the multi-agent system. To understand how the `client_example.py` script was generated, please refer to the `how_to.md` file.*

---

### Next Steps and Experimentation

This project serves as a foundational example of a multi-agent system. To deepen your understanding, we strongly recommend the following activities:

*   **Tweak the Prompts:**
    *   Modify the prompts in `client_example.py`. For instance, instruct the `TradingStrategyAgent` to be more cautious and favor 'HOLD' when the VIX is above a certain threshold (e.g., 30).
    *   Change the `SentimentAnalyzerAgent`'s prompt to output its reasoning alongside the score, and modify the code to parse the more complex output.

*   **Extend the Project:**
    *   **Add a New Agent:** A highly valuable exercise is to add a new agent to the workflow. Create a `TechnicalAnalysisAgent` that uses `yfinance` to calculate a technical indicator (e.g., RSI or MACD). Integrate it into the agent chain so this indicator is passed to the final `TradingStrategyAgent`.
    *   **Introduce Memory:** The current system is stateless. Modify the `main()` function to save the last recommendation to a file. In the next run, load that recommendation and pass it as context to the `TradingStrategyAgent` so it can make more informed, sequential decisions.
