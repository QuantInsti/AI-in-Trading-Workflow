"""
## Licensed under the QuantInsti Open License (QOL) v1.1 (the "License").
- Copyright 2025 QuantInsti Quantitative Learning Pvt. Ltd.
- You may not use this file except in compliance with the License.
- You may obtain a copy of the License in LICENSE.md at the repository root or at https://www.quantinsti.com.
- Non-Commercial use only; see the License for permitted use, attribution, and restrictions.
"""

# Import the engine file
from ibkr_stock import engine

# Set all the variables you need for the trading app
###############################################################################
###############################################################################
""" Set the variables as per your trading specifications"""
# Set account name in case you do paper trading
account = 'DU7638356'
# Set the time zone
timezone = 'America/Lima'
# The app port
port = 7497
# The app host
host='127.0.0.1'
# The client id
client_id=1
# The account base currency symbol
account_currency = 'USD'
# The asset symbol
symbol = 'AAPL'
# Optimization to be done
optimization = False
# The daily optimization boolean
daily_optimization = True
# The trading strategy schedule
trading_type = 'close_to_open'
# The data frequency for trading
data_frequency = '5min'
# The auto-restart time
restart_time = '23:00'
# The minutes after the Opening market time
time_after_open = 2
# The minutes before the Closing market time
time_before_close = 150
# The primary exchange - FIXED: AAPL trades on NASDAQ, not NSE
primary_exchange = 'ISLAND'
# The exchange tick size - FIXED: AAPL tick size is 0.01
tick_size = 0.01
# The boolean of the IB SMART execution algorithm
smart_bool = False
# The boolean for the risk management process
risk_management_bool = True
# The base_df file address
base_df_address = 'app_base_df.csv'
# The train span 
train_span = 3500
# Set the number of days to set the test data number of rows   
test_span_days = 1
# Set the seed for the machine-learning model
seed = 2025
# Set the trailing stop loss boolean
trail = False
# Set the strateg file to be used
strategy_file = 'strategy.py'
# The email that will be used to send the emails
smtp_username = 'youremail@gmail.com'
# The email to which the trading info will be sent. It can be the above or any other email
to_email = 'youremail@gmail.com'
# The app password that was obtained in Google. You need to allow app password in Google: https://support.google.com/mail/answer/185833?hl=en
password = 'xreh bdtl tiug dmvn'
# ADDED: Fractional shares support for stocks
fractional_shares = True
###############################################################################
""" Set the additional variables you would like to add for the strategy functions"""
# Example
num_technical_indicators = 50
leverage = 0.02
# ...
###############################################################################
