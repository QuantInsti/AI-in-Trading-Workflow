## An end-to-end setup to trade stocks algorithmically

#### This is your "Start here" document to set up your system for trading stocks algorithmically.
###### QuantInsti Webpage: https://www.quantinsti.com/

**Version 1.0.0**
**Last Updated**: 2025-07-09

-----
## Disclaimer

#### This file is documentation only and should not be used for live trading without appropriate backtesting and tweaking of the strategy parameters.

## Licensed under the Apache License, Version 2.0 (the "License"). 
- Copyright 2024 QuantInsti Quantitative Learnings Pvt Ltd. 
- You may not use this file except in compliance with the License. 
- You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 
- Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

## Table of contents
1. [Introduction](#introduction)
2. [Crucial Attributes](#crucial_attributes)
3. [Setup Notes](#setup_notes)
4. [Interactive Brokers setup requirements](#ib_requirements)
5. [Setup of variables](#variables_setup)

<a id='introduction'></a>
## Introduction 
We are happy to introduce a working version of our Python-based setup to trade stocks algorithmically. It is meant for stock trading with the Interactive Brokers API. This script allows you to execute transactions in the stock market using a customizable strategy, and swap out stock assets as needed. 

The script-based application aims to teach you how to use a ready-made IB-API-based trading setup and how it works during each trading period. We refer to our labor of love as a Python-based setup, trading app, or similar such names. We hope it's self-evident that they all refer to the same thing!

<a id='crucial_attributes'></a>
## Crucial attributes:
- stock trading: Our script functions and is optimized for this asset class in a streamlined manner because we created it with stock trading in mind. You can execute trades confidently because we've created it considering the nuances of the stock markets. 
- Strategy customization: Our script empowers you to modify trading strategies according to your preferences and market conditions. You can control your trading approach by adjusting risk parameters or refining entry and exit criteria.
- Flexible asset selection: You can modify your trading strategies to profit from any stock by having the flexibility to switch up your stock assets. You can use this trading application on as many stocks as IB allows.
- Integration with Interactive Brokers API: Our script utilizes the Interactive Brokers API to allow you to execute trades quickly and connect you to real-time stock market data. This integration ensures reliable access to market data and execution capabilities.
- Effective operation: Devoid of graphical user interfaces, we use only scripts if you want to quickly learn the intricacies of the trading setup code. You can make trades quickly and concentrate on the main file variables of the trading app.

<a id='setup_notes'></a>
## Setup notes
1. If you want to use the same strategy to check how the setup works, you should only need to modify the "main.py" file . In case you want to modify the strategy at your convenience, please also modify the "strategy.py" file (both files are located in the "user_config" folder). Only stock contracts should be traded with this trading app.
2. If you run the trading setup for the first time, you'll see that you'll be downloading historical minute data. It will take like 3 to 5 days to complete the downloading (it will download from 2005 to 2024). This only happens at the very first time. Once you have the historical minute data up to date, you'll have the trading setup running.
3. The stock market closes at 4 pm Eastern time and the stop-loss and take-profit targets get discarded at market close. Each day the setup will close all the existing positions before market close. 
4. The setup will not leave any open positions on weekends. 
5. The strategy is based on bagging with a random forest algorithm. It creates long and short signals. To learn more about it, refer to the MLT-04 lecture.
6. The trading setup is designed to retrieve historical data from up to 10 previous days. If your historical data has missing data for more than 10 days, you'll need to run the setup to download historical data and update the dataframe.
7. In case you want to get the live equity curve of the strategy, once you start trading, please go to the "database.xlsx" Excel file, sheet "cash_balance", column "value". Plot that column to see the equity curve graphically.
8. In case you want to make more changes to the setup so it can be better customized per your needs, please modify all the other relevant files as needed.

<a id='ib_requirements'></a>
## Interactive Brokers setup requirements

1. Installation of the **offline stable** version of the TWS. Save the TWS file in "path_to/Jts/tws_platform"
2. Installation of the **stable** version of the IB API. Save the IB API files in "path_to/Jts/tws_api"
3. Log in with your account credentials in the IB web platform and then go to Settings. Next, in the "Account Configuration" section, click on "Paper Trading Account". Finally, click on the "Yes" button against the question "Share real-time market data subscriptions with paper trading account?" and click on "Save". Wait at least 2 hours to let IB make the paper account have market data subscriptions.
4. In the TWS or IB Gateway platform, do the following: Go to File, Global configuration, API, and in Settings:
    1. Check "ActiveX and Socket Clients"
    2. Uncheck the "Read-Only API"
    3. In the "send instrument-specific attributes for dual-mode API client in" box, select "operator timezone".
    4. Click on the "Reset API order ID sequence" whenever you need to restart paper or live trading.
5. In the TWS or IB Gateway platform, do the following: Go to File, Global configuration, Configuration and in "Lock and Exit":
    - In the "Set Auto Logoff Timer" section, choose your local time to auto-log off or auto-restart the platform. Due to the IB platform specifications, in case you select auto-restart, it must restart at the specific hour you select. Be careful with this. When selecting auto restart, sometimes it doesn't work properly, so you might need to log in to the platform again manually. 
6. In Configuration, Export trade Reports, check the "Export trade reports periodically".
7. In the same section from above, in the "Export filename", type: "\path_to\Jts\setup\user_config\data\reports\report.txt". This file will give you a trade report of all the trading positions you took while trading.
8. In the same section from above, in the "Export directory", type: "\path_to\Jts\setup\user_config\data\reports". This folder will be used to save the trade report from above.
9. In the same section above, specify the interval at which you would like the reports to be generated.
10. Depending on your initial equity and trading frequency, you will have different equity curves throughout time. If you first want to try paper trading, you should set the initial equity value. To do this, please go to https://www.interactivebrokers.co.uk/sso/Login and do the following:
    1. Select "Paper", instead of "Live"
    2. Login with your username and password
    3. Go to "Settings"
    4. Go to "Account Settings"
    5. In "Configuration", click on the nut button of the "Paper Trading Account Reset"
    6. In the "Select Reset Amount" box, click on "Other Amount". In the "Amount" box, write a specific amount you want to use as an initial equity value. Read the below instructions and click on Continue.
11. In case you want to reset the paper trading account to default settings, do the following:
    1. Drop all the created files saved in the "data" folder and sub-folders.
    2. Go to the TWS platform, go to the "File" tab, click on "Global Configuration", click on "API settings", and click on the "Reset API order ID sequence" button. Finally, click on "Apply" and "Ok". Then you can paper trade once again from the start. In case you have live traded, please close any existing position on any asset before you restart live trading with the app.
12. To profit from stock leverage, you need to **ask IB to have a margin account for stocks**. If you don't do it, you will not be able to trade at all your capacity.

<a id='variables_setup'></a>
## Setup of variables
Inside the "main.py" file, you can change the following variables per your trading requirements. Each variable is explained and some extra information is added.

### Core Trading Configuration
- **account**: The account name of your IB account. This account name starts with U followed by a number for a live trading account and starts with DU followed by a number for a paper trading account. The system automatically detects paper vs live accounts based on the port number (4796/4001 for live, 7497 for paper). Learn more in the TBP-01 lecture.

- **timezone**: Set the timezone of your country of residence using the format 'Continent/City' (e.g., 'America/Lima', 'Europe/London', 'Asia/Tokyo'). This is used to convert between your local time and the stock exchange timezone for proper trading schedule calculations. The system uses pytz library for timezone handling.

- **port**: The port number for connecting to IB TWS or Gateway. Common ports: 7497 (paper trading), 7496 (live trading TWS), 4001 (live trading Gateway). The system uses this to determine if you're using paper or live trading.

- **host**: The host address for connecting to IB TWS or Gateway. Typically set to '127.0.0.1' for local connections. This is passed to the IB API's connect() method.

- **client_id**: A unique identifier for this trading application instance. Must be different from other applications connected to the same TWS/Gateway. The system uses this to establish the connection and manage multiple client sessions.

- **account_currency**: The base currency of your IB account (e.g., 'USD', 'EUR', 'INR'). This is used for capital calculations and currency conversions when trading stocks denominated in different currencies.

- **symbol**: The stock symbol to be traded (e.g., 'AAPL', 'MSFT', 'GOOGL'). Must be a valid symbol available on the specified primary exchange. The system uses this to create the contract object for trading.

- **primary_exchange**: The primary exchange where the stock is listed (e.g., 'NYSE', 'NASDAQ', 'NSE'). This is used to fetch contract details and trading hours from IB. The system calls `get_tradable_dates_and_stock_currency()` to get exchange-specific information.

- **tick_size**: The minimum price movement for the stock (e.g., 0.01 for penny stocks, 0.05 for others). Set to 0.0 for automatic detection from IB contract details. Used for price rounding in order placement.

### Trading Strategy Configuration
- **trading_type**: The trading strategy schedule with three options:
  - 'intraday': Trades throughout the day at specified intervals
  - 'open_to_close': Trades from market open to close with position management
  - 'close_to_open': Trades from market close to next day's open (overnight positions)
  The system uses this to determine trading windows and position management logic.

- **data_frequency**: The frequency for data bars and trading decisions (e.g., '5min', '15min', '1h', '1D'). The system converts this to IB API bar size format and calculates periods per day. For daily trading, use '1D'. Higher frequencies require more computational time for signal generation.

- **restart_time**: The local timezone time for TWS auto-restart in 'HH:MM' format (e.g., '23:00'). The system uses this to schedule daily restarts and ensure fresh connections. Must match your TWS auto-restart setting.

- **time_after_open**: Minutes to wait after market open before starting trades (default: 2). This avoids initial market volatility and ensures stable price feeds.

- **time_before_close**: Minutes before market close to stop trading (default: 150). This ensures all positions are properly managed before market close.

### Machine Learning and Optimization
- **optimization**: Boolean flag to enable/disable strategy parameter optimization. When True, the system runs `strategy_parameter_optimization()` to train new models. When False, uses existing pre-trained models.

- **daily_optimization**: Boolean flag to enable/disable daily model retraining. When True, the system checks if optimization is needed for the current trading day and runs optimization if required.

- **base_df_address**: File path for the feature-engineered dataframe (e.g., 'app_base_df.csv'). This contains technical indicators and features used by the machine learning model. The system loads this for signal generation.

- **train_span**: Number of historical periods to use for model training (default: 3500). This determines how much historical data is used to fit the machine learning model. Should be less than available data in your historical dataset.

- **test_span_days**: Number of days to use for validation/testing (default: 1). The system multiplies this by periods per day to get the test span. Used for model evaluation and backtesting.

- **seed**: Random seed for reproducible model training (default: 2025). The system uses this to generate multiple random seeds for ensemble model creation. Each seed creates a different model variant.

### Risk Management
- **risk_management_bool**: Boolean flag to enable/disable risk management features. When True, the system automatically places stop-loss and take-profit orders. When False, only market orders are placed.

- **trail**: Boolean flag to enable/disable trailing stop-loss orders. When True, uses IB's TRAIL order type. When False, uses standard STP stop-loss orders. The trailing stop follows the price movement.

- **leverage**: Position sizing multiplier (default: 0.02 = 2% of capital). This determines what percentage of your account capital to risk per trade. The system calculates position size as: (capital * leverage) / current_price.

### Execution Settings
- **smart_bool**: Boolean flag to enable/disable IB SMART routing. When True, uses 'SMART' exchange for order routing. When False, uses the stock's primary exchange. SMART routing finds the best execution venue.

- **fractional_shares**: Boolean flag to enable/disable fractional share trading. When True, allows decimal quantities in orders. When False, rounds to whole shares. Requires account support for fractional trading.

### Strategy File
- **strategy_file**: Name of the strategy file to import (default: 'strategy.py'). The system dynamically imports this file to access strategy functions like `get_signal()`, `set_stop_loss_price()`, etc.

### Email Notifications
- **smtp_username**: Gmail address for sending trading notifications (e.g., 'youremail@gmail.com'). The system uses this to authenticate with Gmail's SMTP server.

- **to_email**: Email address to receive trading notifications (e.g., 'youremail@gmail.com'). Can be the same as smtp_username or different. The system sends daily trading summaries to this address.

- **password**: Gmail app password (16-character string). This is NOT your regular Gmail password. You must generate an app password in Google Account settings. The system uses this for SMTP authentication.

### Additional Strategy Variables
You can add additional variables in the "Set the additional variables you would like to add for the strategy functions" section of main.py. These variables are passed to your strategy functions and can be used to customize trading parameters. For example:
- `num_technical_indicators`: Number of technical indicators to calculate
- `leverage`: Override the default leverage setting
- Any other parameters your strategy functions need

### System-Generated Variables
The following variables are automatically calculated by the system and should not be modified:
- `test_span`: Calculated as `test_span_days * periods_per_day`
- `historical_data_address`: Set to 'data/historical_data.csv'
- `model_datetime`: Set to the current trading day for model loading
- `stock_timezone`: Retrieved from IB contract details
- `fractional_shares`: Set based on account capabilities
