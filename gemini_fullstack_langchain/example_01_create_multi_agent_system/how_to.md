# How to Create `client_example.py` with Gemini CLI

This guide provides a step-by-step tutorial on how to use the Gemini CLI
to generate the `client_example.py` script. This script is a standalone
client that runs a multi-agent system to get a trading recommendation
for a financial asset.

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
    > `EXCHANGE`, `REASONING_MODEL`, etc.

2.  > **Agent Classes:** Define Python classes for the four agents:

    - `NewsGathererAgent`: Takes an asset and exchange to find recent
      news.
    - `SentimentAnalyzerAgent`: Takes news summaries and returns a
      sentiment score from -1 to +1.
    - `MarketDataFetcher`: Fetches the CBOE Volatility Index (VIX) using
      the `yfinance` library.
    - `TradingStrategyAgent`: Takes the sentiment score and VIX to
      produce a final JSON recommendation containing an `action`,
      `confidence`, and `reasoning`.

3.  > **PDF Report Generation:** Add a function that generates a PDF
    > report summarizing the entire analysis. The report should include:
    > - An executive summary of the final recommendation.
    > - The input parameters used (asset, sentiment, VIX).
    > - A "chain of thought" section detailing the findings of each agent.
    > - A disclaimer.

4.  > **Agent Logic:** The agents will be responsible for creating the correct prompts and processing the results. The `gemini-fullstack-langchain` library handles the `graph.invoke()` method.

5.  > **Main Function:** Include a `main()` function that:

    - Initializes all the agents.
    - Executes them in the correct order: News -> Sentiment -> VIX ->
      Strategy.
    - Calls the function to generate the PDF report.
    - Prints the final recommendation to the console.

6.  > **Imports:** Include all necessary imports, like `datetime`,
    > `yfinance`, `json`, and the `reportlab` library for PDF generation.

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
