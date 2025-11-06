# An End-to-End Setup to Trade Stocks Algorithmically

#### This document details the strategy used to trade stocks.

###### QuantInsti Webpage: [https://www.quantinsti.com/](https://www.quantinsti.com/)

**Version 1.0.1**
**Last Updated**: 2025-07-09

-----

# Disclaimer

#### This file is documentation only and should not be used for live trading without appropriate backtesting and parameter adjustments.

## Licensed under the Apache License, Version 2.0 (the "License").

  - Copyright 2025 QuantInsti Quantitative Learnings Pvt Ltd.
  - You may not use this file except in compliance with the License.
  - You may obtain a copy of the License at [http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0)
  - Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

-----

## Table of Contents

1.  [Introduction](#introduction)
2.  [General Guidelines](#general-guidelines)
3.  [Workflow Overview](#workflow)
4.  [Core Components](#core-components)
      - 4.1 [Data Preparation](#data-preparation)
      - 4.2 [Signal Generation](#signal-generation)
      - 4.3 [Risk Management](#risk-management)
      - 4.4 [Model Training & Optimization](#model-training--optimization)
5.  [Function Reference](#function-reference)
      - 5.1 [`create_classifier_model()`](#create_classifier_model)
      - 5.2 [`set_stop_loss_price()`](#set_stop_loss_price)
      - 5.3 [`set_take_profit_price()`](#set_take_profit_price)
      - 5.4 [`prepare_base_df()`](#prepare_base_df)
      - 5.5 [`get_signal()`](#get_signal)
      - 5.6 [`strategy_parameter_optimization()`](#strategy_parameter_optimization)
6.  [Dependencies](#dependencies)
7.  [Modification Guidelines](#modification-guidelines)

-----

<a id='introduction'></a>

## Introduction

The `strategy.py` module is the algorithmic core of this trading system. It combines machine learning (Hidden Markov Models, Random Forests) with technical analysis to generate signals, manage risk, and adapt to market regimes. Key features:

  - **Automated Signal Generation**: Predicts market direction using pre-trained models.
  - **Risk Management**: Sets stop-loss/take-profit levels based on pre-defined risk parameters.
  - **Weekly Retraining**: Ensures models adapt to new market conditions.
  - **Important Notes**:
      - You can modify the internal logic of the functions. However, pay close attention to the function signatures (inputs and outputs) if the system calling this strategy file expects a specific interface.
      - If you need to introduce new parameters, you can modify the function definitions. Consider how these parameters will be passed from the calling environment (e.g., `main.py` or an `app` object).

-----

<a id='general-guidelines'></a>

## General Guidelines

1.  **Mandatory Inputs**:

      - Certain functions rely on an `app` object to pass necessary data like `base_df`, `signal`, `last_value`, `model_datetime`, and `final_input_features`. Ensure this object is correctly populated.
      - The `historical_data` DataFrame for `prepare_base_df()` is crucial.

2.  **Modifications**:

      - Feel free to alter the internal logic of functions like `prepare_base_df()` or `get_signal()`.
      - Example: You could adjust the fixed risk parameters within `set_stop_loss_price()` or make them dynamic based on `app` attributes.

3.  **Reproducibility**:

      - The `seed` input parameter from the `main.py` file is used in `strategy_parameter_optimization()` for consistent model training and HMM initialization.

-----

<a id='workflow'></a>

## Workflow Overview

### Weekly Tasks

1.  **Model Optimization**:
      - Run `strategy_parameter_optimization()` to retrain models and save them to the `data/models/` folder. This function also saves the prepared `base_df` and the list of initial features.

### Intraday Tasks (Per Trading Period)

  - The following tasks are orchestrated by the trading setup using this `strategy.py` file.

<!-- end list -->

1.  **Data Preparation**:
      - Generate `base_df` and `final_input_features` using `prepare_base_df()` with historical data. These are often then passed via the trading  `app` object for subsequent steps.
2.  **Signal Generation**:
      - Call `get_signal()` (passing the `app` object containing `base_df`, `final_input_features`, and `model_datetime`) to get a directional signal (`-1`, `1`) and leverage.
3.  **Order Execution**:
      - Send market orders based on the signal.
4.  **Risk Management**:
      - Calculate stop-loss/take-profit prices with `set_stop_loss_price()` and `set_take_profit_price()` (passing the `app` object containing `signal` and `last_value`).

### **Execution Flow**:

````
```
Weekly: strategy_parameter_optimization() → Per trading period: prepare_base_df() → get_signal() → Market Order → set_stop_loss_price()/set_take_profit_price()
```
````

-----

<a id='core-components'></a>

## Core Components of the strategy

<a id='data-preparation'></a>

### 4.1 Data Preparation

**Purpose**: Transforms raw OHLC data into a feature-rich DataFrame.

  - **Key Function**: `prepare_base_df()`
  - **Outputs**:
      - `base_df`: Contains the target variable (`y`), datetime features (one-hot encoded month, weekday, hour), technical indicators (for windows 3, 4, 5), lagged OHLC percentage changes (up to 9 lags), stationarity-enforced features, volatility signals, and normalized features.
      - `final_input_features`: List of feature names generated and selected for model input.

<a id='signal-generation'></a>

### 4.2 Signal Generation

**Purpose**: Predicts market direction using pre-trained ML models and HMM-based regime states.

  - **Key Function**: `get_signal()`
  - **Dependencies**: Pre-trained models (`hmm_model_YYYY_MM_DD.pickle`, `model_object_YYYY_MM_DD.pickle`) loaded based on `model_datetime`. The `app` object provides `base_df`, `final_input_features`, and `model_datetime`.

<a id='risk-management'></a>

### 4.3 Risk Management

**Purpose**: Sets stop-loss and take-profit prices based on fixed risk parameters.

  - **Key Functions**:
      - `set_stop_loss_price()`: Calculates stop-loss based on the signal, last price, and a fixed 4% risk target with a 1x multiplier.
      - `set_take_profit_price()`: Calculates take-profit based on the signal, last price, and a fixed 4% return target with a 1x multiplier.
  - **Note**: Both functions receive trading context (signal, last price) via the `app` object.

<a id='model-training--optimization'></a>

### 4.4 Model Training & Optimization

**Purpose**: Retrains models weekly to adapt to market changes, performs feature selection, and saves artifacts.

  - **Key Function**: `strategy_parameter_optimization()`
  - **Process**:
    1.  Prepares `base_df` from raw minute data, including resampling and feature engineering.
    2.  Trains an HMM for regime detection.
    3.  Performs feature selection using Boruta-Shap on the training data.
    4.  Trains multiple classifier models with different seeds on selected features.
    5.  Selects the best model based on annualized Sharpe ratio on test data.
    6.  Saves the HMM, best classifier model, the initial list of features (`optimal_features_df.xlsx`), and the processed `base_df`.

-----

<a id='function-reference'></a>

## Function Reference

  - In the column "Required" we set:
      - **Yes**: Input **cannot** be dropped as the function's current implementation relies on it.
      - **No**: Input is optional or has a default; dropping it might change behavior but not necessarily break the function if handled internally.

<a id='create_classifier_model'></a>

### 5.1 `create_classifier_model(seed)`

  - **Purpose**: Creates a calibrated bagging classifier model with a Random Forest base estimator.
  - **Input Parameters**:
    | Parameter | Type  | Required? | Description                                                                                                |
    |-----------|-------|-----------|------------------------------------------------------------------------------------------------------------|
    | `seed`    | `int` | Yes       | Random seed for reproducibility in base estimator, bagging, and calibration.                               |
  - **Returns**:
    | Output  | Type                     | Description                                                                                                |
    |---------|--------------------------|------------------------------------------------------------------------------------------------------------|
    | `model` | `CalibratedClassifierCV` | A classifier model combining bagged random forests and calibrated probabilities using isotonic regression. |
  - **Note**: This is the only function you can drop it from this strategy.py file if you'd like to. The rest of the functions are mandatory to exist.

-----

<a id='set_stop_loss_price'></a>

### 5.2 `set_stop_loss_price(app)`

  - **Purpose**: Calculates and sets the stop-loss price based on the trading signal and predefined risk parameters.
  - **Input Parameters**:
    | Parameter | Type     | Required? | Description                                                                                                                                                              |
    |-----------|----------|-----------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
    | `app`     | `object` | Yes       | The trading application object, expected to have `signal` (trading direction: \>0 for long, \<0 for short) and `last_value` (entry price) attributes.                       |
  - **Returns**:
    | Output        | Type    | Description                                      | Required  |
    |---------------|---------|--------------------------------------------------|-----------|
    | `order_price` | `float` | The calculated stop-loss price. | Yes       |
  - **Notes**: Uses fixed internal risk parameters: 4% risk target, 1x stop-loss multiplier. For long positions: stop_loss = last_value * (1 - 0.04). For short positions: stop_loss = last_value * (1 + 0.04). You can set your own formula, too, as long as you set the order_price for both long and short positions.

-----

<a id='set_take_profit_price'></a>

### 5.3 `set_take_profit_price(app)`

  - **Purpose**: Calculates and sets the take-profit price based on the trading signal and predefined risk parameters.
  - **Input Parameters**:
    | Parameter | Type     | Required? | Description                                                                                                                                                              |
    |-----------|----------|-----------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
    | `app`     | `object` | Yes       | The trading application object, expected to have `signal` (trading direction: \>0 for long, \<0 for short) and `last_value` (entry price) attributes.                       |
  - **Returns**:
    | Output        | Type    | Description                                        | Required  |
    |---------------|---------|----------------------------------------------------|-----------|
    | `order_price` | `float` | The calculated take-profit price. | Yes       |
  - **Notes**: Uses fixed internal risk parameters: 4% return target, 1x take-profit multiplier. For long positions: take_profit = last_value * (1 + 0.04). For short positions: take_profit = last_value * (1 - 0.04). You can set your own formula, too, as long as you set the order_price for both long and short positions.

-----

<a id='prepare_base_df'></a>

### 5.4 `prepare_base_df(historical_data, train_span=None)`

  - **Purpose**: Prepares a feature-engineered DataFrame for model training and analysis from raw OHLC historical data.
  - **Input Parameters**:
    | Parameter         | Type           | Required? | Description                                                                                                                                         |
    |-------------------|----------------|-----------|-----------------------------------------------------------------------------------------------------------------------------------------------------|
    | `historical_data` | `pd.DataFrame` | Yes       | Raw input DataFrame with 'Open', 'High', 'Low', 'Close' columns and a datetime index.                                                                 |
    | `train_span`      | `int`, optional| No        | If provided, truncates the processed DataFrame to the last N observations. Defaults to `None` (uses all available data after initial processing). |
  - **Returns**:
    | Output                 | Type           | Description                                                                                                                                                             | Required  |
    |------------------------|----------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------|
    | `base_df`              | `pd.DataFrame` | Processed DataFrame with engineered features (datetime, technical indicators, lags, volatility signals), target variable ('y'), normalized, and cleaned data.         | Yes       |
    | `final_input_features` | `list`         | List of strings containing the names of the final input features generated and selected by the function (e.g., `['MONTH(index1)_1', 'trend_rsi_3', 'Open_dif_1']`). | No      |
  - **Notes**: Max window for technical indicators is internally set to 6, generating indicators for windows 3, 4, and 5. The second output can be dropped in case your strategy is based in technical indicators only, for example.

-----

<a id='get_signal'></a>

### 5.5 `get_signal(app)`

  - **Purpose**: Generates a trading signal and leverage using a pre-trained classifier and HMM-based regime detection.
  - **Input Parameters**:
    | Parameter | Type     | Required? | Description                                                                                                                                                                                                                          |
    |-----------|----------|-----------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
    | `app`     | `object` | Yes       | The trading application object. Expected attributes: `final_input_features` (list of feature names), `base_df` (DataFrame from `prepare_base_df`), `model_datetime` (datetime object for loading date-specific models). |
  - **Returns**:
    | Output     | Type           | Description                                                              | Required  |
    |------------|----------------|--------------------------------------------------------------------------|-----------|
    | `signal`   | `float`        | Trading signal: `1.0` (long), `-1.0` (short).                            | Yes       |
    | `leverage` | `float`        | Leverage for the trade (currently hardcoded to `0.02` = 2% of capital). | No       |
  - **Notes**: Relies on models in `data/models/` named with `YYYY_MM_DD` format based on `model_datetime`. Purging and embargo are set to 1 period internally. The leverage output is optional if you define it as a fixed variable in the `main.py` file.

-----

<a id='strategy_parameter_optimization'></a>

### 5.6 `strategy_parameter_optimization(seed, data_frequency, base_df_address, train_span, test_span, historical_data_address, model_datetime)`

  - **Purpose**: Executes an end-to-end pipeline to train, select, and save a trading strategy model for a specific period.
  - **Key Input Parameters**:
    | Parameter                        | Type                | Required? | Description                                                                                                                             |
    |----------------------------------|---------------------|-----------|-----------------------------------------------------------------------------------------------------------------------------------------|
    | `seed`                           | `int`               | Yes       | Random seed for reproducibility (HMM, Boruta-Shap, classifier seeds).                                                                     |
    | `data_frequency`                 | `str`               | Yes       | Resampling frequency for raw minute data (e.g., `"15min"`).                                                                             |
    | `base_df_address`                | `str`               | Yes       | Filename (relative to 'data/') to save the processed `base_df` (e.g., `"processed_data/my_base_df.csv"`).                               |
    | `train_span`                     | `int`     | Yes        | Number of periods from data end for initial `base_df` creation. If `None`, all data used.                                               |
    | `test_span`                      | `int`     | Yes        | Number of periods for test set. Defaults to 5 trading days worth of periods based on `data_frequency`.                                  |
    | `historical_data_address` | `str`               | Yes       | Path to CSV file with raw OHLC minute data (e.g., `"raw_data/stock_minute.csv"`).                                                        |
    | `model_datetime`               | `datetime.datetime` | Yes       | Market open timestamp for data alignment and model filename formatting (DD in filename is `model_datetime.day`).                   |
  - **Outputs**:
      - Saves to disk:
          - `data/models/hmm_model_YYYY_MM_DD.pickle`: Trained HMM with 2 hidden states and diagonal covariance matrix.
          - `data/models/model_object_YYYY_MM_DD.pickle`: Best trained classifier based on Sharpe ratio.
          - `data/models/optimal_features_df.xlsx`: Excel file with the list of initial features generated by `prepare_base_df` before Boruta-Shap.
          - `data/{base_df_address}`: The processed `base_df` DataFrame.
      - No explicit Python return value.
  - **Notes**: Purged window and embargo period are internally set to 1. Three classifier models are trained with different seeds; the best by Sharpe ratio is saved. HMM uses theta=0.00002 for directional change events.

-----

<a id='dependencies'></a>

## Dependencies

  - **Python Libraries**: `pickle`, `numpy`, `pandas`, `hmmlearn`, `datetime`, `sklearn` (specifically `check_random_state`, `BaggingClassifier`, `RandomForestClassifier`, `CalibratedClassifierCV`), `featuretools` (and its primitives), `ta`, `statsmodels` (`adfuller`).
  - **Custom Modules**: `trading_functions.py` (contains functions like `tf.dropLabels`, `tf.rolling_zscore_function`, `tf.create_Xy`, `tf.train_test_split`, `tf.directional_change_events`, `tf.get_periods_per_day`, `tf.library_boruta_shap`).

-----

<a id='modification-guidelines'></a>

## Modification Guidelines

### Safe Modifications

1.  **Tune Parameters**:
      - Adjust `n_estimators` or `class_weight` in `create_classifier_model()`.
      - Change fixed risk percentages or multipliers in `set_stop_loss_price()` / `set_take_profit_price()`.
      - Modify window sizes or feature list within `prepare_base_df()`.
2.  **Alter Logic**:
      - Implement a different feature selection method in `strategy_parameter_optimization()`.
      - Change the type of HMM or classifier used.
      - You can alter the whole code of the `prepare_base_df()`, `get_signal(app)` and the `strategy_parameter_optimization` functions at your discretion as long as you respect the inputs and outputs requirements as explained above.
      - You can alter the whole code of the `set_stop_loss_price()` and the `set_take_profit_price()` functions as long as you set the `order_price` output for both long and short positions.

### Restricted Modifications

1.  **Function Signatures (if called by an unchanged external system)**:
      - Radically changing the input parameters of functions like `get_signal(app)` or `set_stop_loss_price(app)` might break integration if the calling script (e.g., `main.py`) expects the current `app` object structure. If you control the calling script, you have more flexibility.
      - Removing the `historical_data` input from `prepare_base_df()` will prevent it from processing data.

### Example: Adding a New Feature in `prepare_base_df`

```python
def prepare_base_df(historical_data, train_span=None):
    # ... (existing setup) ...
    max_window = 6
    df = historical_data.copy()

    # ... (Section 1 & 2 remain largely the same) ...

    # Add your new feature, e.g., a custom volatility measure
    df['custom_volatility'] = df['Close'].rolling(window=10).std() * np.sqrt(252) # Example

    # ... (rest of Section 3, including technical_features_df creation) ...

    # Ensure your new feature is added to scalable_features if it needs normalization
    # scalable_features.append('custom_volatility') # If it's added before base_df concat

    # Concatenate your feature if it's not already part of df
    # base_df = pd.concat([technical_features_df, df[ohlc_lags_list], datetime_features, df[['custom_volatility']]], axis=1)
    # Or if 'custom_volatility' was added to 'df' directly earlier:
    base_df = pd.concat([technical_features_df, df[ohlc_lags_list + ['custom_volatility']], datetime_features], axis=1)


    # ... (rest of the function, ensuring 'custom_volatility' is in final_input_features) ...
    final_input_features = base_df.columns.tolist() # This might be too broad, be specific
    # Or more carefully:
    # final_input_features.append('custom_volatility') # After existing features are added to this list

    # ... (Section 4 & 5) ...
    # Ensure 'custom_volatility' is included in scalable_features if it needs z-scoring
    # scalable_features.append('custom_volatility') # Before calling rolling_zscore_function

    # base_df, _ = tf.rolling_zscore_function(base_df, scalable_features, 30)

    return base_df, final_input_features
```

**Note on Example**: When adding features, ensure they are included in `final_input_features` and, if applicable, in `scalable_features` for normalization. The exact point of addition to `final_input_features` and `base_df` concatenation depends on how the feature is derived.
