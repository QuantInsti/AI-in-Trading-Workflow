"""
## Licensed under the QuantInsti Open License (QOL) v1.1 (the "License").
- Copyright 2025 QuantInsti Quantitative Learning Pvt. Ltd.
- You may not use this file except in compliance with the License.
- You may obtain a copy of the License in LICENSE.md at the repository root or at https://www.quantinsti.com.
- Non-Commercial use only; see the License for permitted use, attribution, and restrictions.
"""

# Import the necessary libraries
import pandas as pd
from ibkr_stock import trading_functions as tf

def create_trading_info_workbook(smtp_username, to_email, password):

    # Dataframe to save the open orders
    order_df = pd.DataFrame(columns=['PermId', 'ClientId', 'OrderId', \
                                     'Account', 'Symbol', 'SecType', 'Exchange', \
                                     'Action', 'OrderType', 'TotalQty', \
                                     'CashQty', 'LmtPrice', 'AuxPrice', \
                                     'Status', 'market_week_open_time', 'market_week_close_time'])  
          
    # Dataframe to save the orders' status
    orders_status = pd.DataFrame(columns=["OrderId", "Status", "Filled", \
                                         "PermId", "ClientId","Remaining", \
                                         "AvgFillPrice", "LastFillPrice", \
                                         'market_week_open_time', 'market_week_close_time'])        
    
    # Dataframe to save the executions 
    exec_df = pd.DataFrame(columns=["OrderId", "PermId", \
                                    "ExecutionId", "Symbol", "Side", \
                                    "Price", "AvPrice", "cumQty", "Currency", \
                                    "SecType", "Position", "Execution Time", \
                                    "Last Liquidity", "OrderRef", \
                                    'market_week_open_time', 'market_week_close_time'])        
    
    # Dataframe to save the commissions' report
    comm_df = pd.DataFrame(columns=['ExecutionId', 'Commission', 'Currency', 'Realized PnL', \
                                    'market_week_open_time', 'market_week_close_time'])        
    
    # Dataframe to save the equity time series     
    cash_balance = pd.DataFrame(columns=['value', 'leverage', 'signal', 'market_week_open_time', 'market_week_close_time'])
            
    # Dataframe to save the historical positions
    pos_df = pd.DataFrame(columns=['Account', 'Symbol', 'SecType', 'Currency', 'Position', 'Avg cost', \
                                   'market_week_open_time', 'market_week_close_time'])   
        
    # Dataframe to save the total number of seconds that takes to run the whole trading strategy per period
    app_time_spent = pd.DataFrame(columns=['seconds'], index=[0]) 
    # Setting the seconds value to zero
    app_time_spent.loc[0,'seconds'] = 0
    
    # Dataframe to save periods datetime and if they were traded
    periods_traded = pd.DataFrame(columns=['trade_time', 'trade_done', 'trader_start_datetime', 'trader_end_datetime', 'market_week_open_time', 'market_week_close_time']) 
    
    # Join all the dataframes into a dictionary   
    dictfiles = {'open_orders':order_df,\
                 'orders_status':orders_status,\
                 'executions':exec_df,\
                 'commissions':comm_df,\
                 'positions':pos_df,\
                 'cash_balance':cash_balance,\
                 'app_time_spent':app_time_spent,\
                 'periods_traded':periods_traded}
         
    # Save the dataframes into a single Excel workbook
    tf.save_xlsx(dict_df = dictfiles, path = 'data/database.xlsx')
    
    # Create the email information dataframe
    email_password = pd.DataFrame(columns=['smtp_username', 'to_email', 'password'], index=[0])
    # The email that will be used to send the emails
    email_password.loc[0, 'smtp_username'] = smtp_username
    # The email to which the trading info will be sent
    email_password.loc[0, 'to_email'] = to_email
    # The app password that was obtained in Google. You need to allow the app password in Google: https://support.google.com/mail/answer/185833?hl=en
    email_password.loc[0, 'password'] = password
    # Save the email dataframe
    email_password.to_excel('data/email_info.xlsx')
