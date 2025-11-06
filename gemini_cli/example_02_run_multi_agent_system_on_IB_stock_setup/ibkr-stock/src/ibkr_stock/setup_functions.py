"""
## Licensed under the QuantInsti Open License (QOL) v1.1 (the "License").
- Copyright 2025 QuantInsti Quantitative Learning Pvt. Ltd.
- You may not use this file except in compliance with the License.
- You may obtain a copy of the License in LICENSE.md at the repository root or at https://www.quantinsti.com.
- Non-Commercial use only; see the License for permitted use, attribution, and restrictions.
"""

# Import the necessary libraries
import math
import time
import smtplib
import inspect
import numpy as np
import pandas as pd
import datetime as dt
import yfinance as yf
import strategy as stra
from decimal import Decimal
from threading import Event
from ibkr_stock import trading_functions as tf
from ibkr_stock import ib_functions as ibf
from concurrent.futures import ThreadPoolExecutor
from ibapi.order_cancel import OrderCancel

def connection_monitor(app):
    ''' Check continuously if there's a need to disconnect the app '''

    while True:
        # If the app is disconnected
        if not app.isConnected():
            print("Not connected. Breaking loop...")
            app.logging.info("Not connected. Breaking loop.")
            stop(app)
            break
        # If the app is disconnected based on the errors' dictionary
        if (502 in list(app.errors_dict.keys())):
            print("Not connected. Breaking loop...")
            app.logging.info("Not connected. Breaking loop.")
            stop(app)
            break
        if app.last_value_count >= 50:
            print("count got to 50. Let's disconnect...")
            print("Not connected. Breaking loop.")
            app.logging.info("Not connected. Breaking loop.")
            stop(app)
            break
        # If the strategy was finished correctly
        if app.strategy_end == True:
            print("Strategy is done. Let's disconnect...")
            app.logging.info("Strategy is done. Let's disconnect...")
            stop(app)
            break      
        if (1100 in list(app.errors_dict.keys())):
            print("Not connected. Breaking loop...")
            app.logging.info("Not connected. Breaking loop.")
            stop(app)
            break
        
def request_orders(app):
    ''' Function to request the open orders and orders status'''
    print('Requesting open positions and orders status...')
    app.logging.info('Requesting open positions and orders status...')
    
    # If the app is connected
    if app.isConnected():
        # Clear the threading event
        app.orders_request_event.clear()
        # Request the open orders and orders status
        app.reqOpenOrders()
        # Make the event end when the request is done
        app.orders_request_event.wait()
    else:
        return
    
    # If the temporary open orders dataframe is not empty
    if (app.temp_open_orders.empty == False):
        # Set the datetime column as index
        app.temp_open_orders.set_index('datetime',inplace=True)
        # Erase the index name
        app.temp_open_orders.index.name = ''
        # Concatenate the temporary dataframe with the whole corresponding dataframe
        app.open_orders = pd.concat([app.open_orders,app.temp_open_orders])
        # Drop row duplicates
        app.open_orders.drop_duplicates(inplace=True)
        # Sort the whole dataframe by index
        app.open_orders.sort_index(ascending=True, inplace=True)
        # Clear the temporary dataframe
        app.temp_open_orders = pd.DataFrame()

    # If the temporary orders status dataframe is not empty
    if (app.temp_orders_status.empty == False):
        # Set the datetime column as index
        app.temp_orders_status.set_index('datetime',inplace=True)
        # Erase the index name
        app.temp_orders_status.index.name = ''
        # Concatenate the temporary dataframe with the whole corresponding dataframe
        app.orders_status = pd.concat([app.orders_status,app.temp_orders_status])
        # Drop row duplicates            
        app.orders_status.drop_duplicates(inplace=True)
        # Sort the whole dataframe by index
        app.orders_status.sort_index(ascending=True, inplace=True)
        # Clear the temporary dataframe
        app.temp_orders_status = pd.DataFrame()

    print('Open positions and orders status successfully requested...')
    app.logging.info('Open positions and orders status successfully requested...')

def request_positions(app):
    ''' Function to request the trading positions'''
    print('Requesting positions...')
    app.logging.info('Requesting positions...')
    
    # If the app is connected
    if app.isConnected():
        # Clear the threading event
        app.positions_request_event.clear()
        # Request the trading positions
        app.reqPositions()
        # Set the event to wait until the request is finished
        app.positions_request_event.wait()
    else:
        return
    
    # If the temporary positions dataframe is not empty
    if (app.temp_pos_df.empty == False):
        pd.set_option('display.max_columns', None)
        # Set the datetime column as index
        app.temp_pos_df.set_index('datetime',inplace=True)
        # Erase the index name
        app.temp_pos_df.index.name = ''
        # Concatenate the temporary dataframe with the main dataframe
        app.pos_df = pd.concat([app.pos_df, app.temp_pos_df])
        # Drop duplicates
        app.pos_df.drop_duplicates(inplace=True)
        # Sort the positions dataframe by index
        app.pos_df.sort_index(ascending=True, inplace=True)
        # Clear the temporary dataframe
        app.temp_pos_df = pd.DataFrame()
    print('Open positions successfully requested...')
    app.logging.info('Open positions successfully requested...')

# Function to download the historical data from the IBKR server.
def download_hist_data(app, days_passed):
    # A comment indicating the function's purpose.
    """Function to download the historical data"""

    # Determine the duration string for the API request based on the number of days needed.
    if days_passed>252:
        # If more than a business year's worth of days, request data in terms of years ('Y') for efficiency.
        span_string = f'{math.ceil(days_passed/252)} Y'
    else:
        # Otherwise, request data in terms of days ('D').
        span_string = f'{days_passed} D'
        
    # Check if the application is currently connected to the IBKR server.
    if app.isConnected():
        # Create a new threading Event object on the app instance to manage asynchronous data flow.
        app.event = Event()
        # Ensure the event's internal flag is initially set to false.
        app.event.clear()
        
        # Determine the bar size string for the API request based on the data frequency set in the app.
        if 'min' in app.data_frequency:
            # Format the bar size string for minutes (e.g., '5 mins').
            hist_bar = f'{int(app.data_frequency[:app.data_frequency.find("m")])} mins'
        elif 'h' in app.data_frequency:
            # Format the bar size string for hours (e.g., '1 hour').
            hist_bar = f'{int(app.data_frequency[:app.data_frequency.find("h")])} hours'
        elif 'D' in app.data_frequency:
            # Format the bar size string for days (e.g., '1 day').
            hist_bar = f'{int(app.data_frequency[:app.data_frequency.find("D")])} day'
               
        # Send the historical data request using the EClient method from the app object.
        app.reqHistoricalData(0, app.contract, '', span_string, hist_bar, \
                               'ADJUSTED_LAST', 1, 1, False, [])
            
        # Pause the execution of this function here and wait until the event is set.
        # The event will be set by the 'historicalDataEnd' callback in 'setup.py' when the download is complete.
        app.event.wait()
    else:
        # If the app is not connected, exit the function immediately.
        return
    
# Function to process and clean the newly downloaded historical data.
def prepare_df(app):
    # Print a status message to the console.
    print('preparing the historical adjusted data...')
    # Log the same status message for record-keeping.
    app.logging.info('preparing the historical adjusted data...')
        
    # Sort the dataframe by its index (which contains the datetime of each bar).
    app.new_df.sort_index(inplace=True)
    # Remove any rows with a duplicate index, keeping only the first occurrence.
    app.new_df = app.new_df[~app.new_df.index.duplicated(keep='first')]
    
    # Check if the data frequency is daily.
    if 'D' in app.data_frequency:
        # If daily, convert the index to datetime objects using a simple date format.
        app.new_df.index = pd.to_datetime(app.new_df.index, format='%Y%m%d')
    else:
        # If intraday, convert the index to datetime objects using a more detailed format that includes timezone.
        app.new_df.index = pd.to_datetime(app.new_df.index, format='%Y%m%d %H:%M:%S %Z')
        # Remove the timezone information from the index to make it timezone-naive, simplifying calculations.
        app.new_df.index = app.new_df.index.tz_localize(None)        
        # Filter the dataframe to keep only the bars that fall within the asset's official liquid trading hours.
        app.new_df = app.new_df.between_time(app.trader_start_datetime.time(), app.trader_end_datetime.time()).copy()  
    
    # Save the cleaned and processed dataframe to the CSV file specified in the app's configuration.
    app.new_df.to_csv(app.historical_data_address)
    
    # Print a confirmation message that the data preparation is complete.
    print('The adjusted data is prepared...')
    # Log the same confirmation message.
    app.logging.info('The adjusted data is prepared...')
       
# Function to orchestrate the full process of updating historical data.
def update_hist_data(app):
    # This comment indicates the function's purpose.
    ''' Request the historical data '''
    
    # Print a status message indicating the start of the data request.
    print("Requesting the historical data...")
    # Log the same status message.
    app.logging.info("Requesting the historical data...")
    
    # Translate the app's data frequency into a pandas-compatible frequency string for date range generation.
    if 'D' in app.data_frequency:
        # Set frequency to daily.
        app.date_range_freq = 'D'
    elif 'min' in app.data_frequency:
        # Set frequency to minutes (e.g., '5min').
        app.date_range_freq = app.data_frequency
    elif 'h' in app.data_frequency:
        # Set frequency to hours (e.g., '1h').
        app.date_range_freq = app.data_frequency
    elif '1w' == app.data_frequency:
        # Set frequency to weekly, anchored to Friday.
        app.date_range_freq = 'W-FRI'
    elif '1M' == app.data_frequency:
        # Set frequency to business month end.
        app.date_range_freq = 'BM'

    # Generate a theoretical series of datetimes to determine the start date for the download.
    datetimes = pd.date_range(end=dt.datetime.now().replace(second=0,microsecond=0),
                                # The total number of periods needed is the training span plus a 500-period buffer.
                                periods=(app.train_span+500),
                                # Use the pandas-compatible frequency string.
                                freq=app.date_range_freq)
    
    # Calculate the total number of calendar days that have passed from the calculated start date to the current time.
    days_passed = math.ceil(((app.current_period - datetimes[0]) + dt.timedelta(days=1)).days+1)
    
    # Check if the application is currently connected to the IBKR server.
    if app.isConnected():
        # Call the helper function to perform the actual download, passing the required number of days.
        download_hist_data(app, days_passed)
    else:
        # If not connected, exit the function.
        return

    # After downloading, check again if the application is connected.
    if app.isConnected():
        # Call the helper function to clean and process the downloaded data.
        prepare_df(app)
    else:
        # If not connected, exit the function.
        return
        
    # Replace the old historical data on the app object with the newly downloaded and cleaned data.
    app.historical_data = app.new_df.copy()
    
    # Print a confirmation message that the entire process is complete.
    print("Historical data was successfully prepared...")
    # Log the same confirmation message.
    app.logging.info("Historical data was successfully prepared...")
    
def update_asset_last_value(app):
    ''' Request the update of the last value of the asset'''
    print("Updating the last value of the asset...")
    app.logging.info("Updating the last value of the asset...")
    # Set the last value to zero
    app.last_value = 0
    # ###########################################################################
    # # Loop to get the last Close price tick value
    # # Use the while loop in case the app has issues while requesting the last value
    # while True:
    #     # Reques the last value of the asset price
    #     app.reqTickByTickData(0, app.contract, \
    #                             'MidPoint', 0, True)
    #     time.sleep(2)
    #     # Cancel the request
    #     app.cancelTickByTickData(0)
    #     time.sleep(1)
    #     # Check if the app tried more than 50 times
    #     if app.last_value_count >= 50:
    #         print("The app couldn't get the midpoint data, it will restart...")
    #         app.logging.info("The app couldn't get the midpoint data, it will restart...")
    #         break
    #     # Check if the last value is different from zero
    #     if app.last_value != 0:
    #         print('Midpoint data obtained...')
    #         app.logging.info('Midpoint data obtained...')
    #         break
    #     # Check if the app is disconnected
    #     if not app.isConnected(): return
                
    #     print("Couldn't get Tick midpoint data, it will try again...")
    #     app.logging.info("Couldn't get Tick midpoint data, it will try again...")
        
    #     # Update the last value count
    #     app.last_value_count += 1
    ###########################################################################
    # Code to get the last Close bar price value
    app.last_value = app.historical_data['Close'].values[-1]

# Function to get the account's capital value converted to the stock's specific currency.
def get_capital_as_per_stock_currency(app, capital_datetime):
    
    # Check if the stock's currency is the same as the account's base currency.
    if app.contract.currency==app.account_currency:
        # If they are the same, no currency conversion is needed.
        # Get the account capital value directly from the cash balance dataframe.
        capital = app.cash_balance.loc[capital_datetime, 'value']
    else:            
        # If currencies differ, find the exchange rate from the account update data provided by IBKR.
        # The exchange rate where the divisor is the account base currency and the dividend is the stock base currency
        exchange_rate = app.acc_update[(app.acc_update['key']=='ExchangeRate') & \
                                        (app.acc_update['Currency'] == app.contract.currency)]['Value'].values.tolist()
            
        # Check if the exchange rate was found in the IBKR account data.
        if len(exchange_rate)!=0:
            # If a rate is available, print the values for debugging purposes.
            print(f"app.acc_update['Currency'] is {app.acc_update[(app.acc_update['key']=='ExchangeRate') & \
                                            (app.acc_update['Currency'] == app.contract.currency)]['Value']}")
            # Print the specific exchange rate being used.
            print(f"exchange rate of the app is {exchange_rate}")
            # Calculate the capital in the stock's currency by dividing the base currency capital by the exchange rate.
            capital = app.cash_balance.loc[capital_datetime, 'value'] / float(exchange_rate[0])
        else:
            # If no real-time exchange rate is available from IBKR, use Yahoo Finance as a backup.
            # Set the end date for the Yahoo Finance download to one day after the current period.
            end = app.current_period + dt.timedelta(days=1)
            # Set the start date to two days before the end date to ensure data is captured.
            start = end - dt.timedelta(days=2)
            
            # Construct the currency pair symbol required by the yfinance library (e.g., 'EURUSD=X').
            exchange_rate_symbol = f'{app.contract.currency}{app.account_currency}=X'

            # Download the minute-by-minute exchange rate data from Yahoo Finance.
            # Get the USD/contract_symbol exchange rate data
            contrac_curr_to_acc_curr_data = yf.download(exchange_rate_symbol, start=start, end=end, interval='1m', group_by='ticker')[exchange_rate_symbol]
            # Convert the downloaded data's index to datetime objects and localize it to the app's timezone.
            # Set the index as datetime and convert it to the app timezone
            contrac_curr_to_acc_curr_data.index = pd.to_datetime(contrac_curr_to_acc_curr_data.index).tz_convert(app.zone)
            # Get the most recent closing price from the downloaded exchange rate data.
            # Get the USD/contract_symbol exchange rate most-recent value
            contrac_curr_to_acc_curr_forex = contrac_curr_to_acc_curr_data['Close'].iloc[-1]
            
            # Convert the capital and apply a 5% "haircut" as a safety margin, since Yahoo Finance data may have a slight delay.
            # Use the 95% of the portfolio value just in case the forex pair has changed dramatically (Yahoo Finance data is not up to date)
            capital = app.cash_balance.loc[capital_datetime, 'value'] * contrac_curr_to_acc_curr_forex * 0.95
            
    # Return the final calculated capital value in the stock's currency.
    return capital

# Function to update the application's record of the account's cash balance and available capital.
def update_capital(app):
    # This comment indicates the function's purpose.
    ''' Function to update the capital value'''
    # Print a status message to the console.
    print('Update the cash balance datetime and value...')
    # Log the same status message for record-keeping.
    app.logging.info('Update the cash balance datetime and value...')
    
    # Check if the application is currently connected to the IBKR server.
    if app.isConnected():
        # Clear the threading event flag to prepare for a new request/response cycle.
        app.account_update_event.clear()
        # Send a request to the IBKR server to start streaming account updates for the specified account.
        app.reqAccountUpdates(True,app.account)
        # Pause the execution of this function here and wait for the 'accountDownloadEnd' callback to set the event.
        app.account_update_event.wait()
        # After receiving the data, send a request to stop the stream of account updates.
        app.reqAccountUpdates(False,app.account)
        # Pause for 1 second to ensure the unsubscribe request is processed.
        time.sleep(1)
        # Print a confirmation that the account values have been updated.
        print('Account values successfully updated ......')
        # Log the same confirmation message.
        app.logging.info('Account values successfully requested...')
    else:
        # If the app is not connected, exit the function.
        return
    
    # Find the datetime of the most recent 'TotalCashBalance' update from the received account data.
    capital_datetime = \
        app.acc_update[(app.acc_update['key']=='TotalCashBalance') & \
                        (app.acc_update['Currency']=='BASE') ]['datetime'].tail(1).values[0]
            
    # Extract the 'TotalCashBalance' value and save it to the app's 'cash_balance' dataframe.
    app.cash_balance.loc[capital_datetime, 'value'] = \
        float(app.acc_update[(app.acc_update['key']=='TotalCashBalance') & \
                        (app.acc_update['Currency']=='BASE') ]['Value'].tail(1).values[0])
       
    # Call the helper function to convert the new cash balance into the stock's currency and update the app's capital attribute.
    app.capital = get_capital_as_per_stock_currency(app, capital_datetime)
    
    # Forward-fill any missing values in the cash balance dataframe to ensure a continuous timeseries.
    app.cash_balance.ffill(inplace=True)
        
    # Print a confirmation message that the capital value has been updated.
    print('Capital value successfully updated ...')
    # Log the same confirmation message.
    app.logging.info('Capital value successfully updated ...')
    
# Function to update the app's state with the IDs and status of active risk management orders.
def update_risk_management_orders(app):
    # This comment indicates the function's purpose.
    ''' Function to update the risk management orders IDs and their status'''

    # Print a status message to the console.
    print('Updating the risk management orders IDs and their status...')
    # Log the same status message.
    app.logging.info('Updating the risk management orders IDs and their status...')
    
    # Check if the 'open_orders' dataframe is not empty.
    if not app.open_orders.empty:
        # Check if the strategy is using a trailing stop loss.
        if app.trail:
            # If so, filter the open orders to find the most recent 'TRAIL' order for the current symbol and get its ID.
            app.sl_order_id = int(app.open_orders[(app.open_orders["Symbol"]==app.contract.symbol) & (app.open_orders["OrderType"]=='TRAIL')]["OrderId"].sort_values(ascending=True).values[-1])
        else:
            # If not using a trailing stop, filter for the most recent standard 'STP' (stop) order and get its ID.
            app.sl_order_id = int(app.open_orders[(app.open_orders["Symbol"]==app.contract.symbol) & (app.open_orders["OrderType"]=='STP')]["OrderId"].sort_values(ascending=True).values[-1])
        # Filter the open orders to find the most recent 'LMT' (limit) order, which serves as the take-profit, and get its ID.
        app.tp_order_id = int(app.open_orders[(app.open_orders["Symbol"]==app.contract.symbol) & (app.open_orders["OrderType"]=='LMT')]["OrderId"].sort_values(ascending=True).values[-1])
        
        # Check the status of the identified stop loss order to see if it has been canceled or filled.
        # Set a boolean to True if the previous stop loss is filled or canceled
        app.sl_filled_or_canceled_bool = (app.open_orders[app.open_orders['OrderId'] == app.sl_order_id]['Status'].str.contains('canceled').sum()==1) or \
                                           (app.open_orders[app.open_orders['OrderId'] == app.sl_order_id]['Status'].str.contains('Filled').sum()==1) 
            
        # Check the status of the identified take profit order to see if it has been canceled or filled.
        # Set a boolean to True if the previous take profit is filled or canceled
        app.tp_filled_or_canceled_bool = (app.open_orders[app.open_orders['OrderId'] == app.tp_order_id]['Status'].str.contains('canceled').sum()==1) or \
                                           (app.open_orders[app.open_orders['OrderId'] == app.tp_order_id]['Status'].str.contains('Filled').sum()==1) 

    else:
        # If the 'open_orders' dataframe is empty, there are no active risk management orders.
        # Set the stop loss order ID to NaN (Not a Number).
        app.sl_order_id = np.nan
        # Set the take profit order ID to NaN.
        app.tp_order_id = np.nan            

        # Set the status flag for the stop loss to False.
        app.sl_filled_or_canceled_bool = False
        # Set the status flag for the take profit to False.
        app.tp_filled_or_canceled_bool = False
    
    # Print a confirmation message that the process is complete.
    print('The risk management orders IDs and their status were successfully updated...')
    # Log the same confirmation message.
    app.logging.info('The risk management orders IDs and their status were successfully updated...')
    
def update_remaining_position_based_on_risk_management(app, risk_management_threshold):
    ''' Function to update the remaining position and cash balance based on the selected risk management threshold'''
    
    # If the risk management selected is the stop-loss order
    if risk_management_threshold == 'sl':
        # If the previous stop loss order is filled or canceled
        if app.sl_filled_or_canceled_bool == True:
            
            # Set the remaining position value from the orders status dataframe
            remaining = float(app.orders_status[app.orders_status['OrderId'] == app.sl_order_id]['Remaining'].values[-1])
            # Set the position remaining datetime
            remaining_datetime = app.orders_status[app.orders_status['OrderId'] == app.sl_order_id].index.values[-1]
            
            # Set the average traded price from the position
            average_price = pd.to_numeric(app.exec_df[app.exec_df['OrderId'] == app.sl_order_id]['AvPrice'].values[-1])
            
            # Create a new row for the positions dataframe with the remaining datetime
            app.pos_df.loc[remaining_datetime,:] = app.pos_df[(app.pos_df['Symbol']==app.contract.symbol) & 
                                                                (app.pos_df['Currency']==app.contract.currency)].iloc[-1,:]
            # Save the last position value in the positions dataframe
            app.pos_df.loc[remaining_datetime,'Position'] = remaining
            # Save the last average cost in the positions dataframe
            app.pos_df.loc[remaining_datetime,'Avg cost'] = average_price
            
            # Update the leverage value in the cash balance dataframe
            app.cash_balance.loc[dt.datetime.now().replace(microsecond=0), 'leverage'] = app.leverage
            # Update the signal value in the cash balance dataframe
            app.cash_balance.loc[dt.datetime.now().replace(microsecond=0), 'signal'] = 0     
            # Forward fill the cash balance dataframe
            app.cash_balance.ffill(inplace=True)
        
    # If the risk management selected is the take-profit order
    elif risk_management_threshold == 'tp':
        # If the previous take profit order is filled or canceled
        if app.tp_filled_or_canceled_bool == True:
            
            # Set the remaining position value from the orders status dataframe
            remaining = float(app.orders_status[app.orders_status['OrderId'] == app.tp_order_id]['Remaining'].values[-1])
            # Set the position remaining datetime
            remaining_datetime = app.orders_status[app.orders_status['OrderId'] == app.tp_order_id].index.values[-1]
            
            # Set the average traded price from the position
            average_price = pd.to_numeric(app.exec_df[app.exec_df['OrderId'] == app.tp_order_id]['AvPrice'].values[-1])
            
            # Create a new row for the positions dataframe with the remaining datetime
            app.pos_df.loc[remaining_datetime,:] = app.pos_df[(app.pos_df['Symbol']==app.contract.symbol) & 
                                                                (app.pos_df['Currency']==app.contract.currency)].iloc[-1,:]
            # Save the last position value in the positions dataframe
            app.pos_df.loc[remaining_datetime,'Position'] = remaining
            # Save the last average cost in the positions dataframe
            app.pos_df.loc[remaining_datetime,'Avg cost'] = average_price
        
            # Update the leverage value in the cash balance dataframe
            app.cash_balance.loc[dt.datetime.now().replace(microsecond=0), 'leverage'] = app.leverage
            # Update the signal value in the cash balance dataframe
            app.cash_balance.loc[dt.datetime.now().replace(microsecond=0), 'signal'] = 0     
            # Forward fill the cash balance dataframe
            app.cash_balance.ffill(inplace=True)
  
def update_submitted_orders(app):
    ''' Function to update the submitted orders'''
    
    print('Updating the submitted orders ...')
    app.logging.info('Updating the submitted orders ...')
    
    # If it is our first trade period of the week
    if len(app.periods_traded[app.periods_traded['trade_time']>=app.market_week_open_time].index)==1:
        # Set the last trade period 
        last_trade_time = app.previous_period.strftime(f'%Y%m%d %H:%M:%S {app.zone}')
    # If we have already traded more than one time
    else:
        # Set the last trade period as the previous period traded
        last_trade_time = app.periods_traded[app.periods_traded.trade_done == 1]['trade_time'].iloc[-1].strftime(f'%Y%m%d %H:%M:%S {app.zone}')
    
    # If the app is connected
    if app.isConnected():
        print('Requesting executions...')
        app.logging.info('Requesting executions...')
        # Clear the threading event
        app.executions_request_event.clear()
        # Request the previous trading executions and commissions
        app.reqExecutions(0, ibf.executionFilter(last_trade_time))
        # Make the event wait until the request is done
        app.executions_request_event.wait()
        
        print('Successfully requested execution and commissions details...')
        app.logging.info('Successfully requested execution and commissions details...')
    else:
        return
    
    # If the app is connected
    if app.isConnected():
        # Update the risk management orders IDs and their status
        update_risk_management_orders(app)  
    
        # If the temporal executions dataframe is not empty
        if (app.temp_exec_df.empty == False):  
            # Get rid of the time zone in the execution time column values
            app.temp_exec_df['Execution Time'] = \
                pd.to_datetime(app.temp_exec_df['Execution Time'].replace(rf"{ app.zone}", "", regex=True).values)
            # Set the datetime as index
            app.temp_exec_df.set_index('datetime',inplace=True)
            # Erase the index name
            app.temp_exec_df.index.name = ''
            # Concatenate the temporary dataframe with the main dataframe
            app.exec_df = pd.concat([app.exec_df,app.temp_exec_df])
            # Drop duplicates
            app.exec_df.drop_duplicates(inplace=True)
            # Sort the dataframe by index
            app.exec_df.sort_index(ascending=True, inplace=True)
            # Clear the temporary dataframe
            app.temp_exec_df = pd.DataFrame()
            
            # Set the datetime as index
            app.temp_comm_df.set_index('datetime',inplace=True)
            # Erase the index name
            app.temp_comm_df.index.name = ''
            # Convert to NaN Realized PnL whose values are extremely high (due to IB mistake value)
            mask = app.temp_comm_df['Realized PnL'].astype(float) == 1.7976931348623157e+308
            app.temp_comm_df.loc[mask,'Realized PnL'] = np.nan
            # Concatenate the temporary dataframe with the main dataframe
            app.comm_df = pd.concat([app.comm_df,app.temp_comm_df])
            # Drop duplicates
            app.comm_df.drop_duplicates(inplace=True)
            # Sor the dataframe by index
            app.comm_df.sort_index(ascending=True, inplace=True)
            # Clear the temporary dataframe
            app.temp_comm_df = pd.DataFrame()

            
            # If the orders status and positions dataframes are not empty
            if (app.orders_status.empty == False) and (app.pos_df.empty == False):
                
                # If the previous stop-loss and take-profit target were filled or cancelled
                if (app.sl_filled_or_canceled_bool == True) and (app.tp_filled_or_canceled_bool == True):
                    # Set the stop-loss order execution time
                    sl_order_execution_time = dt.datetime.strptime(app.exec_df[app.exec_df['OrderId'] == app.sl_order_id]['Execution Time'].values[-1], '%Y-%m-%d %H:%M:%S')
                    # Set the take-profit order execution time
                    tp_order_execution_time = dt.datetime.strptime(app.exec_df[app.exec_df['OrderId'] == app.sl_order_id]['Execution Time'].values[-1], '%Y-%m-%d %H:%M:%S')
                    
                    # If the stop-loss execution time is later than than the take-profit execution time
                    if sl_order_execution_time > tp_order_execution_time:
                        # Update the remaining position based on the previous stop-loss order
                        update_remaining_position_based_on_risk_management(app, 'sl')
                    else:
                        # Update the remaining position based on the previous take-profit order
                        update_remaining_position_based_on_risk_management(app, 'tp')
                        
                # If the previous stop loss order is filled or canceled
                elif app.sl_filled_or_canceled_bool == True:                    
                    # Update the remaining position based on the previous stop-loss order
                    update_remaining_position_based_on_risk_management(app, 'sl')
                    
                # If the previous take profit order is filled or canceled
                elif app.tp_filled_or_canceled_bool == True:                       
                    # Update the remaining position based on the previous take-profit order
                    update_remaining_position_based_on_risk_management(app, 'tp')
                    
        print('The submitted orders were successfully updated...')
        app.logging.info('The submitted orders were successfully updated...')
    
# Function to calculate the final position size based on available capital and strategy leverage.
def portfolio_allocation(app): 
    # This comment indicates the function's purpose.
    ''' Function to update the portfolio allocation'''

    # Print a status message to the console.
    print('Make the portfolio allocation ...')
    # Log the same status message for record-keeping.
    app.logging.info('Make the portfolio allocation ...')
    
    # Check if the application is currently connected to the IBKR server.
    if app.isConnected():
        # Call the function to fetch the latest account capital from the server.
        update_capital(app)            
        # If fractional shares are allowed by the user's settings.
        if app.fractional_shares:
            # Set the capital to the asset's last price (Note: This is unusual and likely part of a specific strategy's logic where quantity is derived differently).
            app.capital = app.last_value
        else:
            # If only whole shares are allowed, calculate the number of shares that can be purchased with 94% of the capital.
            # The '//' ensures the result is an integer (whole number of shares).
            app.capital = (app.capital*0.94)//app.last_value 
        # Apply the leverage defined by the strategy (from strategy.py) to the calculated position size.
        app.capital *= app.leverage
    else:
        # If the app is not connected, exit the function.
        return

    # Print a confirmation message.
    print('Successfully Portfolio Allocation...')
    # Log the same confirmation message.
    app.logging.info('Successfully Portfolio Allocation...')
                                                
def cancel_previous_stop_loss_order(app):
    ''' Function to cancel the previous stop-loss order'''

    # If there is a previous stop-loss order
    if isinstance(app.sl_order_id, int):
        # If the previous stop-loss order is not filled or canceled
        if (app.sl_filled_or_canceled_bool == False):
            # If the app is connected
            if app.isConnected():
                # Cancel the previous stop loss order
                app.cancelOrder(app.sl_order_id, OrderCancel())
                time.sleep(1)
                print('Canceled old stop-loss order to create a new one...')
                app.logging.info('Canceled old stop-loss order to create a new one...')
            else:
                return

def cancel_previous_take_profit_order(app):
    ''' Function to cancel the previous take profit order'''

    # If there is a previous take-profit order
    if isinstance(app.tp_order_id, int):
        # If the previous take-profit order is not filled or canceled
        if (app.tp_filled_or_canceled_bool == False):
            # If the app is connected
            if app.isConnected():
                # Cancel the previous take-profit order
                app.cancelOrder(app.tp_order_id, OrderCancel())
                time.sleep(1)
                print('Canceled old take-profit order to create a new one...')
                app.logging.info('Canceled old take-profit order to create a new one...')
            else:
                return

def cancel_risk_management_previous_orders(app):
    ''' Function to cancel the previous risk management orders'''
    
    print('Canceling the previous risk management orders if needed...')
    app.logging.info('Canceling the previous risk management orders if needed...')
               
    # Drop the code errors related to canceling orders                                         
    app.errors_dict.pop(202, None)  
    app.errors_dict.pop(10147, None)  
    app.errors_dict.pop(10148, None)  
 
    # Create a list of executors
    executors_list = []
    # Create the executors as per each function
    with ThreadPoolExecutor(2) as executor:
        executors_list.append(executor.submit(cancel_previous_stop_loss_order, app)) 
        executors_list.append(executor.submit(cancel_previous_take_profit_order, app)) 

    # Run the executors
    for x in executors_list:
        x.result()
        
    # Drop the code errors related to canceling orders                                         
    app.errors_dict.pop(202, None)  
    app.errors_dict.pop(10147, None)  
    app.errors_dict.pop(10148, None)  
 
    print('The previous risk management orders were canceled if needed...')
    app.logging.info('The previous risk management orders were canceled if needed...')
               
# Function to construct and send a stop-loss or trailing stop-loss order.
def send_stop_loss_order(app, order_id, quantity): 
    # This comment indicates the function's purpose.
    ''' Function to send a stop loss order
        - The function has a while loop to incorporate the fact that sometimes
          the order is not sent due to decimal errors'''
    
    # Initialize the trailing amount to None; it will be set only if a trailing stop is used.
    trailing_amount = None

    # This condition checks if we are adjusting an existing position in the same direction, not opening a new one.
    if (app.previous_quantity!=0) and (np.sign(app.previous_quantity)==app.signal) and (app.open_orders.empty==False):
        # Check if the strategy is configured to use a trailing stop.
        if app.trail:
            # If so, get a new stop-loss price from the strategy file, likely to adjust the trail.
            order_price = round(stra.set_stop_loss_price(app),2)
            # Ensure the calculated price conforms to the exchange's minimum tick size using a helper from 'trading_functions.py'.
            order_price = tf.get_price_by_tick_size(order_price, app.tick_size)
            # Get the number of decimal places for the tick size.
            num_decimals = tf.get_num_decimals(app.tick_size)
            # Calculate the trailing amount as the difference between the entry price and the initial stop price.
            entry_price = Decimal(str(round(app.last_value,num_decimals)))
            initial_stop = Decimal(str(order_price))
            trailing_amount = entry_price - initial_stop
        else:
            # If using a standard stop, retrieve the price from the previous stop-loss order to keep it the same.
            order_price = app.open_orders[app.open_orders["OrderId"]==app.sl_order_id]["AuxPrice"].values[-1]
            # Ensure the retrieved price conforms to the exchange's minimum tick size.
            order_price = tf.get_price_by_tick_size(order_price, app.tick_size)

        # Use the quantity from the previous position since we are only adjusting risk management.
        quantity = int(abs(app.previous_quantity))
    # This block executes if we are opening a completely new position.
    else:
        # Get the stop-loss price by calling the function defined in the 'strategy.py' file.
        order_price = stra.set_stop_loss_price(app)
        # Convert the desired quantity to an integer.
        quantity = int(abs(quantity))
   
        # Ensure the calculated price conforms to the exchange's minimum tick size.
        order_price = tf.get_price_by_tick_size(order_price, app.tick_size)

    # Determine the action for the stop order based on the trading signal.
    if app.signal > 0:
        # If the main position is long (buy), the stop order must be a 'SELL'.
        direction = 'SELL'
    elif app.signal < 0:
        # If the main position is short (sell), the stop order must be a 'BUY' to cover.
        direction = 'BUY'
        
    # Initialize a small value to add to the price in case of API errors.
    add = 0.0
    # Start a loop to handle potential order submission errors related to price precision.
    while add<=0.00010:
        # Place the stop-loss order using the app's EClient method and an order object from 'ib_functions.py'.
        app.placeOrder(order_id, app.contract, ibf.stopOrder(direction, quantity, order_price, app.trail, trailing_amount))
        # Pause for 3 seconds to allow the order to be processed by the server.
        time.sleep(3)
        # Check if any common price-related error codes have been received from the API.
        data = (321 in list(app.errors_dict.keys())) or \
                (110 in list(app.errors_dict.keys())) or \
                (463 in list(app.errors_dict.keys()))
        # If a price-related error occurred.
        if data == True:
            # Increment the price slightly by the tick size.
            add += app.tick_size
            # Recalculate the order price with the small adjustment.
            order_price = round(order_price+add,2)
            
            # Print a message indicating a retry attempt.
            print("Couldn't transmit the stop-loss order, the app will try again...")
            # Log the same message.
            app.logging.info("Couldn't transmit the-stop loss order, the app will try again...")
            
            # Clear the errors dictionary to prepare for the next attempt.
            app.errors_dict = {}
        else:
            # If no errors occurred, the order was sent successfully. Print a confirmation.
            print(f'Stop loss sent with direction {direction}, quantity {quantity}, order price {order_price}')
            # Log the same confirmation.
            app.logging.info(f'Stop loss sent with direction {direction}, quantity {quantity}, order price {order_price}')
            # Break the retry loop.
            break
        # If a disconnection error (504) is received, exit the loop.
        if 504 in list(app.errors_dict.keys()):
            break
        
# Function to construct and send a take-profit (limit) order.
def send_take_profit_order(app, order_id, quantity): 
    # This comment indicates the function's purpose.
    ''' Function to send a take profit order
        - The function has a while loop to incorporate the fact that sometimes
          the order is not sent due to decimal errors'''
    
    # This condition checks if we are adjusting an existing position in the same direction, not opening a new one.
    if (app.previous_quantity!=0) and (np.sign(app.previous_quantity)==app.signal) and (app.open_orders.empty==False):
        # If so, retrieve the price from the previous take-profit order to keep it the same.
        order_price = app.open_orders[app.open_orders["OrderId"]==app.tp_order_id]["LmtPrice"].values[-1]
        # Use the quantity from the previous position.
        quantity = int(abs(app.previous_quantity))
            
    # This block executes if we are opening a completely new position.
    else:
        # Get the take-profit price by calling the function defined in the 'strategy.py' file.
        order_price = stra.set_take_profit_price(app)
        # Convert the desired quantity to an integer.
        quantity = int(abs(quantity))
        
    # Ensure the calculated price conforms to the exchange's minimum tick size using a helper from 'trading_functions.py'.
    order_price = tf.get_price_by_tick_size(order_price, app.tick_size)

    # Determine the action for the take-profit order based on the trading signal.
    if app.signal > 0:
        # If the main position is long (buy), the take-profit order must be a 'SELL'.
        direction = 'SELL'
    elif app.signal < 0:
        # If the main position is short (sell), the take-profit order must be a 'BUY' to cover.
        direction = 'BUY'
        
    # Initialize a small value to subtract from the price in case of API errors.
    add = 0.0
    # Start a loop to handle potential order submission errors related to price precision.
    while add<=0.00010:
        # Place the take-profit order using the app's EClient method and an order object from 'ib_functions.py'.
        app.placeOrder(order_id, app.contract, ibf.tpOrder(direction, quantity, order_price))
        # Pause for 3 seconds to allow the order to be processed by the server.
        time.sleep(3)
        # Check if any common price-related error codes have been received from the API.
        data = (321 in list(app.errors_dict.keys())) or \
                (110 in list(app.errors_dict.keys())) or \
                (463 in list(app.errors_dict.keys()))
        # If a price-related error occurred.
        if data == True:
            # Increment the adjustment value.
            add += 0.00001
            # Recalculate the order price with a small downward adjustment.
            order_price = round(order_price-add,2)
            
            # Print a message indicating a retry attempt.
            print("Couldn't transmit the take-profit order, the app will try again...")
            # Log the same message.
            app.logging.info("Couldn't transmit the take-profit order, the app will try again...")
            
            # Clear the errors dictionary to prepare for the next attempt.
            app.errors_dict = {}
        else:
            # If no errors occurred, the order was sent successfully. Print a confirmation.
            print(f'Take profit sent with direction {direction}, quantity {quantity}, order price {order_price}')
            # Log the same confirmation.
            app.logging.info(f'Take profit sent with direction {direction}, quantity {quantity}, order price {order_price}')
            # Break the retry loop.
            break
        # If a disconnection error (504) is received, exit the function.
        if 504 in list(app.errors_dict.keys()):
            return
        
# Function to construct and send a market order to the IBKR server.
def send_market_order(app, order_id, quantity):
    # This comment indicates the function's purpose.
    ''' Function to send a market order '''
    
    # Print a status message to the console.
    print('Sending the market order...')
    # Log the same status message for record-keeping.
    app.logging.info('Sending the market order...')
    
    # This comment explains the alpha stage note about fractional shares.
    # alpha: get rid of the int conversion in case we adopt fractional shares in the future using the IB API
    
    # Check if the trading type is either 'intraday' or 'open_to_close'.
    if (app.trading_type == 'intraday') or (app.trading_type == 'open_to_close'):
        # Check if the current trading period is NOT the final period of the day used for closing positions.
        if app.current_period != app.trading_day_end_datetime:
            # If the strategy signal is positive (buy).
            if app.signal > 0:
                # Set the order direction to 'BUY'.
                direction = 'BUY'
            # If the strategy signal is negative (sell).
            elif app.signal < 0:
                # Set the order direction to 'SELL'.
                direction = 'SELL'
            # Check if the application is currently connected to the IBKR server.
            if app.isConnected():
                # Place the market order using the app's EClient method and an order object from 'ib_functions.py'.
                app.placeOrder(order_id, app.contract, ibf.marketOrder(direction, int(abs(quantity))))                       
                # Pause for 3 seconds to allow the order to be processed by the server.
                time.sleep(3)                                                
                # Print a confirmation message.
                print("Market order sent...")
                # Log the same confirmation message.
                app.logging.info("Market order sent...")
            else:
                # If the app is not connected, exit the function.
                return
        # This block executes if it is the final period of the day, meaning we need to close any open position.
        else:
            # If the existing position quantity is positive (a long position).
            if quantity > 0:
                # Set the direction to 'SELL' to close the long position.
                direction = 'SELL'
            # If the existing position quantity is negative (a short position).
            elif quantity < 0:
                # Set the direction to 'BUY' to cover the short position.
                direction = 'BUY'   
            # Check if the application is connected.
            if app.isConnected():
                # Place the market order to close the position.
                app.placeOrder(order_id, app.contract, ibf.marketOrder(direction, int(abs(quantity))))
                # Pause for 3 seconds.
                time.sleep(3)                                                
                # Print a confirmation message.
                print("Market order sent...")
                # Log the same confirmation message.
                app.logging.info("Market order sent...")
            else:
                # If the app is not connected, exit the function.
                return
    # This block executes for an overnight ('close_to_open') strategy.
    elif (app.trading_type == 'close_to_open'):
        # Check if it's the start of the day, which is the time to CLOSE the overnight position.
        if app.current_period == app.trader_start_adj_datetime:
            # Set the signal to neutral as we are closing the position.
            app.signal = 0
            # Set the direction to 'SELL' to close the long position held overnight.
            direction = 'SELL'
            # Check if the application is connected.
            if app.isConnected():
                # Place the market order to close the position.
                app.placeOrder(order_id, app.contract, ibf.marketOrder(direction, int(abs(quantity))))                       
                # Pause for 3 seconds.
                time.sleep(3)                                                
                # Print a confirmation message.
                print("Market order sent...")
                # Log the same confirmation message.
                app.logging.info("Market order sent...")
            else:
                # If the app is not connected, exit the function.
                return
        # Check if it's the end of the day, which is the time to OPEN a new overnight position.
        elif app.current_period == app.trading_day_end_datetime:
            # Set the direction to 'BUY' to open the long position.
            direction = 'BUY'
            # Check if the application is connected.
            if app.isConnected():
                # Place the market order to open the position.
                app.placeOrder(order_id, app.contract, ibf.marketOrder(direction, int(abs(quantity))))
                # Pause for 3 seconds.
                time.sleep(3)                                                
                # Print a confirmation message.
                print("Market order sent...")
                # Log the same confirmation message.
                app.logging.info("Market order sent...")
            else:
                # If the app is not connected, exit the function.
                return
                    
# Function to get the quantity of the currently held position from the app's state.
def get_previous_quantity(app):
    # This comment indicates the function's purpose.
    ''' Function to get the previous position quantity'''
    
    # Check if the app's position dataframe is not empty.
    if app.pos_df.empty==False:
        # Check if the symbol of the current contract exists in the position dataframe.
        if app.contract.symbol in app.pos_df['Symbol'].to_list():
            # If a position exists, filter the dataframe for the correct symbol and currency and get the last recorded position size.
            app.previous_quantity = app.pos_df[(app.pos_df['Symbol']==app.contract.symbol) & \
                                                 (app.pos_df['Currency']==app.contract.currency)]["Position"].iloc[-1]
        else:
            # If the symbol is not in the dataframe, it means there is no position, so set the quantity to 0.
            app.previous_quantity = 0

    # This block executes if the position dataframe is empty.
    else:
        # If there is no position data at all, set the previous quantity to 0.
        app.previous_quantity = 0
        
# Function to calculate the target quantity for a new trade based on the allocated capital.
def get_current_quantity(app):
    # This comment indicates the function's purpose.
    ''' Function to get the current position quantity'''
            
    # Check the user setting to see if fractional shares are allowed.
    if app.fractional_shares:
        # If yes, the target quantity is the allocated capital amount, rounded to 2 decimal places.
        app.current_quantity = np.round(app.capital,2)
    else:
        # If only whole shares are allowed, the target quantity is the integer part of the allocated capital
        # (where capital has already been converted to a number of shares in portfolio_allocation).
        app.current_quantity = int(app.capital)
        
def get_previous_and_current_quantities(app):
    ''' Function to get the previous and current positions quantities'''
    
    print('Update the previous and current positions quantities...')
    app.logging.info('Update the previous and current positions quantities...')
    
    # If the app is connected
    if app.isConnected():
        # Update the last value of the asset
        update_asset_last_value(app)
        # Update the portfolio allocation
        portfolio_allocation(app)
    else:
        return

    # If the app is connected
    if app.isConnected():
        # Set the executors list
        executors_list = []
        # Append the functions to be multithreaded
        with ThreadPoolExecutor(2) as executor:
            executors_list.append(executor.submit(get_previous_quantity, app)) 
            executors_list.append(executor.submit(get_current_quantity, app)) 

        # Run the executors in parallel
        for x in executors_list:
            x.result()
    else:
        return
            
    print('The previous and current positions quantities were successfully updated...')
    app.logging.info('The previous and current positions quantities were successfully updated...')
    
def update_trading_info(app):
    ''' Function to get the previous trading information'''

    print('Update the previous trading information...')
    app.logging.info('Update the previous trading information...')
    
    # alpha
    # # Set the executors list
    # executors_list = []
    # # Append the functions to be used in parallel
    # with ThreadPoolExecutor(3) as executor:
    #     executors_list.append(executor.submit(request_positions, app)) 
    #     executors_list.append(executor.submit(request_orders, app)) 
    #     executors_list.append(executor.submit(update_submitted_orders, app)) 

    # # Run the functions in parallel
    # for x in executors_list:
    #     x.result()
        
    # Call the function to request the latest account positions from the server.
    request_positions(app)
    # Call the function to request the latest open orders and their statuses.
    request_orders(app)
    # Conditionally call the function to update execution details.
    # This is skipped for 'close_to_open' strategies where intraday execution details are less relevant.
    if (app.trading_type!='close_to_open') and app.risk_management_bool:
        # Call the function to request recent trade executions and commission reports.
        update_submitted_orders(app)
    
def update_cash_balance_values_for_signals(app):
    ''' Function to update the cash balance signal and leverage'''

    print('Update the cash balance signal and leverage...')
    app.logging.info('Update the cash balance signal and leverage...')
    
    # Update the leverage value in the cash balance dataframe
    app.cash_balance.loc[dt.datetime.now().replace(microsecond=0), 'leverage'] = app.leverage
    # Update the signal value in the cash balance dataframe
    app.cash_balance.loc[dt.datetime.now().replace(microsecond=0), 'signal'] = app.signal     
    # Forward fill the cash balance dataframe
    app.cash_balance.ffill(inplace=True)
            
    print('The cash balance signal and leverage were successfully updated...')
    app.logging.info('The cash balance signal and leverage were successfully updated...')
    
# Function to send a combination of orders, acting as a flexible bracket order submission.
def send_orders_as_bracket(app, order_id, quantity, mkt_order, sl_order, tp_order, rm_quantity=None):
    # This comment indicates the function's purpose.
    ''' Function to send the orders as a bracket'''
    
    # This block executes if a market order, stop-loss, and take-profit are all requested (a full bracket).
    if (mkt_order==True) and (sl_order==True) and (tp_order==True):
        # First, send the primary market order to enter the position.
        send_market_order(app, order_id, quantity)
        # Check if a specific quantity for risk management orders is provided.
        if rm_quantity is None:
            # If not, the stop-loss and take-profit will have the same quantity as the market order (for a new position).
            send_stop_loss_order(app, order_id+1, quantity)
            send_take_profit_order(app, order_id+2, quantity)
        else:
            # If provided, use the 'rm_quantity' for the stop-loss and take-profit (for adjusting an existing position).
            send_stop_loss_order(app, order_id+1, rm_quantity)
            send_take_profit_order(app, order_id+2, rm_quantity)
    # This block executes if only the risk management orders (stop-loss and take-profit) are requested.
    elif (mkt_order==False) and (sl_order==True) and (tp_order==True):
        # Send the stop-loss order.
        send_stop_loss_order(app, order_id, quantity)
        # Send the take-profit order.
        send_take_profit_order(app, order_id+1, quantity)
    # This block executes if only a market order is requested, with no risk management.
    elif (mkt_order==True) and (sl_order==False) and (tp_order==False):
        # Send only the market order.
        send_market_order(app, order_id, quantity)
    else:
        # If no valid combination of flags is provided, do nothing.
        pass
    
# Function to calculate the quantities for adjusting an existing position due to a leverage change.
def set_new_and_rm_orders_quantities(app):
    
    # Store the original signal before any potential adjustments.
    signal = app.signal
    
    # Check if there was a previously recorded leverage value.
    if app.previous_leverage != 0:
        # Calculate the change in quantity needed based on the change in leverage, proportional to the previous quantity.
        new_quantity = (app.leverage - app.previous_leverage)*app.previous_quantity/app.previous_leverage
    else:
        # If there was no previous leverage, the new quantity is simply the full target quantity for the new position.
        new_quantity = app.current_quantity

    # If the calculated quantity adjustment is negative (a reduction in position size).
    if new_quantity < 0:
        # Check if fractional shares are allowed.
        if app.fractional_shares:
            # The market order quantity is the absolute value of the reduction, rounded to 2 decimals.
            new_quantity = np.round(abs(new_quantity),2)
            # Check if there was a previous leverage to calculate the new total position size.
            if app.previous_leverage != 0:
                # The new risk management quantity is the previous quantity minus the reduction.
                rm_quantity = round(app.previous_quantity - new_quantity,2)
            else:
                # If no previous leverage, this case is not applicable for reduction, so set to None.
                rm_quantity = None
        else:
            # For whole shares, the market order quantity is the absolute floor value of the reduction.
            new_quantity = math.floor(abs(new_quantity))
            # Check if there was a previous leverage.
            if app.previous_leverage != 0:
                # The new risk management quantity is the previous quantity minus the reduction (integer).
                rm_quantity = int(app.previous_quantity - new_quantity)
            else:
                # If no previous leverage, set to None.
                rm_quantity = None
        # Set the signal to -1 to indicate a sell (or buy to cover) action for the adjustment order.
        signal = -1.0
    # If the calculated quantity adjustment is positive (an increase in position size).
    elif new_quantity > 0:
        # Check if fractional shares are allowed.
        if app.fractional_shares:
            # The market order quantity is the absolute value of the increase, rounded to 2 decimals.
            new_quantity = np.round(abs(new_quantity),2)
            # Check if there was a previous leverage.
            if app.previous_leverage != 0:
                # The new risk management quantity is the previous quantity plus the increase.
                rm_quantity = round(app.previous_quantity + new_quantity,2)
            else:
                # If no previous leverage, set to None.
                rm_quantity = None
        else:
            # For whole shares, the market order quantity is the absolute floor value of the increase.
            new_quantity = math.floor(abs(new_quantity))
            # Check if there was a previous leverage.
            if app.previous_leverage != 0:
                # The new risk management quantity is the previous quantity plus the increase (integer).
                rm_quantity = int(app.previous_quantity + new_quantity)
            else:
                # If no previous leverage, set to None.
                rm_quantity = None
    # If the calculated quantity adjustment is zero (no change).
    else:
        # The new market order quantity is the same as the previous quantity (no adjustment order needed).
        new_quantity = app.previous_quantity
        # The risk management quantity is None because no new RM orders are needed.
        rm_quantity = None
    
    # Return the potentially adjusted signal, the quantity for the adjustment market order, and the new total quantity for RM orders.
    return signal, new_quantity, rm_quantity
         
# Function to orchestrate the sending of orders based on the new trading signal and current positions.
def send_orders(app):
    # This comment indicates the function's purpose.
    ''' Function to send the orders if needed'''

    # Print a status message to the console.
    print('Sending the corresponding orders if needed...')
    # Log the same status message for record-keeping.
    app.logging.info('Sending the corresponding orders if needed...')
    
    # Check if the cash balance dataframe has any existing leverage data.
    if len(app.cash_balance.loc[:, 'leverage'].index) != 0:
        # If yes, retrieve the most recent leverage value to know the previous state.
        app.previous_leverage = app.cash_balance['leverage'].iloc[-1]
        # Retrieve the most recent signal value.
        app.previous_signal = app.cash_balance['signal'].iloc[-1]
    else:
        # If no data exists, this is the first run, so set previous leverage and signal to 0.
        app.previous_leverage = 0.0
        app.previous_signal = 0.0
        
    # Call the function to get the latest trading info (positions, open orders) from the server.
    update_trading_info(app)  
    # Call the function to determine the previous (actual) and current (target) position quantities.
    get_previous_and_current_quantities(app)

    # Initialize the order ID to 0.
    order_id = 0
    # Check if the application is connected to the IBKR server.
    if app.isConnected():
        # Request the next valid order ID from the server to avoid conflicts.
        app.reqIds(-1)
        # Pause for 2 seconds to allow the server to respond with the ID.
        time.sleep(2)        
        # Store the received order ID in the 'order_id' variable.
        order_id = app.nextValidOrderId
    else:
        # If not connected, exit the function.
        return
    
    # Print a separator for visual clarity in the console.
    print('='*50)
    # Print another separator.
    print('='*50)
    # Print the previously held quantity.
    print(f'previous quantity is {app.previous_quantity}')
    # Print the new target quantity based on the current signal.
    print(f'current quantity is {app.signal*app.current_quantity}')
    # Print a smaller separator.
    print('='*25)
    # Print the signal from the previous period.
    print(f'previous signal is {app.previous_signal}')
    # Print the new signal for the current period.
    print(f'signal is {app.signal}')
    # Print another smaller separator.
    print('='*25)
    # Print the leverage from the previous period.
    print(f'previous leverage is {app.previous_leverage}')
    # Print the new leverage for the current period.
    print(f'leverage is {app.leverage}')
    # Print a final separator.
    print('='*50)
    # Print one more separator.
    print('='*50)
        
    # This block handles the case where the new target leverage is 0 (i.e., flatten any position).
    if (app.leverage == 0.0):
        # Check if there is an existing long position.
        if app.previous_quantity > 0:
            # Set the signal to -1 to indicate a 'SELL' action to close the position.
            app.signal = -1.0

            # Check if risk management is enabled.
            if app.risk_management_bool:
                # Initialize a list for parallel execution.
                executors_list = []
                # Use a ThreadPoolExecutor to run tasks concurrently.
                with ThreadPoolExecutor(2) as executor:
                    # Submit the task to cancel any existing risk management orders.
                    executors_list.append(executor.submit(cancel_risk_management_previous_orders, app))
                    # Submit the task to send a market order to close the position (no new SL/TP).
                    executors_list.append(executor.submit(send_orders_as_bracket, app, order_id, app.previous_quantity, True, False, False))
        
                # Wait for both parallel tasks to complete.
                for x in executors_list:
                    x.result()
                    
                # Print a confirmation message.
                print('The previous long position is closed and the risk management thresholds were closed if needed...')
                # Log the confirmation.
                app.logging.info('We proceed to close the position...')
            else:
                # If risk management is disabled, just send the market order to close the position.
                send_orders_as_bracket(app, app, order_id, app.previous_quantity, True, False, False)
                # Print a confirmation.
                print("Closed the long position...")
                # Log the confirmation.
                app.logging.info("Closed the long position...")
            
            # Reset the signal to 0 after the closing action is complete.
            app.signal = 0.0
            
        else:
            # If leverage is 0 and there's no position, do nothing.
            print('Leverage is 0.0. There will be no orders to send...')
            # Log the message.
            app.logging.info('Leverage is 0.0. There will be no orders to send...')
        
    # This block handles the case where the leverage has NOT changed.
    elif (app.previous_leverage == app.leverage):
        # This condition checks if we are flipping from a long position to a long position (i.e. signal is still 1).
        # This is likely meant to be app.previous_quantity != 0 and app.signal is different, or to update RM orders.
        # Based on the print statement, it's for updating risk management orders for an existing position.
        if app.previous_quantity > 0 and app.signal == 1:
            
            # Check if risk management is enabled.
            if app.risk_management_bool:
                # Initialize a list for parallel execution.
                executors_list = []
                # Use a ThreadPoolExecutor to run tasks concurrently.
                with ThreadPoolExecutor(2) as executor:
                    # Submit the task to cancel the old risk management orders.
                    executors_list.append(executor.submit(cancel_risk_management_previous_orders, app))
                    # Submit the task to send new risk management orders for the existing position.
                    executors_list.append(executor.submit(send_orders_as_bracket, app, order_id, app.previous_quantity, False, True, True))
        
                # Wait for both parallel tasks to complete.
                for x in executors_list:
                    x.result()
        
                # Print a confirmation message.
                print('Only the new risk management orders were sent...')
                # Log the confirmation.
                app.logging.info('Only the new risk management orders were sent...')
            else:
                # If risk management is disabled, nothing needs to be done.
                print("No market order was sent because it's the same signal and leverage than the previous one...")
                # Log the message.
                app.logging.info('Only the new risk management orders were sent...')
                
        # This condition checks if there's an existing long position but the new signal is 0 (neutral).
        elif app.previous_quantity > 0 and app.signal == 0:
                
            # Set the signal to -1 to indicate a 'SELL' action to close the position.
            app.signal = -1.0

            # Check if risk management is enabled.
            if app.risk_management_bool:
                # Use a ThreadPoolExecutor to run tasks concurrently.
                executors_list = []
                with ThreadPoolExecutor(2) as executor:
                    # Submit the task to cancel any existing risk management orders.
                    executors_list.append(executor.submit(cancel_risk_management_previous_orders, app))
                    # Submit the task to send a market order to close the position.
                    executors_list.append(executor.submit(send_orders_as_bracket, app, order_id, app.previous_quantity, True, False, False))
        
                # Wait for both parallel tasks to complete.
                for x in executors_list:
                    x.result()
                    
                # Print a confirmation message.
                print('The previous long position is closed and the risk management thresholds were closed if needed...')
                # Log the confirmation.
                app.logging.info('We proceed to close the position...')
            else:
                # If risk management is disabled, just send the market order to close.
                send_orders_as_bracket(app, app, order_id, app.previous_quantity, True, False, False)
                # Print a confirmation.
                print("Closed the long position...")
                # Log the confirmation.
                app.logging.info("Closed the long position...")
            
            # Reset the signal to 0 after the closing action.
            app.signal = 0.0

        # This condition checks if there is no previous position and the new signal is to go long.
        elif app.previous_quantity == 0 and app.signal == 1:
            
            # Check if risk management is enabled.
            if app.risk_management_bool:
                # Use a ThreadPoolExecutor to run tasks concurrently.
                executors_list = []
                with ThreadPoolExecutor(2) as executor:
                    # Submit the task to cancel any lingering risk management orders from a previous trade.
                    executors_list.append(executor.submit(cancel_risk_management_previous_orders, app))
                    # Submit the task to send a full bracket order (MKT + SL + TP) to open the new position.
                    executors_list.append(executor.submit(send_orders_as_bracket, app, order_id, app.current_quantity, True, True, True))
        
                # Wait for both parallel tasks to complete.
                for x in executors_list:
                    x.result()
        
                # Print a confirmation message.
                print('The new long position is opened and new risk management thresholds were set...')
                # Log the confirmation.
                app.logging.info('The new long position is opened and new risk management thresholds were set...')
            else:
                # If risk management is disabled, just send the market order.
                send_orders_as_bracket(app, app, order_id, app.current_quantity, True, False, False)
                # Print a confirmation.
                print("We proceed to open a new long position...")
                # Log the confirmation.
                app.logging.info("We proceed to open a new long position...")
            
        # This condition checks if there is no previous position and the new signal is neutral.
        elif app.previous_quantity == 0 and app.signal == 0:
                                        
            # Check if risk management is enabled.
            if app.risk_management_bool:
                # Cancel any lingering risk management orders.
                cancel_risk_management_previous_orders(app)
                # Print a status message.
                print('Cancelling the risk management threshold if needed...')
                # Log the status message.
                app.logging.info('Cancelling the risk management threshold if needed...')
            # Print a message indicating that no action is needed.
            print('No previous quantity and current signal is zero. No market order sent then...')
            # Log the message.
            app.logging.info('No previous quantity and current signal is zero. No market order sent then...')
                    
    # This block handles the case where the leverage has changed.
    elif (app.previous_leverage != app.leverage):
        # This condition checks if there is an existing long position and the new signal is also long (but with different leverage).
        if app.previous_quantity > 0 and app.signal == 1:
            
            # Call the helper function to calculate the adjustment quantity and the new total quantity for RM orders.
            app.signal, new_quantity, rm_quantity = set_new_and_rm_orders_quantities(app)
            
            # Check if risk management is enabled.
            if app.risk_management_bool:
                # Use a ThreadPoolExecutor to run tasks concurrently.
                executors_list = []
                with ThreadPoolExecutor(2) as executor:
                    # Submit the task to cancel the old risk management orders.
                    executors_list.append(executor.submit(cancel_risk_management_previous_orders, app))
                    # Submit the task to send the adjustment market order and new bracket orders for the new total size.
                    executors_list.append(executor.submit(send_orders_as_bracket, app, order_id, new_quantity, True, True, True, rm_quantity))
                    
                # Wait for both parallel tasks to complete.
                for x in executors_list:
                    x.result()   

                # Print a confirmation message.
                print('The existing market order was adjusted as per the new levevere and risk management thresholds were set...')
                # Log the confirmation.
                app.logging.info('The existing market order was adjusted as per the new levevere and risk management thresholds were set...')
            else:
                # If risk management is disabled, just send the adjustment market order.
                send_orders_as_bracket(app, order_id, new_quantity, True, False, False)
                # Print a confirmation.
                print("The existing market order was adjusted as per the new levevere...")
                # Log the confirmation.
                app.logging.info("The existing market order was adjusted as per the new levevere...")
                
            # This resets the signal to its original state if it was temporarily changed in the quantity calculation function.
            if app.signal < 0.0:
                # Restore the signal to 1.0 for a long position.
                app.signal = 1.0
                
        # This condition checks if there's an existing long position but the new signal is neutral.
        elif app.previous_quantity > 0 and app.signal == 0:
                
            # Set the signal to -1 to indicate a 'SELL' action to close the position.
            app.signal = -1.0

            # Check if risk management is enabled.
            if app.risk_management_bool:
                # Use a ThreadPoolExecutor to run tasks concurrently.
                executors_list = []
                with ThreadPoolExecutor(2) as executor:
                    # Submit the task to cancel any existing risk management orders.
                    executors_list.append(executor.submit(cancel_risk_management_previous_orders, app))
                    # Submit the task to send a market order to close the position.
                    executors_list.append(executor.submit(send_orders_as_bracket, app, order_id, app.previous_quantity, True, False, False))
        
                # Wait for both parallel tasks to complete.
                for x in executors_list:
                    x.result()
                    
                # Print a confirmation message.
                print('The previous long position is closed and the risk management thresholds were cancelled if needed...')
                # Log the confirmation.
                app.logging.info('The previous long position is closed and the risk management thresholds were cancelled if needed...')
            else:
                # If risk management is disabled, just send the market order to close.
                send_orders_as_bracket(app, app, order_id, app.previous_quantity, True, False, False)
                # Print a confirmation.
                print("The previous long position is closed...")
                # Log the confirmation.
                app.logging.info("The previous long position is closed...")
            
            # Reset the signal to 0 after the closing action.
            app.signal = 0.0

        # This condition checks if there is no previous position and the new signal is to go long.
        elif app.previous_quantity == 0 and app.signal == 1:
            
            # Check if risk management is enabled.
            if app.risk_management_bool:
                # Use a ThreadPoolExecutor to run tasks concurrently.
                executors_list = []
                with ThreadPoolExecutor(2) as executor:
                    # Submit the task to cancel any lingering risk management orders.
                    executors_list.append(executor.submit(cancel_risk_management_previous_orders, app))
                    # Submit the task to send a full bracket order to open the new position.
                    executors_list.append(executor.submit(send_orders_as_bracket, app, order_id, app.current_quantity, True, True, True))
        
                # Wait for both parallel tasks to complete.
                for x in executors_list:
                    x.result()
        
                # Print a confirmation message.
                print('A new long position is opened and risk management orders were sent...')
                # Log the confirmation.
                app.logging.info('A new long position is opened and risk management orders were sent...')
            else:
                # If risk management is disabled, just send the market order.
                send_orders_as_bracket(app, app, order_id, app.current_quantity, True, False, False)
                # Print a confirmation.
                print("We proceed to open a new long position...")
                # Log the confirmation.
                app.logging.info("We proceed to open a new long position...")
            
        # This condition checks if there is no previous position and the new signal is neutral.
        elif app.previous_quantity == 0 and app.signal == 0:
                                        
            # Check if risk management is enabled.
            if app.risk_management_bool:
                # Cancel any lingering risk management orders.
                cancel_risk_management_previous_orders(app)
                # Print a status message.
                print('Cancelling the risk management threshold if needed...')
                # Log the status message.
                app.logging.info('Cancelling the risk management threshold if needed...')

            # Print a message indicating that no action is needed.
            print('No previous quantity and current signal is zero. No market order sent then...')
            # Log the message.
            app.logging.info('No previous quantity and current signal is zero. No market order sent then...')
                    
    # Call the function to update the cash balance dataframe with the new signal and leverage that were just acted upon.
    update_cash_balance_values_for_signals(app)
        
    # Call the function to get the latest trading info again to confirm the state after sending orders.
    update_trading_info(app)
                                        
# Function to orchestrate the process of generating the latest trading signal and leverage value from the strategy.
def get_signal_and_leverage_values(app): 
    # This comment indicates the function's purpose.
    ''' Function to get the strategy run'''
    
    # Print a status message to the console.
    print('Running the necessary to get signal and leverage values...')
    # Log the same status message.
    app.logging.info('Running the necessary to get signal and leverage values...')         
    
    # Initialize a default empty dataframe for the base features.
    base_df = pd.DataFrame()
    
    # Extract user-defined variables from the 'main.py' configuration file using a helper from 'trading_functions.py'.
    variables = tf.extract_variables('main.py')
    
    # Add the current week's market open time to the variables dictionary.
    variables['market_week_open_time'] = app.market_week_open_time
    # Add the path to the historical data file.
    variables['historical_data_address'] = 'data/historical_data.csv'
    # Add the test span value.
    variables['test_span'] = app.test_span
        
    # Add a 500-period buffer to the training span to ensure enough data for lookbacks in feature engineering.
    variables['train_span'] += 500

    # Use Python's 'inspect' module to dynamically get the arguments of the 'prepare_base_df' function in 'strategy.py'.
    signature = inspect.signature(stra.prepare_base_df)
    
    # Get a dictionary of all attributes from the main trading app object.
    setup_variables = vars(app)
    
    # Get the names of the variables returned by the 'prepare_base_df' function using a helper from 'trading_functions.py'.
    return_variables = tf.get_return_variable_names(app.strategy_file, "prepare_base_df")
    
    # Check if the strategy is configured to use ML-based optimization.
    if app.optimization:
    
        # Initialize a list to hold the parameters for the 'prepare_base_df' function call.
        prepare_base_func_params = list()
        # Loop through each required parameter of the function.
        for name, param in signature.parameters.items():
            # Check if the parameter exists as an attribute in the main app object.
            if name in setup_variables.keys():
                # If yes, add its value to the parameters list.
                prepare_base_func_params.append(setup_variables[name])
            # Specifically handle the 'base_df' parameter.
            elif name == 'base_df':
                # Pass the app's historical data as the 'base_df'.
                prepare_base_func_params.append(app.historical_data)
            else:
                # For other parameters, get their values from the variables extracted from 'main.py'.
                prepare_base_func_params.append(variables[name])
                
        # Call the function to download the latest historical data.
        update_hist_data(app)
        
        # Call the 'prepare_base_df' function from 'strategy.py' with the dynamically prepared list of arguments.
        results = stra.prepare_base_df(*prepare_base_func_params)
        # Extract the resulting feature-engineered dataframe from the results tuple.
        base_df = results[return_variables.index('base_df')]
        
        # Update the app's main base_df with the newly prepared data, up to the current period.
        app.base_df = base_df.loc[base_df.index<=app.current_period,:].copy()
            
        # Save the feature-engineered dataframe to a CSV file for analysis or quicker loading next time.
        base_df.iloc[-app.train_span:].to_csv('data/'+app.base_df_address)
                        
        # Check if the app is connected before requesting a signal.
        if app.isConnected():
    
            # Print a status message.
            print('Getting the current signal...')
            # Log the status message.
            app.logging.info('Getting the current signal...')
            
            # Get the names of the variables returned by the 'get_signal' function.
            return_variables = tf.get_return_variable_names(app.strategy_file, "get_signal")
        
            # Call the 'get_signal' function from 'strategy.py' to get the latest trading signal and leverage.
            results = stra.get_signal(app)
            
            # Extract the trading signal from the results and assign it to the app object.
            app.signal = results[return_variables.index('signal')]
    
            # Check if 'leverage' is returned by the strategy function.
            if 'leverage' in return_variables:
                # Check if the returned leverage is not None.
                if results[return_variables.index('leverage')] is not None:
                    # If valid, assign the leverage from the strategy to the app object.
                    app.leverage = results[return_variables.index('leverage')]
                # If the strategy returned None, check if leverage is defined in 'main.py'.
                elif 'leverage' in variables.keys():
                    # Use the leverage from the configuration file.
                    app.leverage = variables['leverage']
                else:
                    # If no leverage is defined anywhere, use a default value of 0.5.
                    app.leverage = 0.5
                    
            # If the strategy doesn't return leverage, check the 'main.py' configuration.
            elif 'leverage' in variables.keys():
                # Check if the configured leverage is a valid number.
                if isinstance(variables['leverage'], (int, float)):
                    # Use the configured leverage, rounded to 2 decimal places.
                    app.leverage = round(variables['leverage'],2)
                else:
                    # If not valid, use a default value of 0.5.
                    app.leverage = 0.5
            
            # If leverage is still not set, use a default value.
            elif app.leverage is None:
                # Set the leverage to a default of 0.5.
                app.leverage = 0.5
            # Print a confirmation message.
            print('The current signal was successfully created...')
            # Log the confirmation.
            app.logging.info('The current signal was successfully created...')
        
        else:
            # If not connected, exit the function.
            return
        
    # This block handles non-optimization strategies (simpler strategies).
    else:
        # Download the latest historical data.
        update_hist_data(app)
        
        # Set a default signal (e.g., 1.0 for always long).
        app.signal = 1.0
        # Check if leverage is defined in the configuration file.
        if 'leverage' in variables.keys():
            # If yes, use the configured leverage.
            app.leverage = variables['leverage']
        else:
            # Otherwise, use a default leverage of 0.9.
            app.leverage = 0.9
            
    # Print a final confirmation message.
    print('The signal and leverage values were obtained...')
    # Log the confirmation.
    app.logging.info('The signal and leverage values were obtained...')
    
# Function to add contextual datetime columns to all relevant dataframes before saving.
def save_week_open_and_close_datetimes(app):
    # This comment indicates the function's purpose.
    """ Function to fill all the dataframes with the week's open and close datetimes"""
    
    # Print a status message to the console.
    print("Saving the corresponding week's open and close datetimes in the corresponding dataframes...")
    # Log the same status message.
    app.logging.info("Saving the corresponding week's open and close datetimes in the corresponding dataframes...")
    
    # Create a list of all dataframes that need to be stamped with contextual datetimes.
    for dataframe in [app.open_orders, app.orders_status, app.exec_df, app.comm_df, \
                      app.pos_df, app.cash_balance]:
        
        # Check if the dataframe is not empty.
        if len(dataframe.index)!=0:
        
            # Create a boolean mask to identify all rows that fall within the current trading day.
            mask = (dataframe.index>=app.trader_start_datetime) & (dataframe.index<=app.trader_end_datetime)
            # Add a new column 'trader_start_datetime' to the masked rows, stamping them with the day's start time.
            dataframe.loc[mask,'trader_start_datetime'] = app.trader_start_datetime
            # Add a new column 'trader_end_datetime' to the masked rows, stamping them with the day's end time.
            dataframe.loc[mask,'trader_end_datetime'] = app.trader_end_datetime
            
            # Create a boolean mask to identify all rows that fall within the current trading week.
            mask = (dataframe.index>=app.market_week_open_time) & (dataframe.index<=app.market_week_close_time)
            # Add a new column 'market_week_open_time' to the masked rows, stamping them with the week's open time.
            dataframe.loc[mask,'market_week_open_time'] = app.market_week_open_time
            # Add a new column 'market_week_close_time' to the masked rows, stamping them with the week's close time.
            dataframe.loc[mask,'market_week_close_time'] = app.market_week_close_time
            
            # This line filters the dataframe to keep only rows that are complete duplicates, which is likely an error.
            # The intention was probably to drop duplicates: `dataframe.drop_duplicates(inplace=True)`.
            # As per instructions, the line is kept as is and commented on its literal action.
            dataframe = dataframe[dataframe.duplicated(subset=dataframe.columns)]
        
    # Check if the 'periods_traded' dataframe is not empty.
    if len(app.periods_traded.index)!=0:
        # Create a boolean mask for rows within the current trading day.
        mask = (app.periods_traded['trade_time']>=app.trader_start_datetime) & (app.periods_traded['trade_time']<=app.trader_end_datetime)
        # Add the 'trader_start_datetime' column to the masked rows.
        app.periods_traded.loc[mask,'trader_start_datetime'] = app.trader_start_datetime
        # Add the 'trader_end_datetime' column to the masked rows.
        app.periods_traded.loc[mask,'trader_end_datetime'] = app.trader_end_datetime
    
        # Create a boolean mask for rows within the current trading week.
        mask = (app.periods_traded['trade_time']>=app.market_week_open_time) & (app.periods_traded['trade_time']<=app.market_week_close_time)
        # Add the 'market_week_open_time' column to the masked rows.
        app.periods_traded.loc[mask,'market_week_open_time'] = app.market_week_open_time
        # Add the 'market_week_close_time' column to the masked rows.
        app.periods_traded.loc[mask,'market_week_close_time'] = app.market_week_close_time

        # Print a confirmation message.
        print("The corresponding week's and day's open and close datetimes were successfully added on the dataframes...")
        # Log the same confirmation message.
        app.logging.info("The corresponding week's open and close datetimes were successfully added on the dataframes...")
        
def save_data(app):
    """ Function to save the data"""
    
    print("Saving all the data...")
    app.logging.info("Saving all the data...")
    
    # Forward-fill the cash balance dataframe values
    app.cash_balance.ffill(inplace=True)
    
    # Save the open and close market datetimes in all dataframes
    save_week_open_and_close_datetimes(app)

    # Group all the dataframes in a single dictionary
    dictfiles = {'open_orders':app.open_orders,\
                 'orders_status':app.orders_status,\
                 'executions':app.exec_df,\
                 'commissions':app.comm_df,\
                 'positions':app.pos_df,\
                 'cash_balance':app.cash_balance,\
                 'app_time_spent':app.app_time_spent,\
                 'periods_traded':app.periods_traded}
         
    # Save the dataframes in a single Excel workbook
    tf.save_xlsx(dict_df = dictfiles, path = 'data/database.xlsx')

    # Save the historical data
    app.historical_data.to_csv(app.historical_data_address)
    
    print("All data saved...")
    app.logging.info("All data saved...")

def save_data_and_send_email(app):
    """ Function to save the data and send email"""
    
    print("Saving the data and sending the email...")
    app.logging.info("Saving the data and sending the email...")
    
    # If the app is connected
    if app.isConnected():
        # Set the executors list
        executors_list = []
        # Append the functions to be used in parallel
        with ThreadPoolExecutor(2) as executor:
            # Save the data
            executors_list.append(executor.submit(save_data, app))
            # Send the email
            executors_list.append(executor.submit(send_email, app))

        # Run the functions in parallel
        for x in executors_list:
            x.result()

        print("The data was saved successfully...")
        app.logging.info("The data was saved successfully...")
    
def run_strategy(app):
    """ Function to run the whole strategy, including the signal"""

    print("Running the strategy, the signal and sending the orders if necessary...")
    app.logging.info("Running the strategy, the signal and sending the orders if necessary...")
    
    # Run the strategy
    get_signal_and_leverage_values(app)
    
    # If the app is connected
    if app.isConnected():
        # Send the orders
        send_orders(app)
        
    # Save the total seconds spent while trading in each period
    app.app_time_spent['seconds'].iloc[0] = (dt.datetime.now() - app.app_start_time).total_seconds() + 3
    
    # Set the current period as traded
    app.periods_traded['trade_done'].iloc[-1] = 1
    
    save_data_and_send_email(app)

    # Tell the app the strategy is done so it can be disconnected       
    app.strategy_end = True
    
# Function to orchestrate the execution of the 'close-to-open' (overnight) strategy for a single trading event.
def run_strategy_close_to_open(app):
    # This comment indicates the function's purpose and its inclusion of signal generation.
    """ Function to run the whole strategy, including the signal"""

    # Print a status message to the console indicating the start of the process.
    print("Running the strategy, the signal and sending the orders if necessary...")
    # Log the same status message for record-keeping.
    app.logging.info("Running the strategy, the signal and sending the orders if necessary...")
    
    # Call the function to get the latest trading signal and leverage from the strategy logic in 'strategy.py'.
    get_signal_and_leverage_values(app)
    
    # Check if the application is currently connected to the IBKR server.
    if app.isConnected():
        # If connected, call the function that contains the specific order-sending logic for this strategy type.
        send_close_to_open_orders(app)
        
    # Record the total time spent in this trading period by calculating the difference from the app's start time.
    app.app_time_spent['seconds'].iloc[0] = (dt.datetime.now() - app.app_start_time).total_seconds() + 2
    
    # Mark the current period as traded by setting the 'trade_done' flag to 1 in the app's state.
    app.periods_traded['trade_done'].iloc[-1] = 1
    
    # Call the function to save all updated dataframes to the database and send a notification email.
    save_data_and_send_email(app)

    # Set the 'strategy_end' flag to True to signal that the logic for this period is complete.
    app.strategy_end = True
    
# Function with the specific logic for sending orders for a 'close-to-open' (overnight) strategy.
def send_close_to_open_orders(app):
    # This comment indicates the function's purpose.
    ''' Function to send the orders if needed'''

    # Print a status message to the console.
    print('Sending the corresponding orders if needed...')
    # Log the same status message.
    app.logging.info('Sending the corresponding orders if needed...')
    
    # Check if the cash balance dataframe has any existing leverage data.
    if len(app.cash_balance.loc[:, 'leverage'].index) != 0:
        # If yes, retrieve the most recent leverage value to know the previous state.
        app.previous_leverage = app.cash_balance['leverage'].iloc[-1]
        # Retrieve the most recent signal value.
        app.previous_signal = app.cash_balance['signal'].iloc[-1]
    else:
        # If no data exists, this is the first run, so set previous leverage and signal to 0.
        app.previous_leverage = 0.0
        app.previous_signal = 0.0
        
    # Call the function to get the latest trading info (positions, open orders) from the server.
    update_trading_info(app)  
    # Call the function to determine the previous (actual) and current (target) position quantities.
    get_previous_and_current_quantities(app)

    # Initialize the order ID to 0.
    order_id = 0
    # Check if the application is connected to the IBKR server.
    if app.isConnected():
        # Request the next valid order ID from the server to avoid conflicts.
        app.reqIds(-1)
        # Pause for 2 seconds to allow the server to respond with the ID.
        time.sleep(2)        
        # Store the received order ID in the 'order_id' variable.
        order_id = app.nextValidOrderId
    else:
        # If not connected, exit the function.
        return
    
    # Print a separator for visual clarity in the console.
    print('='*50)
    # Print another separator.
    print('='*50)
    # Print the previously held quantity.
    print(f'previous quantity is {app.previous_quantity}')
    # Print the new target quantity based on the current signal.
    print(f'current quantity is {app.signal*app.current_quantity}')
    # Print a smaller separator.
    print('='*25)
    # Print the signal from the previous period.
    print(f'previous signal is {app.previous_signal}')
    # Print the new signal for the current period.
    print(f'signal is {app.signal}')
    # Print another smaller separator.
    print('='*25)
    # Print the leverage from the previous period.
    print(f'previous leverage is {app.previous_leverage}')
    # Print the new leverage for the current period.
    print(f'leverage is {app.leverage}')
    # Print a final separator.
    print('='*50)
    # Print one more separator.
    print('='*50)
        
    # This condition checks if the current action is happening at the END of the day (time to OPEN an overnight position).
    if (app.current_period - app.previous_period) <= (app.trader_end_datetime - app.trader_start_datetime):
        
        # This block handles the case where the new target leverage is 0 (i.e., flatten any position).
        if (app.leverage == 0.0):
            # Check if there is an existing long position.
            if app.previous_quantity > 0:
                # Set the signal to -1 to indicate a 'SELL' action to close the position.
                app.signal = -1.0
    
                # Check if risk management is enabled.
                if app.risk_management_bool:
                    # Initialize a list for parallel execution.
                    executors_list = []
                    # Use a ThreadPoolExecutor to run tasks concurrently.
                    with ThreadPoolExecutor(2) as executor:
                        # Submit the task to cancel any existing risk management orders.
                        executors_list.append(executor.submit(cancel_risk_management_previous_orders, app))
                        # Submit the task to send a market order to close the position.
                        executors_list.append(executor.submit(send_orders_as_bracket, app, order_id, app.previous_quantity, True, False, False))
            
                    # Wait for both parallel tasks to complete.
                    for x in executors_list:
                        x.result()
                        
                    # Print a confirmation message.
                    print('The previous long position is closed and the risk management thresholds were closed if needed...')
                    # Log the confirmation.
                    app.logging.info('We proceed to close the position...')
                else:
                    # If risk management is disabled, just send the market order to close.
                    send_orders_as_bracket(app, app, order_id, app.previous_quantity, True, False, False)
                    # Print a confirmation.
                    print("Closed the long position...")
                    # Log the confirmation.
                    app.logging.info("Closed the long position...")
                
                # Reset the signal to 0 after the closing action is complete.
                app.signal = 0.0
                
            else:
                # If leverage is 0 and there's no position, do nothing.
                print('Leverage is 0.0. There will be no orders to send...')
                # Log the message.
                app.logging.info('Leverage is 0.0. There will be no orders to send...')
            
        # This block handles the case where the leverage has NOT changed.
        elif app.previous_leverage == app.leverage:
            # Check if there is an existing long position and the signal is still to be long.
            if app.previous_quantity > 0 and app.signal == 1:                
                # In this case, no new order is needed as the position is already open.
                print('The market order was not sent because there was an open position with the same leverage as of now...')
                # Log the message.
                app.logging.info('The market order was not sent because there was an open position with the same leverage as of now...')
                
            # Check if there's a long position but the new signal is neutral (0).
            elif app.previous_quantity > 0 and app.signal == 0:        
                # Set the signal to -1 to indicate a 'SELL' action to close the position.
                app.signal = -1.0
                # Send a market order to close the position.
                send_orders_as_bracket(app, order_id, app.previous_quantity, True, False, False)
                # Print a confirmation.
                print('The market order to close the existing position was sent...')
                # Log the confirmation.
                app.logging.info('The market order to close the existing position was sent...')
                # Reset the signal to 0.
                app.signal = 0.0
                
            # Check if there's no position and the signal is neutral.
            elif app.previous_quantity == 0 and app.signal == 0:        
                # In this case, no order is needed.
                print('The market order was not sent because there is no long signal...')
                # Log the message.
                app.logging.info('The market order was not sent because there is no long signal...')
                
            else:
                # This is the primary case for opening a new overnight position.
                print('='*100)
                # Print a debugging message.
                print('hola1')
                # Print the signal and leverage for debugging.
                print(app.signal)
                print(app.leverage)
                # Send the market order to open the new overnight position.
                send_orders_as_bracket(app, order_id, app.current_quantity, True, False, False)
                # Print a confirmation.
                print('The market order to open an overnight position was sent...')
                # Log the confirmation.
                app.logging.info('The market order to open an overnight position was sent...')
                
        # This block handles the case where leverage has changed at the end of the day.
        else:
            # Check if there's an existing long position and the signal is still to be long.
            if app.previous_quantity > 0 and app.signal == 1:
                
                # Check if the new target quantity is greater than the previous one.
                if app.current_quantity > app.previous_quantity:
                    # Print debugging messages.
                    print('='*100)
                    print('hola2')
                    print(app.signal)
                    print(app.leverage)
                    # Calculate the quantity to add to the position.
                    final_quantity = (app.current_quantity - app.previous_quantity)
                    # Send a market order for the additional quantity.
                    send_orders_as_bracket(app, order_id, final_quantity, True, False, False)
                    # Print a confirmation.
                    print('The market order to open an overnight position was sent...')
                    # Log the confirmation.
                    app.logging.info('The market order to open an overnight position was sent...')
                
                # Check if the quantities are the same (no change needed).
                elif app.current_quantity == app.previous_quantity:
                    # Print a message indicating no action is needed.
                    print('The market order was not sent because both previous and current quantities are equal...')
                    # Log the message.
                    app.logging.info('The market order was not sent because both previous and current quantities are equal...')
                
                # This handles reducing the position size.
                else:
                    # Calculate the quantity to be sold from the position.
                    final_quantity = (app.previous_quantity - app.current_quantity)
                    # Temporarily set the signal to -1 for a 'SELL' action.
                    app.signal = -1.0
                    # Send the market order to reduce the position.
                    send_orders_as_bracket(app, order_id, final_quantity, True, False, False)
                    # Print a confirmation.
                    print('The market order to reduce the position due to a previous one was sent...')
                    # Log the confirmation.
                    app.logging.info('The market order to reduce the position due to a previous one was sent...')
                    # Restore the signal to 1.0.
                    app.signal = 1.0
                
            # Check if there's a long position but the new signal is neutral (0).
            elif app.previous_quantity > 0 and app.signal == 0:        
                # Set the signal to -1 for a 'SELL' action.
                app.signal = -1.0
                # Send the market order to close the position.
                send_orders_as_bracket(app, order_id, app.previous_quantity, True, False, False)
                # Print a confirmation.
                print('The market order to close the existing position was sent...')
                # Log the confirmation.
                app.logging.info('The market order to close the existing position was sent...')
                # Reset the signal to 0.
                app.signal = 0.0
               
            # Check if there's no position and the signal is neutral.
            elif app.previous_quantity == 0 and app.signal == 0:        
                # No action is needed.
                print('The market order was not sent because there is no long signal...')
                # Log the message.
                app.logging.info('The market order was not sent because there is no long signal...')
                
            else:
                # This is the primary case for opening a new overnight position when leverage changes.
                print('='*100)
                # Print debugging messages.
                print('hola3')
                print(app.signal)
                print(app.leverage)
                # Send the market order to open the new position.
                send_orders_as_bracket(app, order_id, app.current_quantity, True, False, False)
                # Print a confirmation.
                print('The market order to open an overnight position was sent...')
                # Log the confirmation.
                app.logging.info('The market order to open an overnight position was sent...')
                
    # This condition checks if the current action is happening at the START of the day (time to CLOSE the overnight position).
    elif (app.current_period - app.previous_period) > (app.trader_end_datetime - app.trader_start_datetime):

        # Check if there is an existing long position held overnight.
        if app.previous_quantity > 0:                
            # Set the signal to -1 for a 'SELL' action.
            app.signal = -1.0
            # Send the market order to close the overnight position.
            send_orders_as_bracket(app, order_id, app.previous_quantity, True, False, False)
            # Print a confirmation.
            print('The market order to close the overnight position was sent...')
            # Log the confirmation.
            app.logging.info('The market order to close the overnight position was sent...')
            # Reset the signal to 0.
            app.signal = 0.0
            
        else:        
            # If there was no position, no action is needed.
            print('The market order was not sent because there was no position held overnight...')
            # Log the message.
            app.logging.info('The market order was not sent because there was no position held overnight...')
            
    # Call the function to update the cash balance dataframe with the new signal and leverage that were just acted upon.
    update_cash_balance_values_for_signals(app)
        
    # Call the function to get the latest trading info again to confirm the state after sending orders.
    update_trading_info(app)
    
# Function to orchestrate the execution of the 'open-to-close' strategy for a single trading event.
def run_strategy_open_to_close(app):
    # This comment indicates the function's purpose and its inclusion of signal generation.
    """ Function to run the whole strategy, including the signal"""

    # Print a status message to the console indicating the start of the process.
    print("Running the strategy, the signal and sending the orders if necessary...")
    # Log the same status message for record-keeping.
    app.logging.info("Running the strategy, the signal and sending the orders if necessary...")
    
    # Call the function to get the latest trading signal and leverage from the strategy logic in 'strategy.py'.
    get_signal_and_leverage_values(app)
    
    # Check if the application is currently connected to the IBKR server.
    if app.isConnected():
        # If connected, call the function that contains the specific order-sending logic for this strategy type.
        send_open_to_close_orders(app)
        
    # Record the total time spent in this trading period by calculating the difference from the app's start time.
    app.app_time_spent['seconds'].iloc[0] = (dt.datetime.now() - app.app_start_time).total_seconds() + 3
    
    # Mark the current period as traded by setting the 'trade_done' flag to 1 in the app's state.
    app.periods_traded['trade_done'].iloc[-1] = 1
    
    # Call the function to save all updated dataframes to the database and send a notification email.
    save_data_and_send_email(app)

    # Set the 'strategy_end' flag to True to signal that the logic for this period is complete.
    app.strategy_end = True
    
# Function with the specific logic for sending orders for an 'open-to-close' day-trading strategy.
def send_open_to_close_orders(app):
    # This comment indicates the function's purpose.
    ''' Function to send the orders if needed'''

    # Print a status message to the console.
    print('Sending the corresponding orders if needed...')
    # Log the same status message for record-keeping.
    app.logging.info('Sending the corresponding orders if needed...')
    
    # Check if the cash balance dataframe has any existing leverage data.
    if len(app.cash_balance.loc[:, 'leverage'].index) != 0:
        # If yes, retrieve the most recent leverage value to know the previous state.
        app.previous_leverage = app.cash_balance['leverage'].iloc[-1]
        # Retrieve the most recent signal value.
        app.previous_signal = app.cash_balance['signal'].iloc[-1]
    else:
        # If no data exists, this is the first run, so set previous leverage and signal to 0.
        app.previous_leverage = 0.0
        app.previous_signal = 0.0
        
    # Call the function to get the latest trading info (positions, open orders) from the server.
    update_trading_info(app)  
    # Call the function to determine the previous (actual) and current (target) position quantities.
    get_previous_and_current_quantities(app)

    # Initialize the order ID to 0.
    order_id = 0
    # Check if the application is connected to the IBKR server.
    if app.isConnected():
        # Request the next valid order ID from the server to avoid conflicts.
        app.reqIds(-1)
        # Pause for 2 seconds to allow the server to respond with the ID.
        time.sleep(2)        
        # Store the received order ID in the 'order_id' variable.
        order_id = app.nextValidOrderId
    else:
        # If not connected, exit the function.
        return
    
    # Print a separator for visual clarity in the console.
    print('='*50)
    # Print another separator.
    print('='*50)
    # Print the previously held quantity.
    print(f'previous quantity is {app.previous_quantity}')
    # Print the new target quantity based on the current signal.
    print(f'current quantity is {app.signal*app.current_quantity}')
    # Print a smaller separator.
    print('='*25)
    # Print the signal from the previous period.
    print(f'previous signal is {app.previous_signal}')
    # Print the new signal for the current period.
    print(f'signal is {app.signal}')
    # Print another smaller separator.
    print('='*25)
    # Print the leverage from the previous period.
    print(f'previous leverage is {app.previous_leverage}')
    # Print the new leverage for the current period.
    print(f'leverage is {app.leverage}')
    # Print a final separator.
    print('='*50)
    # Print one more separator.
    print('='*50)
        
    # This condition checks if the current action is happening at the START of the day (time to OPEN a day-trade position).
    if (app.current_period - app.previous_period) > (app.trader_end_datetime - app.trader_start_datetime):
        
        # This block handles the case where the new target leverage is 0 (i.e., flatten any position).
        if (app.leverage == 0.0):
            # Check if there is an existing long position.
            if app.previous_quantity > 0:
                # Set the signal to -1 to indicate a 'SELL' action to close the position.
                app.signal = -1.0
    
                # Check if risk management is enabled.
                if app.risk_management_bool:
                    # Use a ThreadPoolExecutor to run tasks concurrently.
                    executors_list = []
                    with ThreadPoolExecutor(2) as executor:
                        # Submit the task to cancel any existing risk management orders.
                        executors_list.append(executor.submit(cancel_risk_management_previous_orders, app))
                        # Submit the task to send a market order to close the position.
                        executors_list.append(executor.submit(send_orders_as_bracket, app, order_id, app.previous_quantity, True, False, False))
            
                    # Wait for both parallel tasks to complete.
                    for x in executors_list:
                        x.result()
                        
                    # Print a confirmation message.
                    print('The previous long position is closed and the risk management thresholds were closed if needed...')
                    # Log the confirmation.
                    app.logging.info('We proceed to close the position...')
                else:
                    # If risk management is disabled, just send the market order to close.
                    send_orders_as_bracket(app, app, order_id, app.previous_quantity, True, False, False)
                    # Print a confirmation.
                    print("Closed the long position...")
                    # Log the confirmation.
                    app.logging.info("Closed the long position...")
                
                # Reset the signal to 0 after the closing action.
                app.signal = 0.0
                
            else:
                # If leverage is 0 and there's no position, do nothing.
                print('Leverage is 0.0. There will be no orders to send...')
                # Log the message.
                app.logging.info('Leverage is 0.0. There will be no orders to send...')
            
        # This block handles the case where the leverage has NOT changed.
        elif app.previous_leverage == app.leverage:
            # Check if there is an existing long position and the signal is still to be long.
            if app.previous_quantity > 0 and app.signal == 1:        
                # Check if risk management is enabled.
                if app.risk_management_bool:
                    # Use a ThreadPoolExecutor to run tasks concurrently.
                    executors_list = []
                    with ThreadPoolExecutor(2) as executor:
                        # Submit the task to cancel the old risk management orders.
                        executors_list.append(executor.submit(cancel_risk_management_previous_orders, app))
                        # Submit the task to send new risk management orders for the existing position.
                        executors_list.append(executor.submit(send_orders_as_bracket, app, order_id, app.previous_quantity, False, True, True))
            
                    # Wait for both parallel tasks to complete.
                    for x in executors_list:
                        x.result()
                        
                    # Print a confirmation message.
                    print('The new risk management orders were sent...')
                    # Log the confirmation.
                    app.logging.info('We proceed to close the position...')
                else:
                    # If risk management is disabled, no action is needed.
                    print('The market order was not sent because there was an overnight position with the same leverage as of now...')
                    # Log the message.
                    app.logging.info('The market order was not sent because there was an overnight position with the same leverage as of now...')
                    
            # Check if there's a long position but the new signal is neutral (0).
            elif app.previous_quantity > 0 and app.signal == 0:        
                # Set the signal to -1 for a 'SELL' action.
                app.signal = -1.0
                # Send the market order to close the position.
                send_orders_as_bracket(app, order_id, app.previous_quantity, True, False, False)
                # If risk management is enabled, cancel any associated orders.
                if app.risk_management_bool:
                    cancel_risk_management_previous_orders(app)
                    print("Cancelling any risk management threshold if there's any...")
                # Print a confirmation.
                print('The market order to close the existing overnight position was sent as per the current signal...')
                # Log the confirmation.
                app.logging.info('The market order to close the existing overnight position was sent as per the current signal...')
                # Reset the signal to 0.
                app.signal = 0.0
                
            # Check if there is no position and the signal is to go long.
            elif app.previous_quantity == 0 and app.signal == 1:        
                # Check if risk management is enabled.
                if app.risk_management_bool:
                    # Use a ThreadPoolExecutor to run tasks concurrently.
                    executors_list = []
                    with ThreadPoolExecutor(2) as executor:
                        # Submit the task to cancel any lingering risk management orders.
                        executors_list.append(executor.submit(cancel_risk_management_previous_orders, app))
                        # Submit the task to send a full bracket order to open the new day-trade position.
                        executors_list.append(executor.submit(send_orders_as_bracket, app, order_id, app.current_quantity, True, True, True))
            
                    # Wait for both parallel tasks to complete.
                    for x in executors_list:
                        x.result()
            
                    # Print a confirmation.
                    print('The new long position and risk management thresholds were sent for the day...')
                    # Log the confirmation.
                    app.logging.info('The new long position and risk management thresholds were sent for the day...')
                else:
                    # If risk management is disabled, just send the market order.
                    send_orders_as_bracket(app, order_id, app.current_quantity, True, False, False)
                    # Print a confirmation.
                    print('The market order to open a daily position was sent...')
                    # Log the confirmation.
                    app.logging.info('The market order to open a daily was sent...')

            # Check if there's no position and the signal is neutral.
            elif app.previous_quantity == 0 and app.signal == 0:        
                # If risk management is enabled, cancel any lingering orders.
                if app.risk_management_bool:
                    cancel_risk_management_previous_orders(app)
                    print("Cancelling any risk management threshold if there's any...")
                # No action is needed.
                print('The market order was not sent because there is no long signal...')
                # Log the message.
                app.logging.info('The market order was not sent because there is no long signal...')
                                
        # This block handles the case where leverage has changed at the start of the day.
        else:
            # Check if there's an existing long position and the signal is still to be long.
            if app.previous_quantity > 0 and app.signal == 1:        
                # Call the helper function to calculate the adjustment quantity and the new total quantity for RM orders.
                app.signal, new_quantity, rm_quantity = set_new_and_rm_orders_quantities(app)
                
                # Check if risk management is enabled.
                if app.risk_management_bool:
                    # Use a ThreadPoolExecutor to run tasks concurrently.
                    executors_list = []
                    with ThreadPoolExecutor(2) as executor:
                        # Submit the task to cancel the old risk management orders.
                        executors_list.append(executor.submit(cancel_risk_management_previous_orders, app))
                        # Submit the task to send the adjustment market order and new bracket orders for the new total size.
                        executors_list.append(executor.submit(send_orders_as_bracket, app, order_id, new_quantity, True, True, True, rm_quantity))
                        
                    # Wait for both parallel tasks to complete.
                    for x in executors_list:
                        x.result()   
    
                    # Print a confirmation.
                    print('The existing market order was adjusted as per the new levevere and risk management thresholds were set...')
                    # Log the confirmation.
                    app.logging.info('The existing market order was adjusted as per the new levevere and risk management thresholds were set...')
                    
                # This resets the signal to its original state if it was temporarily changed.
                if app.signal < 0.0:
                    app.signal = 1.0
                    
                # This 'else' seems misplaced. It should likely be outside the risk management 'if' block.
                # As written, it only executes if risk management is false.
                else:
                    # Send the adjustment market order without risk management.
                    send_orders_as_bracket(app, order_id, new_quantity, True, False, False)
                    # Print a confirmation.
                    print("The existing market order was adjusted as per the new levevere...")
                    # Log the confirmation.
                    app.logging.info("The existing market order was adjusted as per the new levevere...")
                
            # Check if there's a long position but the new signal is neutral.
            elif app.previous_quantity > 0 and app.signal == 0:        
                # Set the signal to -1 for a 'SELL' action.
                app.signal = -1.0
                # Send the market order to close the position.
                send_orders_as_bracket(app, order_id, app.previous_quantity, True, False, False)
                # If risk management is enabled, cancel any associated orders.
                if app.risk_management_bool:
                    cancel_risk_management_previous_orders(app)
                    print("Cancelling any risk management threshold if there's any...")
                # Print a confirmation.
                print('The market order to close the existing overnight position was sent as per the current signal...')
                # Log the confirmation.
                app.logging.info('The market order to close the existing overnight position was sent as per the current signal...')
                # Reset the signal to 0.
                app.signal = 0.0
                
            # Check if there's no position and the signal is to go long.
            elif app.previous_quantity == 0 and app.signal == 1:        
                # Check if risk management is enabled.
                if app.risk_management_bool:
                    # Use a ThreadPoolExecutor to run tasks concurrently.
                    executors_list = []
                    with ThreadPoolExecutor(2) as executor:
                        # Submit the task to cancel any lingering risk management orders.
                        executors_list.append(executor.submit(cancel_risk_management_previous_orders, app))
                        # Submit the task to send a full bracket order to open the new position.
                        executors_list.append(executor.submit(send_orders_as_bracket, app, order_id, app.current_quantity, True, True, True))
            
                    # Wait for both parallel tasks to complete.
                    for x in executors_list:
                        x.result()
            
                    # Print a confirmation.
                    print('The new long position and risk management thresholds were sent for the day...')
                    # Log the confirmation.
                    app.logging.info('The new long position and risk management thresholds were sent for the day...')
                else:
                    # If risk management is disabled, just send the market order.
                    send_orders_as_bracket(app, order_id, app.current_quantity, True, False, False)
                    # Print a confirmation.
                    print('The market order to open a daily position was sent...')
                    # Log the confirmation.
                    app.logging.info('The market order to open a daily was sent...')

            # Check if there's no position and the signal is neutral.
            elif app.previous_quantity == 0 and app.signal == 0:        
                # If risk management is enabled, cancel any lingering orders.
                if app.risk_management_bool:
                    cancel_risk_management_previous_orders(app)
                    print("Cancelling any risk management threshold if there's any...")
                # No action is needed.
                print('The market order was not sent because there is no long signal...')
                # Log the message.
                app.logging.info('The market order was not sent because there is no long signal...')
                                                                
    # This condition checks if the current action is happening at the END of the day (time to CLOSE the day-trade position).
    elif (app.current_period - app.previous_period) <= (app.trader_end_datetime - app.trader_start_datetime):

        # Check if risk management is enabled.
        if app.risk_management_bool:
            # Check if a position is currently open.
            if app.previous_quantity > 0:                
                # Set the signal to -1 for a 'SELL' action.
                app.signal = -1.0
                # Use a ThreadPoolExecutor to run tasks concurrently.
                executors_list = []
                with ThreadPoolExecutor(2) as executor:
                    # Submit the task to cancel the risk management orders.
                    executors_list.append(executor.submit(cancel_risk_management_previous_orders, app))
                    # Submit the task to send a market order to close the position.
                    executors_list.append(executor.submit(send_orders_as_bracket, app, order_id, app.previous_quantity, True, False, False))
                
                # Wait for both parallel tasks to complete.
                for x in executors_list:
                    x.result()
    
                # Print a confirmation.
                print("The market order to close today's position was sent and the risk management orders were closed if needed...")
                # Log the confirmation.
                app.logging.info("The market order to close today's position was sent and the risk management orders were closed if needed...")
                # Reset the signal to 0.
                app.signal = 0.0
                
            else:        
                # If there's no position to close, no action is needed.
                print('The market order was not sent because there was no position held today or a risk management threshold was breached during the day...')
                # Log the message.
                app.logging.info('The market order was not sent because there was no position held today or a risk management threshold was breached during the day...')
            
        else:        
            # If risk management is disabled, check if a position is open.
            if app.previous_quantity > 0:                
                # Set the signal to -1 for a 'SELL' action.
                app.signal = -1.0
                # Send the market order to close the position.
                send_orders_as_bracket(app, order_id, app.previous_quantity, True, False, False)
                
                # Print a confirmation.
                print("The market order to close today's position was sent...")
                # Log the confirmation.
                app.logging.info("The market order to close today's position was sent...")
                # Reset the signal to 0.
                app.signal = 0.0
                
            else:        
                # If there's no position, no action is needed.
                print('The market order was not sent because there was no position held today...')
                # Log the message.
                app.logging.info('The market order was not sent because there was no position held today...')
            
            
    # Call the function to update the cash balance dataframe with the new signal and leverage that were just acted upon.
    update_cash_balance_values_for_signals(app)
        
    # Call the function to get the latest trading info again to confirm the state after sending orders.
    update_trading_info(app)
    
# Function to select and run the correct strategy orchestrator based on the configured trading type.
def run_strategy_for_the_period(app):
    # This comment indicates the function's purpose.
    """ Function to run the whole strategy together with the connection monitor function"""

    # Check the trading type set in the app's configuration.
    if app.trading_type == 'intraday':
        # If 'intraday', call the main intraday strategy orchestrator.
        run_strategy(app)
    elif app.trading_type == 'open_to_close':
        # If 'open_to_close', call the orchestrator for that specific strategy type.
        run_strategy_open_to_close(app)
    elif app.trading_type == 'close_to_open':
        # If 'close_to_open', call the orchestrator for that specific strategy type.
        run_strategy_close_to_open(app)
    else:
        # If the trading type is not recognized, print an error message.
        print('You have set an incorrect trading type')
        # Exit the function.
        return

    # This commented-out line suggests a potential feature for monitoring the connection continuously.
    # app.connection_monitor()
        
    # After the strategy for the period is complete, disconnect the app from the IBKR server.
    stop(app)
    
    # Print a message indicating the bot is now waiting for the next scheduled trading period.
    print("Let's wait for the next period to trade...")
    # Log the same message.
    app.logging.info("Let's wait for the next period to trade...")
    
def wait_for_next_period(app): 
    """ Function to wait for the next period"""
    
    print("Let's wait for the next period to trade...")
    app.logging.info("Let's wait for the next period to trade...")
    
    # Disconnect the app
    stop(app)
                
    # Wait until we arrive at the next trading period
    time.sleep(0 if (app.next_period-dt.datetime.now()).total_seconds()<0 else (app.next_period-dt.datetime.now()).total_seconds())

# Function to perform end-of-day cleanup: update all data and close any open positions.
def update_and_close_positions(app):
    # This comment indicates the function's purpose.
    """ Function to update and close the current position before the day closes"""

    # Print a status message to the console.
    print('Update the trading info and closing the position...')
    # Log the same status message.
    app.logging.info('Update the trading info and closing the position...')
    
    # Call the function to get the latest trading info (positions, open orders) from the server.
    update_trading_info(app)  
    
    # Check if the trading type is 'intraday'.
    if (app.trading_type == 'intraday'):
        # If so, cancel any lingering risk management orders.
        cancel_risk_management_previous_orders(app)                      
    # Check if the type is 'open_to_close' and risk management is enabled.
    elif (app.trading_type == 'open_to_close') and app.risk_management_bool:
        # If so, cancel any lingering risk management orders.
        cancel_risk_management_previous_orders(app)   
    # Check if the type is 'close_to_open'.
    elif (app.trading_type == 'close_to_open'):
        # For this type, download fresh historical data in preparation for the end-of-day signal.
        update_hist_data(app)

    # Set the target signal and leverage to zero, as the goal is to have a flat position.
    app.signal = app.leverage = 0
    
    # Call the function to update the previous and current (now target) position quantities.
    get_previous_and_current_quantities(app)
    # Explicitly set the target quantity to zero to ensure the position is closed.
    app.current_quantity = 0.0
    
    # Check if the application is connected to the IBKR server.
    if app.isConnected():
        # Request the next valid order ID for the closing trade.
        app.reqIds(-1)
        # Pause for 2 seconds to allow the server to respond.
        time.sleep(2)        
        # Store the received order ID.
        order_id = app.nextValidOrderId
    
    # Check again if the application is connected.
    if app.isConnected():
        # Check if there is an existing position to close.
        if app.previous_quantity != 0.0:
            # If so, send a market order to flatten the position.
            send_market_order(app, order_id, app.previous_quantity) 
    
    # Call the function to update the cash balance dataframe with the final (zero) signal and leverage.
    update_cash_balance_values_for_signals(app)
    
    # Check again if the application is connected.
    if app.isConnected():
        # Update all trading info one last time to confirm the closing trades and final positions.
        update_trading_info(app)  
    
    # Fetch the final end-of-day capital value.
    update_capital(app)
    
    # Mark the final period of the day as traded by setting the 'trade_done' flag to 1.
    app.periods_traded['trade_done'].iloc[-1] = 1

    # Call the function to save all the final data to the database and send a notification email.
    save_data_and_send_email(app)
    
    # Print a confirmation message.
    print('The trading info was updated and the position was closed successfully...')
    # Log the confirmation.
    app.logging.info('The trading info was updated and the position was closed successfully...')
    
    # Check if this is not the last trading day of the week.
    if (app.next_period != app.market_week_close_time):
        # Determine the correct waiting message based on the trading type.
        if (app.trading_type == 'intraday') or (app.trading_type == 'open_to_close'):
            # For these types, the bot waits for the next day to start.
            print("Let's wait for the next trading day to start...")
            # Log the message.
            app.logging.info("Let's wait the next trading day to start...")
        elif (app.trading_type == 'close_to_open'):
            # For this type, the bot waits for the end of the next day to open a new position.
            print("Let's wait for the end of the day to open a new position...")
            # Log the message.
            app.logging.info("Let's wait for the end of the day to open a new position...")
    else:
        # If it is the end of the trading week.
        print("Let's wait for the market to get closed...")
        # Log the message.
        app.logging.info("Let's wait for the market to get closed...")
        
    # Disconnect the app from the IBKR server.
    stop(app)
    
    # Pause the entire application until the next scheduled trading period begins.
    time.sleep(0 if (app.next_period-dt.datetime.now()).total_seconds()<0 else (app.next_period-dt.datetime.now()).total_seconds())
    
# Function to send an email notification with a summary of the current period's trading activity.
def send_email(app): 
    # This comment indicates the function's purpose.
    """ Function to send an email with relevant information of the trading current period"""

    # Check if both the open_orders and orders_status dataframes contain data before attempting to send a detailed email.
    if (app.open_orders.empty==False) and (app.orders_status.empty==False):
        
        # Start a try block to gracefully handle any errors that might occur during data extraction or email sending.
        try:
            # Filter the open_orders dataframe to get the ID of the most recent market ('MKT') order.
            mkt_order_id = int(app.open_orders[(app.open_orders["Symbol"]==app.contract.symbol) & (app.open_orders["OrderType"]=='MKT')]["OrderId"].sort_values(ascending=True).values[-1])
            # Check if the strategy is using a trailing stop.
            if app.trail:
                # If yes, get the ID of the most recent trailing stop ('TRAIL') order.
                sl_order_id = int(app.open_orders[(app.open_orders["Symbol"]==app.contract.symbol) & (app.open_orders["OrderType"]=='TRAIL')]["OrderId"].sort_values(ascending=True).values[-1])
            else:
                # Otherwise, get the ID of the most recent standard stop ('STP') order.
                sl_order_id = int(app.open_orders[(app.open_orders["Symbol"]==app.contract.symbol) & (app.open_orders["OrderType"]=='STP')]["OrderId"].sort_values(ascending=True).values[-1])
            # Get the ID of the most recent take-profit ('LMT') order.
            tp_order_id = int(app.open_orders[(app.open_orders["Symbol"]==app.contract.symbol) & (app.open_orders["OrderType"]=='LMT')]["OrderId"].sort_values(ascending=True).values[-1])
            
            # Extract the average fill price for the market order from the orders_status dataframe.
            market_order_price = float(app.orders_status[(app.orders_status['OrderId'] == mkt_order_id) & (app.orders_status['Status'] == 'Filled')]['AvgFillPrice'].sort_values(ascending=True).values[-1])
            # Extract the trigger price for the stop-loss order from the open_orders dataframe.
            sl_order_price = float(app.open_orders[app.open_orders['OrderId'] == sl_order_id]['AuxPrice'].sort_values(ascending=True).values[-1])
            # Extract the limit price for the take-profit order from the open_orders dataframe.
            tp_order_price = float(app.open_orders[app.open_orders['OrderId'] == tp_order_id]['LmtPrice'].sort_values(ascending=True).values[-1])
                 
            # Read the email credentials and settings from the 'email_info.xlsx' file using pandas.
            email_password = pd.read_excel('data/email_info.xlsx', index_col = 0)
            
            # Set the SMTP server address for Gmail.
            smtp_server = 'smtp.gmail.com'
            # Set the SMTP port for TLS connection.
            smtp_port = 587
            # Get the sender's email address from the data read from the Excel file.
            smtp_username = email_password['smtp_username'].iloc[0]
            # Get the sender's app password from the Excel file.
            smtp_password = email_password['password'].iloc[0]
            
            # Get the sender's email address again to use in the 'From' field.
            from_email = email_password['smtp_username'].iloc[0]
            # Get the recipient's email address from the Excel file.
            to_email = email_password['to_email'].iloc[0]
                
            # Define the subject line for the email.
            subject = 'EPAT Trading App Status'
            # Compose the first line of the email body with the current trading period.
            body0 = f'- The period {app.current_period} was successfully traded'
            # Compose the line with the stock symbol being traded.
            body1 = f'- The Stock is {app.symbol}'
            # Compose the line with the trading signal.
            body2 = f'- The signal is {app.signal}'
            # Compose the line with the leverage used.
            body3 = f'- The leverage is {app.leverage}'
            # Compose the line with the current cash balance.
            body4 = f"- The cash balance value is {round(app.cash_balance['value'].values[-1],2)} {app.account_currency}"
            # Compose the line with the current position quantity.
            body5 = f'- The current position quantity is {app.current_quantity} {app.contract.symbol}'
            # Compose the line with the stop-loss price.
            body6 = f'- The stop-loss price is {sl_order_price}'
            # Compose the line with the market entry price.
            body7 = f'- The market price is {market_order_price}'
            # Compose the line with the take-profit price.
            body8 = f'- The take-profit price is {tp_order_price}'
            
            # Assemble the final email message, combining the subject and all body lines.
            message = f'Subject: {subject}\n\n{body0}\n\n{body1}\n{body2}\n{body3}\n{body4}\n{body5}\n{body6}\n{body7}\n{body8}'
            
            # Use a 'with' statement to establish a connection to the SMTP server, ensuring it's properly closed.
            with smtplib.SMTP(smtp_server, smtp_port) as smtp:
                # Upgrade the connection to a secure TLS connection.
                smtp.starttls()
                # Log in to the email server using the username and password.
                smtp.login(smtp_username, smtp_password)
                # Send the email from the 'from_email' to the 'to_email' with the composed message.
                smtp.sendmail(from_email, to_email, message)
                
            # Print a confirmation message to the console.
            print("The email was sent successfully...")
            # Log the same confirmation message.
            app.logging.info("The email was sent successfully...")
    
        # This block catches any exception that occurs in the 'try' block.
        except:
            # Define a simplified subject line for the fallback email.
            subject = 'EPAT Trading app Status'
            # Compose a simplified email body, only confirming that the period was traded.
            body0 = f'- The period {app.current_period} was successfully traded'
            
            # Assemble the simplified email message.
            message = f'Subject: {subject}\n\n{body0}'
            
            # Print a confirmation message, even for the simplified email.
            print("The email was sent successfully...")
            # Log the same confirmation message.
            app.logging.info("The email was sent successfully...")
            
# Disconnect the app
def stop(app):
    print('Disconnecting...')
    app.disconnect()
