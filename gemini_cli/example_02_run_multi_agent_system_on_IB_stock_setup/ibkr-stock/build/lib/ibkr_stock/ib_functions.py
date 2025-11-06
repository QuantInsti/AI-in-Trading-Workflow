"""
## Licensed under the QuantInsti Open License (QOL) v1.1 (the "License").
- Copyright 2025 QuantInsti Quantitative Learning Pvt. Ltd.
- You may not use this file except in compliance with the License.
- You may obtain a copy of the License in LICENSE.md at the repository root or at https://www.quantinsti.com.
- Non-Commercial use only; see the License for permitted use, attribution, and restrictions.
"""

# Import the necessary libraries
from ibapi.order import Order
from ibapi.client import Contract
from ibapi.execution import ExecutionFilter

def marketOrder(direction,quantity):
    ''' Function to set the market order object'''
    # Set the variable as an Order object
    order = Order()
    # Set the direction of the market order: Buy or Sell
    order.action = direction
    # Set the order as a market one
    order.orderType = "MKT"
    # Set the quantity
    order.totalQuantity = quantity
    # Transmit the order
    order.transmit = True
    # Trade with electronic quotes
    order.eTradeOnly = 0
    # Trade with firm quotes
    order.firmQuoteOnly = 0        
    return order

def stopOrder(direction, quantity, st_price, trail=False, trailing_amount=None):
    ''' 
    Function to set the stop loss or trailing stop loss order object.
    
    :param direction: "SELL" or "BUY"
    :param quantity: The number of shares.
    :param st_price: The trigger price for a standard stop, or the *initial* trigger price for a trailing stop.
    :param trail: Boolean. Set to True to create a trailing stop.
    :param trailing_amount: The offset amount for the trail (e.g., 0.50 for $0.50). Required if trail is True.
    '''
    # Set the variable as an Order object
    order = Order()
    # Set the direction of the order
    order.action = direction
    # Set the quantity
    order.totalQuantity = quantity
    # Transmit the order
    order.transmit = True

    if trail == False:
        # --- This creates a standard, fixed Stop Loss order ---
        order.orderType = "STP"
        # The trigger price for the stop loss
        order.auxPrice = st_price
        
    elif trail == True:
        # --- This creates a Trailing Stop Loss order ---
        order.orderType = "TRAIL"
        
        # This is the trailing offset amount in dollars.
        # It's the "cushion" or distance the stop will follow the price.
        order.auxPrice = trailing_amount
        
        # This is the initial price that the trail will start from.
        # The stop is active immediately at this price.
        order.trailStopPrice = st_price
        
    return order

def tpOrder(direction,quantity,tp_price):
    ''' Function to set the take profit order object'''
    # Set the variable as an Order object
    order = Order()
    # Set the direction of the take profit order: Buy or Sell
    order.action = direction
    # Set the order as a limit order
    order.orderType = "LMT"
    # Set the quantity
    order.totalQuantity = quantity
    # Transmit the order
    order.transmit = True
    # Set the take profit breach price
    order.lmtPrice = tp_price
    # Trade with electronic quotes
    order.eTradeOnly = 0
    # Trade with firm quotes
    order.firmQuoteOnly = 0        
    return order

def executionFilter(time_):
    ''' Function to set the executions filter object'''
    # Set the executions filter
    execFilter = ExecutionFilter()
    # Set the time to be used to request the executions data based on the filter
    execFilter.time = time_
    return execFilter
