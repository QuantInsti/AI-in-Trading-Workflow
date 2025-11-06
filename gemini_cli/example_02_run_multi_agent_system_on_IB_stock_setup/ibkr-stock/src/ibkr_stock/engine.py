"""
## Licensed under the QuantInsti Open License (QOL) v1.1 (the "License").
- Copyright 2025 QuantInsti Quantitative Learning Pvt. Ltd.
- You may not use this file except in compliance with the License.
- You may obtain a copy of the License in LICENSE.md at the repository root or at https://www.quantinsti.com.
- Non-Commercial use only; see the License for permitted use, attribution, and restrictions.
"""

# Import the necessary libraries
import os
import time
import inspect
import logging
import numpy as np
import datetime as dt
import pandas as pd
from threading import Thread
from ibkr_stock import create_database as cd
import strategy as stra
from ibkr_stock import trading_functions as tf
from ibkr_stock import setup_functions as sf
from ibkr_stock import setup_for_download_data as sdd
from ibkr_stock.setup import trading_app
from ibkr_stock.setup_for_contract_details import get_tradable_dates_and_stock_currency

# Get the current time to create a unique log file name.
now_ = dt.datetime.now()

# Set the month string to save the log file, ensuring a leading zero for single-digit months.
if now_.month < 10:
    # If the month is a single digit, prepend a '0'.
    month = '0'+str(now_.month)
else:
    # Otherwise, use the two-digit month number.
    month = now_.month
# Set the day string to save the log file, ensuring a leading zero for single-digit days.
if now_.day < 10:
    # If the day is a single digit, prepend a '0'.
    day = '0'+str(now_.day)
else:
    # Otherwise, use the two-digit day number.
    day = now_.day
# Set the hour string to save the log file, ensuring a leading zero for single-digit hours.
if now_.hour < 10:
    # If the hour is a single digit, prepend a '0'.
    hour = '0'+str(now_.hour)
else:
    # Otherwise, use the two-digit hour number.
    hour = now_.hour
# Set the minute string to save the log file, ensuring a leading zero for single-digit minutes.
if now_.minute < 10:
    # If the minute is a single digit, prepend a '0'.
    minute = '0'+str(now_.minute)
else:
    # Otherwise, use the two-digit minute number.
    minute = now_.minute
# Set the second string to save the log file, ensuring a leading zero for single-digit seconds.
if now_.second < 10:
    # If the second is a single digit, prepend a '0'.
    second = '0'+str(now_.second)
else:
    # Otherwise, use the two-digit second number.
    second = now_.second

# Configure the logging system to save all trading app info to a uniquely named log file.
logging.basicConfig(filename=f'data/log/log_file_{now_.year}_{month}_{day}_{hour}_{minute}_{second}.log',
                    # Set the logging level to DEBUG to capture all levels of messages.
                    level=logging.DEBUG,
                    # Define the format for log messages, including timestamp, level, module, function, and the message itself.
                    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Define a function for daily optimization of strategy parameters.
def daily_parameter_optimization(stra_opt_dates_filename, model_datetime, additional_variables=None):

    # Extract user-defined variables from the main configuration file ('main.py') using a helper from 'trading_functions.py'.
    variables = tf.extract_variables('main.py')

    # Calculate the test span in terms of data periods, not days, using a helper from 'trading_functions.py'.
    test_span = variables['test_span_days']*tf.get_periods_per_day(variables['data_frequency'])

    # Add the calculated test span to the training span to ensure enough data is downloaded.
    variables['train_span'] += test_span

    # Add the current model's datetime to the variables dictionary for the strategy.
    variables['model_datetime'] = model_datetime
    # Add the calculated test span in periods to the variables dictionary.
    variables['test_span'] = test_span
    # Define the path for the historical data CSV, to be used by the strategy.
    variables['historical_data_address'] = 'data/historical_data.csv'

    # Inspect the 'strategy_parameter_optimization' function in 'strategy.py' to determine its required arguments.
    signature = inspect.signature(stra.strategy_parameter_optimization)

    # Prepare the list of arguments to pass to the strategy optimization function by matching names.
    stra_func_params = [variables[name] for name, param in signature.parameters.items()]

    # Check if the file tracking optimization dates already exists.
    if os.path.exists(stra_opt_dates_filename):
        # If it exists, read the CSV file containing the dates of previous optimizations.
        stra_opt_dates = pd.read_csv(stra_opt_dates_filename, index_col=0)
        # Convert the index of the dataframe to datetime objects for proper comparison.
        stra_opt_dates.index = pd.to_datetime(stra_opt_dates.index)

        # Check if the last optimization date is different from the current model's required date.
        if stra_opt_dates.index[-1].date() != model_datetime.date():

            # Inspect the data download function in 'setup_for_download_data.py' to get its arguments.
            signature = inspect.signature(sdd.run_hist_data_download_app)

            # Prepare the arguments for the historical data download function.
            hist_data_app_variables = [variables[name] if name in variables else additional_variables[name]
                                       for name, param in signature.parameters.items()]

            # Print a message indicating that historical data is being downloaded.
            print('Creating the whole historical data...')
            # Execute the historical data download by calling the function from 'setup_for_download_data.py'.
            sdd.run_hist_data_download_app(*hist_data_app_variables)

            # Print a message indicating that strategy optimization is starting.
            print('Optimize the strategy parameters...')
            # Run the main strategy optimization function from 'strategy.py'.
            stra.strategy_parameter_optimization(*stra_func_params)

            # Record that an update was performed for the current model datetime.
            stra_opt_dates.loc[model_datetime, 'update'] = 1
            # Sort the dataframe by date.
            stra_opt_dates.sort_index(inplace=True)
            # Save the updated optimization dates back to the CSV file.
            stra_opt_dates.to_csv(stra_opt_dates_filename)

        else:
            # If optimization for today is already done, print a confirmation message.
            print('There was no need to optimize the parameters because it was already done...')
            # Log the same confirmation message.
            logging.info('There was no need to optimize the parameters because it was already done...')
    else:

        # If the optimization tracking file doesn't exist, inspect the data download function.
        signature = inspect.signature(sdd.run_hist_data_download_app)

        # Prepare the arguments for the historical data download function.
        hist_data_app_variables = [variables[name] if name in variables else additional_variables[name]
                                   for name, param in signature.parameters.items()]

        # Print a message indicating that historical data is being downloaded.
        print('Creating the whole historical data...')
        # Execute the historical data download.
        sdd.run_hist_data_download_app(*hist_data_app_variables)

        # Run the main strategy optimization function from 'strategy.py'.
        stra.strategy_parameter_optimization(*stra_func_params)

        # Create a new dataframe to start tracking optimization dates.
        stra_opt_dates = pd.DataFrame(columns=['update'])

        # Create the dataframe again (redundant line, but kept as per instructions).
        stra_opt_dates = pd.DataFrame(columns=['update'])
        # Record that an update was performed for the current model datetime.
        stra_opt_dates.loc[model_datetime, 'update'] = 1
        # Sort the dataframe by date.
        stra_opt_dates.sort_index(inplace=True)
        # Save the new optimization dates file.
        stra_opt_dates.to_csv(stra_opt_dates_filename)

# Function to run the trading logic for an intraday strategy for a single period.
def intraday_trading_sequence(app, current_period, next_period, trader_start_datetime, day_datetime_before_end):

    # Check if the current time is before the designated end-of-day trading cutoff.
    if dt.datetime.now() < day_datetime_before_end:

        # Check the 'periods_traded' dataframe to see if the current period has already been traded (trade_done == 0 means not traded).
        if app.periods_traded.loc[app.periods_traded['trade_time']==current_period]['trade_done'].values[0] == 0:

            # Check if the time spent on the previous trade has been recorded.
            if app.previous_time_spent > 0:
                # If the previous run took longer than the interval to the next period, cap the value to 60 seconds to avoid skipping.
                if app.previous_time_spent >= (next_period - current_period).total_seconds():
                    # Set a default time of 60 seconds if the recorded time was too long.
                    app.previous_time_spent = 60
                # Check if there is enough time remaining before the next period to execute the full strategy.
                if app.previous_time_spent < (next_period - dt.datetime.now()).total_seconds():
                    # If there's enough time, execute the main trading logic for the period using a function from 'setup_functions.py'.
                    sf.run_strategy_for_the_period(app)
                    # Check if the strategy execution completed successfully.
                    if app.strategy_end:

                        # Pause execution until the start of the next trading period.
                        time.sleep(0 if (next_period-dt.datetime.now()).total_seconds()<0 else (next_period-dt.datetime.now()).total_seconds())
                        # Return 0 to signal the successful completion and break the parent loop.
                        return 0
                    else:
                        # If the strategy did not complete (e.g., connection issue), print an error message.
                        print("Couldn't connect to the IB server, could be due to internet issues or the TWS/IB Gateway is not opened...")
                        # Log the same error message.
                        logging.info("Couldn't connect to the IB server, could be due to internet issues or the TWS/IB Gateway is not opened...")
                else:
                    # If there isn't enough time, print a warning message.
                    print("Time up to the next period is not sufficient to run the strategy for the current period...")
                    # Log the same warning.
                    logging.info("Time up to the next period is not sufficient to run the strategy for the current period...")
                    # Call the function from 'setup_functions.py' to disconnect and wait for the next period.
                    sf.wait_for_next_period(app)
                    # Pause execution until the start of the next trading period.
                    time.sleep(0 if (next_period-dt.datetime.now()).total_seconds()<0 else (next_period-dt.datetime.now()).total_seconds())
                    # Return 0 to signal completion and break the parent loop.
                    return 0

            # This block handles the very first trade where no 'previous_time_spent' exists.
            else:
                # Execute the main trading logic for the period using a function from 'setup_functions.py'.
                sf.run_strategy_for_the_period(app)
                # Check if the strategy execution completed successfully.
                if app.strategy_end:

                    # Pause execution until the start of the next trading period.
                    time.sleep(0 if (next_period-dt.datetime.now()).total_seconds()<0 else (next_period-dt.datetime.now()).total_seconds())
                    # Return 0 to signal successful completion.
                    return 0
                else:
                    # If the strategy did not complete, print an error message.
                    print("Couldn't connect to the IB server, could be due to internet issues or the TWS/IB Gateway is not opened...")
                    # Log the same error.
                    logging.info("Couldn't connect to the IB server, could be due to internet issues or the TWS/IB Gateway is not opened...")

        # If the 'trade_done' flag for the current period is 1.
        else:
            # Print a message indicating the period has already been processed.
            print("The current period has already been traded. Let's wait for the next period...")
            # Log the same message.
            logging.info("The current period has already been traded. Let's wait for the next period...")
            # Call the function from 'setup_functions.py' to disconnect and wait for the next period.
            sf.wait_for_next_period(app)
            # Return 0 to signal completion.
            return 0
    # If the current time is past the end-of-day trading cutoff.
    else:
        # Print a message indicating the end of the trading day.
        print("The trading end datetime has arrived. Let's close the existing position if exists and update the trading info...")
        # Log the same message.
        logging.info("The trading end datetime has arrived. Let's close the existing position if exists and update the trading info...")
        # Check if the final period of the day has not yet been processed.
        if app.periods_traded.loc[app.periods_traded['trade_time']==day_datetime_before_end]['trade_done'].values[0] == 0:
            # Call the function from 'setup_functions.py' to close any open positions and save final data.
            sf.update_and_close_positions(app)
        else:
            # If the final cleanup is already done, print a confirmation.
            print("The last position was already closed and the trading info was already updated...")
            # Log the same confirmation.
            logging.info("The last position was already closed and the trading info was already updated...")

        # Print a message indicating the wait for the next trading day.
        print("Let's wait until the new trading day begins...")
        # Log the same message.
        logging.info("Let's wait until the new trading day begins...")
        # Return 0 to signal completion.
        return 0
    
# Function to initialize and run the main trading application for a specific period.
def run_app(host, trading_type, port, account, stra_opt_dates_filename, client_id, timezone, now_, account_currency, contract, leverage, risk_management_bool,  
            base_df_address, data_frequency,  
            trader_end_datetime, day_datetime_before_end, trader_start_datetime, trader_start_adj_datetime, trader_next_start_datetime, trader_next_end_datetime, 
            market_week_open_time, market_week_close_time, train_span, test_span, trail, fractional_shares, optimization, tick_size, strategy_file):

    # Log a separator to clearly distinguish a new app run in the log file.
    logging.info('='*100)
    # Log a second separator line.
    logging.info('='*100)
    # Log a third separator line.
    logging.info('='*100)
    # Print a separator to the console.
    print('='*100)
    # Print a second separator to the console.
    print('='*100)
    # Print a third separator to the console.
    print('='*100)

    # Print a welcome message to the console.
    print('Running the app...wish you the best!')
    # Log the same welcome message.
    logging.info('Running the app...wish you the best!')

    # Determine the previous, current, and next trading periods using a datetime helper from 'trading_functions.py'.
    previous_period, current_period, next_period = tf.get_the_closest_periods(dt.datetime.now(), trading_type, data_frequency, 
                                                                              trader_start_adj_datetime, trader_start_datetime, 
                                                                              trader_end_datetime, day_datetime_before_end, 
                                                                              trader_next_start_datetime, trader_next_end_datetime)

    # Start an infinite loop that will be broken internally once the trading logic for the period is complete.
    while True:
        # Instantiate the main trading application client from 'setup.py', passing all necessary configuration and state.
        app = trading_app(logging, account, account_currency, stra_opt_dates_filename, contract, timezone, trading_type, 
                          data_frequency,  
                          risk_management_bool, base_df_address,  
                          market_week_open_time, market_week_close_time, 
                          trader_start_datetime, trader_start_adj_datetime, trader_end_datetime, day_datetime_before_end, trader_next_start_datetime, trader_next_end_datetime,
                          current_period, previous_period, next_period, train_span, test_span, trail, leverage, fractional_shares, optimization, tick_size, strategy_file)

        # Print a status message indicating connection attempt to the IB server.
        print('Connecting the app to the IB server...')
        # Log the same status message.
        logging.info('Connecting the app to the IB server...')
        # Establish connection to the Interactive Brokers TWS or Gateway.
        app.connect(host=host, port=port, clientId=client_id)

        # Create a new thread to run the app's message-receiving loop, preventing the main thread from blocking.
        thread1 = Thread(target=app.run, daemon=True)

        # Start the app's message-receiving thread.
        thread1.start()

        # Pause execution for 5 seconds to allow the connection to be established.
        time.sleep(5)

        # Print the current trading period to the console for user visibility.
        print(f'\t- Current period is {current_period}')
        # Log the current trading period.
        logging.info(f'\t- Current period is {current_period}')
        # Print the next scheduled trading period to the console.
        print(f'\t- Next period is {next_period}')
        # Log the next scheduled trading period.
        logging.info(f'\t- Next period is {next_period}')
        # Print the adjusted start time (after the market opens) for trading.
        print(f'\t- Start datetime after some minutes the market opens is {trader_start_adj_datetime}')
        # Log the adjusted start time.
        logging.info(f'\t- Start datetime after some minutes the market opens is {trader_start_adj_datetime}')
        # Print the official start of the trading day.
        print(f'\t- Trading day start datetime is {trader_start_datetime}')
        # Log the official start of the trading day.
        logging.info(f'\t- Trading start end datetime is {trader_start_datetime}')
        # Print the official end of the trading day.
        print(f'\t- Trading day end datetime is {trader_end_datetime}')
        # Log the official end of the trading day.
        logging.info(f'\t- Trading day end datetime is {trader_end_datetime}')
        # Print the calculated time to close positions before the market officially closes.
        print(f'\t- Day end datetime before market closes is {day_datetime_before_end}')
        # Log the calculated end-of-day cutoff time.
        logging.info(f'\t- Day end datetime before market closes is {day_datetime_before_end}')
        # Print the start time of the next trading day.
        print(f'\t- Trading next-day start datetime is {trader_next_start_datetime}')
        # Log the start time of the next trading day.
        logging.info(f'\t- Trading next-day start datetime is {trader_next_start_datetime}')

        # Check if the current time is before the market closes for the week.
        if dt.datetime.now() < market_week_close_time:

            # Execute the intraday trading logic sequence for the current period.
            value = intraday_trading_sequence(app, current_period, next_period, trader_start_datetime, day_datetime_before_end)
            # If the sequence returns 0, it means it completed successfully for this period.
            if value == 0:
                # Break the while loop to end the function for this trading period.
                break
        # If the current time is after the market has closed for the week.
        else:   
            # Print a status message indicating the market is closed.
            print('The market has closed...')       
            # Log the same status message.
            logging.info('The market has closed...')       
            # Break the while loop to exit the function.
            break
                
# Main loop to run the trading setup for the entire duration of the trading week.
def run_trading_setup_loop(host, daily_optimization, dict_dates, contract, stra_opt_dates_filename, trading_type, 
                           port, account, client_id, data_frequency, risk_management_bool,  
                           timezone, restart_time, time_after_open, time_before_close, stock_timezone, 
                           now_, account_currency, symbol, primary_exchange, tick_size, smart_bool, 
                           leverage, 
                           base_df_address, train_span, test_span, trail, fractional_shares, optimization, strategy_file):  

    # Log a separator to mark the start of a new major process in the log file.
    logging.info('='*100)
    # Log a second separator line.
    logging.info('='*100)
    # Log a third separator line.
    logging.info('='*100)
    # Print a separator to the console.
    print('='*100)
    # Print a second separator to the console.
    print('='*100)
    # Print a third separator to the console.
    print('='*100)

    # Parse the restart hour from the 'restart_time' string (e.g., '23:00' -> 23).
    restart_hour = int(restart_time[:2])
    # Parse the restart minute from the 'restart_time' string (e.g., '23:00' -> 0).
    restart_minute = int(restart_time[3:])

    # Get the current and next tradable session datetimes using a helper from 'trading_functions.py'.
    current_and_next_dates = tf.get_closest_tradable_datetimes(dict_dates, dt.datetime.now(), timezone, stock_timezone, data_frequency, 
                                                               restart_hour, restart_minute, time_after_open, time_before_close)

    # Unpack the start and end datetimes for the current trading day.
    trader_start_datetime, trader_end_datetime = current_and_next_dates[0], current_and_next_dates[1]


    # Define the entire trading week's open and close times using a helper from 'trading_functions.py'.
    market_week_open_time, market_week_close_time = tf.define_trading_week(timezone, trader_start_datetime.hour, trader_start_datetime.minute, 
                                                                           trader_end_datetime.hour, trader_end_datetime.minute)

    # Start a loop that continues as long as the current time is within the trading week's hours.
    while dt.datetime.now() >= market_week_open_time and dt.datetime.now() <= market_week_close_time:

        # Print a status message about fetching tradable dates.
        print('Getting the current and next tradable dates...')

        # Re-parse the restart hour (in case settings were changed, though unlikely in this loop).
        restart_hour = int(restart_time[:2])
        # Re-parse the restart minute.
        restart_minute = int(restart_time[3:])

        # Re-calculate the closest tradable session dates to ensure the bot is always synced with the correct session.
        current_and_next_dates = tf.get_closest_tradable_datetimes(dict_dates, dt.datetime.now(), timezone, stock_timezone, data_frequency, 
                                                                   restart_hour, restart_minute, time_after_open, time_before_close)

        # Unpack the start and end datetimes for the current trading day.
        trader_start_datetime, trader_end_datetime = current_and_next_dates[0], current_and_next_dates[1]
        # Unpack the start and end datetimes for the next trading day.
        trader_next_start_datetime, trader_next_end_datetime = current_and_next_dates[2], current_and_next_dates[3]


        # Re-define the trading week's boundaries.
        market_week_open_time, market_week_close_time = tf.define_trading_week(timezone, trader_start_datetime.hour, trader_start_datetime.minute, 
                                                                               trader_end_datetime.hour, trader_end_datetime.minute)

        # Calculate all critical intra-day time points using a helper from 'trading_functions.py'.
        trader_start_datetime, trader_start_adj_datetime, day_datetime_before_end,\
              auto_restart_start_datetime, auto_restart_datetime_before_end, \
                  auto_restart_end_datetime = \
                    tf.get_restart_and_day_close_datetimes(trading_type, data_frequency, restart_hour, restart_minute, 
                                                            trader_start_datetime, trader_end_datetime,  trader_next_start_datetime, trader_next_end_datetime,
                                                            time_after_open, time_before_close)

        # Print a status message indicating the start of the weekly trading loop.
        print('Running the trading app for the week...')
        # Log the same status message.
        logging.info('Running the trading app for the week...')

        # Print the calculated market open time for the week.
        print(f'market week open time is {market_week_open_time}')
        # Log the market open time for the week.
        logging.info(f'market week open time is {market_week_open_time}')
        # Print the calculated market close time for the week.
        print(f'market week close time is {market_week_close_time}')
        # Log the market close time for the week.
        logging.info(f'market week close time is {market_week_close_time}')

        # Print the time when trading can resume after a potential daily restart of the IB Gateway/TWS.
        print(f'\t - auto_restart_start_datetime is {auto_restart_start_datetime}')
        # Log the auto-restart start time.
        logging.info(f'\t - auto_restart_start_datetime is {auto_restart_start_datetime}')
        # Print the time when the IB Gateway/TWS is expected to restart.
        print(f'\t - auto_restart_end_datetime is {auto_restart_end_datetime}')
        # Log the auto-restart end time.
        logging.info(f'\t - auto_restart_end_datetime is {auto_restart_end_datetime}')
        # Print the cutoff time for placing new trades for the day.
        print(f'\t - last period to trade before market closes is {day_datetime_before_end}')
        # Log the cutoff time.
        logging.info(f'\t - last period to trade before market closes is {day_datetime_before_end}')
        # Print the start of the asset's liquid trading hours.
        print(f'\t - Market liquid start hour is {trader_start_datetime}')
        # Log the start of liquid hours.
        logging.info(f'\t - Market liquid start hour is {trader_start_datetime}')
        # Print the end of the asset's liquid trading hours.
        print(f'\t - Market liquid end hour is {trader_end_datetime}')
        # Log the end of liquid hours.
        logging.info(f'\t - Market liquid end hour is {trader_end_datetime}')
        # Print the adjusted start time for trading (after the initial market volatility).
        print(f'\t - trader start datetime with minutes after market opens: {trader_start_datetime}')
        # Log the adjusted start time.
        logging.info(f'\t - trader start datetime with minutes after market opens: {trader_start_datetime}')
        # Print the adjusted end time for trading (before the final market close).
        print(f'\t - trader end datetime with minutes before market closes: {day_datetime_before_end}')
        # Log the adjusted end time.
        logging.info(f'\t - trader end datetime with minutes before market closes: {day_datetime_before_end}')


        # Create a dictionary of additional variables that might be needed by other functions.
        additional_variables = {'contract':contract, 'current_and_next_dates':current_and_next_dates}

        # Check if the current time is before the market opens for the week.
        if dt.datetime.now() < market_week_open_time:
            # Print a message indicating the bot is waiting for the market to open.
            print("Let's wait until the market opens...")
            # Log the same message.
            logging.info("Let's wait until the market opens...")
            # Enter a holding loop that waits for the market open time to be reached.
            while dt.datetime.now() <= market_week_open_time: continue

        # Check if the trading type is 'intraday'.
        if trading_type == 'intraday':
            # Call the specific loop handler for intraday trading.
            loop_for_intrady_trading(trader_start_adj_datetime, market_week_open_time, market_week_close_time, 
                                    host, port, client_id, symbol, primary_exchange, tick_size, smart_bool, 
                                    timezone, stock_timezone, data_frequency, restart_hour, restart_minute, time_after_open, time_before_close,
                                    trading_type, account, stra_opt_dates_filename, account_currency, 
                                    leverage, risk_management_bool, base_df_address, train_span, test_span, trail, fractional_shares,
                                    optimization, daily_optimization, additional_variables, strategy_file)
        # Check if the trading type is 'open_to_close'.
        elif trading_type == 'open_to_close':
            # Call the specific loop handler for open-to-close trading.
            loop_for_open_to_close_trading(trader_start_adj_datetime, market_week_open_time, market_week_close_time, 
                                            host, port, client_id, symbol, primary_exchange, tick_size, smart_bool, 
                                            timezone, stock_timezone, data_frequency, restart_hour, restart_minute, time_after_open, time_before_close,
                                            trading_type, account, stra_opt_dates_filename, account_currency, 
                                            leverage, risk_management_bool, base_df_address, train_span, test_span, trail, fractional_shares,
                                            optimization, daily_optimization, additional_variables, strategy_file)

        # Check if the trading type is 'close_to_open'.
        elif trading_type == 'close_to_open':
            # Call the specific loop handler for close-to-open trading.
            loop_for_close_to_open_trading(trader_start_adj_datetime, market_week_open_time, market_week_close_time, 
                                            host, port, client_id, symbol, primary_exchange, tick_size, smart_bool, 
                                            timezone, stock_timezone, data_frequency, restart_hour, restart_minute, time_after_open, time_before_close,
                                            trading_type, account, stra_opt_dates_filename, account_currency, 
                                            leverage, risk_management_bool, base_df_address, train_span, test_span, trail, fractional_shares,
                                            optimization, daily_optimization, additional_variables, strategy_file)
            
# Function to manage the main daily loop for an 'intraday' trading strategy.
def loop_for_intrady_trading(trader_start_adj_datetime, market_week_open_time, market_week_close_time, 
                             host, port, client_id, symbol, primary_exchange, tick_size, smart_bool, 
                             timezone, stock_timezone, data_frequency, restart_hour, restart_minute, time_after_open, time_before_close,
                             trading_type, account, stra_opt_dates_filename, account_currency, 
                             leverage, risk_management_bool, base_df_address, train_span, test_span, trail, fractional_shares,
                             optimization, daily_optimization, additional_variables, strategy_file):
    
    # Check if the current time is before the adjusted trading start time (which is after the market opens).
    if dt.datetime.now() < trader_start_adj_datetime:            
        # If so, print a message indicating the bot is waiting.
        print("Let's wait until the trading day starts...")
        # Log the same waiting message.
        logging.info("Let's wait until the trading day starts...")
        # Enter a holding loop that pauses execution until the designated trading start time is reached.
        while dt.datetime.now() <= trader_start_adj_datetime: continue
        
    # Get the current time to use as a reference for fetching session data.
    now_ = dt.datetime.now()
    
    # Fetch the latest tradable dates and contract details using the function from 'setup_for_contract_details.py'.
    dict_dates, contract, _ = get_tradable_dates_and_stock_currency(host, port, client_id, symbol, primary_exchange, smart_bool)
    
    # Calculate the precise start and end datetimes for the current and next trading sessions using a helper from 'trading_functions.py'.
    current_and_next_dates = tf.get_closest_tradable_datetimes(dict_dates, now_, timezone, stock_timezone, data_frequency, 
                                                                                   restart_hour, restart_minute, time_after_open, time_before_close)
    
    # Unpack the start and end datetimes for the current trading day.
    trader_start_datetime, trader_end_datetime = current_and_next_dates[0], current_and_next_dates[1]
    # Unpack the start and end datetimes for the next trading day.
    trader_next_start_datetime, trader_next_end_datetime =  current_and_next_dates[2],  current_and_next_dates[3]
    
    # Calculate all critical intra-day time points (like restart times and end-of-day cutoffs) using a helper from 'trading_functions.py'.
    trader_start_datetime, trader_start_adj_datetime, day_datetime_before_end,\
          auto_restart_start_datetime, auto_restart_datetime_before_end, \
              auto_restart_end_datetime = \
                tf.get_restart_and_day_close_datetimes(trading_type, data_frequency, restart_hour, restart_minute, 
                                                        trader_start_datetime, trader_end_datetime,  trader_next_start_datetime, trader_next_end_datetime,
                                                        time_after_open, time_before_close)
               
    # Set the datetime for the machine learning model, typically the day before the next trading session, for file naming.
    model_datetime = trader_next_start_datetime - dt.timedelta(days=1)
    
    # Check if the current time is already past the end of today's trading session.
    if dt.datetime.now() > trader_end_datetime:
        # If so, print a message to wait for the next day.
        print("Let's wait until the next day to trade...")
        # Log the same waiting message.
        logging.info("Let's wait until the next day to trade...")
        # Pause execution until the start of the next trading day.
        time.sleep(0 if (trader_next_start_datetime-dt.datetime.now()).total_seconds()<0 else (trader_next_start_datetime-dt.datetime.now()).total_seconds())
        
    # If we are within the current trading day.
    else:
    
        # Check if there is a scheduled auto-restart for the IB Gateway/TWS during trading hours.
        if auto_restart_start_datetime is not None:
                
            # Check if the current time is within the day's liquid trading hours.
            if ((dt.datetime.now() >= trader_start_adj_datetime) and (dt.datetime.now() <= trader_end_datetime)): 
    
                # Check if the current time is before the scheduled auto-restart time.
                if (dt.datetime.now() < auto_restart_end_datetime): 
                
                    # Start a loop to run the trading app for each period before the restart.
                    while True:
                        # Check if the current time is still before the restart time.
                        if (dt.datetime.now() < auto_restart_end_datetime):
                            # Execute the main app logic for the current trading period.
                            run_app(host, trading_type, port, account, stra_opt_dates_filename, client_id, timezone, now_, account_currency, 
                                    contract, leverage, risk_management_bool, base_df_address, data_frequency, 
                                    trader_end_datetime, day_datetime_before_end, trader_start_datetime, trader_start_adj_datetime, trader_next_start_datetime, trader_next_end_datetime, 
                                    market_week_open_time, market_week_close_time, train_span, test_span, trail, fractional_shares, optimization, tick_size, strategy_file)
                        # If the current time has passed the restart time.
                        else:
                            # Break the pre-restart trading loop.
                            break
                    # Enter a holding loop to wait for the restart process to complete (e.g., a 5-minute window).
                    while (dt.datetime.now() >= auto_restart_end_datetime) and (dt.datetime.now() < auto_restart_start_datetime): continue
                
                    # Start a new loop to run the trading app for each period after the restart until the end-of-day cutoff.
                    while True:
                        # Check if the current time is still before the end-of-day trading cutoff.
                        if (dt.datetime.now() < day_datetime_before_end):
                            # Execute the main app logic for the current trading period.
                            run_app(host, trading_type, port, account, stra_opt_dates_filename, client_id, timezone, now_, account_currency, 
                                    contract, leverage, risk_management_bool, base_df_address, data_frequency, 
                                        trader_end_datetime, day_datetime_before_end, trader_start_datetime, trader_start_adj_datetime, trader_next_start_datetime, trader_next_end_datetime, 
                                        market_week_open_time, market_week_close_time, train_span, test_span, trail, fractional_shares, optimization, tick_size, strategy_file)
                        # If the current time has passed the end-of-day cutoff.
                        else:
                            # Break the post-restart trading loop.
                            break
                    # Start a final loop for the cleanup phase between the trading cutoff and the official market close.
                    while True:                
                        # Check if the current time is in the final window of the day.
                        if (dt.datetime.now() >= day_datetime_before_end) and (dt.datetime.now() < trader_end_datetime):
                            # Execute the app logic one last time, which will trigger position closing.
                            run_app(host, trading_type, port, account, stra_opt_dates_filename, client_id, timezone, now_, account_currency, 
                                    contract, leverage, risk_management_bool, base_df_address, data_frequency, 
                                        trader_end_datetime, day_datetime_before_end, trader_start_datetime, trader_start_adj_datetime, trader_next_start_datetime, trader_next_end_datetime, 
                                        market_week_open_time, market_week_close_time, train_span, test_span, trail, fractional_shares, optimization, tick_size, strategy_file)
                        # If the current time is past the official market close.
                        else:
                            # Break the final cleanup loop.
                            break
                        
                    # If optimization and daily_optimization flags are set, run the parameter optimization process.
                    if optimization and daily_optimization:
                        # Print a status message indicating the start of optimization.
                        print('Optimizating the strategy parameters this day...')
                        # Log the same status message.
                        logging.info('Optimizating the strategy parameters this day...')
                        
                        # Execute the daily parameter optimization function defined earlier in this file.
                        daily_parameter_optimization(stra_opt_dates_filename, model_datetime, additional_variables)
                    
                # This block handles the case where the current time is after a scheduled restart has already occurred.
                else:
                    # Start a loop to run the app from the current time until the end-of-day cutoff.
                    while True:                
                        # Check if the current time is still before the end-of-day trading cutoff.
                        if (dt.datetime.now() < day_datetime_before_end):
                            # Execute the main app logic for the current trading period.
                            run_app(host, trading_type, port, account, stra_opt_dates_filename, client_id, timezone, now_, account_currency, 
                                    contract, leverage, risk_management_bool, base_df_address, data_frequency, 
                                        trader_end_datetime, day_datetime_before_end, trader_start_datetime, trader_start_adj_datetime, trader_next_start_datetime, trader_next_end_datetime, 
                                        market_week_open_time, market_week_close_time, train_span, test_span, trail, fractional_shares, optimization, tick_size, strategy_file)
                        # If the current time has passed the end-of-day cutoff.
                        else:
                            # Break the main trading loop.
                            break
                            
                    # Start the final loop for the cleanup phase.
                    while True:                
                        # Check if the current time is in the final window of the day.
                        if (dt.datetime.now() >= day_datetime_before_end) and (dt.datetime.now() < trader_end_datetime):
                            # Execute the app logic one last time for position closing.
                            run_app(host, trading_type, port, account, stra_opt_dates_filename, client_id, timezone, now_, account_currency, 
                                    contract, leverage, risk_management_bool, base_df_address, data_frequency, 
                                        trader_end_datetime, day_datetime_before_end, trader_start_datetime, trader_start_adj_datetime, trader_next_start_datetime, trader_next_end_datetime, 
                                        market_week_open_time, market_week_close_time, train_span, test_span, trail, fractional_shares, optimization, tick_size, strategy_file)
                        # If the current time is past the official market close.
                        else:
                            # Break the final cleanup loop.
                            break
                    # Print a status message indicating the trading day is over.
                    print("The trading day is over...")
                    # Log the same status message.
                    logging.info("The trading day is over...")
                                
                    # If optimization is enabled, run the daily optimization process.
                    if optimization and daily_optimization:
                        # Print a status message for optimization.
                        print('Optimizating the strategy parameters this day...')
                        # Log the same status message.
                        logging.info('Optimizating the strategy parameters this day...')
                        
                        # Execute the daily parameter optimization function.
                        daily_parameter_optimization(stra_opt_dates_filename, model_datetime, additional_variables)               
                                        
        # This block handles a normal trading day with no scheduled auto-restart.
        else:
            
            # Start a loop to run the app for each period until the end-of-day cutoff.
            while True:                
                # Check if the current time is still before the end-of-day trading cutoff.
                if (dt.datetime.now() < day_datetime_before_end):
                    # Execute the main app logic for the current trading period.
                    run_app(host, trading_type, port, account, stra_opt_dates_filename, client_id, timezone, now_, account_currency, 
                            contract, leverage, risk_management_bool, base_df_address, data_frequency, 
                                trader_end_datetime, day_datetime_before_end, trader_start_datetime, trader_start_adj_datetime, trader_next_start_datetime, trader_next_end_datetime, 
                                market_week_open_time, market_week_close_time, train_span, test_span, trail, fractional_shares, optimization, tick_size, strategy_file)
                # If the current time has passed the end-of-day cutoff.
                else:
                    # Break the main trading loop.
                    break
                    
            # Start the final loop for the cleanup phase.
            while True:                
                # Check if the current time is in the final window of the day.
                if (dt.datetime.now() >= day_datetime_before_end) and (dt.datetime.now() < trader_end_datetime):
                    # Execute the app logic one last time for position closing.
                    run_app(host, trading_type, port, account, stra_opt_dates_filename, client_id, timezone, now_, account_currency, 
                            contract, leverage, risk_management_bool, base_df_address, data_frequency,  
                                trader_end_datetime, day_datetime_before_end, trader_start_datetime, trader_start_adj_datetime, trader_next_start_datetime, trader_next_end_datetime, 
                                market_week_open_time, market_week_close_time, train_span, test_span, trail, fractional_shares, optimization, tick_size, strategy_file)
                # If the current time is past the official market close.
                else:
                    # Break the final cleanup loop.
                    break
                
            # Print a status message indicating the trading day is over.
            print("Trading day is over...")
            # Log the same status message.
            logging.info("Trading day is over...")
    
            # If optimization is enabled, run the daily optimization process.
            if optimization and daily_optimization:
                # Print a status message for optimization.
                print('Optimizating the strategy parameters this day...')
                # Log the same status message.
                logging.info('Optimizating the strategy parameters this day...')
                
                # Execute the daily parameter optimization function.
                daily_parameter_optimization(stra_opt_dates_filename, model_datetime, additional_variables)
                
# Function to execute the logic for an 'open-to-close' trading strategy.
def run_open_to_close_strategy(host, port, client_id, account, account_currency, stra_opt_dates_filename, contract, timezone, 
                               trading_type, data_frequency, risk_management_bool, base_df_address,  
                               market_week_open_time, market_week_close_time, 
                               trader_start_adj_datetime, trader_start_datetime, 
                               trader_end_datetime, day_datetime_before_end, 
                               trader_next_start_datetime, trader_next_end_datetime, auto_restart_end_datetime,
                               train_span, test_span, trail, leverage, fractional_shares, optimization, tick_size, strategy_file):

    # Determine the previous, current, and next trading periods using a datetime helper from 'trading_functions.py'.
    previous_period, current_period, next_period = tf.get_the_closest_periods(dt.datetime.now(), trading_type, data_frequency, 
                                                                              trader_start_adj_datetime, trader_start_datetime, 
                                                                              trader_end_datetime, day_datetime_before_end, 
                                                                              trader_next_start_datetime, trader_next_end_datetime)
    
    # Instantiate the main trading application client from 'setup.py', providing all necessary configuration and state.
    app = trading_app(logging, account, account_currency, stra_opt_dates_filename, contract, timezone, trading_type, 
                      data_frequency,  
                      risk_management_bool, base_df_address,  
                      market_week_open_time, market_week_close_time, 
                      trader_start_datetime, trader_start_adj_datetime, trader_end_datetime, day_datetime_before_end, trader_next_start_datetime, trader_next_end_datetime,
                      current_period, previous_period, next_period, train_span, test_span, trail, leverage, fractional_shares, optimization, tick_size, strategy_file)
            
    # Print a status message indicating a connection attempt to the IB server.
    print('Connecting the app to the IB server...')
    # Log the same status message for record-keeping.
    logging.info('Connecting the app to the IB server...')
    # Establish the connection to the Interactive Brokers TWS or Gateway.
    app.connect(host=host, port=port, clientId=client_id)
    
    # Create a new thread to run the app's message-receiving loop, preventing the main thread from blocking.
    thread1 = Thread(target=app.run, daemon=True)

    # Start the app's message-receiving thread.
    thread1.start()
        
    # Pause execution for 5 seconds to allow the connection to be established securely.
    time.sleep(5)
       
    # Print the current trading period for user visibility.
    print(f'\t- Current period is {current_period}')
    # Log the current trading period.
    logging.info(f'\t- Current period is {current_period}')
    # Print the next scheduled trading period.
    print(f'\t- Next period is {next_period}')
    # Log the next scheduled trading period.
    logging.info(f'\t- Next period is {next_period}')
    # Print the adjusted start time for trading.
    print(f'\t- Start datetime after some minutes the market opens is {trader_start_adj_datetime}')
    # Log the adjusted start time.
    logging.info(f'\t- Start datetime after some minutes the market opens is {trader_start_adj_datetime}')
    # Print the official start of the trading day.
    print(f'\t- Trading day start datetime is {trader_start_datetime}')
    # Log the official start of the trading day.
    logging.info(f'\t- Trading start end datetime is {trader_start_datetime}')
    # Print the official end of the trading day.
    print(f'\t- Trading day end datetime is {trader_end_datetime}')
    # Log the official end of the trading day.
    logging.info(f'\t- Trading day end datetime is {trader_end_datetime}')
    # Print the calculated time to close positions before the market officially closes.
    print(f'\t- Day end datetime before market closes is {day_datetime_before_end}')
    # Log the calculated end-of-day cutoff time.
    logging.info(f'\t- Day end datetime before market closes is {day_datetime_before_end}')
    # Print the start time of the next trading day.
    print(f'\t- Trading next-day start datetime is {trader_next_start_datetime}')
    # Log the start time of the next trading day.
    logging.info(f'\t- Trading next-day start datetime is {trader_next_start_datetime}')        
        
    # Check the 'periods_traded' dataframe to see if the current period has not yet been traded.
    if app.periods_traded.loc[app.periods_traded['trade_time']==current_period]['trade_done'].values[0] == 0:
        # If not traded, execute the specific open-to-close strategy logic from 'setup_functions.py'.
        sf.run_strategy_open_to_close(app)
        # Check if the strategy execution completed successfully by checking a flag on the app object.
        if app.strategy_end:
            # Disconnect the app from the IB server using the helper function in 'setup_functions.py'.
            sf.stop(app)
                
            # If there is no scheduled auto-restart for the IB Gateway/TWS.
            if auto_restart_end_datetime is None:
                # Pause execution until the start of the next trading period (which is the end-of-day closing time for this strategy).
                time.sleep(0 if (next_period-dt.datetime.now()).total_seconds()<0 else (next_period-dt.datetime.now()).total_seconds())
                # Print a message indicating the bot is waiting to close the position.
                print("Let's wait until some minutes before the market closes so we can close the current position in case we have it...")
                # Log the same waiting message.
                logging.info("Let's wait until some minutes before the market closes so we can close the current position in case we have it...")

                # Return 0 to signal successful completion for this cycle.
                return 0
            # If there is a scheduled auto-restart.
            else:
                # Check if the current time is before the restart time.
                if dt.datetime.now() < auto_restart_end_datetime:
                    # If so, pause execution until the restart is scheduled to begin.
                    print("Let's wait until we reach the auto-restart time to continue trading...")
                    # Log the same waiting message.
                    logging.info("Let's wait until we reach the auto-restart time to continue trading...")
                    # Sleep until the auto-restart time.
                    time.sleep(0 if (auto_restart_end_datetime-dt.datetime.now()).total_seconds()<0 else (auto_restart_end_datetime-dt.datetime.now()).total_seconds())
                # If the current time is already past the restart time.
                else:
                    # Pause execution until the next scheduled trading period.
                    print("Let's wait until we reach the next period...")
                    # Log the same waiting message.
                    logging.info("Let's wait until we reach the next period...")
                    # Sleep until the next period.
                    time.sleep(0 if (next_period-dt.datetime.now()).total_seconds()<0 else (next_period-dt.datetime.now()).total_seconds())
                
                # Return 0 to signal successful completion for this cycle.
                return 0    
        # If the strategy did not complete successfully (e.g., connection issue).
        else:
            # Print an error message detailing the likely cause.
            print("Couldn't connect to the IB server, could be due to internet issues or the TWS/IB Gateway is not opened...")
            # Log the same error message.
            logging.info("Couldn't connect to the IB server, could be due to internet issues or the TWS/IB Gateway is not opened...")
    # If the current period has already been traded.
    else:
        # Print a confirmation that the action for this period is already complete.
        print("The last position was already closed and the trading info was already updated...")
        # Log the same confirmation.
        logging.info("The last position was already closed and the trading info was already updated...")
        
        # Disconnect the app from the IB server.
        sf.stop(app)
                
        # If there is no scheduled auto-restart.
        if auto_restart_end_datetime is None:
            # Pause execution until the start of the next trading period.
            time.sleep(0 if (next_period-dt.datetime.now()).total_seconds()<0 else (next_period-dt.datetime.now()).total_seconds())

            # Return 0 to signal successful completion of this (skipped) cycle.
            return 0
        # If there is a scheduled auto-restart.
        else:
            # Check if the current time is before the restart.
            if dt.datetime.now() < auto_restart_end_datetime:
                # Print a message indicating the bot is waiting for the restart.
                print("Let's wait until we reach the auto-restart time to continue trading...")
                # Log the same waiting message.
                logging.info("Let's wait until we reach the auto-restart time to continue trading...")
                # Pause execution until the restart time.
                time.sleep(0 if (auto_restart_end_datetime-dt.datetime.now()).total_seconds()<0 else (auto_restart_end_datetime-dt.datetime.now()).total_seconds())
            # If the current time is already past the restart.
            else:
                # Print a message indicating the bot is waiting for the next period.
                print("Let's wait until we reach the next period...")
                # Log the same waiting message.
                logging.info("Let's wait until we reach the next period...")
                # Pause execution until the next period.
                time.sleep(0 if (next_period-dt.datetime.now()).total_seconds()<0 else (next_period-dt.datetime.now()).total_seconds())
            
            # Return 0 to signal successful completion of this (skipped) cycle.
            return 0
        
# Function that manages the main daily loop for an 'open_to_close' trading strategy.
def loop_for_open_to_close_trading(trader_start_adj_datetime, market_week_open_time, market_week_close_time, 
                                     host, port, client_id, symbol, primary_exchange, tick_size, smart_bool, 
                                     timezone, stock_timezone, data_frequency, restart_hour, restart_minute, time_after_open, time_before_close,
                                     trading_type, account, stra_opt_dates_filename, account_currency, 
                                     leverage, risk_management_bool, base_df_address, train_span, test_span, trail, fractional_shares,
                                     optimization, daily_optimization, additional_variables, strategy_file):
    
    # Fetch the latest tradable dates and contract details by calling the function from 'setup_for_contract_details.py'.
    dict_dates, contract, _ = get_tradable_dates_and_stock_currency(host, port, client_id, symbol, primary_exchange, smart_bool)
    
    # Calculate the precise start/end datetimes for the current and next trading sessions using a helper from 'trading_functions.py'.
    current_and_next_dates = tf.get_closest_tradable_datetimes(dict_dates, dt.datetime.now(), timezone, stock_timezone, data_frequency, 
                                                               restart_hour, restart_minute, time_after_open, time_before_close)
    
    # Unpack the start and end datetimes for the current trading day.
    trader_start_datetime, trader_end_datetime = current_and_next_dates[0], current_and_next_dates[1]
    # Unpack the start and end datetimes for the next trading day.
    trader_next_start_datetime, trader_next_end_datetime =  current_and_next_dates[2],  current_and_next_dates[3]
    
    # Calculate all critical intra-day time points (like restart times and end-of-day cutoffs) using a helper from 'trading_functions.py'.
    trader_start_datetime, trader_start_adj_datetime, day_datetime_before_end,\
          auto_restart_start_datetime, auto_restart_datetime_before_end, \
              auto_restart_end_datetime = \
                tf.get_restart_and_day_close_datetimes(trading_type, data_frequency, restart_hour, restart_minute, 
                                                        trader_start_datetime, trader_end_datetime,  trader_next_start_datetime, trader_next_end_datetime,
                                                        time_after_open, time_before_close)
                        
    # Set the datetime for the machine learning model, used for naming saved model files.
    model_datetime = trader_next_start_datetime - dt.timedelta(days=1)

    # Check if the current time is before the adjusted trading start time for the day.
    if dt.datetime.now() < trader_start_adj_datetime:            
        # If so, print a message indicating the bot is waiting.
        print("Let's wait until the trading day starts...")
        # Log the same waiting message.
        logging.info("Let's wait until the trading day starts...")
        # Enter a holding loop that pauses execution until the designated start time is reached.
        while dt.datetime.now() <= trader_start_adj_datetime: continue
    
    # Check if the current time is already past the end of today's trading session.
    if dt.datetime.now() > trader_end_datetime:
        # If so, print a message indicating the bot will wait for the next day.
        print("Let's wait until the next day to trade...")
        # Log the same waiting message.
        logging.info("Let's wait until the next day to trade...")
        # Pause execution until the start of the next trading day.
        time.sleep(0 if (trader_next_start_datetime-dt.datetime.now()).total_seconds()<0 else (trader_next_start_datetime-dt.datetime.now()).total_seconds())
        
    # If the current time is within the trading day.
    else:
        # Check if the current time is still before the market closes for the week.
        if dt.datetime.now() < market_week_close_time:
       
            # Check if there is a scheduled auto-restart for the IB Gateway/TWS during trading hours.
            if auto_restart_start_datetime is not None:
                    
                # Check if the current time is within the day's liquid trading hours.
                if ((dt.datetime.now() >= trader_start_adj_datetime) and (dt.datetime.now() <= trader_end_datetime)): 
        
                    # Check if the current time is before the scheduled auto-restart time.
                    if (dt.datetime.now() < auto_restart_end_datetime): 
                    
                        # Start a loop to run the trading strategy before the restart.
                        while True:
                            # Confirm the current time is still before the restart time.
                            if (dt.datetime.now() < auto_restart_end_datetime):
                                # Execute the core 'open-to-close' strategy logic.
                                run_open_to_close_strategy(host, port, client_id, account, account_currency, stra_opt_dates_filename, contract, timezone, 
                                                           trading_type, data_frequency, risk_management_bool, base_df_address,  
                                                           market_week_open_time, market_week_close_time, 
                                                           trader_start_adj_datetime, trader_start_datetime, 
                                                           trader_end_datetime, day_datetime_before_end, 
                                                           trader_next_start_datetime, trader_next_end_datetime, auto_restart_end_datetime,
                                                           train_span, test_span, trail, leverage, fractional_shares, optimization, tick_size, strategy_file)
                            # If the restart time has been reached.
                            else:
                                # Break the pre-restart trading loop.
                                break
                        # Enter a holding loop to wait for the restart process (e.g., a 5-minute window) to complete.
                        while (dt.datetime.now() >= auto_restart_end_datetime) and (dt.datetime.now() < auto_restart_start_datetime): continue
                    
                        # Start a new loop to run the strategy after the restart until the end-of-day cutoff.
                        while True:
                            # Confirm the current time is still before the end-of-day cutoff.
                            if (dt.datetime.now() < day_datetime_before_end):
                                # Execute the core 'open-to-close' strategy logic.
                                run_open_to_close_strategy(host, port, client_id, account, account_currency, stra_opt_dates_filename, contract, timezone, 
                                                           trading_type, data_frequency, risk_management_bool, base_df_address,  
                                                           market_week_open_time, market_week_close_time, 
                                                           trader_start_adj_datetime, trader_start_datetime, 
                                                           trader_end_datetime, day_datetime_before_end, 
                                                           trader_next_start_datetime, trader_next_end_datetime, auto_restart_end_datetime,
                                                           train_span, test_span, trail, leverage, fractional_shares, optimization, tick_size, strategy_file)
                            # If the end-of-day cutoff has been reached.
                            else:
                                # Break the post-restart trading loop.
                                break
                        # Start a final loop for the cleanup phase between the trading cutoff and the official market close.
                        while True:                
                            # Check if the current time is in this final window of the day.
                            if (dt.datetime.now() >= day_datetime_before_end) and (dt.datetime.now() < trader_end_datetime):
                                # Execute the strategy logic one last time, which will trigger position closing.
                                run_open_to_close_strategy(host, port, client_id, account, account_currency, stra_opt_dates_filename, contract, timezone, 
                                                           trading_type, data_frequency, risk_management_bool, base_df_address,  
                                                           market_week_open_time, market_week_close_time, 
                                                           trader_start_adj_datetime, trader_start_datetime, 
                                                           trader_end_datetime, day_datetime_before_end, 
                                                           trader_next_start_datetime, trader_next_end_datetime, auto_restart_end_datetime,
                                                           train_span, test_span, trail, leverage, fractional_shares, optimization, tick_size, strategy_file)
                            # If the official market close time has been reached.
                            else:
                                # Break the final cleanup loop.
                                break
                            
                        # If optimization and daily_optimization flags are enabled, run the parameter optimization process.
                        if optimization and daily_optimization:
                            # Print a status message indicating the start of optimization.
                            print('Optimizating the strategy parameters this day...')
                            # Log the same status message.
                            logging.info('Optimizating the strategy parameters this day...')
                            
                            # Execute the daily parameter optimization function.
                            daily_parameter_optimization(stra_opt_dates_filename, model_datetime, additional_variables)
                        
                    # This block handles the case where the current time is after a scheduled restart has already occurred.
                    else:
                        # Start a loop to run the strategy from the current time until the end-of-day cutoff.
                        while True:                
                            # Check if the current time is still before the end-of-day cutoff.
                            if (dt.datetime.now() < day_datetime_before_end):
                                # Execute the core 'open-to-close' strategy logic.
                                run_open_to_close_strategy(host, port, client_id, account, account_currency, stra_opt_dates_filename, contract, timezone, 
                                                           trading_type, data_frequency, risk_management_bool, base_df_address,  
                                                           market_week_open_time, market_week_close_time, 
                                                           trader_start_adj_datetime, trader_start_datetime, 
                                                           trader_end_datetime, day_datetime_before_end, 
                                                           trader_next_start_datetime, trader_next_end_datetime, auto_restart_end_datetime,
                                                           train_span, test_span, trail, leverage, fractional_shares, optimization, tick_size, strategy_file)
                            # If the end-of-day cutoff has been reached.
                            else:
                                # Break the main trading loop.
                                break
                                
                        # Start the final loop for the cleanup phase.
                        while True:                
                            # Check if the current time is in the final window of the day.
                            if (dt.datetime.now() >= day_datetime_before_end) and (dt.datetime.now() < trader_end_datetime):
                                # Execute the strategy logic one last time for position closing.
                                run_open_to_close_strategy(host, port, client_id, account, account_currency, stra_opt_dates_filename, contract, timezone, 
                                                           trading_type, data_frequency, risk_management_bool, base_df_address,  
                                                           market_week_open_time, market_week_close_time, 
                                                           trader_start_adj_datetime, trader_start_datetime, 
                                                           trader_end_datetime, day_datetime_before_end, 
                                                           trader_next_start_datetime, trader_next_end_datetime, auto_restart_end_datetime,
                                                           train_span, test_span, trail, leverage, fractional_shares, optimization, tick_size, strategy_file)
                            # If the official market close time has been reached.
                            else:
                                # Break the final cleanup loop.
                                break

                        # Print a message indicating the trading day is over and what happens next.
                        print("Trading day is over. In case it's not stock's timezone Thursday, let's wait until the market opens the next day to open a position once again. Otherwise we close the app...")
                        # Log the same message.
                        logging.info("Trading day is over. In case it's not stock's timezone Thursday, let's wait until the market opens the next day to open a position once again. Otherwise we close the app...")
            
                        # If optimization is enabled, run the daily optimization process.
                        if optimization and daily_optimization:
                            # Print a status message for optimization.
                            print('Optimizating the strategy parameters this day...')
                            # Log the same status message.
                            logging.info('Optimizating the strategy parameters this day...')
                            
                            # Execute the daily parameter optimization function.
                            daily_parameter_optimization(stra_opt_dates_filename, model_datetime, additional_variables)
                                                                   
            # This block handles a normal trading day with no scheduled auto-restart.
            else:
                
                # Start a loop to run the strategy until the end-of-day cutoff.
                while True:                
                    # Check if the current time is still before the end-of-day cutoff.
                    if (dt.datetime.now() < day_datetime_before_end):
                        # Execute the core 'open-to-close' strategy logic.
                        run_open_to_close_strategy(host, port, client_id, account, account_currency, stra_opt_dates_filename, contract, timezone, 
                                                   trading_type, data_frequency, risk_management_bool, base_df_address,  
                                                   market_week_open_time, market_week_close_time, 
                                                   trader_start_adj_datetime, trader_start_datetime, 
                                                   trader_end_datetime, day_datetime_before_end, 
                                                   trader_next_start_datetime, trader_next_end_datetime, auto_restart_end_datetime,
                                                   train_span, test_span, trail, leverage, fractional_shares, optimization, tick_size, strategy_file)
                    # If the end-of-day cutoff has been reached.
                    else:
                        # Break the main trading loop.
                        break
                        
                # Start the final loop for the cleanup phase.
                while True:                
                    # Check if the current time is in the final window of the day.
                    if (dt.datetime.now() >= day_datetime_before_end) and (dt.datetime.now() < trader_end_datetime):
                        # Execute the strategy logic one last time for position closing.
                        run_open_to_close_strategy(host, port, client_id, account, account_currency, stra_opt_dates_filename, contract, timezone, 
                                                   trading_type, data_frequency, risk_management_bool, base_df_address,  
                                                   market_week_open_time, market_week_close_time, 
                                                   trader_start_adj_datetime, trader_start_datetime, 
                                                   trader_end_datetime, day_datetime_before_end, 
                                                   trader_next_start_datetime, trader_next_end_datetime, auto_restart_end_datetime,
                                                   train_span, test_span, trail, leverage, fractional_shares, optimization, tick_size, strategy_file)
                    # If the official market close time has been reached.
                    else:
                        # Break the final cleanup loop.
                        break
                    
                # Print a message indicating the trading day is over.
                print("Trading day is over. In case it's not stock's timezone Thursday, let's wait until the market opens the next day to open a position once again. Otherwise we close the app...")
                # Log the same message.
                logging.info("Trading day is over. In case it's not stock's timezone Thursday, let's wait until the market opens the next day to open a position once again. Otherwise we close the app...")
    
                # If optimization is enabled, run the daily optimization process.
                if optimization and daily_optimization:
                    # Print a status message for optimization.
                    print('Optimizating the strategy parameters this day...')
                    # Log the same status message.
                    logging.info('Optimizating the strategy parameters this day...')
                    
                    # Execute the daily parameter optimization function.
                    daily_parameter_optimization(stra_opt_dates_filename, model_datetime, additional_variables)
                    
# Function to execute the logic for a 'close-to-open' (overnight) trading strategy.
def run_close_to_open_strategy(app, current_period, next_period, auto_restart_end_datetime, close_position=False):
    # Check the 'periods_traded' dataframe to see if the action for the current period has not yet been completed.
    if app.periods_traded.loc[app.periods_traded['trade_time']==current_period]['trade_done'].values[0] == 0:
        # Check if the function is NOT in position-closing mode (i.e., it's time to open a position at the end of the day).
        if close_position==False:
            # Execute the specific 'close-to-open' strategy logic from 'setup_functions.py' to open an overnight position.
            sf.run_strategy_close_to_open(app)

            # Check if the strategy execution completed successfully by checking a flag on the app object.
            if app.strategy_end:

                # Disconnect the app from the IB server using the helper function in 'setup_functions.py'.
                sf.stop(app)
                    
                # Pause execution until the start of the next trading period (which is the market open of the next day).
                time.sleep(0 if (next_period-dt.datetime.now()).total_seconds()<0 else (next_period-dt.datetime.now()).total_seconds())
                # Print a message indicating the bot is now waiting to close the position on the next day.
                print("Let's wait until the market opens the next day so we can close the current position in case we have it...")
                # Log the same waiting message.
                logging.info("Let's wait until the market opens the next day so we can close the current position in case we have it...")
    
                # Return 0 to signal successful completion for this cycle.
                return 0
            # If the strategy did not complete successfully (e.g., connection issue).
            else:
                # Print an error message detailing the likely cause.
                print("Couldn't connect to the IB server, could be due to internet issues or the TWS/IB Gateway is not opened...")
                # Log the same error message.
                logging.info("Couldn't connect to the IB server, could be due to internet issues or the TWS/IB Gateway is not opened...")

        # If the function is in position-closing mode (which runs at the start of the day).
        else:
            # Execute the function from 'setup_functions.py' that specifically closes any open positions.
            sf.update_and_close_positions(app)

            # Pause execution until the start of the next trading period (which is the end of the current day, to open a new position).
            time.sleep(0 if (next_period-dt.datetime.now()).total_seconds()<0 else (next_period-dt.datetime.now()).total_seconds())
            # Print a message indicating the bot is waiting until the end of the day to open a new position.
            print("Let's wait until the market closes this day so we can open a new position...")
            # Log the same waiting message.
            logging.info("Let's wait until the market closes this day so we can open a new position...")

            # Return 0 to signal successful completion of the closing action.
            return 0

    # If the action for the current period has already been completed.
    else:
        # Check if the function was supposed to open a position.
        if close_position==False:
            # If so, disconnect the app from the IB server.
            sf.stop(app)
            
            # Print a confirmation that the position was already opened for the night.
            print("The last position was already opened and the trading info was already updated...")
            # Log the same confirmation message.
            logging.info("The last position was already opened and the trading info was already updated...")
            
        # If the function was supposed to close a position (and it's already done).
        else:
            # Print a message indicating the bot is waiting until the end of the day.
            print("Let's wait until we reach the end of the day to open a new position...")
            # Log the same waiting message.
            logging.info("Let's wait until we reach the end of the day to open a new position...")
            # Pause execution until the next scheduled period (end of day).
            time.sleep(0 if (next_period-dt.datetime.now()).total_seconds()<0 else (next_period-dt.datetime.now()).total_seconds())
        
        # Return 0 to signal that this (skipped) cycle is complete.
        return 0
    
# Function that manages the main daily loop for a 'close_to_open' (overnight) trading strategy.
def loop_for_close_to_open_trading(trader_start_adj_datetime, market_week_open_time, market_week_close_time, 
                                     host, port, client_id, symbol, primary_exchange, tick_size, smart_bool, 
                                     timezone, stock_timezone, data_frequency, restart_hour, restart_minute, time_after_open, time_before_close,
                                     trading_type, account, stra_opt_dates_filename, account_currency, 
                                     leverage, risk_management_bool, base_df_address, train_span, test_span, trail, fractional_shares,
                                     optimization, daily_optimization, additional_variables, strategy_file):
    
    # Fetch the latest tradable dates and contract details using the function from 'setup_for_contract_details.py'.
    dict_dates, contract, _ = get_tradable_dates_and_stock_currency(host, port, client_id, symbol, primary_exchange, smart_bool)
    
    # Calculate the precise start/end datetimes for the current and next trading sessions using a helper from 'trading_functions.py'.
    current_and_next_dates = tf.get_closest_tradable_datetimes(dict_dates, dt.datetime.now(), timezone, stock_timezone, data_frequency, 
                                                                                   restart_hour, restart_minute, time_after_open, time_before_close)
    
    # Unpack the start and end datetimes for the current trading day.
    trader_start_datetime, trader_end_datetime = current_and_next_dates[0], current_and_next_dates[1]
    # Unpack the start and end datetimes for the next trading day.
    trader_next_start_datetime, trader_next_end_datetime =  current_and_next_dates[2],  current_and_next_dates[3]
    # Calculate the adjusted start time for the next day, which is a few minutes after the official open.
    trader_next_start_adj_datetime = trader_next_start_datetime + dt.timedelta(minutes=time_after_open)
    
    # Calculate all critical intra-day time points (like restart times and end-of-day cutoffs) using a helper from 'trading_functions.py'.
    trader_start_datetime, trader_start_adj_datetime, day_datetime_before_end,\
          auto_restart_start_datetime, auto_restart_datetime_before_end, \
              auto_restart_end_datetime = \
                tf.get_restart_and_day_close_datetimes(trading_type, data_frequency, restart_hour, restart_minute, 
                                                        trader_start_datetime, trader_end_datetime,  trader_next_start_datetime, trader_next_end_datetime,
                                                        time_after_open, time_before_close)
                        
    # Set the datetime for the machine learning model, used for naming saved model files.
    model_datetime = trader_next_start_datetime - dt.timedelta(days=1)

    # Check if the current time is before the adjusted trading start time for the day (time to close the position).
    if dt.datetime.now() < trader_start_adj_datetime:            
        # If so, print a message indicating the bot is waiting to close any existing overnight position.
        print("Let's wait until some minutes after the market opens to close an existing position...")
        # Log the same waiting message.
        logging.info("Let's wait until some minutes after the market opens to close an existing position...")
        # Enter a holding loop that pauses execution until the designated start time is reached.
        while dt.datetime.now() < trader_start_adj_datetime: continue
    
    # Check if the current time is already past the end of today's trading session.
    if dt.datetime.now() > trader_end_datetime:
        # If so, print a message indicating the bot will wait for the next day to begin.
        print("Let's wait until the next day starts to close the position...")
        # Log the same waiting message.
        logging.info("Let's wait until the next day starts to close the position...")
        # Pause execution until the start of the next trading day.
        time.sleep(0 if (trader_next_start_datetime-dt.datetime.now()).total_seconds()<0 else (trader_next_start_datetime-dt.datetime.now()).total_seconds())
        
    # If the current time is within the trading day.
    else:
        
        # Determine the previous, current, and next trading periods using a helper from 'trading_functions.py'.
        previous_period, current_period, next_period = tf.get_the_closest_periods(dt.datetime.now(), trading_type, data_frequency, 
                                                                                  trader_start_adj_datetime, trader_start_datetime, 
                                                                                  trader_end_datetime, day_datetime_before_end, 
                                                                                  trader_next_start_datetime, trader_next_end_datetime)
        
        # Instantiate the main trading application client from 'setup.py', providing all necessary configuration and state.
        app = trading_app(logging, account, account_currency, stra_opt_dates_filename, contract, timezone, trading_type, 
                          data_frequency,  
                          risk_management_bool, base_df_address,  
                          market_week_open_time, market_week_close_time, 
                          trader_start_datetime, trader_start_adj_datetime, trader_end_datetime, day_datetime_before_end, trader_next_start_datetime, trader_next_end_datetime,
                          current_period, previous_period, next_period, train_span, test_span, trail, leverage, fractional_shares, optimization, tick_size, strategy_file)
                
        # Print a status message indicating a connection attempt to the IB server.
        print('Connecting the app to the IB server...')
        # Log the same status message for record-keeping.
        logging.info('Connecting the app to the IB server...')
        # Establish the connection to the Interactive Brokers TWS or Gateway.
        app.connect(host=host, port=port, clientId=client_id)
        
        # Create a new thread to run the app's message-receiving loop, preventing the main thread from blocking.
        thread1 = Thread(target=app.run, daemon=True)
    
        # Start the app's message-receiving thread.
        thread1.start()
            
        # Pause execution for 5 seconds to allow the connection to be established securely.
        time.sleep(5)
           
        # Print the current trading period for user visibility.
        print(f'\t- Current period is {current_period}')
        # Log the current trading period.
        logging.info(f'\t- Current period is {current_period}')
        # Print the next scheduled trading period.
        print(f'\t- Next period is {next_period}')
        # Log the next scheduled trading period.
        logging.info(f'\t- Next period is {next_period}')
        # Print the adjusted start time for trading.
        print(f'\t- Start datetime after some minutes the market opens is {trader_start_adj_datetime}')
        # Log the adjusted start time.
        logging.info(f'\t- Start datetime after some minutes the market opens is {trader_start_adj_datetime}')
        # Print the official start of the trading day.
        print(f'\t- Trading day start datetime is {trader_start_datetime}')
        # Log the official start of the trading day.
        logging.info(f'\t- Trading start end datetime is {trader_start_datetime}')
        # Print the official end of the trading day.
        print(f'\t- Trading day end datetime is {trader_end_datetime}')
        # Log the official end of the trading day.
        logging.info(f'\t- Trading day end datetime is {trader_end_datetime}')
        # Print the calculated time to open positions before the market officially closes.
        print(f'\t- Day end datetime before market closes is {day_datetime_before_end}')
        # Log the calculated end-of-day cutoff time.
        logging.info(f'\t- Day end datetime before market closes is {day_datetime_before_end}')
        # Print the start time of the next trading day.
        print(f'\t- Trading next-day start datetime is {trader_next_start_datetime}')
        # Log the start time of the next trading day.
        logging.info(f'\t- Trading next-day start datetime is {trader_next_start_datetime}')
        
        # Check if the current time is still before the market closes for the week.
        if dt.datetime.now() < market_week_close_time:
       
            # This condition checks if it's the end of the day, the time to OPEN an overnight position.
            if ((dt.datetime.now() >= day_datetime_before_end) and (dt.datetime.now() <= trader_end_datetime)): 
                # Start a loop to run the "open position" logic.
                while True:                
                    # Confirm the current time is within the end-of-day window.
                    if (dt.datetime.now() >= day_datetime_before_end) and (dt.datetime.now() < trader_end_datetime):
                        # Execute the core strategy with 'close_position=False' to open a new position.
                        run_close_to_open_strategy(app, current_period, next_period, auto_restart_end_datetime)
                    # If the time has passed this window.
                    else:
                        # Break the loop.
                        break
                        
                # Print a message indicating the trading day is over and what happens next.
                print("Trading day is over. In case it's not stock's timezone Thursday, let's wait until the market opens the next day to close the position once again. Otherwise we close the app...")
                # Log the same message.
                logging.info("Trading day is over. In case it's not stock's timezone Thursday, let's wait until the market opens the next day to close the position once again. Otherwise we close the app...")
    
                # Wait until the start of the next trading day to close the position.
                while ((dt.datetime.now() >= trader_end_datetime) and (dt.datetime.now() < trader_next_start_adj_datetime)): continue
        
            # This condition checks if it's the start of the day, the time to CLOSE the overnight position.
            elif ((dt.datetime.now() >= trader_start_adj_datetime) and (dt.datetime.now() < day_datetime_before_end)): 
                # Print a status message indicating it's time to close the position.
                print("We're in a new current day, let's close the position in case there's any...")
                # Log the same status message.
                logging.info("We're in a new current day, let's close the position in case there's any...")
    
                # Start a loop to run the "close position" logic.
                while True:
                    # Execute the core strategy with 'close_position=True' to close the existing position.
                    run_close_to_open_strategy(app, current_period, next_period, auto_restart_end_datetime, True)
                    
                    # If optimization and daily_optimization flags are enabled, run the parameter optimization process.
                    if optimization and daily_optimization:
                        # Print a status message indicating the start of optimization.
                        print('Optimizating the strategy parameters this day...')
                        # Log the same status message.
                        logging.info('Optimizating the strategy parameters this day...')
                        
                        # Execute the daily parameter optimization function.
                        daily_parameter_optimization(stra_opt_dates_filename, model_datetime, additional_variables)
                                                       
                    # Break the loop after the action is performed once.
                    break
                
# Main function that serves as the entry point for the entire application.
def main():   
     
    # Extract all user-defined variables from the 'main.py' configuration file using a helper from 'trading_functions.py'.
    variables = tf.extract_variables('main.py')
    
    # Assign the 'daily_optimization' boolean from the configuration variables.
    daily_optimization = variables['daily_optimization']
    # Assign the IBKR TWS/Gateway host IP address.
    host = variables['host']
    # Assign the type of trading strategy to be used (e.g., 'intraday').
    trading_type = variables['trading_type']
    # Assign the IBKR account number.
    account = variables['account']
    # Assign the user's local timezone.
    timezone = variables['timezone']
    # Assign the port number for the IBKR TWS/Gateway.
    port = variables['port']
    # Assign the base currency of the IBKR account.
    account_currency = variables['account_currency']
    # Assign the stock symbol to be traded.
    symbol = variables['symbol']
    # Assign the filename of the custom strategy logic.
    strategy_file = variables['strategy_file']
    
    # Set the data frequency based on the trading type.
    if trading_type == 'intraday':
        # For intraday strategies, use the frequency specified in 'main.py'.
        data_frequency = variables['data_frequency']
    else:
        # For swing or overnight strategies, default to daily ('1D') data frequency.
        data_frequency = '1D'
        
    # Define the file path for the downloaded historical data CSV.
    variables['historical_data_address'] = 'data/historical_data.csv'
    # Assign the file path for the feature-engineered base dataframe.
    base_df_address = variables['base_df_address']
    # Assign the number of historical periods to use for training the model.
    train_span = variables['train_span']
    # Assign the number of days to use for the test set during optimization.
    test_span_days = variables['test_span_days']
    # Assign the client ID for the IBKR API connection.
    client_id = variables['client_id']
    # Assign the seed for random number generation to ensure reproducibility.
    seed = variables['seed']
    # Check if 'fractional_shares' is defined in the configuration.
    if 'fractional_shares' in variables:
        # If yes, assign its value.
        fractional_shares = variables['fractional_shares']
    else:
        # Otherwise, default to False.
        fractional_shares = False
    # Assign the minimum price movement (tick size) for the asset.
    tick_size = variables['tick_size']
    
    # Check if a 'leverage' value is defined and positive in the configuration.
    if 'leverage' in variables.keys():
        if (variables['leverage'] is not None) or (variables['leverage'] > 0):
            # If so, assign the leverage value.
            leverage = variables['leverage']
    else:
        # Otherwise, set leverage to None, indicating it may be set dynamically by the strategy.
        leverage = None
        
    # Assign the sender's email address for notifications.
    smtp_username = variables['smtp_username']
    # Assign the recipient's email address for notifications.
    to_email = variables['to_email']
    
    # Calculate the test span in terms of data periods (not days) using a helper from 'trading_functions.py'.
    test_span = test_span_days*tf.get_periods_per_day(data_frequency)
        
    # For 'intraday' trading, optimization is implicitly enabled.
    if trading_type == 'intraday':
        # Set the optimization flag to True.
        optimization = True
        
        # Add the test span to the training span to ensure enough data is downloaded for both.
        train_span += test_span
        
        # Update the variables dictionary with the calculated test and train spans.
        variables['test_span'] = test_span
        variables['train_span'] = train_span

    # For other trading types, check if optimization is explicitly enabled.
    else:
        # Check if 'optimization' is defined in the configuration.
        if 'optimization' in variables:
            # Assign the value of the optimization flag.
            optimization = variables['optimization']
            # If optimization is enabled.
            if optimization:
                # Calculate the test span in periods.
                test_span = test_span_days*tf.get_periods_per_day(data_frequency)
                
                # Add the test span to the training span.
                train_span += test_span
                
                # Update the variables dictionary with the new spans.
                variables['test_span'] = test_span
                variables['train_span'] = train_span
            else:
                # If optimization is disabled, set default small spans.
                variables['test_span'] = test_span
                variables['train_span'] = 500

        else:
            # If optimization is not defined, default it to False and set small spans.
            optimization = False
            variables['test_span'] = test_span
            variables['train_span'] = 500
            
    # Assign the email password for sending notifications.
    password = variables['password']
    # Assign the trailing stop loss boolean flag.
    trail = variables['trail']
    # Assign the boolean for using IBKR's SMART routing.
    smart_bool = variables['smart_bool']
    # Assign the primary exchange for the asset.
    primary_exchange = variables['primary_exchange']
    # Assign the boolean for enabling the risk management module (stop-loss/take-profit).
    risk_management_bool = variables['risk_management_bool']
    # Assign the scheduled time for IBKR TWS/Gateway daily restart.
    restart_time = variables['restart_time']
    # Assign the number of minutes to wait after market open before trading.
    time_after_open = max(1,variables['time_after_open'])
    # Assign the number of minutes before market close to stop opening new trades.
    time_before_close = max(1,variables['time_before_close'])
    
    # Define the file path for the CSV that tracks strategy optimization dates.
    stra_opt_dates_filename = 'data/models/stra_opt_dates.csv'
    
    # Fetch the asset's contract details and its exchange's timezone using the helper from 'setup_for_contract_details.py'.
    dict_dates, contract, stock_timezone = get_tradable_dates_and_stock_currency(host,port,client_id,symbol,primary_exchange, smart_bool)

    # Calculate the precise start and end datetimes for the current and next trading sessions using a helper from 'trading_functions.py'.
    current_and_next_dates = tf.get_closest_tradable_datetimes(dict_dates, now_, timezone, stock_timezone, data_frequency, 
                                                                                   restart_time[:2], restart_time[2:], time_after_open, time_before_close)
    
    # Unpack the start and end datetimes for the current trading day.
    trader_start_datetime, trader_end_datetime = current_and_next_dates[0], current_and_next_dates[1]
    # Unpack the start datetime for the next trading day.
    trader_next_start_datetime = current_and_next_dates[2]
            
    # Define the entire trading week's open and close times using a helper from 'trading_functions.py'.
    market_week_open_time, market_week_close_time = tf.define_trading_week(timezone, trader_start_datetime.hour, trader_start_datetime.minute, trader_end_datetime.hour, trader_end_datetime.minute)
    
    # Set the model datetime for file naming purposes, using the start of the week.
    variables['model_datetime'] = market_week_open_time
    
    # Inspect the 'strategy_parameter_optimization' function in 'strategy.py' to determine its required arguments.
    signature = inspect.signature(stra.strategy_parameter_optimization)
    
    # Prepare the list of arguments to pass to the strategy optimization function.
    stra_func_params = [variables[name] for name, param in signature.parameters.items()]
    
    # Create a dictionary of additional variables that might be needed by other functions.
    additional_variables = {'contract':contract, 'current_and_next_dates':current_and_next_dates}
            
    # Set the seed for numpy's random number generator for reproducibility.
    np.random.seed(seed)
    
    # If optimization is enabled, perform the pre-run optimization.
    if optimization:
        # If daily optimization is enabled.
        if daily_optimization:
            # Print a status message.
            print('Optimizating the strategy parameters if needed...')
            # Log the status message.
            logging.info('Optimizating the strategy parameters if needed...')
            
            # Determine the correct date to use for the model based on the trading type and current time.
            if (trading_type=='intraday') or (trading_type=='open_to_close'):
                # If we are before the end of the day, use yesterday relative to the start of the day.
                if dt.datetime.now() < trader_end_datetime:
                    model_datetime = trader_start_datetime - dt.timedelta(days=1)
                # If we are after the end of the day, use yesterday relative to the start of the next day.
                else:
                    model_datetime = trader_next_start_datetime - dt.timedelta(days=1)
            # Logic for close-to-open strategy.
            elif trading_type=='close_to_open':
                # If we are before the next day starts, use today's start date for the model.
                if dt.datetime.now() < trader_next_start_datetime:
                    model_datetime = trader_start_datetime
                # Otherwise, use the next day's start date.
                else:
                    model_datetime = trader_next_start_datetime
                
            # Execute the daily parameter optimization function to check if retraining is needed.
            daily_parameter_optimization(stra_opt_dates_filename, model_datetime, additional_variables)
        # If daily optimization is disabled, run a one-time optimization.
        else:
    
            # Prepare arguments for the historical data download app.
            hist_data_app_variables = [variables[name] if name in variables else additional_variables[name] 
                                       for name, param in signature.parameters.items()]
        
            # Print a status message.
            print('Creating the whole historical data...')
            # Run the historical data download app from 'setup_for_download_data.py'.
            sdd.run_hist_data_download_app(*hist_data_app_variables)
            
            # Run the full strategy parameter optimization from 'strategy.py'.
            stra.strategy_parameter_optimization(*stra_func_params)
        
    
            # If the optimization tracking file exists.
            if os.path.exists(stra_opt_dates_filename):
                # Load the file, add a new entry for today, and save it.
                stra_opt_dates = pd.read_csv(stra_opt_dates_filename, index_col=0, parse_dates=True)
                stra_opt_dates.loc[market_week_open_time.date(), 'update'] = 1
                stra_opt_dates.sort_index(inplace=True)
                stra_opt_dates.to_csv(stra_opt_dates_filename)
            # If the file doesn't exist.
            else:
                # Create a new dataframe, add the first entry, and save it.
                stra_opt_dates = pd.DataFrame(columns=['update'])
                stra_opt_dates.loc[market_week_open_time.date(), 'update'] = 1
                stra_opt_dates.sort_index(inplace=True)
                stra_opt_dates.to_csv(stra_opt_dates_filename)
            
    # Check if the main database Excel file exists.
    if os.path.exists("data/database.xlsx")==False:
        
        # If not, print a message indicating its creation.
        print('Creating the trading information database...')
        # Call the function from 'create_database.py' to create the initial database and email info files.
        cd.create_trading_info_workbook(smtp_username, to_email , password)
        
    # Launch the main, persistent trading loop for the week.
    run_trading_setup_loop(host, daily_optimization, dict_dates, contract, stra_opt_dates_filename, trading_type, 
                           port, account, client_id, data_frequency, risk_management_bool, 
                           timezone, restart_time, time_after_open, time_before_close, stock_timezone, 
                           dt.datetime.now(), account_currency, symbol, primary_exchange, tick_size, smart_bool, 
                           leverage, 
                           base_df_address, train_span, 1, trail, fractional_shares, optimization, strategy_file)
            
    # After the main trading loop finishes, run a final optimization check if enabled.
    if optimization:
        
        # Parse the restart hour and minute again.
        restart_hour = int(restart_time[:2])
        restart_minute = int(restart_time[3:])
        
        # Get the latest tradable datetimes.
        current_and_next_dates = tf.get_closest_tradable_datetimes(dict_dates, now_, timezone, stock_timezone, data_frequency, 
                                                                   restart_hour, restart_minute, time_after_open, time_before_close)
        
        # Unpack the datetimes.
        trader_start_datetime, trader_end_datetime = current_and_next_dates[0], current_and_next_dates[1]
        trader_next_start_datetime = current_and_next_dates[2]
                
        # Prepare additional variables.
        additional_variables = {'contract':contract, 'current_and_next_dates':current_and_next_dates}
                
        # If daily optimization is enabled.
        if daily_optimization:
            # Print a status message.
            print('Optimizating the strategy parameters if needed...')
            # Log the status message.
            logging.info('Optimizating the strategy parameters if needed...')
            
            # Determine the correct model date based on the trading type and current time.
            if (trading_type=='intraday') or (trading_type=='open_to_close'):
                if dt.datetime.now() < trader_end_datetime:
                    model_datetime = trader_start_datetime - dt.timedelta(days=1)
                else:
                    model_datetime = trader_next_start_datetime - dt.timedelta(days=1)
            elif trading_type=='close_to_open':
                if dt.datetime.now() < trader_next_start_datetime:
                    model_datetime = trader_start_datetime
                else:
                    model_datetime = trader_next_start_datetime
                
            # Check if the optimization tracking file exists.
            if os.path.exists(stra_opt_dates_filename):
                # Load the file.
                stra_opt_dates = pd.read_csv(stra_opt_dates_filename, index_col=0)
                # Convert its index to datetime objects.
                stra_opt_dates.index = pd.to_datetime(stra_opt_dates.index)
                
                # Check if the last optimization date is different from the required model date.
                if stra_opt_dates.index[-1].date() != model_datetime.date():
        
                    # If different, run the daily parameter optimization.
                    daily_parameter_optimization(stra_opt_dates_filename, model_datetime, additional_variables)
                    
                # If already optimized for the date.
                else:
                    # Print a confirmation message.
                    print('Strategy paramter opimization was already done...')
            
        # If daily optimization is disabled, run the one-time optimization.
        else:
    
            # Define the week's trading boundaries.
            market_week_open_time, market_week_close_time = tf.define_trading_week(timezone, trader_start_datetime.hour, trader_start_datetime.minute, 
                                                                                   trader_end_datetime.hour, trader_end_datetime.minute)
            
            # Set the model datetime for file naming.
            variables['model_datetime'] = market_week_open_time
        
            # Prepare arguments for the strategy optimization function.
            stra_func_params = [variables[name] for name, param in signature.parameters.items()]
    
            # Prepare arguments for the data download app.
            hist_data_app_variables = [variables[name] if name in variables else additional_variables[name] 
                                       for name, param in signature.parameters.items()]
    
            # Print a status message.
            print('Creating the whole historical data...')
            # Run the data download app.
            sdd.run_hist_data_download_app(*hist_data_app_variables)
            
            # Run the full strategy parameter optimization.
            stra.strategy_parameter_optimization(*stra_func_params)
        
            # If the tracking file exists.
            if os.path.exists(stra_opt_dates_filename):
                # Update it with the latest optimization date.
                stra_opt_dates = pd.read_csv(stra_opt_dates_filename, index_col=0, parse_dates=True)
                stra_opt_dates.loc[market_week_open_time.date(), 'update'] = 1
                stra_opt_dates.sort_index(inplace=True)
                stra_opt_dates.to_csv(stra_opt_dates_filename)
            # If not, create it.
            else:
                stra_opt_dates = pd.DataFrame(columns=['update'])
                stra_opt_dates.loc[market_week_open_time.date(), 'update'] = 1
                stra_opt_dates.sort_index(inplace=True)
                stra_opt_dates.to_csv(stra_opt_dates_filename)

    # Print a final message indicating the trading week is over.
    print('Trading week is over, we close now the setup and run it once again with some tim...')

# This line calls the main function, starting the entire application when the script is executed.
main()
