# Gemini CLI in Trading Workflows

**For Educational and Paper Trading Purposes Only**

The content, code, and strategies provided in this repository are for educational and informational purposes only. They are not intended as financial advice, investment recommendations, or a solicitation to buy or sell any securities.

**Trading financial markets involves substantial risk, and you are solely responsible for any decisions you make. The authors and contributors of this repository assume no liability for any financial losses you may incur.**

Always conduct your own thorough research and risk assessment before deploying any trading strategy in a live environment. You should start by using these examples with paper trading accounts.

---

This section demonstrates the use of Google’s Gemini models via a command-line interface (CLI) to augment trading workflows.

A CLI provides a direct method for interacting with AI models, suitable for scripting, automation, and integration into local development environments.

### CLI Approach

*   **Automation & Scripting:** Incorporate AI-powered tasks into automated scripts and workflows.
*   **Efficiency:** A CLI can be a fast way for developers to perform tasks.
*   **Flexibility:** A CLI approach allows for control and the ability to pipe outputs between tools.

## Getting Started

### Prerequisites

*   Python 3.12
*   Git
*   A Google Gemini API Key

### Step 1: Clone the Repository

First, clone this repository to your local machine:

```bash
git clone https://github.com/QuantInsti/AI-in-Trading-Workflow.git
```

### Step 2: Navigate to the Directory

Navigate to the `gemini_cli` directory in your terminal or Anaconda Prompt.

**For Windows users:**
```bash
cd AI-in-Trading-Workflow\gemini_cli
```

**For Mac/Linux users:**
```bash
cd AI-in-Trading-Workflow/gemini_cli
```

### Step 3: Set up the Environment

We recommend using a Conda environment for these examples.

**1. Create and activate the environment:**
From your terminal (or Anaconda Prompt on Windows), run:
```bash
conda create --name gemini_cli_env python=3.12
conda activate gemini_cli_env
```

**2. Install the Gemini CLI:**
For the latest installation and setup instructions, please refer to the official [Gemini CLI repository](https://github.com/google-gemini/gemini-cli).

You can also follow the below steps:
1. Go to https://nodejs.org/en/blog/release/v12.22.3
2. Download node.js based on your specific Operating System.
3. Open the downloaded excutable file and install the program.
4. Install Node.js:
	4.1 For Windows, in the same previous terminal, type mkdir "%AppData%\npm"
	4.2 For Linux OS, go to https://nodejs.org/en/download/current and follow the instructions
5. Type: npx https://github.com/google-gemini/gemini-cli

### Step 4: Set up Your Gemini API Key

Set your Gemini API Key as an environment variable.

**For Windows (in Anaconda Prompt):**

```bash
set GEMINI_API_KEY="YOUR_ACTUAL_GEMINI_API_KEY"
```

**For macOS and Linux (in a terminal with an activated Anaconda environment):**

```bash
export GEMINI_API_KEY="YOUR_ACTUAL_GEMINI_API_KEY"
```

### Step 5: Open Gemini CLI
In your same terminal, type:
```bash
gemini
```

### Step 6: Run the Examples

Once the Gemini CLI is installed and your API key is set, navigate to the specific example directory you wish to run and follow its `README.md` for detailed execution instructions.

## Available Use Cases

The following examples are available in this directory:

*   [**Example 01: Create Backtesting Code for BTC-USD**](./example_01_create_backtesting_code/README.md): This example demonstrates using Gemini CLI to generate a Python script for backtesting a trading strategy using BTC-USD, including parameter optimization and a PDF report for strategy performance metrics and plots.

*   [**Example 02: Run a Multi-Agent System on an IB Stock Setup**](./example_02_run_multi_agent_system_on_IB_stock_setup/README.md): This example demonstrates how to integrate a multi-agent system for news analysis into an existing IB-based stock trading setup.
