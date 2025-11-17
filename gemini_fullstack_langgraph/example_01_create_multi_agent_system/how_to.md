# How to Create `client_example.py` with Gemini CLI

This guide provides a step-by-step tutorial on how to use the Gemini CLI
to generate the `client_example.py` script. This script is a standalone
client that runs a multi-agent system to get a trading recommendation
for a financial asset.

To get started, first clone the repository:

```bash
git clone https://github.com/QuantInsti/AI-in-Trading-Workflow.git
```

The CLI will be instructed to use the code and patterns from the
`gemini-fullstack-langchain` project as a reference.

---

## Disclaimer: LLMs are Probabilistic

The code and prompts provided in this guide are for educational purposes. Due to the probabilistic nature of Large Language Models (LLMs), you may not get the exact same output even when using the identical prompts. The generated code can vary. The Python scripts included in this repository represent a final, working version that may have required multiple iterations and refinements.

------------------------------------------------------------------------

### Step 1: Provide Context to the CLI

First, provide the Gemini CLI with the necessary context by asking it to
read the core files from the `gemini-fullstack-langchain` project.

**Example Prompt:**

> I want to create a Python script for a multi-agent trading analysis
> system. Please read the following files to understand the architecture
> and logic:

1.  `/path/to/AI-in-Trading-Workflow-final/gemini_fullstack_langchain/README.md`
2.  `/path/to/AI-in-Trading-Workflow-final/LLMs/example_01_create_ib_mcp_server_in_python/ib_mcp_server.py`

*(Note: The paths should be absolute.)*

------------------------------------------------------------------------

### Step 2: Give Clear Instructions to Generate the Script

Once the CLI has the context, provide a detailed prompt to generate the
`client_example.py` script.

**Example Prompt:**

> Please create a new Python script named `client_example.py`. This
> script should be a standalone client that orchestrates a multi-agent
> system for trading analysis.
>
> The requirements for the script are as follows:

1.  > **Configuration:** At the top of the script, include a
    > configuration section for parameters like `ASSET_NAME`,
    > `EXCHANGE`, `INITIAL_QUERIES`, `MAX_LOOPS`, and `REASONING_MODEL`.

2.  > **Dynamic Prompts:** Create functions that generate prompts dynamically. For example, `get_news_gathering_prompt(asset_name, exchange)` should return a formatted string with the proper instructions. Create similar functions for the sentiment analysis and trading strategy agents.

3.  > **Agent Classes:** Define Python classes for the agents. Each agent class should have an `execute` method.
    > - `NewsGathererAgent`: Takes an asset and exchange, uses the dynamic prompt, invokes the graph, and returns the news summaries.
    > - `SentimentAnalyzerAgent`: Takes news summaries, handles cases where no news is found, invokes the graph, and parses the sentiment score. It should include robust error handling to parse a float from the model's response, including normalizing scores that might be on a 0-100 scale.
    > - `MarketDataFetcher`: A class (not an agent that calls the graph) that fetches the CBOE Volatility Index (VIX) using the `yfinance` library. It should handle cases where the data might not be available.
    > - `TradingStrategyAgent`: Takes the sentiment score and VIX, invokes the graph, and parses the final JSON recommendation. It must handle potential JSON decoding errors and provide a default 'HOLD' recommendation if parsing fails.

4.  > **Report Generation:**
    > - Create a function `generate_markdown_report` that takes all the data (asset name, recommendation, news, scores) and compiles a detailed Markdown report.
    > - Create a second function `generate_pdf_from_cleaned_content` that takes the Markdown content, cleans it (e.g., removes links), and uses the `reportlab` library to generate a professional-looking PDF report.

5.  > **Helper Functions:**
    > - Include a helper function `extract_last_message_content` to safely get content from the last message in the graph's result.
    > - Add functions like `remove_links` and `clean_news_summaries` to process the text before generating the final report.

6.  > **Main Function:** Include a `main()` function that:
    > - Initializes all the agent classes.
    - Executes them in the correct order: News -> Sentiment -> VIX -> Strategy.
    - Cleans the news summaries before passing them to the sentiment agent.
    - Calls the functions to generate the Markdown and PDF reports, and then deletes the intermediate Markdown file.
    - Prints the final recommendation to the console and includes example downstream logic (e.g., "Triggering order placement logic.").
    - Records and prints the total time taken for the agent workflow to complete.

7.  > **Imports:** Include all necessary imports, like `datetime`, `yfinance`, `json`, `os`, `re`, and the `reportlab` library for PDF generation.

> Please generate the complete code for this `client_example.py` file.

------------------------------------------------------------------------

### Step 3: Create a `requirements.txt` File

After generating the script, ask the CLI to create a `requirements.txt`
file to ensure all dependencies are properly managed.

**Example Prompt:**

> Please create a `requirements.txt` file and add the following
> libraries to it:
>
> yfinance
> langchain-core
> reportlab

------------------------------------------------------------------------

### Step 4: Review and Save the Code

Review the generated Python code to ensure it meets all the
requirements. If it is correct, ask the CLI to save it.

**Example Prompt:**

> The code is correct. Please save it to the file
> `/path/to/AI-in-Trading-Workflow-final/gemini_fullstack_langchain/example_01_create_multi_agent_system/client_example.py`.

After running the script, a PDF file named
`[ASSET_NAME]_trading_report_[TIMESTAMP].pdf` will be created in the
same directory.
