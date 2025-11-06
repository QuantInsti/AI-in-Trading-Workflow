## An end-to-end setup to trade stocks algorithmically

#### This is your "Guidelines" document to modify and Running the `ib_stock_setup` Trading Code
###### QuantInsti Webpage: https://www.quantinsti.com/

**Version 1.0.0**
**Last Updated**: 2025-07-09

-----

## Disclaimer

#### This document provides instructions for you if you want to modify the source code of the `ib_stock_setup` trading application, rebuild the package, and run your modified setup.

## Licensed under the QuantInsti Open License (QOL) v1.1 (the "License").
- Copyright 2025 QuantInsti Quantitative Learning Pvt. Ltd.
- You may not use this document except in compliance with the License.
- You may obtain a copy of the License in `LICENSE.md` at the repository root or at https://www.quantinsti.com.
- Non-Commercial use only; see the License for permitted use, attribution, and restrictions.

## Table of contents
1.  [Introduction](#introduction)
2.  [Step-by-Step Guide to Modifying and Running](#guide)
    1. [Step 1: Navigate to the Project Root](#navigate)
    2. [Step 2: Make Your Code Modifications](#modify)
    3. [Step 3: Build the Package](#build)
    4. [Step 4: Reinstall the Modified Package](#reinstall)
    5. [Step 5: Run the Trading Setup](#run) 
3.  [Important Considerations](#considerations)

<a id='introduction'><a>
## 1. Introduction

The `ib_stock_setup` is a Python-based trading application designed for stock trading with Interactive Brokers. Once you make changes to source code files, this little guide focuses on enabling you to:
1. Build the setup wheel once you tweak anything of the source code.
2. Force the reinstallation of the setup package in the Python environment.
3. Run once again your setup with the new changes made.

<a id='guide'><a>
## 2. Step-by-Step Guide to Modifying and Running

You can follow these steps to modify the code, rebuild, reinstall, and run the application:

<a id='navigate'><a>
### Step 1: Navigate to the Project Root
You should navigate to the root directory of the `ib_stock_setup` project. This is the directory that contains the `src/` folder. You can check any of the Python files located in the `src/` folder and see which files and their functions you want to modify or tweak.

<a id='modify'><a>
### Step 2: Make Your Code Modifications

1.  **Identify the files to modify**:
    * For **strategy logic** (signals, stop-loss, take-profit, feature engineering): You should edit `user_config/strategy.py`.
    * For **core application logic** (how the engine runs, data handling, IB interactions): You should edit files within `src/ib_stock_setup/`.
    * For **run parameters** (account, symbol, timezone, etc.): You can modify `user_config/main.py`.

2.  **Edit the Python files**: You can use your preferred text editor or IDE to make the desired changes to the `.py` files. For example, you might change the logic in `get_signal` within `user_config/strategy.py` or adjust parameters in `user_config/main.py`.

<a id='build'><a>
### Step 3: Build the Package

Once you have made your changes, you need to rebuild the Python package.

1. **Open a terminal and type the following:**
```bash
cd path_to/ib_stock_setup
```
*(You should replace `path_to/ib_stock_setup` with the actual path to your project.)*

2.  **Install the `build` tool (if you haven't already)**:
    ```bash
    pip install build
    ```

3.  **Build the package**:
    From the root directory of the `ib_stock_setup` project, you should run:
    ```bash
    python -m build
    ```
    This command reads the `pyproject.toml` (or `setup.py`) and creates the package. You will see output in your terminal indicating the build process. Upon completion, a `dist/` directory will be created (or updated) in your project root, containing files like `ib_stock_setup-1.0.0-py3-none-any.whl` (the version number might differ).

<a id='reinstall'><a>
### Step 4: Reinstall the Modified Package

To ensure your Python environment uses your newly modified code, you must reinstall the package from the wheel file you just built. The `--force-reinstall` flag is important to ensure the existing version is overwritten.

```bash
pip install dist/ib_stock_setup-1.0.0-py3-none-any.whl --force-reinstall
```
*(You should adjust the filename `ib_stock_setup-1.0.0-py3-none-any.whl` if your built package has a different version or name. You can check the contents of your `dist/` folder.)*

This step updates the installed `ib_stock_setup` library in your Python environment with the changes you made in the `src/` directory.

<a id='run'><a>
### Step 5: Run the Trading Setup

After successfully reinstalling the package, you can run the main application script.

1.  **Navigate to the directory containing `main.py`**:
    Based on the project folder, this is located in the `user_config` directory. 

    ```bash
    cd user_config 
    ```

2.  **Execute the main script**:
    ```bash
    python main.py
    ```

The application should now run with your modifications. You should check the console output and any generated log files (e.g., in `data/log/`) to verify your changes are active and behaving as expected. The `main.py` script in the `user_config` folder is set up to import and use the `ib_stock_setup` package you just rebuilt and reinstalled.

<a id='considerations'><a>
## 3. Important Considerations

* **Virtual Environments**: It is highly recommended that you use a Python virtual environment (like Conda environments, as suggested in the `README.md`) for this project. This isolates dependencies and ensures a clean workspace. You should make sure you are in your activated environment when running these commands.
* **Dependencies**: If you add new library dependencies in your code modifications (e.g., by importing a new package in `strategy.py`), you might need to update the project's dependencies, typically listed in `pyproject.toml` or a `requirements.txt` file, and reinstall them in your environment. However, for simple logic changes within existing files, this is often not necessary.
* **Testing**: You should thoroughly test your changes in a paper trading account before deploying them in a live trading environment.
* **Backup `data/` folder**: The `data/` folder (especially `database.xlsx` and model files in `data/models/`) stores important trading information and trained models. You should back it up regularly, especially before making significant changes or running new optimization processes.
* **Strategy Optimization**: The `strategy.py` file includes a function `strategy_parameter_optimization()`. If you modify features or core logic used by this optimization, you may need to re-run it to ensure your models are tuned to your new setup. This function saves models like `hmm_model_YYYY_MM_DD.pickle` and `model_object_YYYY_MM_DD.pickle` in the `data/models/` directory.
* **Stock-Specific Considerations**: 
  - You should ensure your stock symbols are valid for the specified primary exchange.
  - You should check that your account has the necessary permissions for stock trading.
  - You should verify that the trading hours and timezone settings match your target stock exchange.
  - You should consider the impact of market holidays and trading sessions on your strategy.

By following these steps, you can effectively customize the `ib_stock_setup` to your trading needs. You should remember to always proceed with caution, especially when dealing with financial applications.
