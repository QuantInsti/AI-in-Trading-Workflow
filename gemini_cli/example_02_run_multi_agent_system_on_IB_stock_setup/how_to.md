# Guide to Creating `AI_strategy.py` from `client_example.py`

This guide outlines the process of using the Gemini CLI to create the
`AI_strategy.py` file for the `ib_stock_setup` framework, using the
logic from `client_example.py` as a starting point.

To get started, first clone the repository:

```bash
git clone https://github.com/QuantInsti/AI-in-Trading-Workflow.git
```

The process involves providing the CLI with both files and then giving
it instructions on how to combine them.

Then, you can open Gemini CLI as it is described in the README file of the folder [https://github.com/QuantInsti/AI-in-Trading-Workflow/tree/main/gemini_cli](https://github.com/QuantInsti/AI-in-Trading-Workflow/tree/main/gemini_cli)

---

## Disclaimer: LLMs are Probabilistic

The code and prompts provided in this guide are for educational purposes. Due to the probabilistic nature of Large Language Models (LLMs), you may not get the exact same output even when using the identical prompts. The generated code can vary. The Python scripts included in this repository represent a final, working version that may have required multiple iterations and refinements.

------------------------------------------------------------------------

### Step 1: Providing Context to the CLI

The first step is to have the CLI read both `client_example.py` (which
contains the agent logic) and the existing `strategy.py` (which has
the required structure for the trading application).

Example prompt:

> I want to use my client_example.py file for my trading application named ib_stock_setup. Please read the following two files: 
> 1. `/path/to/AI-in-Trading-Workflow-final/gemini_cli/example_02_run_multi_agent_system_on_IB_stock_setup/client_example.py`
> 2. `/path/to/AI-in-Trading-Workflow-final/gemini_cli/example_02_run_multi_agent_system_on_IB_stock_setup/ib_stock_setup/user_config/strategy.py`

------------------------------------------------------------------------

### Step 2: Providing Instructions

Once the CLI has read the files, provide a detailed list of instructions
for the necessary changes.

Example prompt:

> Please update `strategy.py` using the code from `client_example.py`
> as follows:

1.  > **Copy agent code**: Copy the agent classes (`NewsGathererAgent`,
    > `SentimentAnalyzerAgent`, etc.) and the helper functions for
    > creating prompts from `client_example.py` into `AI_strategy.py`.

2.  > **Move logic to** `get_signal`: Move the logic from the `main()`
    > function of `client_example.py` into the `get_signal(app)`
    > function in `AI_strategy.py`.

3.  > **Use the** `app` **object**: In the `get_signal` function, the
    > script should get the stock symbol and exchange from the `app`
    > object (e.g., `asset_name = app.symbol`), not from the hardcoded
    > `ASSET_NAME` in the original example.

4.  > **Translate the final recommendation**: The `TradingStrategyAgent`
    > returns a dictionary with an 'action' and 'confidence'. The
    > `get_signal` function needs to return a tuple of
    > `(signal, leverage)`. A 'BUY' action should become a signal of
    > `1`, and 'HOLD' or 'SELL' should become `0`. The `confidence`
    > score should be used as the `leverage`.

5.  > **Retain other functions**: Keep the other functions like
    > `set_stop_loss_price` and `set_take_profit_price` in
    > `AI_strategy.py`.

> Please provide the new version as a new file named `AI_strategy.py`.

------------------------------------------------------------------------

### Step 3: Review and Save

Review the generated code to ensure it matches the requirements. If it
is correct, instruct the CLI to save the file.

Example prompt:

> The code is correct. Please save this new version to
> `path/to/ib_stock_setup/user_config/AI_strategy.py`.
