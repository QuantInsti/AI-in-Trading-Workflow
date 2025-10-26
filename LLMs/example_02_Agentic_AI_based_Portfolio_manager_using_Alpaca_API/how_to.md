# How to Build an AI Portfolio Manager with an LLM Assistant

This guide outlines the process of building an agentic AI portfolio
manager using an LLM assistant like Gemini. The following prompts can be
used to guide the AI to write the script from scratch.

The goal is to create a Python script that acts as an autonomous, continuously running trading bot capable of analyzing stocks, managing a portfolio, and executing trades at intraday frequencies.

---

## Disclaimer: LLMs are Probabilistic

The code and prompts provided in this guide are for educational purposes. Due to the probabilistic nature of Large Language Models (LLMs), you may not get the exact same output even when using the identical prompts. The generated code can vary. The Python scripts included in this repository represent a final, working version that may have required multiple iterations and refinements.

---

### System Architecture

The system uses a "graph" where different "nodes" act as specialists. This entire workflow runs in a continuous loop during market hours.

1.  **The Analyst:** Gathers news and market data to form a preliminary
    "BUY" or "HOLD" opinion on multiple stocks.
2.  **The Portfolio Manager:** Takes the "BUY" recommendations and
    decides how to allocate capital between them.
3.  **The Trader:** Connects to a brokerage (Alpaca) and executes the
    trades based on the manager's decisions.
4.  **The Email Notifier:** Sends an email summary of the day's actions.

---

### Step 1: Setting Up the Project

First, set up the environment by creating a file for secret keys and
installing the necessary Python libraries.

#### **Prompting for the Setup:**

1.  "Please list the Python libraries required for a project that uses
    LangChain/LangGraph, Google's Gemini for the AI, Alpaca for the
    trading API, Tavily for web searches, pandas for data, scikit-learn
    for a model, and quantstats for reports."
2.  "Also, show me how to create a `.env` file to store API keys for
    Alpaca, Gemini, and a Gmail App Password for sending email
    notifications."

The AI will provide a `requirements.txt` file and a template for the
`.env` file.

---

### Step 2: Creating the Agent's Tools

Create a set of Python functions that the agent can call to interact
with the outside world.

#### **Prompting for the Tools:**

> "Please write a series of Python functions to do the following:"

1.  `load_portfolio_state` **&** `save_portfolio_state`**:** These two
    functions should read from and write to an Excel file named
    `portfolio_state.xlsx`. This will serve as the agent's long-term
    memory.
2.  `web_search_for_news`**:** A function that takes a stock ticker and
    uses the `TavilySearch` tool to find recent financial news.
3.  `fetch_historical_data`**:** A function that takes a ticker and uses
    the `alpaca-trade-api` to get the last 90 days of stock data from
    the IEX feed.
4.  `get_market_schedule`**:** A function that connects to the Alpaca API
    to get the market calendar for the next few days, including the open
    and close times for each day in the user's local timezone.
5.  `send_email_notification`**:** A function that uses `smtplib` to
    send an email summary and attach a file.

---

### Step 3: Building the Specialist Nodes

Create the core logic for each specialist. Each specialist is a Python
function that will become a "node" in the AI graph. The prompts for these nodes remain largely the same as their core responsibilities haven't changed.

#### **Prompting for the Analyst Node:**

> "Please write a Python function called `analysis_node` that takes a
> list of stock tickers. For each ticker, it should:
> 1. Use the `fetch_historical_data` tool to get market data.
> 2. Use the `web_search_for_news` tool to get recent news.
> 3. Perform a **qualitative analysis**: Use the Gemini LLM to
> read the news and decide if the sentiment is a "BUY" (1) or "HOLD"
> (0).
> 4. Perform a **quantitative analysis**: Use `scikit-learn` to
> train a `RandomForestClassifier` on the historical data (using SMAs
> and RSI as features) to predict if the next day's price will go up (1)
> or down (0).
> 5. Combine the signals: The final signal should be "BUY"
> (1) only if **both** the qualitative and quantitative analyses agree.
> 6. It should return the signals and news for all tickers."

#### **Prompting for the Portfolio Manager Node:**

> "Next, write a function `portfolio_agent_node` that receives the
> analysis from the previous step. Its function is as follows:
> 1. It should look at all the stocks that received a "BUY" signal.
> 2. It will then use the Gemini LLM as its "brain," feeding it all the news summaries for the recommended stocks.
> 3. The prompt to the LLM should be: 'You are a portfolio manager.
> Based on this news, allocate weights to these stocks. The weights must
> sum to 1.0. Respond with only a JSON object.'
> 4. If the LLM fails to provide valid JSON, it should fall back to an equal-weight allocation.
> 5. The function should return a dictionary of the final portfolio
> weights (e.g., `{'AAPL': 0.6, 'MSFT': 0.4}`)."

#### **Prompting for the Trader Node:**

> "Now, write a function `execution_node` that receives the portfolio
> weights. This function needs to:
> 1. Connect to the Alpaca API.
> 2. **Liquidate positions:** It should submit an order to `close_all_positions()` to
> rebalance.
> 3. **Place new orders:** It should loop through the
> portfolio weights and submit new 'market' orders using the `notional`
> (dollar amount) parameter.
> 4. It should also be able to add a
> `stop_loss` and `take_profit` to the orders if risk management
> parameters are provided.
> 5. Finally, it should update the agent's
> memory (the portfolio state) with the new trades and account equity."

#### **Prompting for the Email Notifier Node:**

> "Finally, create an `email_notification_node`. This function should:
> 1.  Generate a performance report using a `create_performance_report` tool.
> 2.  Construct an email subject and body that summarizes the agent's actions, including the final portfolio weights and the execution log.
> 3.  Call the `send_email_notification` tool to send the email with the performance report attached."

---

### Step 4: Assembling and Running the System

With all the specialists created, assemble them into a continuous workflow.

#### **Prompting for the Graph and Main Loop:**

> "Please write the final part of the script to do the following:
> 1. Use `langgraph.StateGraph` to create a new workflow and add the specialist nodes in the correct sequence: `analysis` -> `portfolio_allocator` -> `executor` -> `email_notifier`.
> 2. Create a main `engine_loop` function that runs a continuous `while True` loop.
> 3. Inside the loop, it should:
>    a. Get the market schedule.
>    b. If the market is closed, calculate the time until the next market open and sleep.
>    c. If the market is open, enter another `while` loop that runs until the market closes for the day.
>    d. Inside this inner loop, it should invoke the graph to run the full trading process.
>    e. After each run, it should sleep for a duration based on a `data_frequency` parameter (e.g., '5min').
> 4. Create a separate `main.py` file with an `if __name__ == "__main__":` block to call the `engine_loop` with a sample list of tickers and a `data_frequency`."