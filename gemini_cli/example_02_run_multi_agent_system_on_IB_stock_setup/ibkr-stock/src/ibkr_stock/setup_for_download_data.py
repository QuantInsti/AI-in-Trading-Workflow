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
import pandas as pd
from threading import Event
from threading import Thread
import datetime as dt
from ibapi.client import EClient
from ibapi.wrapper import EWrapper

import warnings
warnings.filterwarnings('ignore')

##########################################################################
# Define a new client class that serves as both the client and the wrapper for data downloading.
class app_for_download_data(EWrapper, EClient):
    # This comment indicates the class serves as both the client and the wrapper.
    ''' Serves as the client and the wrapper '''
    # The constructor for the class, taking connection, contract, and data parameters.
    def __init__(self, addr, client_id, file_name, train_span=3500, \
                 contract = {}, timezone= 'US/Eastern', data_frequency = '1 D', current_and_next_dates = list()):
        
        # Initialize the EClient part of the class, which sets up the connection mechanism.
        EClient.__init__(self, self)
        
        # Define the number of worker threads (though not actively used in the provided logic).
        # Number of threads
        self.workers = 4
        
        # Store the user's local timezone to be used for date calculations.
        # Set the time zone of the trader
        self.zone = timezone
                
        # Store the contract object (defined in 'ib_functions.py') for the asset to be downloaded.
        # Get the Stock contract
        self.contract = contract

        # Initialize an empty pandas DataFrame to store the incoming historical data.
        # Dataframe dictionary to save the historical dataframes
        self.df = pd.DataFrame()
        
        # Initialize an empty DataFrame to hold the final, processed data before saving.
        # DataFrame to save the completed dataframe to be saved
        self.end_df = pd.DataFrame()
                        
        # Store the desired file name for the output CSV file.
        # File name to be used to save the historical data
        self.file_name = file_name
                            
        # A list of default IBKR ports to try connecting to (TWS and Gateway, live and paper).
        # A list of all the IB ports
        self.ports = [7497,7496,4001,4002]
        # Store the IP address of the machine running TWS/Gateway.
        # The addr value
        self.addr = addr
        # Store the client ID for this specific API connection.
        # Set the client id number
        self.client_id = client_id

        # Initialize a dictionary to store any error codes and messages received from the API.
        # Error Dictionary
        self.errors_code_dict = {}
        
        # Store the list containing the current and next trading session start/end times.
        # Set the current and next trading dates
        self.current_and_next_dates = current_and_next_dates
        
        # Store the number of historical periods to download for the training set.
        # Set the train span to download data
        self.train_span = train_span

        # A boolean flag to track if the initial connection launch message has been printed.
        # Launch app message boolean
        self.launch_message_bool = False
        
        # Parse the 'data_frequency' string to determine the format needed for API requests and date ranges.
        # Set the data frequency
        if 'D' in data_frequency:
            # If frequency is in days, format it for the API (e.g., '1 D').
            self.data_frequency = f'{data_frequency[:data_frequency.find('D')]} D'
            # Set the frequency string for pandas date_range function.
            self.date_range_freq = 'D'
        elif 'min' in data_frequency:
            # If frequency is in minutes.
            self.date_range_freq = data_frequency
            # Special case for 1 minute.
            if int(data_frequency[:data_frequency.find('min')])==1:
                # Format for the API as '1 min'.
                self.data_frequency = '1 min'
                # Set the frequency string for pandas.
                self.date_range_freq = 'min'
            else:
                # Format for the API as 'X mins'.
                self.data_frequency = f'{data_frequency[:data_frequency.find('min')]} mins'       
        elif 'h' in data_frequency:
            # If frequency is in hours.
            self.date_range_freq = data_frequency
            # Special case for 1 hour.
            if int(data_frequency[:data_frequency.find('h')])==1:
                # Format for the API as '1 hour'.
                self.data_frequency = '1 hour'
            else:
                # Format for the API as 'X hours'.
                self.data_frequency = f'{data_frequency[:data_frequency.find('hours')]} hours'
                # Set the frequency string for pandas.
                self.date_range_freq = 'h'
        elif '1w' == data_frequency:
            # Format weekly data for the API.
            self.data_frequency = '1 week'        
            # Set the frequency string for pandas to be weekly, ending on Friday.
            self.date_range_freq = 'W-FRI'
        elif '1M' == data_frequency:
            # Format monthly data for the API.
            self.data_frequency = f"{data_frequency[:data_frequency.find('M')]} month"
            # Set the frequency string for pandas to be business month end.
            self.date_range_freq = 'BM'

        # Call the method to launch the connection sequence.
        # Launch the app
        self.LaunchApp()
        
        # Check if the connection was successfully launched.
        if self.launch_message_bool == True: # Successful App Launching
            # If connected, start the client's message-processing loop in a separate background thread.
            # Launch the client thread
            thread = Thread(target=self.run)
            thread.start()
            # Once the thread is running, call the method to initiate the data download algorithm.
            # Once the thread starts, Initiate the app algorithm
            result = self.InitiateAlgorithm(1)
            # Check if the initialization failed and returned an error.
            # If the initialization failed
            if isinstance(result,ValueError):
                # If there was an error, wait for 3 seconds.
                # In case there is an error, disconnect the app
                time.sleep(3)
                # Disconnect the client from the server.
                self.disconnect()
            # Check if the initialization was successful and returned a DataFrame.
            # If the initialization was successful
            elif isinstance(result, pd.DataFrame):
                # If the algorithm finished, wait for 3 seconds.
                # In case the whole algorithm ends, disconnect the app
                time.sleep(3)
                # Disconnect the client from the server.
                self.disconnect()
            
    # This is an EWrapper callback that is triggered when an error is received from IBKR.
    def error(self, reqId, code, msg, advancedOrderRejectJson=''):
        # This comment indicates the function is called if an error occurs.
        ''' Called if an error occurs '''
        
        # Store the error message in the errors dictionary with the code as the key.
        # Save tje ,essage
        self.errors_code_dict[code] = msg
        # Print the error message to the console, but filter out common, non-critical status messages.
        # Print only the following messages
        if (code != 502 or code != 504 or \
            code != 2103 or code != 2104  or code != 2105 or \
            code != 2106 or code != 2107 or code != 2157 or code != 2158):
            print('Error {}: {}'.format(code, msg))
        # Check for critical connection loss errors.
        if msg == 'Not connected' or \
            msg == \
            "Connectivity between IB and Trader Workstation has been lost." \
            or msg == 'HMDS data farm connection is broken:cashhmds':
            # If a critical error occurs, wait for 3 seconds.
            time.sleep(3)
            # Disconnect the client.
            self.disconnect()
            
    # This method handles the initial connection to the IBKR server.
    def LaunchApp(self):
        # This comment indicates the function's purpose.
        ''' Function to launch the app '''
        # Loop through the list of available ports to find an open TWS or Gateway instance.
        for port in self.ports:
            # Attempt to connect to the IBKR server on the current port.
            # Create the client and connect to TWS with live trading
            self.connect(self.addr, port, self.client_id)
            # Pause for 4 seconds to allow time for the connection attempt.
            time.sleep(4)
            # Check if the connection was successful by seeing if connection errors (504, 502) are NOT in the errors dictionary.
            # If the connection wasn't established or the port wasn't the correct one
            if (504 in self.errors_code_dict) == False and \
               (502 in self.errors_code_dict) == False:
                # Check if the port corresponds to a live TWS session.
                if port == 7496:  
                    # Print a success message.
                    print("="*80)
                    print('Setup successfully launched with IB TWS for downloading historical data...')
                    print("="*80)
                # Check if the port corresponds to a paper TWS session.
                elif port == 7497:
                    # Print a success message.
                    print("="*80)
                    print('Setup successfully launched with IB TWS for downloading historical data...')
                    print("="*80)
                # Check if the port corresponds to a live Gateway session.
                elif port == 4001:
                    # Print a success message.
                    print("="*80)
                    print('Setup successfully launched with IB Gateway for downloading historical data...')
                    print("="*80)
                # Check if the port corresponds to a paper Gateway session.
                elif port == 4002:
                    # Print a success message.
                    print("="*80)
                    print('Setup successfully launched with IB Gateway for downloading historical data...')
                    print("="*80)
                # If connection is successful, set the launch message flag to True.
                # Let's download the historical data
                self.launch_message_bool = True
                # Exit the loop since a connection has been established.
                break
            
            # If connection on the current port failed, clear the errors dictionary for the next attempt.
            # Clean the errors dictionary
            self.errors_code_dict = {}
        # If the loop finishes and error 504 (not connected) is present, it means no connection could be made.
        # If any port worked
        if 504 in self.errors_code_dict:
            # Print a message prompting the user to open TWS/Gateway.
            print('Please open the IB Gateway or TWS...')
        # If error 502 is present, it's a specific connection issue.
        # Print the 502 error in case you haven't followed the appropriate instructions
        elif 502 in self.errors_code_dict:
            # Print the detailed error message from the dictionary.
            print(self.errors_code_dict[502])
            
    # This method initiates the main data download logic after a successful connection.
    def InitiateAlgorithm(self, activate = False):
        # This comment indicates the function's purpose.
        ''' Function to initiate the historical data download algorithm '''
        
        # Check if the activation flag is set to True.
        # If the app was successfully launched
        if activate == True:
            # Wait for 3 seconds to ensure all connections are stable.
            time.sleep(3)
            # Print the start time of the download.
            print(f'Download starts at {dt.datetime.now()}')
            # Call the method that requests the historical data from the server.
            # Download the data and save the result
            # result = self.multithreading_loop()
            self.request_data()
            # After the download is complete, disconnect the client.
            # Disconnect the app
            self.disconnect()
            # Return the populated DataFrame.
            return self.df
        
    # This is an EWrapper callback that is triggered for each bar of historical data received.
    #@iswrapper
    def historicalData(self, reqId, bar):
        # This comment indicates the function's purpose.
        ''' Called in response to reqHistoricalData '''
        
        # Add the Close price of the current bar to the DataFrame, using the bar's date as the index.
        self.df.loc[bar.date,'Close'] = bar.close
        # Add the Open price.
        self.df.loc[bar.date,'Open'] = bar.open
        # Add the High price.
        self.df.loc[bar.date,'High'] = bar.high
        # Add the Low price.
        self.df.loc[bar.date,'Low'] = bar.low
        # Add the Volume.
        self.df.loc[bar.date,'Volume'] = bar.volume

    # This EWrapper callback is triggered when all historical data for a request has been received.
    def historicalDataEnd(self, reqId, start, end):
        # This comment indicates the function's purpose.
        ''' Called when the historical data for reqId is finished '''
        # Call the parent class's method to ensure proper behavior.
        super().historicalDataEnd(reqId, start, end)
        # Print a confirmation message indicating the download for this request ID is complete.
        print(f"Historical Data for ID {reqId} Download End")
        # Set the threading event to signal that the download is finished, unblocking the main thread.
        self.event.set()
            
    # This method constructs and sends the historical data request.
    def request_data(self):
        # This comment indicates the function's purpose.
        ''' Called when the historical data for reqId is finished '''
        
        # Print a message indicating the start of the download request.
        print("Historical Data for ID 0 Download Starts...")
        
        # Create a threading Event object that will be used to pause the script until the download is complete.
        # Set the threading event for the download request
        self.event = Event()
        # Ensure the event is in a cleared (not set) state initially.
        # Clear the threading event
        self.event.clear()
        
        # Calculate the start date for the data download using the train_span and frequency.
        # Set the datetime to be the first historical data point
        first_datetime = pd.date_range(end=dt.datetime.now().replace(microsecond=0, second=0), 
                                       periods=self.train_span, 
                                       freq=f"{self.date_range_freq}")[0]

        # Calculate the number of days required for the download duration string.
        # Set the number of days to be used to download the historical adjusted data
        num_days = math.ceil((dt.datetime.now().replace(second=0,microsecond=0) - first_datetime).days+1)
        # Determine if the duration should be specified in Years ('Y') or Days ('D') for the API request.
        if num_days>252:
            # If more than a business year, use Years.
            span_string = f'{math.ceil(num_days/252)} Y'
        else:
            # Otherwise, use Days.
            span_string = f'{num_days} D'
            
        # Format the bar size string for the API request based on the data frequency.
        if 'min' in self.data_frequency:
            # Format for minutes.
            hist_bar = f'{int(self.data_frequency[:self.data_frequency.find('m')])} mins'
        elif 'h' in self.data_frequency:
            # Format for hours.
            hist_bar = f'{int(self.data_frequency[:self.data_frequency.find('h')])} hours'
        elif 'D' in self.data_frequency:
            # Format for days.
            hist_bar = f'{int(self.data_frequency[:self.data_frequency.find('D')])} day'
               
        # Send the historical data request to the IBKR server with all the specified parameters.
        # Download the data
        self.reqHistoricalData(0, self.contract, '', span_string, hist_bar, \
                               'ADJUSTED_LAST', 1, 1, False, []) # alpha
        # Pause the main thread here; it will wait until the 'historicalDataEnd' callback calls 'self.event.set()'.
        # Make the event to wait until the download is completed
        self.event.wait()
        # Once the download is complete and the event is set, call the method to process and save the data.
        # Prepare the historical dataframe
        self.prepare_df()
        
    # This method performs final cleaning and formatting of the downloaded data.
    def prepare_df(self):
        # This comment indicates the function's purpose.
        ''' Function to update the whole historical dataframe '''
        
        # Sort the DataFrame by its index (which is the date).
        # Sort the dataframe by index
        self.df.sort_index(inplace=True)
        # Remove any duplicate index entries, keeping the first occurrence.
        # Drop duplicates
        self.df = self.df[~self.df.index.duplicated(keep='first')]
        # Convert the index from a string format to a proper pandas datetime object.
        # Set the index to datetime type            
        self.df.index = pd.to_datetime(self.df.index, format='%Y%m%d %H:%M:%S %Z')
        # Remove any timezone information from the datetime index to make it timezone-naive.
        # Get rid of the timezone tag
        self.df.index = self.df.index.tz_localize(None)
        # Filter the DataFrame to include only the rows that fall within the asset's liquid trading hours.
        # Subset the DataFrame to get rows between start_time and end_time (inclusive)
        self.df = self.df.between_time(self.current_and_next_dates[0].time(), self.current_and_next_dates[1].time()).copy()  
        
        # Save the final, cleaned DataFrame to a CSV file.
        # Save the historical dataframe into a CSV file
        self.df.to_csv(self.file_name, encoding='utf-8', index=True)
                                  
# -------------------------x-----------------------x--------------------------#
# -------------------------x-----------------------x--------------------------#
# -------------------------x-----------------------x--------------------------#    

# This is a wrapper function to conveniently start the historical data download process.
def run_hist_data_download_app(historical_data_address, train_span, timezone, data_frequency, 
                               contract, current_and_next_dates):
    # This comment indicates the function's purpose.
    ''' Function to download the historical data and create the resampled historical data '''

    # Instantiate the main data download class, which will automatically trigger the connection and download sequence.
    # Run the download app
    app_for_download_data('127.0.0.1', 0, historical_data_address, train_span, contract, timezone, 
                          data_frequency, current_and_next_dates)
