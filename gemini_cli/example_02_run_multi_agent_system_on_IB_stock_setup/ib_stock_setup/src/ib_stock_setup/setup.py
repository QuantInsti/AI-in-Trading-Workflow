"""
## Licensed under the Apache License, Version 2.0 (the "License"). 
- Copyright 2025 QuantInsti Quantitative Learnings Pvt Ltd. 
- You may not use this file except in compliance with the License. 
- You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 
- Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""

# Import the necessary libraries
import os
import time
import numpy as np
import pandas as pd
import datetime as dt
from ib_stock_setup import ib_functions as ibf
from threading import Event
from ib_stock_setup import trading_functions as tf
from ibapi.client import EClient
from ibapi.wrapper import EWrapper

# Define the main trading application class, inheriting from IBKR's EClient and EWrapper.
class trading_app(EClient, EWrapper):
    
    # The constructor for the class, responsible for initializing the app's state and configuration.
    def __init__(self, logging, account, account_currency, stra_opt_dates_filename, contract, timezone, trading_type, 
                      data_frequency, 
                      risk_management_bool, base_df_address,  
                      market_week_open_time, market_week_close_time, 
                      trader_start_datetime, trader_start_adj_datetime, trader_end_datetime, day_datetime_before_end, trader_next_start_datetime, trader_next_end_datetime,
                      current_period, previous_period, next_period, train_span, test_span, trail, leverage, fractional_shares, optimization, tick_size, strategy_file):
        
        # Initialize the parent classes, EClient and EWrapper.
        EClient.__init__(self, self)
        
        # Record the exact time when the app object is created, used for performance tracking.
        self.app_start_time = dt.datetime.now()
        
        # Store the account's base currency (e.g., 'USD').
        self.account_currency = account_currency
        
        # This logic to check the port is commented out but would determine if it's a paper or live account.
        # Set the account string depending on whether we're using a paper or real account
        if self.port == 4796 or self.port == 4001:
            # Set the account string for a live account.
            self.account = 'account'
        else:
            # Store the paper trading account number provided from the configuration.
            self.account = account
            
        # Store the file path for the main historical data CSV.
        self.historical_data_address = 'data/historical_data.csv'

        # Check if the strategy uses machine learning optimization.
        if optimization:
            # If so, read the date of the last strategy optimization from its tracking file.
            self.model_datetime = pd.read_csv(stra_opt_dates_filename, index_col=0, parse_dates=True).index[-1]
            # Load the historical data from the CSV file into a pandas DataFrame.
            self.historical_data = pd.read_csv(self.historical_data_address, index_col=0, parse_dates=True)
        # Store the data frequency (e.g., '5min', '1D').
        self.data_frequency = data_frequency
        # Store the user's local timezone.
        self.zone = timezone
        
        # Store the calculated open time for the current trading week.
        self.market_week_open_time = market_week_open_time
        # Store the calculated close time for the current trading week.
        self.market_week_close_time = market_week_close_time
        # Store the official start datetime of the current trading day.
        self.trader_start_datetime = trader_start_datetime
        # Store the adjusted start datetime (after market open volatility) for placing trades.
        self.trader_start_adj_datetime = trader_start_adj_datetime
        # Store the calculated end-of-day cutoff time for placing trades.
        self.trading_day_end_datetime = day_datetime_before_end
        # Store the official end datetime of the current trading day.
        self.trader_end_datetime = trader_end_datetime
        # Store the start datetime of the next trading day.
        self.trader_next_start_datetime = trader_next_start_datetime
        # Store the end datetime of the next trading day.
        self.trader_next_end_datetime = trader_next_end_datetime
        # Store the current trading period's timestamp.
        self.current_period = current_period
        # Store the previous trading period's timestamp.
        self.previous_period = previous_period
        # Store the next trading period's timestamp.
        self.next_period = next_period
        # Store the number of periods to use for the training dataset.
        self.train_span = train_span
        # Store the number of periods to use for the test dataset.
        self.test_span = test_span
        # Store the file path for the feature-engineered dataframe.
        self.base_df_address = base_df_address
        # Store the boolean flag for enabling risk management (stop-loss/take-profit).
        self.risk_management_bool = risk_management_bool
        # Store the boolean flag for allowing fractional share trading.
        self.fractional_shares = fractional_shares
        # Store the type of trading strategy being executed (e.g., 'intraday').
        self.trading_type = trading_type
        
        # Get the numerical value and string part of the data frequency using a helper from 'trading_functions.py'.
        self.frequency_number, self.frequency_string = tf.get_data_frequency_values(data_frequency)
        
        # Load the main database file, which is an Excel workbook.
        database = pd.ExcelFile('data/database.xlsx')
        # Load the 'open_orders' sheet from the database into a DataFrame.
        self.open_orders = pd.read_excel(database, "open_orders", index_col = 0)
        # Load the 'orders_status' sheet into a DataFrame.
        self.orders_status = pd.read_excel(database, "orders_status", index_col = 0)
        # Load the 'executions' sheet into a DataFrame.
        self.exec_df = pd.read_excel(database, "executions", index_col = 0)
        # Load the 'commissions' sheet into a DataFrame.
        self.comm_df = pd.read_excel(database, "commissions", index_col = 0)
        # Load the 'positions' sheet into a DataFrame.
        self.pos_df = pd.read_excel(database, "positions", index_col = 0)
        # Load the 'cash_balance' sheet into a DataFrame.
        self.cash_balance = database.parse("cash_balance", index_col = 0)

        # Convert the index of the open_orders dataframe to datetime objects for time-series analysis.
        self.open_orders.index = pd.to_datetime(self.open_orders.index)
        # Convert the index of the orders_status dataframe.
        self.orders_status.index = pd.to_datetime(self.orders_status.index)
        # Convert the index of the executions dataframe.
        self.exec_df.index = pd.to_datetime(self.exec_df.index)
        # Convert the index of the commissions dataframe.
        self.comm_df.index = pd.to_datetime(self.comm_df.index)
        # Convert the index of the positions dataframe.
        self.pos_df.index = pd.to_datetime(self.pos_df.index)
        # Convert the index of the cash_balance dataframe.
        self.cash_balance.index = pd.to_datetime(self.cash_balance.index)

        # Load the 'app_time_spent' sheet, which tracks performance.
        self.app_time_spent = database.parse("app_time_spent", index_col=0)
        # Get the time spent from the previous run to estimate time needed for the current run.
        self.previous_time_spent = float(self.app_time_spent['seconds'].iloc[0])        

        # Load the 'periods_traded' sheet, which logs which periods have been processed.
        self.periods_traded = database.parse("periods_traded", index_col = 0)
        
        # Convert the 'trade_time' column to datetime objects.
        self.periods_traded['trade_time'] = pd.to_datetime(self.periods_traded['trade_time'])
        
        # Add a new row for the current trading period, marking it as not yet traded (trade_done = 0).
        self.periods_traded.loc[len(self.periods_traded.index),:] = [current_period, 0, trader_start_datetime, trader_end_datetime, market_week_open_time, market_week_close_time]
        
        # Initialize an empty DataFrame to temporarily hold newly downloaded historical data.
        self.new_df = pd.DataFrame()
       
        
        # Store the fully defined contract object for the asset being traded.
        self.contract = contract
        
        # Initialize a dictionary to store any error messages received from the API.
        self.errors_dict = {}
        
        # Store the leverage value to be used for trading.
        self.leverage = leverage
        
        # Check if a file containing optimal features exists (for ML strategies).
        if os.path.exists('data/models/optimal_features_df.xlsx'):            
            # If it exists, load the features from the Excel file.
            features_df = pd.read_excel('data/models/optimal_features_df.xlsx', index_col=0)
            # Store the list of feature names to be used in the strategy.
            self.final_input_features = features_df['final_features'].dropna().tolist()
        else:
            # If the file doesn't exist, print a warning.
            print('There were no final features saved in the strategy_parameter_optimization function')
        
        # Initialize the stop-loss order ID to NaN (Not a Number).
        self.sl_order_id = np.nan
        # Initialize the take-profit order ID to NaN.
        self.tp_order_id = np.nan
        
        # Initialize a counter, potentially for tracking repeated errors or actions.
        self.count = 0
        # Initialize a counter for tracking failures in getting the last price tick.
        self.last_value_count = 0
        
        # Initialize an empty DataFrame to hold incoming account update information.
        self.acc_update = pd.DataFrame()        
        # Initialize a dictionary to manage threading events for historical data downloads.
        self.hist_data_events = {}
        # Create a threading Event for the BID data request (though not used in this logic).
        self.hist_data_events['0'] = Event()
        # Create a threading Event for the ASK data request (though not used in this logic).
        self.hist_data_events['1'] = Event()
        # Create a threading Event to signal the completion of an open orders request.
        self.orders_request_event = Event()
        # Create a threading Event to signal the completion of a positions request.
        self.positions_request_event = Event()
        # Create a threading Event to signal the completion of an account update request.
        self.account_update_event = Event()
        # Create a threading Event to signal the completion of an executions request.
        self.executions_request_event = Event()

        # Initialize temporary dataframes to stage incoming data from API callbacks before merging with main dataframes.
        self.acc_update = pd.DataFrame()
        self.temp_open_orders = pd.DataFrame()
        self.temp_orders_status = pd.DataFrame()
        self.temp_exec_df = pd.DataFrame()
        self.temp_comm_df = pd.DataFrame()  
        self.temp_pos_df = pd.DataFrame() 
        
        # Store the boolean flag for using a trailing stop-loss.
        self.trail = trail
        
        # Initialize a flag to indicate if the strategy logic for a period has finished.
        self.strategy_end = False
        
        # Store the logging object for use throughout the class.
        self.logging = logging
        
        # Store the boolean flag indicating if optimization is enabled.
        self.optimization = optimization
        
        # Store the minimum price increment (tick size) for the asset.
        self.tick_size = tick_size
        
        # Store the filename of the strategy being used.
        if '.py' not in strategy_file:
            # Add the '.py' extension if it's missing.
            self.strategy_file = strategy_file+'.py'
        else:
            # Use the filename as is.
            self.strategy_file = strategy_file
        
    # This is an EWrapper callback function that is triggered when an error is received from the IBKR server.
    def error(self, reqId, code, msg, advancedOrderRejectJson=''):
        # This comment explains the purpose of the error callback.
        ''' Called if an error occurs '''
        # Store the error message in the errors dictionary with the code as the key.
        self.errors_dict[code] = msg
        # Print the error details to the console.
        print('Error: {} - {} - {}'.format(reqId, code, msg))
        # Log the same error details to the log file.
        self.logging.info('Error: {} - {} - {}'.format(reqId, code, msg))
                
    # This EWrapper callback is triggered by the server to provide the next valid order ID.
    def nextValidId(self, orderId):
        # This comment explains the purpose of the nextValidId callback.
        ''' Set the next order id '''
        # Check if the application is currently connected to the server.
        if self.isConnected():
            # Call the parent class's method to ensure proper behavior.
            super().nextValidId(orderId)
            # Store the received order ID in an instance variable for use when placing new orders.
            self.nextValidOrderId = orderId
            # Print the next valid ID to the console.
            print("NextValidId:", orderId)
            # Log the next valid ID.
            self.logging.info("NextValidId: {}".format(orderId))
            # Pause for 1 second to ensure the ID is processed before any new order is placed.
            time.sleep(1)
        else:
            # If not connected, exit the function.
            return
    
    # This EWrapper callback is triggered for each open order in response to a reqOpenOrders() request.
    def openOrder(self, orderId, contract, order, orderState):
        # This comment explains the purpose of the openOrder callback.
        ''' Function to call the open orders '''
        # Call the parent class's method.
        super().openOrder(orderId, contract, order, orderState)
        # Create a dictionary to structure the received open order data.
        dictionary = {"PermId":order.permId, \
                      "ClientId": order.clientId, \
                      "OrderId": orderId, 
                      "Account": order.account, \
                      "Symbol": contract.symbol, \
                      "SecType": contract.secType,
                      "Exchange": contract.exchange, \
                      "Action": order.action, \
                      "OrderType": order.orderType,
                      "TotalQty": float(order.totalQuantity), \
                      "CashQty": order.cashQty, 
                      "LmtPrice": order.lmtPrice, \
                      "AuxPrice": order.auxPrice,\
                      "Status": orderState.status,\
                      "datetime":dt.datetime.now().replace(microsecond=0)}
        # Append the new order data as a new row to the temporary open orders dataframe.
        self.temp_open_orders = pd.concat([self.temp_open_orders, pd.DataFrame(dictionary, index=[0])], ignore_index=True)

        
    # This EWrapper callback provides status updates for any order.
    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, \
                    permId, parentId, lastFillPrice, clientId, whyHeld, \
                    mktCapPrice):
        # This comment explains the purpose of the orderStatus callback.
        ''' Function to call the orders status'''
        # Call the parent class's method.
        super().orderStatus(orderId, status, filled, remaining, \
                            avgFillPrice, permId, parentId, lastFillPrice, \
                            clientId, whyHeld, mktCapPrice)
        
        # Create a dictionary to structure the received order status data.
        dictionary = {"OrderId": orderId, \
                      "Status":status, \
                      "Filled":filled, \
                      "PermId":permId, \
                      "ClientId": clientId, \
                      "Remaining": float(remaining), \
                      "AvgFillPrice": avgFillPrice, \
                      "LastFillPrice": lastFillPrice, \
                      "datetime":dt.datetime.now().replace(microsecond=0)}
        # Append the new status data as a new row to the temporary orders status dataframe.
        self.temp_orders_status = pd.concat([self.temp_orders_status, pd.DataFrame(dictionary, index=[0])], ignore_index=True)
                
    # This EWrapper callback is triggered when all open order data has been sent by the server.
    def openOrderEnd(self):
        # Print a confirmation message.
        print("Open orders request was successfully completed")
        # Set the threading event to signal that the request is complete, unblocking the main script.
        self.orders_request_event.set()

    # This EWrapper callback is triggered for each execution (fill) of a trade.
    # Receive details when orders are executed        
    def execDetails(self, reqId: int, contract, execution):
        # This comment explains the purpose of the execDetails callback.
        ''' Function to call the trading executions'''
        # Print a status message.
        print('Requesting the trading executions...')
        # Log the status message.
        self.logging.info('Requesting the trading executions...')
        
        # Call the parent class's method.
        super().execDetails(reqId, contract, execution)
        # Create a dictionary to structure the received execution data.
        dictionary = {"OrderId": execution.orderId,  
                      "PermId":execution.permId, \
                      "ExecutionId":execution.execId, \
                      "Symbol": contract.symbol, \
                      "Side":execution.side, \
                      "Price":execution.price, \
                      "AvPrice":execution.avgPrice, \
                      "cumQty":execution.cumQty, \
                      "Currency":contract.currency, \
                      "SecType": contract.secType, \
                      "Position": float(execution.shares), \
                      "Execution Time": execution.time, \
                      "Last Liquidity": execution.lastLiquidity, \
                      "OrderRef":execution.orderRef, \
                      "datetime":dt.datetime.now().replace(microsecond=0)}
            
        # Append the new execution data to the temporary executions dataframe.
        self.temp_exec_df = pd.concat([self.temp_exec_df, pd.DataFrame(dictionary, index=[0])], ignore_index=True)
        
    # This EWrapper callback provides a report on the commission charged for a trade.
    def commissionReport(self, commissionReport):
        # This comment explains the purpose of the commissionReport callback.
        ''' Function to call the trading commissions'''
        # Print a status message.
        print('Requesting the trading commissions...')
        # Log the status message.
        self.logging.info('Requesting the trading commissions...')
        
        # Call the parent class's method.
        super().commissionReport(commissionReport)
        # Create a dictionary to structure the received commission data.
        dictionary = {"ExecutionId":commissionReport.execId, \
                      "Commission": commissionReport.commission, \
                      "Currency":commissionReport.currency, \
                      "Realized PnL": float(commissionReport.realizedPNL), \
                      "datetime":dt.datetime.now().replace(microsecond=0)}
            
        # Append the new commission data to the temporary commissions dataframe.
        self.temp_comm_df = pd.concat([self.temp_comm_df, pd.DataFrame(dictionary, index=[0])], ignore_index=True)

    # This EWrapper callback is triggered when all execution details for a request have been received.
    def execDetailsEnd(self, reqId: int):
        # Call the parent class's method.
        super().execDetailsEnd(reqId)
        # Print a confirmation message with the request ID.
        print("Trading executions request was successfully finished. ReqId:", reqId)
        # Set the threading event to signal that the request is complete.
        self.executions_request_event.set()
                
    # This EWrapper callback is triggered for each position held in the account.
    # Receive the positions from the TWS
    def position(self, account, contract, position, avgCost):
        # This comment explains the purpose of the position callback.
        ''' Function to call the trading positions'''
        # Print a status message.
        print('Requesting the trading positions...')
        # Log the status message.
        self.logging.info('Requesting the trading positions...')
        # Call the parent class's method.
        super().position(account, contract, position, avgCost)
        # Create a dictionary to structure the received position data.
        dictionary = {"Account":account, "Symbol": contract.symbol, \
                      "SecType": contract.secType,
                      "Currency": contract.currency, "Position": float(position), \
                      "Avg cost": avgCost, "datetime":dt.datetime.now().replace(microsecond=0)}
            
        # Append the new position data to the temporary positions dataframe.
        self.temp_pos_df = pd.concat([self.temp_pos_df, pd.DataFrame(dictionary, index=[0])], ignore_index=True)
        
    # This EWrapper callback is triggered when all position data has been received.
    # Display message once the positions are retrieved
    def positionEnd(self):
        # Print a confirmation message.
        print('Positions Retrieved.')
        # Set the threading event to signal that the request is complete.
        self.positions_request_event.set()
                
    # This EWrapper callback is triggered for each bar of historical data received.
    # Receive historical bars from TWS
    def historicalData(self, reqId, bar):
        # This comment explains the purpose of the historicalData callback.
        ''' Function to call the historical data'''
        # Add the Close price of the current bar to the 'new_df' dataframe, using the bar's date as the index.
        self.new_df.loc[bar.date,'Close'] = bar.close
        # Add the Open price.
        self.new_df.loc[bar.date,'Open'] = bar.open
        # Add the High price.
        self.new_df.loc[bar.date,'High'] = bar.high
        # Add the Low price.
        self.new_df.loc[bar.date,'Low'] = bar.low
        # Add the Volume.
        self.new_df.loc[bar.date,'Volume'] = bar.volume
                        
    # This EWrapper callback is triggered when all historical data for a request has been received.
    # Display a message once historical data is retrieved
    def historicalDataEnd(self,reqId,start,end):
        # Call the parent class's method.
        super().historicalDataEnd(reqId,start,end)
        # Print a confirmation message.
        print("Historical Data Download finished...")
        # Log the confirmation message.
        self.logging.info("Historical Data Download finished...")
        # Set the threading event to signal that the download is finished.
        self.event.set()

    # This EWrapper callback receives real-time midpoint price updates.
    def tickByTickMidPoint(self, reqId, tick_time, midpoint):
        # This comment explains the purpose of the tickByTickMidPoint callback.
        ''' Function to call in response to reqTickByTickData '''
        # Store the received midpoint price in the 'last_value' attribute.
        self.last_value = midpoint
                        
    # This EWrapper callback receives updates on account values (like cash balance, equity, etc.).
    def updateAccountValue(self, key, value, currency, accountName):
        # This comment explains the purpose of the updateAccountValue callback.
        ''' Function to call the account values'''
        # Call the parent class's method.
        super().updateAccountValue(key, value, currency, accountName)
        # Create a dictionary to structure the received account data.
        dictionary = {"key":key, "Account": accountName, "Value": value, \
                      "Currency": currency, "datetime":dt.datetime.now().replace(microsecond=0)}
                        
        # Append the new account data to the temporary account update dataframe.
        self.acc_update = pd.concat([self.acc_update, pd.DataFrame(dictionary, index=[0])], ignore_index=True)
            
    # This EWrapper callback provides the server time of the last account update.
    def updateAccountTime(self, timeStamp: str):
        # Print the timestamp to the console.
        print("Account update time is:", timeStamp)
         
    # This EWrapper callback is triggered when the initial download of account data is complete.
    def accountDownloadEnd(self, accountName: str):
        # Print a confirmation message with the account name.
        print("Account download was done for account:", accountName)
        # Log the confirmation message.
        self.logging.info(f"Account download was done for account: {accountName}")
        # Set the threading event to signal that the request is complete.
        self.account_update_event.set()
