# **Tutorial: How to Build a Broker API MCP with an LLM**

This tutorial guides you through the process of using a Large Language Model (LLM) as a development partner to create a **Model Context Protocol (MCP) server** that interfaces with the Interactive Brokers (IB) API.

The goal is not just to present the final code, but to show *how* you can use prompt and context engineering to guide an LLM to build the application from scratch. The final architecture will be a single, powerful Python script.

To get started, first clone the repository:

```bash
git clone https://github.com/QuantInsti/AI-in-Trading-Workflow.git
```

## **1. Core Architectural Components**

Through a series of conversational prompts, we will build an MCP server within a single Python script: `ib_mcp_server.py`. Its responsibilities are:

*   Managing the connection to IB using the official `ibapi` library.
*   Fetching account and position data to build a real-time context.
*   Accepting user input from the command line.
*   Formatting the user's request and the account context into a detailed prompt for the Google Gemini API.
*   Receiving a structured JSON response from the Gemini API.
*   Executing the action described in the JSON, such as placing an order or fetching data.

## **2. Building the MCP Server: A Conversation**

This section outlines a student-friendly, conversational approach to building this application. We'll start with a simple request and gradually add complexity, showing how the Python code and the LLM prompt evolve together.

### **Step 1: The Basic Idea**

**You:** "I want to build a simple tool that lets me trade with my Interactive Brokers account using natural language. Where do I start?"

**Guide:** "Great idea. We can build this in a single Python script. The first step is to establish a basic connection to the Interactive Brokers API. We'll create a class that handles the connection and listens for API events."

### **Step 2: Answering a Simple Question**

**You:** "Okay, I'm connected. Now, how can I make the AI answer a simple question, like 'What is my account balance?'"

**Guide:** "Excellent. We need to add a function to request account data from the IB API and then create a simple prompt to send that data along with your question to the LLM."

### **Step 3: Placing a Market Order**

**You:** "That works! Now, how do I get it to place a trade? For example, if I say, 'Buy 10 shares of GOOG'."

**Guide:** "This is where we introduce structured JSON output. We'll add a `place_order` method in Python and update the prompt to tell the LLM to respond with a JSON object containing the action, symbol, quantity, etc."

### **Step 4: Handling Ambiguity and Errors**

**You:** "What if I say 'cancel my order'? The AI doesn't know which order ID to cancel."

**Guide:** "You've hit on a key point. We need to give the AI an 'escape hatch.' We'll add a `clarify` action to its list of possible commands. We'll also add a section to the prompt for reporting API errors, so the LLM can explain them to you."

### **Step 5: Getting Live Market Data**

**You:** "I can place trades, but I'm flying blind. How can I ask for a stock's current price before I buy?"

**Guide:** "Good thinking. We'll add a new capability.

1.  **In Python:** We'll create a `get_last_price` function that uses `reqMktData` from the API.
2.  **Update the Prompt:** We'll add a new action called `get_data` to the prompt. The LLM can use this action when you ask for information that isn't already in the account summary, like a price."

### **Step 6: Expanding to Limit Orders**

**You:** "Market orders are too risky for me. How can I place a limit order, like 'Buy 10 NVDA at 900.25'?"

**Guide:** "This is a great example of iterative improvement.

1.  **In Python:** We'll update the `place_order` function to check if the `order_type` is 'LMT' and, if so, add the `lmtPrice` to the order object.
2.  **Update the Prompt:** We'll enhance the `place_order` definition in the prompt, telling the LLM it can now use 'LMT' as an `order_type` and that it should also provide a `limit_price`."

### **Step 7: Checking on Our Positions**

**You:** "How can I check what I currently own? I want to be able to ask, 'Do I own any Apple stock?'"

**Guide:** "This is about enriching the context we send to the LLM. The script already fetches position data during the initial connection. The key is to make sure this data is included in the prompt every time you make a request. We'll add a 'Positions' section to the prompt context, so the LLM is always aware of your portfolio."

### **Step 8: Listing Open Orders**

**You:** "I placed a limit order, but I'm not sure if it filled. How can I see all my working orders?"

**Guide:** "Similar to getting prices, we'll add a new function and a new action.

1.  **In Python:** We'll add a `get_open_orders` function that calls `reqOpenOrders`.
2.  **Update the Prompt:** We'll add a `get_open_orders` action. This one is simple; it doesn't need any parameters. The LLM can now trigger a request to see all pending orders."

### **Step 9: Cancelling a Specific Order**

**You:** "Okay, I can see my open orders. Now how do I cancel one? Let's say I want to 'Cancel order 123'."

**Guide:** "Now we can connect the dots.

1.  **In Python:** We'll add a `cancel_order_by_id` function.
2.  **Update the Prompt:** We'll add a `cancel_order` action that requires an `order_id`. This works with the `clarify` action we built in Step 4. If you say 'cancel my order,' the LLM will ask for the ID. If you provide it, the LLM will use this new action."

### **Step 10: Requesting Historical Data**

**You:** "This is powerful. Can I look at past performance, like 'Show me the last 10 days of AAPL'?"

**Guide:** "Yes, but this introduces a new challenge: handling larger amounts of data.

1.  **In Python:** We'll add a `get_historical_data` function.
2.  **Update the Prompt:** We'll expand the `get_data` action. The LLM can now set the `data_type` to 'historical' and provide a symbol."

### **Step 11: Summarizing Data with the LLM (Re-engagement)**

**You:** "When I ask for historical data, the terminal just prints a lot of numbers. Can the AI summarize it for me?"

**Guide:** "This is an advanced and very powerful technique. We'll create a two-step conversation with the LLM.

1.  **In Python:** After we receive the historical data, instead of just printing it, we'll immediately call the LLM *again*.
2.  **Create a Second Prompt:** This new prompt will say, 'Here is the historical data the user asked for. Please provide a simple summary.' This re-engagement makes the assistant feel much more intelligent."

### **Step 12: Checking Profit and Loss (P&L)**

**You:** "How am I doing today? Can I ask, 'What's my P&L?'"

**Guide:** "Absolutely. This follows the same pattern.

1.  **In Python:** We'll add a `get_pnl` function.
2.  **Update the Prompt:** We'll add 'pnl' as another option for the `data_type` in our `get_data` action."

### **Step 13: Improving the User Interface**

**You:** "Sometimes, a message from the server (like a price update) messes up the line where I'm typing my next command. Can we fix that?"

**Guide:** "Yes. This is a common problem in command-line tools. We can implement thread-safe printing. We'll create a `safe_print` function that uses a lock to ensure only one thing is written to the console at a time. It will save what you're typing, print the message on a new line, and then restore your text. It's a small change that makes the tool much more professional."

### **Step 14: Handling Disconnections Gracefully**

**You:** "What happens if I lose my connection to the IB Gateway?"

**Guide:** "A robust application should handle this. We'll add a `handle_reconnect` method. The script will detect a disconnection, and instead of crashing, it will automatically try to reconnect a few times. This makes the assistant much more reliable for long-term use."

By building the script and the prompt iteratively, you create a robust system where the Python code provides the tools (functions to get data and place orders) and the LLM acts as the brain, deciding which tool to use based on your natural language commands.

## **3. Disclaimer**

This project is for **educational and illustrative purposes only**. Trading in financial markets involves substantial risk of loss. The code and concepts discussed here are **not financial advice**. Always exercise caution and thoroughly understand any automated trading system before deploying it in a live environment.