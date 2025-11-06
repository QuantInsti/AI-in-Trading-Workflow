# Agentic AI Portfolio Manager

**For Educational and Paper Trading Purposes Only**

This repository provides content, code, and strategies for educational and informational purposes only. We do not intend for them to be financial advice, investment recommendations, or a solicitation to buy or sell any securities.

**Trading financial markets involves substantial risk, and you are solely responsible for any decisions you make. The authors and contributors of this repository assume no liability for any financial losses you may incur.**

Always conduct your own thorough research and risk assessment before deploying any trading strategy in a live environment. You should start by using these examples with paper trading accounts.

---

This project provides an automated, continuously running trading bot for managing a portfolio. It uses a team of AI agents built with LangGraph to analyze the market, build a portfolio, and execute trades using the Alpaca API. You can configure it to run at various intraday frequencies (e.g., every 5 minutes) or daily.

## How It Works

This trading bot is based on **hybrid intelligence**, combining different types of analysis. It runs in a continuous loop during market hours and uses a team of specialized AI agents for each trading decision:

1.  **The Analyst Agent:** For each stock in the portfolio, this agent performs two tasks:
    *   **Qualitative Analysis:** It uses the **Tavily Search API** to find the latest news and then uses **Google's Gemini model** to determine the sentiment.
    *   **Quantitative Analysis:** It uses a **Random Forest model** trained on historical data and technical indicators (e.g., SMA and RSI) to generate a trading signal.
2.  **The Portfolio Agent:** This agent takes the list of stocks with "BUY" signals and uses the Gemini model to allocate capital (i.e., portfolio weights) based on the news.
3.  **The Execution Agent:** This agent connects to the **Alpaca API** to check the account, sell old positions, and place new orders. It can also add stop-loss and take-profit orders.
4.  **The Email Notifier Agent:** After each trading action, this agent sends an email report (using `quantstats`) and saves the current state of the portfolio to an Excel file.

## Core Agent Prompts

The following prompts guide the AI agents' decisions:

**1. Analyst Agent Prompt (Qualitative Signal):**
This prompt gets a sentiment-based signal from the news.
```
"You are a financial analyst. Based on the news, provide a signal (1 for BUY, 0 for HOLD). Respond with only the number."
```

**2. Portfolio Agent Prompt (Capital Allocation):**
This prompt helps the agent decide how to split the portfolio among the stocks that have a "BUY" signal.
```
"You are a portfolio manager. Based on the provided news summaries for several stocks, allocate portfolio weights. The stocks to allocate are: {tickers}. The weights must sum to 1.0. Respond with a JSON object where keys are ticker symbols and values are their weights (e.g., {{'AAPL': 0.6, 'MSFT': 0.4}})."
```

## Getting Started

### Prerequisites

*   Python 3.12
*   Git
*   An Alpaca Markets account (paper trading recommended for testing).
*   A Google Gemini API Key
*   A Tavily Search API Key
*   A Gmail account with 2-Step Verification enabled and an App Password generated (for email notifications).

### Step 1: Clone the Repository

First, clone this repository to your local machine:

```bash
git clone https://github.com/QuantInsti/AI-in-Trading-Workflow.git
```

### Step 2: Navigate to the Directory

Change to the example's directory in your Anaconda Prompt or terminal.

### Step 3: Install Dependencies

We recommend using a Conda environment for this project:

```bash
conda create --name trading_agent python=3.12
conda activate trading_agent
```

Install the required Python libraries using the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

### Step 4: Configure API Keys and Environment Variables

You need to create a file named **`.env`** in your project directory (the same location as `agentic_AI_portfolio_manager.py`) and add all required API keys and credentials listed below.

#### ** For Mac/Linux Users**

1.  **Open your terminal** and navigate to the project directory.
2.  Use the `touch` command to create the file:
    ```bash
    touch .env
    ```
3.  Use a text editor like `nano` or `vi` (or your preferred editor) to open and edit the file:
    ```bash
    nano .env
    ```
4.  **Copy and paste** the contents below into the `.env` file, replacing the placeholder values with your actual keys and credentials:

#### ** For Windows Users**

1.  **Open your File Explorer** and navigate to the project directory.
2.  **Right-click** in the folder and select **New \> Text Document**.
3.  Name the new file **`.env`** (make sure to include the preceding dot and remove the `.txt` extension). You may need to enable **"File name extensions"** in the **View** tab of File Explorer to rename it correctly.
4.  **Open the `.env` file** with a text editor (like Notepad, VS Code, or Notepad++).
5.  **Copy and paste** the contents below into the `.env` file, replacing the placeholder values with your actual keys and credentials:

#### ** `.env` File Content (Required for both)**

```ini
# Google Gemini API Key (REQUIRED)
GOOGLE_API_KEY="your-google-ai-api-key"

# Tavily Search API Key (REQUIRED)
TAVILY_API_KEY="your-tavily-api-key"

# Alpaca Paper Trading Keys (REQUIRED)
APCA_API_KEY_ID="your-alpaca-key-id"
APCA_API_SECRET_KEY="your-alpaca-secret-key"

# Gmail Credentials for email reports (REQUIRED for email notifications)
SENDER_EMAIL="your-email@gmail.com"
GMAIL_APP_PASSWORD="your-16-digit-app-password"
RECIPIENT_EMAIL="email-to-receive-alerts@example.com"
```

** Important Notes:**

  * **Do not use quotes** around the key values if the key itself does not contain spaces or special characters, but the provided format uses them for consistency, which is generally safe.
  * The **`.env`** file starts with a dot, making it a **hidden file** on Mac/Linux.
  * Refer to the **`keys_setting.md`** file in the same directory for detailed instructions on how to obtain each of these keys.

### Step 5: Configure the Trading Parameters

Open the `main.py` script in a text editor. Here, you can configure the parameters for the `engine_loop` function:

*   **`tickers`**: A list of stock symbols to trade (e.g., `["AAPL", "MSFT", "GOOG"]`).
*   **`data_frequency`**: The timeframe for your data and the execution interval for the bot (e.g., `"1D"`, `"1h"`, `"5min"`).
*   **`trader_timezone`**: Your local timezone (e.g., `"America/New_York"`). A list of valid timezones can be found [here](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).
*   **`news_lookback_minutes`**: How far back to search for news (e.g., `60` for the last hour).
*   **`num_web_links`**: The number of web search results to consider for news analysis.
*   **`risk_management_specs`**: A dictionary for stop-loss/take-profit settings, or `None` to disable.
    *   **Example:** `{"stop_loss": {"type": "percentage", "value": 0.02}, "take_profit": {"type": "percentage", "value": 0.04}}`

### Step 6: Run the Portfolio Manager

Once configured, run the `main.py` script from your terminal:

```bash
python3 main.py
```

## Expected Behavior

The agent will first check the market schedule. If the market is open, it will start its continuous trading loop, executing at the interval defined by `data_frequency`. If the market is closed, it will wait for the next trading day. To stop the bot, press `Ctrl+C` in your terminal.

During operation, you will see log messages in your terminal indicating the agent's actions, such as fetching data, analyzing sentiment, making allocation decisions, and executing trades. If email notifications are configured, you will receive reports in your specified inbox.

### A Note on some Warnings

When running the script, you may see some warnings in the output. These warnings are harmless and **do not** affect the script's execution or the generation of the performance report.

*Note: This README provides an overview of the agentic portfolio manager. To understand how this project was built step-by-step, please refer to the `how_to.md` file.*

---

### Next Steps and Experimentation

This project is a sophisticated example of an autonomous agent. To deepen your understanding, we strongly recommend the following activities:

*   **Tweak the Models:**
    *   The quantitative signal uses a `RandomForestClassifier`. Swap it out for a different model from `scikit-learn`, like `GradientBoostingClassifier` or `SVC`, and observe how it impacts the trading signals.
    *   Adjust the features used for the quantitative model. Add or remove technical indicators in the `analysis_node` to see if you can improve its predictive power.

*   **Tweak the Parameters:**
    *   In `main.py`, change the list of `tickers` to a different basket of stocks, perhaps from a different market sector.
    *   Experiment with different `data_frequency` values like `"15min"` or `"1h"` to see how the bot behaves on different timeframes.
    *   Experiment with different `risk_management_specs`, such as tighter stop-losses or larger take-profit targets.

*   **Extend the Project:**
    *   **Add a New Data Source:** Create a new tool/function for the `analysis_node`. For example, build a tool that pulls fundamental data (like P/E ratios) from a free API (e.g., Alpha Vantage). Then, modify the agent's prompt to incorporate this fundamental data into its analysis.
    *   **Enhance the Portfolio Agent:** Modify the `portfolio_agent_node` to include more sophisticated allocation logic. For example, prompt it to perform a simple risk-parity or mean-variance optimization calculation based on the provided stock signals.
