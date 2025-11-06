"""
## Licensed under the Apache License, Version 2.0 (the "License"). 
- Copyright 2025 QuantInsti Quantitative Learnings Pvt Ltd. 
- You may not use this file except in compliance with the License. 
- You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 
- Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""

# Import necessary libraries
import datetime as dt
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from threading import Thread
import time
from ibapi.common import WshEventData

# Define a new client class that inherits the capabilities of both EClient and EWrapper.
class setup_to_get_contract_details(EClient, EWrapper):
    
    # The constructor for the class.
    def __init__(self):
        # Initialize the EClient part of the class, which sets up the connection mechanism.
        EClient.__init__(self, self)
        
    # This is an EWrapper callback function that is triggered when contract details are received from IBKR.
    def contractDetails(self, reqId, contractDetails):
        # Call the parent class's method to ensure proper behavior.
        super().contractDetails(reqId, contractDetails)
        # Print a status message to the console.
        print('Obtaining Contract details...')
        # Store the received contractDetails object in an instance variable 'self.details' for later access.
        self.details = contractDetails
        
    # This is an EWrapper callback that is triggered in response to a reqMatchingSymbols request.
    def symbolSamples(self, reqId, contractDescriptions):
        # Call the parent class's method.
        super().symbolSamples(reqId, contractDescriptions)
        # Store the received list of contract descriptions in 'self.descriptions'.
        self.descriptions = contractDescriptions
        
    # This EWrapper callback is triggered when all contract details for a request have been received.
    # Overriding the contractDetailsEnd method from EWrapper class.
    def contractDetailsEnd(self, reqId):
        # Print a confirmation message to the console.
        print('Contract Details Ended.')

# -------------------------x-----------------------x---------------------------

# This function orchestrates the process of fetching and parsing contract details for a given stock.
def get_tradable_dates_and_stock_currency(host,port,client_id,symbol,primary_exchange, smart_bool):
    
    # Create an instance of the specialized client class defined above.
    app = setup_to_get_contract_details()
    
    # Start a loop that continues until a successful connection to the IBKR server is made.
    while app.isConnected()==False:
        # Attempt to connect the client to the IB TWS or Gateway using the provided host, port, and client ID.
        app.connect(host=host, port=port, clientId=client_id)
        
        # Pause for 4 seconds to allow time for the connection to be established.
        time.sleep(4)
        
        # Start the client's message-processing loop in a separate background thread so the main script doesn't block.
        Thread(target=app.run, daemon=True).start()
        
        # Check if the connection was successful.
        if app.isConnected():
            # If connected, print a success message.
            print('Setup to get the tradable dates has reached connection to the IB server...')
            # Break the 'while' loop since the connection is established.
            break
        else:
            # If not connected, print an error message prompting the user to check their setup.
            print("Setup to get the tradable dates couldn't connect to the IB server, please verify the host, port are well written or the TWS or Gateway are opened...")
    
    
    # Send a request to find all contracts that match the given stock symbol.
    # Request contract details - EClient
    app.reqMatchingSymbols(0, symbol)

    # Pause for 1 second to allow the server time to respond with symbol samples.
    time.sleep(1)
        
    # Iterate through the list of contract descriptions received from the server.
    for info in app.descriptions:
        # Check if the contract description matches the exact symbol, security type (STK for stock), and primary exchange.
        if (info.contract.symbol==symbol) and (info.contract.secType=='STK') and \
            (info.contract.primaryExchange==primary_exchange):
            # If a match is found, send a new request for the full details of this specific contract.
            # Request contract details - EClient
            app.reqContractDetails(reqId=1, contract=info.contract)
            # Pause for 1 second to allow the server time to respond with the full contract details.
            time.sleep(1)
            
            # Break the loop since the correct contract has been found and its details requested.
            break
      
    # Pause for another second to ensure all data has been received by the callback functions.
    time.sleep(1)
    
    # Retrieve the detailed contract information that was stored by the 'contractDetails' callback.
    results = app.details
    # Get the 'liquidHours' string from the results, which contains the trading schedule, and split it by semicolon.
    liquidHours = results.liquidHours.split(";")
    
    # Disconnect the client from the IBKR server as the required information has been obtained.
    app.disconnect()
    
    # Print a confirmation that the client has disconnected.
    print('Setup to get the tradable dates has been disconnected from the IB server...')
    
    # Initialize an empty dictionary to store the parsed trading dates.
    dates_dict = {}
    # Loop through each component of the liquid hours string.
    for i in range(len(liquidHours)):
        # Check if the session is not marked as 'CLOSED'.
        if 'CLOSED' not in liquidHours[i]:
            # If it's an open session, create a nested dictionary for it.
            dates_dict[f'dates_{i}'] = {}
            # Parse and store the session's start time, converting it to a datetime object.
            dates_dict[f'dates_{i}']['start_date'] = dt.datetime.strptime(liquidHours[i].split('-')[0], "%Y%m%d:%H%M")
            # Parse and store the session's end time, converting it to a datetime object.
            dates_dict[f'dates_{i}']['end_date'] = dt.datetime.strptime(liquidHours[i].split('-')[1], "%Y%m%d:%H%M")
        else:
            # If the session is closed, store the date of the closure.
            dates_dict[f'dates_{i}'] = dt.datetime.strptime(liquidHours[i].split(':')[0], "%Y%m%d").date()
    
    # Check the user's setting for using IBKR's SMART routing.
    if smart_bool:
        # If true, set the contract's exchange to 'SMART'.
        info.contract.exchange = 'SMART'
    else:
        # Otherwise, use the asset's primary exchange.
        info.contract.exchange = info.contract.primaryExchange
    
    # Return the parsed dictionary of tradable dates, the fully defined contract object, and the stock's exchange timezone ID.
    return dates_dict, info.contract, results.timeZoneId
