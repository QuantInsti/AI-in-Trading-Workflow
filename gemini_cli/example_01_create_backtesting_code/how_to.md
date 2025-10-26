# How to Create a Backtesting Script with Gemini CLI

This guide demonstrates how to use the `gemini-cli` to build a Python
backtesting script. The script will download financial data, optimize a
trading strategy, run a backtest, and generate a PDF report of the
results.

The following sections contain a series of prompts that can be given to
the Gemini CLI to generate the Python script.

---

## Disclaimer: LLMs are Probabilistic

The code and prompts provided in this guide are for educational purposes. Due to the probabilistic nature of Large Language Models (LLMs), you may not get the exact same output even when using the identical prompts. The generated code can vary. The Python scripts included in this repository represent a final, working version that may have required multiple iterations and refinements.

------------------------------------------------------------------------

### Objective

The goal is to create a Python script to test a simple moving average
crossover strategy for Bitcoin. The process is broken down into four
main parts:

1.  **Data Gathering:** Fetch historical Bitcoin data.
2.  **Optimization:** Find the best moving average windows to use.
3.  **Backtesting:** Simulate the strategy with the best parameters on
    unseen data.
4.  **Reporting:** Analyze the results and create a PDF report.

------------------------------------------------------------------------

### Step 1: Setting Up the Script

The first part of the script will be for setup and importing libraries.

#### **Prompting for Imports:**

> I'm creating a trading backtest in a Python script. Please give me the
> Python code to import the following libraries: `yfinance` for data,
> `pandas` and `numpy` for manipulation, `matplotlib` for plotting,
> `fpdf` for creating a PDF, and `tqdm` for progress bars.

------------------------------------------------------------------------

### Step 2: Downloading the Data

The backtest requires historical data. The CLI can generate the code to
download Bitcoin data from Yahoo Finance.

#### **Prompting for the Data Download:**

> Please write a Python code block that uses `yfinance` to download
> daily data for 'BTC-USD' from 2014 to today. It should also
> calculate the daily percentage returns and print the first few rows of
> the downloaded data. Include error handling in case the download
> fails.

------------------------------------------------------------------------

### Step 3: Optimizing the Strategy

A crossover strategy has two key parameters: the short window and the
long window for the moving averages. The following prompts will generate
code to find the optimal parameters.

#### **Prompting for the Optimization Logic:**

**First, set up the parameter grid:**

> I want to optimize the moving average windows. Please write the code
> to create a parameter grid. The short window should range from 3 to
> 20, and the long window from 5 to 30. The long window must always be
> greater than the short window.

**Next, create the backtesting function for optimization:**

> I need a function to run a simplified backtest for the optimization
> loop. Please write a Python function that takes the data, a short
> window, and a long window as input. It should calculate the moving
> averages, generate signals (1 for a golden cross, 0 otherwise), and
> return the daily strategy returns.

**Finally, write the optimization loop:**

> Please write the main optimization loop. It should iterate through
> every combination in the parameter grid. In each loop, it should call
> the backtesting function and then calculate the Sortino Ratio of the
> returns. The goal is to find the parameter combination with the
> highest Sortino Ratio. Use `tqdm` to show a progress bar.

------------------------------------------------------------------------

### Step 4: Running the Final Backtest

With the optimal parameters, a more detailed, event-driven backtest can
be run on out-of-sample data (the most recent 10% of the data).

#### **Prompting for the Event-Driven Backtest:**

**First, set up the backtest data:**

> Please write the code to set up the data for the final backtest. It
> should slice the main dataframe, reserving the first 90% for
> optimization and using the last 10% for the backtest. It should also
> use the best short and long window parameters found during
> optimization.

**Next, create the event-driven loop:**

> Now, create the event-driven backtesting loop. It should initialize a
> portfolio with \$100,000 in cash. Then, loop through the backtest data
> day-by-day and do the following: 1. Check for trade entry signals
> (golden cross). 2. Check for trade exit signals (death cross). 3.
> Execute a 2% stop-loss or a 4% take-profit if a position is open. 4.
> Track the portfolio's equity value each day. 5. After the loop, print
> the final equity value.

------------------------------------------------------------------------

### Step 5: Analyzing Results and Creating the PDF Report

The final step is to analyze the results and present them in a report.

#### **Prompting for Metrics, Plots, and the PDF:**

**First, calculate performance metrics:**

> Please write the code to calculate the following performance metrics
> based on the equity curve: Total Return, Sharpe Ratio, Sortino Ratio,
> Maximum Drawdown, Win Rate, and Total Trades.

**Next, create the plots:**

> Please generate two plots using `matplotlib`: 1. An equity curve
> chart, showing the portfolio value over time compared against a
> buy-and-hold strategy, with buy and sell points marked on the chart.
> 2. A drawdown chart, showing the percentage drop from the portfolio's
> peak value over time. Save each plot as a PNG file.

**Finally, generate the PDF report:**

> Write the code to generate a PDF report using the `fpdf` library. The
> report should include: 1. A title. 2. The optimized parameters that
> were used. 3. A table of the performance metrics. 4. The equity curve
> and drawdown plots saved as PNG files. Finally, save the report as
> `backtest_report.pdf`. ---

By breaking down the task of creating a backtesting system into smaller
prompts, you can use the Gemini CLI to build a complete Python script.
