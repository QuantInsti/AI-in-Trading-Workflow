# MCP Server for the Interactive Brokers API

**For Educational and Paper Trading Purposes Only**

This repository provides content, code, and strategies for educational and informational purposes only. We do not intend for them to be financial advice, investment recommendations, or a solicitation to buy or sell any securities.

**Trading financial markets involves substantial risk, and you are solely responsible for any decisions you make. The authors and contributors of this repository assume no liability for any financial losses you may incur.**

Always conduct your own thorough research and risk assessment before deploying any trading strategy in a live environment. You should start by using these examples with paper trading accounts.

---

This project provides a **Model Context Protocol (MCP) server** that interfaces with the **Interactive Brokers (IB) API**. It uses a Large Language Model (LLM) to translate natural language commands into structured trading actions that can be executed through an IB account. A single Python script manages the entire system.

## How It Works

This system uses a single Python script (`ib_mcp_server.py`) to create a robust MCP architecture.

1.  **The Python Script (`ib_mcp_server.py`) - Orchestrator, IB API Client & LLM Bridge**
    *   This is the main script. It connects to your Interactive Brokers account (TWS or Gateway) using the official IB API.
    *   It gathers account context (e.g., balance, positions) and sends it along with your natural language request to the Google Gemini API.
    *   It receives a structured JSON response from the Gemini API and executes the corresponding trade or action via the IB API.

This architecture uses Python for its strengths in interfacing with the IB API and directly integrates with the Gemini API for natural language processing.

## Core Agent Prompts

The following prompt guides the AI agent's decisions. The script sends a detailed prompt to the Gemini API, which includes the user's request, account summary, positions, and open orders. The prompt instructs the LLM to respond with a JSON object that specifies one of the following actions:

*   `answer_question`: To answer questions about account data or API errors.
*   `place_order`: To buy or sell securities.
*   `get_data`: To fetch data like price, historical data, or P&L.
*   `get_open_orders`: To get a list of open orders.
*   `cancel_order`: To cancel an existing order by its ID.
*   `clarify`: To ask for more information if the request is ambiguous.
*   `unsupported_request`: To handle requests that are outside its capabilities.

## Getting Started

### Prerequisites

*   Python 3.12
*   Git
*   An Interactive Brokers (IB) account and TWS/IB Gateway installed and running.
*   A Gemini API Key

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
conda create --name mcp_server python=3.12
conda activate mcp_server
```

Install the required Python libraries using the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

**Important: Install `ibapi` separately.** The `ibapi` library from Interactive Brokers requires a specific installation process. Please follow their official instructions, usually found on the [Interactive Brokers API website](https://interactivebrokers.github.io/tws-api/index.html).

### Step 4: Configure API Keys and Environment Variables

Create a file named `.env` in the project directory (the same directory as `ib_mcp_server.py`) and add your Gemini API key and optionally the server port.

```env
# .env file

# Google Gemini API Key (REQUIRED)
GEMINI_API_KEY="your-google-ai-api-key"

# Optional: Port for the IB TWS/Gateway connection
# Default is 7497 for TWS, 7496 for Gateway
PORT="7497"
```

### Step 5: Launch the Server

Before you start, ensure that your IB TWS or Gateway is running and you are logged in.

Once configured, run the script from your terminal:

```bash
python ib_mcp_server.py
```

The Python script will connect to IB and initialize the Gemini model.

### Step 6: Interact with the MCP Server

With the script running, you can type natural language commands directly into the console. The MCP server will process these commands to generate and execute trades.

**Example Commands:**

*   `What's my current account balance?`
*   `Buy 10 shares of GOOG at the market price.`
*   `Place a limit order to buy 50 shares of NVDA at 900.25.`
*   `Sell 5 shares of TSLA at market.`
*   `What is the latest price of AAPL?`
*   `Show me my P&L.`
*   `What are my open orders?`
*   `Cancel order 123.`

*Note: This README provides an overview of the system. To understand how this project was built step-by-step, please refer to the `how_to.md` file.*

---

### Next Steps and Experimentation

This project provides a foundation for building an LLM-powered trading assistant. To deepen your understanding, we strongly recommend the following activities:

*   **Tweak the Prompts:**
    *   Modify the system prompt within `ib_mcp_server.py` to make the LLM's JSON output more sophisticated. For example, ask it to handle more complex order types.

*   **Extend the Project:**
    *   **Add New Capabilities:** This is the best way to learn. Modify the prompt and the Python client to handle new commands that interact with the IB API. For example:
        *   `"What's my total portfolio value?"`
        *   `"Close my position in AAPL."`
        *   `"Modify my limit order for NVDA to $905."`
    *   This will require adding new functions in `ib_mcp_server.py` to request this data from IB and adding logic to process the new JSON responses from the LLM.