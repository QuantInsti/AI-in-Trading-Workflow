"""
## Licensed under the QuantInsti Open License (QOL) v1.1 (the "License").
- Copyright 2025 QuantInsti Quantitative Learning Pvt. Ltd.
- You may not use this file except in compliance with the License.
- You may obtain a copy of the License in LICENSE.md at the repository root or at https://www.quantinsti.com.
- Non-Commercial use only; see the License for permitted use, attribution, and restrictions.
"""

# Import the necessary libraries
import os
import ast
import sys
import math
import pytz
import inspect
import numpy as np
import pandas as pd
import importlib.util
import datetime as dt
from datetime import datetime
from lightgbm import LGBMClassifier
from shaphypetune import BoostBoruta

def dropLabels(events,minPct=.05):
    """
    Removes under-represented classes from the target variable to address class imbalance.

    Iteratively drops the least frequent class in the 'y' column until:
    1. All remaining classes meet the minimum percentage threshold (minPct), OR
    2. Only two classes remain

    Args:
        events (pd.DataFrame): Input dataframe containing the 'y' target column
        minPct (float, optional): Minimum acceptable percentage for any class (0.05 = 5%)

    Returns:
        pd.DataFrame: Filtered dataframe with balanced classes in 'y' column

    Notes:
        - Operates on a copy of the input dataframe to avoid modifying original data
        - Preserves row indices after filtering
        - Particularly useful for ML models sensitive to class imbalance
        - Final classes will always have ≥ minPct representation or be reduced to 2 classes

    Example:
        If 'y' has classes distributed as [70%, 25%, 5%] with minPct=0.05:
        - First iteration: drops 5% class
        - Result: [73.7%, 26.3%] distribution
    """
    ''' Function to drop the lowest-percentage prediction feature class'''

    # apply weights, drop labels with insufficient examples
    while True:
        # Count the total number of observations per each prediction feature class
        df0=events['y'].value_counts(normalize=True)
        # If the class with the minimum number of observations or if there is only 2 prediction feature labels, then finish the loop
        if (df0.min()>minPct) or (df0.shape[0]<3):break
        # Drop the prediction feature label which has the lowest number of observations
        events = events[events['y']!=df0.index[df0.argmin()]]
    return events

def directional_change_events(data, theta=0.004, columns=None):
    """
    Generates Directional Change (DC) indicators as defined by Chen and Tsang (2021).

    Implements event-driven market regime detection using price thresholds to identify:
    - Peak/trough points
    - Trend magnitude (TMV)
    - Trend duration (T)
    - Time-adjusted returns (R)

    Args:
        data (pd.DataFrame): OHLC price data with 'Close' column
        theta (float, optional): Threshold percentage for DC detection (0.004 = 0.4%)
        columns (list, optional): Subset of columns to return. None returns full dataframe

    Returns:
        pd.DataFrame: Original dataframe augmented with DC indicators:
            - Event: -1 (peak), 1 (trough), 0 (no event)
            - peak_trough_prices: Last detected peak/trough price
            - count: Bars since last DC event
            - TMV: Trend Magnitude Value (price change / (theta * previous peak/trough))
            - T: Time periods between events
            - R: Log-scaled time-adjusted returns

    Notes:
        - Initializes with upward trend assumption from first Close price
        - Events trigger when prices cross theta thresholds from last extremum
        - Forward-fills non-event periods for continuous regime tracking
        - Replaces infinite values with NaNs for robustness
        - Maintains temporal alignment through pandas index
    """
    
    # Copy the dataframe
    data = data.copy()

    # Create the necessary columns and variables
    data["Event"] = 0.0

    # Set the initial event variable value
    event = "upward" # initial event

    # Set the initial value for low and high prices
    ph = data['Close'].iloc[0] # highest price
    pl = data['Close'].iloc[0] # lowest price

    # Create loop to run through each date
    for t in range(0, len(data.index)):
        # Check if we're on a downward trend
        if event == "downward":
            # Check if the close price is higher than the low price by the theta threshold
            if data["Close"].iloc[t] >= pl * (1 + theta):
                # Set the event variable to upward
                event = "upward"
                # Set the high price as the current close price                
                ph = data["Close"].iloc[t]
            # If the close price is lower than the low price by the theta threshold
            else:
                # Check if the close price is less than the low price
                if data["Close"].iloc[t] < pl:
                    # Set the low price as the current close price
                    pl = data["Close"].iloc[t]
                    # Set the Event to upward for the current period
                    data["Event"].iloc[t] = 1
        # Check if we're on an upward trend
        elif event == "upward":
            # Check if the close price is less than the high price by the theta threshold
            if data["Close"].iloc[t] <= ph * (1 - theta):  
                # Set the event variable to downward
                event = "downward"
                # Set the low price as the current close price
                pl = data["Close"].iloc[t]
            # If the close price is higher than the high price by the theta threshold
            else:
                # Check if the close price is higher than the high price
                if data["Close"].iloc[t] > ph:
                    # Set the high price as the current close price
                    ph = data["Close"].iloc[t]
                    # Set the Event to downward for the current period
                    data["Event"].iloc[t] = -1

    # Set the peak and trough prices and forward-fill the column
    data['peak_trough_prices'] = np.where(data['Event']!=0, data['Close'],0)
    data['peak_trough_prices'].replace(to_replace=0, method='ffill', inplace=True)

    # Count the number of periods between a peak and a trough
    data['count'] = 0
    for i in range(1,len(data.index)):
        if data['Event'].iloc[(i-1)]!=0:
            data['count'].iloc[i] = 1+data['count'].iloc[(i-1)]
        else:
            data['count'].iloc[i] = 1

    # Compute the TMV indicator
    data['TMV'] = np.where(data['Event']!=0, abs(data['peak_trough_prices']-data['peak_trough_prices'].shift())/\
                          (data['peak_trough_prices'].shift()*theta),0)

    # Compute the time-completion-for-a-trend indicator
    data['T'] = np.where(data['Event']!=0, data['count'],0)

    # Compute the time-adjusted-return indicator and forward-fill it
    data['R'] = np.where(data['Event']!=0, np.log(data['TMV']/data['T']*theta),0)
    data['R'] = data['R'].replace(to_replace=0, method='ffill')

    # Drop NaN or infinite values
    data.replace([np.inf, -np.inf], np.nan, inplace=True)
    
    if columns is None:
        return data
    else:
        return data[columns]

def library_boruta_shap(X, y, seed, max_iter, date_loc):
    """
    Performs feature selection using Boruta-Shap algorithm with LightGBM integration.

    Args:
        X (pd.DataFrame): Feature matrix with datetime index
        y (pd.Series): Target variable series
        seed (int): Random seed for reproducibility
        max_iter (int): Maximum Boruta iterations for feature confirmation
        date_loc (datetime): Split point for train/validation sets

    Returns:
        list: Selected feature names passing Boruta-Shap criteria. Returns all features if:
            - No features selected
            - Algorithm fails (handles exceptions)

    Notes:
        - Uses LightGBM classifier with fixed hyperparameter grid:
            * learning_rate: [0.2, 0.1]
            * num_leaves: [25]
            * max_depth: [12]
        - Implements BoostBoruta wrapper for SHAP-based feature importance
        - Validation set uses post-date_loc data for early stopping
        - Fallback mechanism returns original features on error
        - Parallel processing enabled (n_jobs=-2)
        - Early stopping after 6 non-improving Boruta rounds
    """

    X_train, X_test = X.loc[:date_loc,:], X.loc[date_loc:,:]
    y_train, y_test = y.loc[:date_loc, 'y'].values.reshape(-1,), y.loc[date_loc:, 'y'].values.reshape(-1,)
    
    # Parameters' range of values
    param_grid = {
                    'learning_rate': [0.2, 0.1],
                    'num_leaves': [25],#, 35],
                    'max_depth': [12]
                }

    clf_lgbm = LGBMClassifier(n_estimators=20, random_state=seed, n_jobs=-2)
    
    ### HYPERPARAM TUNING WITH GRID-SEARCH + BORUTA SHAP ###
    try:
        model = BoostBoruta(clf_lgbm, param_grid=param_grid, max_iter=max_iter, perc=100,
                            importance_type='shap_importances', train_importance=False, sampling_seed=seed, n_jobs=-2, early_stopping_boruta_rounds=6, verbose=0)
        
        model.fit(X_train, y_train, eval_set=[(X_test, y_test)])
        
        best_features = model.support_.tolist()
        
        if len(best_features)!=0:
            return best_features
        else:
            return X.columns.tolist()
    except:
        best_features = X.columns.tolist()
        return best_features

def create_Xy(indf, feature_cols, y_target_col): 
    """
    Splits a dataframe into feature matrix (X) and target variable (y) for machine learning.

    Args:
        indf (pd.DataFrame): Source dataframe containing both features and target
        feature_cols (list): Column names to use as input features
        y_target_col (str): Column name containing target variable to predict

    Returns:
        tuple: Contains two elements:
            - X (pd.DataFrame): Feature matrix with selected columns
            - y (pd.DataFrame): Target variable as single-column dataframe

    Notes:
        - Maintains index alignment between X and y
        - Converts y to DataFrame for sklearn compatibility
        - Does not validate column existence - ensure columns exist in indf
        - Preserves original dataframe ordering
    """
    """ Function to create the input and prediction features dataframes """
    # Create the input features and prediction features dataframes
    X, y = indf[feature_cols], indf[y_target_col].to_frame()
    return X, y

def roll_zscore(x, window):
    """ Function to create the rolling zscore versions of an array """
    # Create the rolling object
    r = x.rolling(window=window)
    # Set the rolling mean
    m = r.mean().shift(1)
    # Set the rolling standard deviation
    s = r.std().shift(1)
    # Compute the zscore values
    z = (x - m) / s
    return z

def rolling_zscore_function(data, scalable_features, window):
    """
    Applies rolling z-score normalization to specified features while preserving non-scalable columns.

    Processes input features by:
    1. Calculating rolling z-scores over a defined window period
    2. Handling infinite/nan values from initial window calculations
    3. Maintaining original feature values when insufficient historical data exists
    4. Merging scaled features with non-scaled columns

    Args:
        data (pd.DataFrame): Input dataframe containing features to scale
        scalable_features (list): Column names to apply rolling z-score normalization
        window (int): Lookback window for z-score calculation (μ and σ)

    Returns:
        tuple: Contains two elements:
            - pd.DataFrame: Processed dataframe with scaled/non-scaled features
            - list: Names of successfully scaled features

    Notes:
        - Features with >window NaN values after scaling retain original values
        - Infinite values are converted to NaN before processing
        - Final output drops all rows with NaN values
        - Preserves non-scalable features from original data
        - Requires `roll_zscore` utility function (assumes standard implementation)

    Example:
        scaled_df, scaled_cols = rolling_zscore_function(df, ['volatility', 'volume'], 30)
        # Result will have z-scores for features with sufficient history, original values otherwise
    """
    """ Function to create the rolling zscore versions of the feature inputs """

    # Create a scaled X dataframe based on the data index
    X_scaled_final = pd.DataFrame(index=data.index)
    # Create the scaled X data 
    X_scaled = roll_zscore(data[scalable_features], window=window)
    # Replace the infinite values with NaN values
    X_scaled.replace([np.inf, -np.inf], np.nan, inplace=True)
        
    # Create a scaled features list
    scaled_features = list()
    
    # Loop through the scaled X data columns
    for feature in X_scaled.columns:
        # If the number of NaN values is higher than the max window used to compute the technical indicators
        if np.isnan(X_scaled[feature]).sum()>window:
            # Save in the scaled X data the same non-scaled feature column
            X_scaled_final[feature] = data[feature].copy()
        # If the number of NaN values is lower than the max window used to compute the technical indicators
        else:
            # Save the scaled column in the final dataframe
            X_scaled_final[feature] = X_scaled[feature].copy()
            # Save the scaled X column name in the list
            scaled_features.append(feature)
            
    # Concatenate the rest of the columns not used in the X_scaled dataframe
    X_scaled_final = pd.concat([X_scaled_final, data[data.columns.difference(scalable_features)]], axis=1)
            
    # Drop the NaN values
    X_scaled_final.dropna(inplace=True)
    
    return X_scaled_final, scaled_features

def train_test_split(X, y, split, purged_window_size, embargo_period):
    """
    Splits time-series data into training/test sets with purging and embargo periods to prevent look-ahead bias.

    Args:
        X (pd.DataFrame): Feature matrix
        y (pd.Series/pd.DataFrame): Target variable
        split (int): Number of observations for test set (last `split` records)
        purged_window_size (int): Number of initial training observations to exclude (prevows model contamination)
        embargo_period (int): Number of final training observations to exclude (post-split buffer)

    Returns:
        tuple: Contains four elements:
            - X_train: Purged/embargoed training features
            - X_test: Test features (last `split` obs)
            - y_train: Purged/embargoed training targets
            - y_test: Test targets

    Notes:
        - Maintains temporal order - test set always uses most recent data
        - Preserves pandas index alignment
        - Purge window removes early potentially unreliable data
        - Embargo creates buffer between train/test to avoid leakage
        - Designed for financial time series where sequence matters
    """

    # If the split variable is an integer
    if isinstance(split, int):
        # Get the train data
        X_train, y_train = X.iloc[:-split], y.iloc[:-split]
        # Get the test data
        X_test, y_test = pd.DataFrame(X.iloc[-split:], index=X.index[-split:]), pd.DataFrame(y.iloc[-split:], index=y.index[-split:])
        
    # The purged start iloc value
    purged_start = max(0, len(y) - (len(y) - purged_window_size))
    # The embargo start iloc value
    embargo_start = max(0, len(y) - embargo_period)
       
    # Defining once again the X train data based on the purged window and embargo period
    X_train = X_train.iloc[purged_start:embargo_start]
    # Defining once again the y train data based on the purged window and embargo period
    y_train = y_train.iloc[purged_start:embargo_start]
    
    return X_train, X_test, y_train, y_test

def define_trading_week(local_timezone, local_trading_start_hour, local_day_start_minute, local_trading_end_hour, local_day_end_minute):
    """
    Calculates the start and end of a trading week that runs from Monday to Friday.

    - If called during the trading week, it returns the current week's boundaries.
    - If called during the weekend or outside market hours, it returns the next week's boundaries.
    """
    
    # Use a consistent anchor timezone for all logic to prevent errors from time shifts.
    anchor_tz = pytz.timezone('America/Bogota')
    
    # Get the current time in the anchor timezone for standardized calculations.
    now_in_anchor_tz = dt.datetime.now(pytz.utc).astimezone(anchor_tz)
    
    # Define the trading start and end times.
    trading_start_time = dt.time(local_trading_start_hour, local_day_start_minute)
    trading_end_time = dt.time(local_trading_end_hour, local_day_end_minute)

    # --- Determine if the current time is outside the Mon-Fri trading window ---
    # In Python's weekday(), Monday is 0, Tuesday is 1, ..., Sunday is 6.
    weekday = now_in_anchor_tz.weekday()
    current_time = now_in_anchor_tz.time()
    
    # The time is "outside" the trading week if it is:
    #   1. Before the market opens on Monday.
    #   2. After the market closes on Friday.
    #   3. Any time on Saturday or Sunday.
    is_before_monday_open = (weekday == 0 and current_time < trading_start_time)
    is_after_friday_close = (weekday == 4 and current_time >= trading_end_time)
    is_saturday_or_sunday = weekday in [5, 6] # 5 is Saturday, 6 is Sunday
    
    is_outside_trading_week = is_before_monday_open or is_after_friday_close or is_saturday_or_sunday
    
    # --- Calculate the start and end dates of the relevant trading week ---
    if is_outside_trading_week:
        # If we are outside the trading window, calculate the NEXT week's start date.
        # We find the date of the upcoming Monday.
        days_until_monday = (7 - weekday) % 7
        start_date = (now_in_anchor_tz + dt.timedelta(days=days_until_monday)).date()
        
    else:
        # If we are inside the trading window, find the CURRENT week's start date.
        # This is the date of the most recent Monday.
        days_since_monday = weekday
        start_date = (now_in_anchor_tz - dt.timedelta(days=days_since_monday)).date()
        
    # The end date of the week is always 4 days after the start date (Monday -> Friday).
    end_date = start_date + dt.timedelta(days=4)

    # --- Create the final start and end datetimes ---
    # First, combine the calculated dates with the trading times in the anchor timezone.
    week_start_anchor = anchor_tz.localize(dt.datetime.combine(start_date, trading_start_time))
    week_end_anchor = anchor_tz.localize(dt.datetime.combine(end_date, trading_end_time))
    
    # Then, convert these back to the user's local timezone and make them naive, as requested.
    local_tz = pytz.timezone(local_timezone)
    week_start_local = week_start_anchor.astimezone(local_tz).replace(tzinfo=None)
    week_end_local = week_end_anchor.astimezone(local_tz).replace(tzinfo=None)
    
    return week_start_local, week_end_local

def save_xlsx(dict_df, path):
    """
    Function to save a dictionary of dataframes to an Excel file, with each dataframe as a separate sheet
    """
    writer = pd.ExcelWriter(path)
    for key in dict_df:
        dict_df[key].to_excel(writer, key)
    writer.close()

def get_end_hours(timezone, london_start_hour, local_restart_hour):
    """ Function to get the end hours based on the Eastern timezone """
    
    # Set the easter timezone string
    est = 'US/Eastern'
    # Get today's datetime
    today_datetime = dt.datetime.now()
    # Set the eastern-timezone-based today's datetime
    eastern = today_datetime.astimezone(pytz.timezone(est))
    # Get the timezone difference hour and minute
    eastern_timestamp = eastern.strftime("%z")
    # Get the eastern timezone difference sign boolean
    eastern_negative_sign_bool = eastern_timestamp.startswith("-")
    # Set the eastern timezone difference sign number
    eastern_sign = -1 if eastern_negative_sign_bool else +1
    
    # Set the trader's timezone now datetime
    trader_datetime = today_datetime.astimezone(pytz.timezone(timezone))
    # Get the timezone difference hour and minute
    trader_datetime_timestamp = trader_datetime.strftime("%z")
    # Get the trader's timezone difference sign boolean
    trader_datetime_negative_sign_bool = trader_datetime_timestamp.startswith("-")
    # Set the trader's timezone difference sign number
    trader_datetime_sign = -1 if trader_datetime_negative_sign_bool else +1
    # Get the number of minutes of the difference between both datetimes
    minutes = int(str(abs(trader_datetime.replace(tzinfo=None) - eastern.replace(tzinfo=None)))[2:4])
    
    # If the trader's timezone sign is different from Eastern's
    if trader_datetime_sign != eastern_sign:
        # Set the restart hour
        restart_hour = local_restart_hour + int(eastern_timestamp[1:3])+int(trader_datetime_timestamp[1:3])
        restart_hour = restart_hour if restart_hour<=23 else restart_hour - 24
        
        # Set the day-end hour
        day_end_hour = 17 + int(eastern_timestamp[1:3])+int(trader_datetime_timestamp[1:3])
        day_end_hour = day_end_hour if day_end_hour<=23 else day_end_hour - 24
        
        # Set the restart minute
        restart_minute = day_end_minute = minutes
    # If the trader's timezone sign is equal to Eastern's
    else:
        # Set the restart hour
        restart_hour = local_restart_hour + int(eastern_timestamp[1:3])-int(trader_datetime_timestamp[1:3])
        restart_hour = restart_hour if restart_hour<=23 else restart_hour - 24
        
        # Set the day-end hour
        day_end_hour = 17 + int(eastern_timestamp[1:3])-int(trader_datetime_timestamp[1:3])
        day_end_hour = day_end_hour if day_end_hour<=23 else day_end_hour - 24
        
        # Set the restart minute
        restart_minute = day_end_minute = minutes
      
    # Set the trading start hour
    trading_start_hour = london_start_hour + trader_datetime_sign*int(trader_datetime_timestamp[1:3])
    trading_start_hour = trading_start_hour if trading_start_hour<=23 else (trading_start_hour - 24)
                    
    return restart_hour, restart_minute, day_end_hour, day_end_minute, trading_start_hour


def convert_stock_datetimes_to_local(trader_timezone, stock_timezone, stock_start_datetime, stock_end_datetime):
    
    # Define the source timezone
    stock_timezone = pytz.timezone(stock_timezone)

    # Define the target timezone
    trader_timezone = pytz.timezone(trader_timezone)

    # Make the start datetime timezone-aware using localize()
    stock_start_datetime = stock_timezone.localize(stock_start_datetime)

    # Convert the timezone-aware start datetime to the target timezone
    trader_start_datetime = stock_start_datetime.astimezone(trader_timezone).replace(tzinfo=None)

    # Make the end datetime timezone-aware using localize()
    stock_end_datetime = stock_timezone.localize(stock_end_datetime)

    # Convert the timezone-aware end datetime to the target timezone
    trader_end_datetime = stock_end_datetime.astimezone(trader_timezone).replace(tzinfo=None)

    return trader_start_datetime, trader_end_datetime
    
def get_data_frequency_values(data_frequency):
    """
    Parses frequency specification string into numerical and categorical components.

    Args:
        data_frequency (str): Frequency string in 'Xmin' or 'Yh' format
            Examples: '15min', '4h'

    Returns:
        tuple: Contains two elements:
            - frequency_number (int): Numerical value of frequency
            - frequency_string (str): Unit identifier ('min' or 'h')

    Notes:
        - Designed to support minute/hour frequencies only
        - Input format must contain either 'min' or 'h' substring
        - Used internally for period/day calculations in `get_periods_per_day`
        - Does not validate input format - assumes proper construction
    """
    
    # If the data frequency is in minutes
    if 'min' in data_frequency:
        # Set the frequency number
        frequency_number = int(data_frequency[:data_frequency.find("min")])
        # Set the frequency string
        frequency_string = data_frequency[data_frequency.find("min"):]
    # If the data frequency is in hours
    elif 'h' in data_frequency:
        # Set the frequency number
        frequency_number = int(data_frequency[:data_frequency.find("h")])
        # Set the frequency string
        frequency_string = data_frequency[data_frequency.find("h"):]
    # If the data frequency is daily
    elif 'D' in data_frequency:
        # Set the frequency number
        frequency_number = 1
        # Set the frequency string
        frequency_string = 'D'
        
    return frequency_number, frequency_string

def get_periods_per_day(data_frequency):
    """
    Calculates the number of data periods per trading day based on the specified frequency.

    Args:
        data_frequency (str): Frequency specification (e.g., '15min', '1h') 

    Returns:
        int: Number of periods in a 24-hour trading day

    Notes:
        - Requires `get_data_frequency_values` helper to parse frequency components
        - Supports minute ('min') and hour ('h') frequencies only
        - Assumes 24-hour trading calendar (no market closure periods)
        - Example: '15min' → 96 periods/day, '4h' → 6 periods/day
    """
    
    # Get the data frequency number and string
    frequency_number, frequency_string = get_data_frequency_values(data_frequency)
    
    # If the data frequency is in minutes
    if frequency_string == 'min':
        # Return the periods per day
        return 24*(60//frequency_number)
    # If the data frequency is in hours
    elif frequency_string == 'h':
        # Return the periods per day
        return 24//frequency_number
    # If the data frequency is in days
    elif frequency_string == 'D':
        # Return the periods per day
        return 1

# Function to calculate critical daily time points, including trading cutoffs and scheduled restarts.
def get_restart_and_day_close_datetimes(trading_type, data_frequency, restart_hour, restart_minute, 
                                        trader_start_datetime, trader_end_datetime,  trader_next_start_datetime, trader_next_end_datetime,
                                        time_after_open, time_before_close):
    # This comment indicates the function's purpose.
    """ Function to get the restart and day close datetimes """
    
    # Initialize a variable with the day's official closing time; this will be adjusted later.
    day_datetime_before_end = trader_end_datetime   
    
    # Check if the trading strategy is 'intraday'.
    if trading_type == 'intraday':
        # Initialize the variable for the last period before a restart to None.
        auto_restart_datetime_before_end = None
    
        # This condition checks if the scheduled restart hour falls within the liquid hours of a single trading day.
        if (restart_hour>trader_start_datetime.hour) and (restart_hour<trader_end_datetime.hour) and (trader_start_datetime.day==trader_end_datetime.day):
            # If so, define the exact datetime when the restart begins.
            auto_restart_end_datetime = dt.datetime(trader_start_datetime.year,trader_start_datetime.month,trader_start_datetime.day,restart_hour,restart_minute,0,0)
            # Define the time when trading can resume, typically 5 minutes after the restart begins.
            auto_restart_start_datetime = auto_restart_end_datetime + dt.timedelta(minutes=5)
        # This condition handles trading sessions that span across midnight.
        elif ((restart_hour+24)>trader_start_datetime.hour) and (restart_hour<trader_end_datetime.hour) and (trader_start_datetime.day!=trader_end_datetime.day):
            # Define the exact datetime for the restart.
            auto_restart_end_datetime = dt.datetime(trader_start_datetime.year,trader_start_datetime.month,trader_start_datetime.day,restart_hour,restart_minute,0,0)
            # Define the time when trading can resume.
            auto_restart_start_datetime = auto_restart_end_datetime + dt.timedelta(minutes=5)
        else:
            # If the restart time is outside trading hours, set the restart datetimes to None.
            auto_restart_end_datetime = None
            auto_restart_start_datetime = None
        
        # Check if the data frequency is in minutes.
        if 'min' in data_frequency:
            # Extract the number of minutes from the frequency string.
            frequency_number = int(data_frequency[:data_frequency.find("min")])
                    
            # Initialize a list of trading periods for the day, starting with the official open time.
            frequency_periods = [trader_start_datetime]
            
            # If a restart is scheduled during trading hours.
            if auto_restart_end_datetime is not None:
        
                # Generate a list of all trading periods for the entire day.
                i = 0
                while frequency_periods[i] <= trader_end_datetime:
                    # Add the next period by incrementing with the frequency timedelta.
                    frequency_periods.append(frequency_periods[i] + dt.timedelta(minutes=frequency_number))
                    # Move to the next index.
                    i += 1
    
                # Find the last trading period that occurs just before the scheduled restart.
                for i in range(len(frequency_periods)):
                    # Check if a period matches the restart time exactly.
                    if frequency_periods[i] == auto_restart_end_datetime:
                        # Set the last tradable period to 5 minutes before the restart.
                        auto_restart_datetime_before_end = auto_restart_end_datetime - dt.timedelta(minutes=5)
                        # Exit the loop.
                        break
                    # Check if the current period has passed the restart time.
                    elif frequency_periods[i] > auto_restart_end_datetime:
                        # If so, the previous period was the last one before the restart.
                        auto_restart_datetime_before_end = frequency_periods[i-1]
                        # Exit the loop.
                        break
                    
                # This loop is redundant but re-calculates the same value. Kept as per instructions.
                for i in range(len(frequency_periods)):
                    if frequency_periods[i] == auto_restart_end_datetime:
                        auto_restart_datetime_before_end = auto_restart_end_datetime - dt.timedelta(minutes=5)
                        break
                    elif frequency_periods[i] > auto_restart_end_datetime:
                        auto_restart_datetime_before_end = frequency_periods[i-1]
                        break
    
            else:
                # If no restart is scheduled, just generate the list of periods for the day.
                i = 0
                while frequency_periods[i] <= day_datetime_before_end:
                    frequency_periods.append(frequency_periods[i] + dt.timedelta(minutes=frequency_number))
                    i += 1
     
        # Check if the data frequency is in hours.
        elif 'h' in data_frequency:
            # Extract the number of hours from the frequency string.
            frequency_number = int(data_frequency[:data_frequency.find("h")])
                    
            # Initialize a list of trading periods.
            frequency_periods = [trader_start_datetime]
            
            # If a restart is scheduled.
            if auto_restart_end_datetime is not None:
        
                # Generate the list of all trading periods for the day.
                i = 0
                while frequency_periods[i] <= trader_end_datetime:
                    frequency_periods.append(frequency_periods[i] + dt.timedelta(hours=frequency_number))
                    i += 1
    
                # Find the last trading period before the restart.
                for i in range(len(frequency_periods)):
                    if frequency_periods[i] == auto_restart_end_datetime:
                        auto_restart_datetime_before_end = auto_restart_end_datetime - dt.timedelta(minutes=5)
                        break
                    elif frequency_periods[i] > auto_restart_end_datetime:
                        auto_restart_datetime_before_end = frequency_periods[i-1]
                        break
                    
                # Find the first trading period after the restart window has passed.
                for i in range(len(frequency_periods)):
                    if frequency_periods[i] >= auto_restart_end_datetime:
                        # Check if this period is also after the 5-minute resume time.
                        if (frequency_periods[i] >= auto_restart_end_datetime + dt.timedelta(minutes=5)):
                            # If so, this is the first safe period to resume trading.
                            auto_restart_start_datetime = frequency_periods[i]  
                            # Exit the loop.
                            break
        
                # This loop is redundant but re-generates the same period list. Kept as per instructions.
                i = 0
                while frequency_periods[i] <= day_datetime_before_end:
                    frequency_periods.append(frequency_periods[i] + dt.timedelta(hours=frequency_number))
                    i += 1
        
            else:
                # If no restart, just generate the list of periods.
                i = 0
                while frequency_periods[i] <= day_datetime_before_end:
                    frequency_periods.append(frequency_periods[i] + dt.timedelta(hours=frequency_number))
                    i += 1
                    
    # Check if the trading type is 'open_to_close' or daily.
    elif (trading_type == 'open_to_close') or (data_frequency == '1D'):
        # Initialize the pre-restart end time to None.
        auto_restart_datetime_before_end = None
        # Check if the trading session is within a single day.
        if (trader_start_datetime.day==trader_end_datetime.day):
            # Check if the restart falls within the session.
            if (restart_hour>trader_start_datetime.hour) and (restart_hour<trader_end_datetime.hour):
                # Define the restart and resume times.
                auto_restart_end_datetime = dt.datetime(trader_start_datetime.year,trader_start_datetime.month,trader_start_datetime.day,restart_hour,restart_minute,0,0)
                auto_restart_start_datetime = auto_restart_end_datetime + dt.timedelta(minutes=5)
            else:
                # If restart is outside the session, set times to None.
                auto_restart_end_datetime = None
                auto_restart_start_datetime = None
        # This handles sessions spanning midnight.
        elif (trader_start_datetime.day<trader_end_datetime.day):
            # Check if restart is after the start time on the first day.
            if (restart_hour>trader_start_datetime.hour):
                auto_restart_end_datetime = dt.datetime(trader_start_datetime.year,trader_start_datetime.month,trader_start_datetime.day,restart_hour,restart_minute,0,0)
                auto_restart_start_datetime = auto_restart_end_datetime + dt.timedelta(minutes=5)
            # Check if restart is before the end time on the second day.
            elif (restart_hour<trader_end_datetime.hour):
                auto_restart_end_datetime = dt.datetime(trader_end_datetime.year,trader_end_datetime.month,trader_end_datetime.day,restart_hour,restart_minute,0,0)
                auto_restart_start_datetime = auto_restart_end_datetime + dt.timedelta(minutes=5)
            else:
                # Otherwise, no restart within the session.
                auto_restart_end_datetime = None
                auto_restart_start_datetime = None
                
    # For overnight strategies, restarts are not handled as they don't trade intraday.
    elif trading_type == 'close_to_open':
        # Set all restart-related datetimes to None.
        auto_restart_datetime_before_end = None
        auto_restart_end_datetime = None
        auto_restart_start_datetime = None
                        
        # Initialize the end-of-day cutoff time.
        day_datetime_before_end = trader_end_datetime   
    
    # Apply the user-defined buffer by subtracting minutes from the day's end time to get the final trading cutoff.
    day_datetime_before_end -= dt.timedelta(minutes=time_before_close)
                
    # Calculate the adjusted trading start time by adding the user-defined buffer to the official open time.
    trader_start_adj_datetime = trader_start_datetime + dt.timedelta(minutes=time_after_open)

    # Return all the calculated critical time points for the trading day.
    return trader_start_datetime, trader_start_adj_datetime, day_datetime_before_end,\
              auto_restart_start_datetime, auto_restart_datetime_before_end, \
                  auto_restart_end_datetime
                  
def get_frequency_change(data_frequency):
    """ Function to get data frequency timedelta """
    
    # If data frequency is in minutes
    if 'min' in data_frequency:
        # Define the data frequency timedelta
        time_change = dt.timedelta(minutes=int(data_frequency[:data_frequency.find("min")]))
    # If data frequency is in hours
    elif 'h' in data_frequency:
        # Define the data frequency timedelta
        time_change = dt.timedelta(hour=int(data_frequency[:data_frequency.find("h")])) 
    elif 'w' in data_frequency:
        # Define the data frequency timedelta
        time_change = dt.timedelta(days=int(7*data_frequency[:data_frequency.find("w")])) 

    return time_change

# Function to generate a list of all trading periods for the current day.
def get_todays_periods(now_, data_frequency, day_start_datetime, trader_start_adj_datetime, day_datetime_before_end, trading_day_end_datetime):
    # This comment explains the function's purpose.
    """ Function to get all the trading periods from the previous-day start datetime up to now 
        - We set the previous day two days ago in case we're close to the previous day"""
    
    # Initialize a list of periods, starting with the official beginning of the trading session.
    periods = [day_start_datetime]
    
    # Start a loop to generate the periods.
    i = 0
    while True:
       # Check if adding the next frequency interval will still be before the end-of-day cutoff.
       if (periods[i] + get_frequency_change(data_frequency)) <= day_datetime_before_end:
           # If so, calculate and append the next period to the list.
           periods.append(periods[i] + get_frequency_change(data_frequency))
       else:
           # If not, exit the loop.
           break
       # Increment the index for the next iteration.
       i += 1
       
    # Replace the first period (official open) with the adjusted start time (after the open buffer).
    periods[0] = trader_start_adj_datetime
    # Add the final end-of-day cutoff time as the last entry in the list.
    periods.append(trading_day_end_datetime)
    
    # The original comment here is slightly misleading; the code adds the end-of-day cutoff, not the "next period from now".
    # # Set the last period of the list as the next period from now
    # periods.append(trading_day_end_datetime)

    # Return the complete list of trading periods for the day.
    return periods

# Function to find the current, previous, and next trading periods relative to the current time.
def get_the_closest_periods(now_, trading_type, data_frequency, 
                            trader_start_adj_datetime, day_start_datetime, 
                            trading_day_end_datetime, day_datetime_before_end, 
                            trader_next_start_datetime, trader_next_end_datetime):
    # This comment explains the function's purpose.
    """ Function to get the closest trading periods to now """
    
    # Check if the trading strategy is 'intraday'.
    if trading_type == 'intraday':
        # Generate the list of all trading periods for the current day.
        periods = get_todays_periods(now_, data_frequency, day_start_datetime, trader_start_adj_datetime, day_datetime_before_end, trading_day_end_datetime)
        
        # Find the index of the current time slot by checking which two consecutive periods 'now_' falls between.
        index = [i for i in range(len(periods)-1) if ((now_ >= periods[i]) and (now_ < periods[i+1]))]

        # Check if the current time is in the very first time slot of the day.
        if index[0] == 0:
            # The previous period is the official day start.
            previous_period = day_start_datetime
            # The current period is the adjusted start time.
            current_period = trader_start_adj_datetime
            # The next period is the second period in the generated list.
            next_period = periods[index[0]+1]
        # Check if the current time is in the last trading slot before the final cleanup period.
        elif periods[index[0]] == day_datetime_before_end:
            # The previous period is the one before the last slot.
            previous_period = periods[(index[0]-1)]
            # The current period is the end-of-day trading cutoff time.
            current_period = day_datetime_before_end
            # The next period is the final cleanup/closing time.
            next_period = trading_day_end_datetime
        else:
            # For any other time slot during the day.
            # The previous period is the one at the preceding index.
            previous_period = periods[(index[0]-1)]
            # The current period is the one at the found index.
            current_period = periods[index[0]]
            # The next period is the one at the following index.
            next_period = periods[(index[0]+1)]

    # Check if the trading type is 'open_to_close' or 'close_to_open', which have simpler, non-intraday period logic.
    elif (trading_type == 'open_to_close') or (trading_type == 'close_to_open'):
        # Check if the current time is before the adjusted start of trading.
        if now_ < trader_start_adj_datetime:
            # The "current" period is considered the end of the previous day, and the next is the start of today.
            previous_period = day_start_datetime - dt.timedelta(days=1)
            current_period = trading_day_end_datetime - dt.timedelta(days=1)
            next_period = trader_start_adj_datetime
        # Check if the current time is during the main trading session.
        elif now_ < day_datetime_before_end:
            # The "current" period is the start of today, and the next is the end-of-day cutoff.
            previous_period = trading_day_end_datetime - dt.timedelta(days=1)
            current_period = trader_start_adj_datetime
            next_period = day_datetime_before_end
        # Check if the current time is in the end-of-day cleanup window.
        elif now_ < trading_day_end_datetime:
            # The "current" period is the end-of-day cutoff, and the next is the start of the next day.
            previous_period = trader_start_adj_datetime
            current_period = day_datetime_before_end
            next_period = trader_next_start_datetime
        # Check if the current time is after today's close but before the next day's start.
        elif now_ < trader_next_start_datetime:
            # The "current" period is the start of the next day, and the next is the end of the next day.
            previous_period = day_datetime_before_end
            current_period = trader_next_start_datetime
            next_period = trader_next_end_datetime

    # Return the calculated previous, current, and next periods.
    return previous_period, current_period, next_period

def allsaturdays(date0):
    """ Function to get all the Saturday dates from 2005 to date0 """
    # Create d to be looped
    d = date0
    # Get the next Saturday
    d += dt.timedelta(days = 5 - d.weekday())
    # Loop from d backwards up to 2005 (arbitrary year)
    while d.year >= 2005:
        # Return d
        yield d
        # Go backwards to the previous Saturday
        d -= dt.timedelta(days = 7)

def saturdays_list(date0): 
    """ Function to get all the Saturday datetimes from 2005 to date0 for the historical data download app"""
    # Get the Saturdays list
    saturdays = list(allsaturdays(date0))
    # Get half of the Saturdays list
    saturdays = saturdays[::2][:-1]
    # Convert the Saturdays to datetimes with 23:59:00 (arbitrarily chosen)
    saturdays = [datetime(date0.year, date0.month, date0.day, 23,59,0) for date0 in saturdays]
    # Convert the Saturdays datetimes to datetime type
    saturdays = [date0.strftime("%Y%m%d-%H:%M:%S") for date0 in saturdays]
    return saturdays

# Function to safely extract variable assignments from a Python source file.
def extract_variables(source_file):
    # This comment explains the function's overall purpose.
    """
    Extracts variables and their values from a Python script and saves them
    to another Python script.
    """
    # Start a try block to gracefully handle potential errors like the file not being found.
    try:
        # Open the specified source file in read mode.
        with open(source_file, "r") as f:
            # Read the entire content of the file into a string.
            source_code = f.read()

        # Parse the source code string into an Abstract Syntax Tree (AST) for programmatic analysis.
        tree = ast.parse(source_code)
        # Initialize an empty dictionary to store the extracted variables and their values.
        variables = {}

        # Walk through all the nodes in the parsed AST.
        for node in ast.walk(tree):
            # Check if the current node represents a variable assignment (e.g., x = 10).
            if isinstance(node, ast.Assign):
                # Loop through the target(s) of the assignment (handles cases like a = b = 10).
                for target in node.targets:
                    # Check if the target is a simple variable name.
                    if isinstance(target, ast.Name):
                        # Get the string name of the variable.
                        variable_name = target.id
                        # Start a try block to handle values that are not simple literals.
                        try:
                            # Use ast.literal_eval to safely evaluate the node's value.
                            # This only works for strings, numbers, booleans, lists, dicts, etc., and prevents arbitrary code execution.
                            variable_value = ast.literal_eval(node.value)
                            # Store the extracted variable name and its value in the dictionary.
                            variables[variable_name] = variable_value
                        # Catch exceptions if the value is not a simple literal (e.g., a function call).
                        except (ValueError, SyntaxError):
                            # Print a warning to the console that this variable could not be extracted.
                            print(f"Warning: Could not extract literal value for {variable_name}")

    # Catch the error if the specified source file does not exist.
    except FileNotFoundError:
        # Print an error message to the console.
        print(f"Error: Source file '{source_file}' not found.")
    # Catch any other exceptions that might occur during the process.
    except Exception as e:
        # Print a generic error message with the exception details.
        print(f"An error occurred: {e}")
        
    # Return the dictionary containing all the successfully extracted variables.
    return variables

# Function to get the names of the variables that a specific function returns.
def get_return_variable_names(filename, function_name):
    # This comment explains the function's purpose.
    """
    Extracts return variable names from a function in a file.
    Args:
        filename (str): Path to the Python file (e.g., "strategy.py").
        function_name (str): Name of the function (e.g., "sum1").
    Returns:
        List of variable names (strings) or empty list if not found.
    """
    # Open the specified Python file in read mode.
    with open(filename, "r") as file:
        # Read the entire content of the file.
        source_code = file.read()
    
    # Parse the source code into an Abstract Syntax Tree.
    tree = ast.parse(source_code)
    # Walk through all the nodes in the AST.
    for node in ast.walk(tree):
        # Check if the current node is a function definition and if its name matches the target function name.
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            # If the correct function is found, iterate through the nodes in its body.
            for body_node in node.body:
                # Check if a node is a 'return' statement.
                if isinstance(body_node, ast.Return):
                    # Get the value part of the return statement.
                    return_value = body_node.value
                    # Check if the return value is a tuple (e.g., return var1, var2).
                    if isinstance(return_value, ast.Tuple):
                        # If so, create a list of the names of each variable in the tuple.
                        return [n.id for n in return_value.elts if isinstance(n, ast.Name)]
                    # Check if the return value is a single variable (e.g., return var1).
                    elif isinstance(return_value, ast.Name):
                        # If so, return a list containing just that single variable name.
                        return [return_value.id]
                    else:
                        # If the return statement contains a complex expression (e.g., return 1+1), return an empty list.
                        return []
    # If the function or a return statement is not found, return an empty list.
    return []

# Helper function to identify the current and next valid trading sessions from a calendar dictionary.
def check_tradable_dates(dict_dates, i, now_, timezone, stock_timezone, data_frequency, 
                         restart_hour, restart_minute, time_after_open, time_before_close):
    
    # Convert the start and end datetimes for the session at index 'i' from the exchange's timezone to the user's local timezone.
    trader_start_datetime, trader_end_datetime = convert_stock_datetimes_to_local(timezone, stock_timezone, 
                                                                                 dict_dates[f'dates_{i}']['start_date'], 
                                                                                 dict_dates[f'dates_{i}']['end_date'])
    # Initialize the datetimes for the next trading day to None.
    trader_next_day_start_datetime = trader_next_day_end_datetime = None

    # Check if the current time is before the end of the session at index 'i', meaning this is the current session.
    if now_ < trader_end_datetime:
        # If so, print a message showing the current session's liquid hours.
        print(f"The current liquid hours are {trader_start_datetime} and {trader_end_datetime}...")
        # Loop through all subsequent keys in the calendar dictionary to find the next open session.
        for key in list(dict_dates.keys())[i+1:]:
            # Check if the entry is a dictionary, which indicates a trading session (not a holiday).
            if isinstance(dict_dates[key], dict):
                # If a valid session is found, convert its start and end times to the local timezone.
                trader_next_day_start_datetime, trader_next_day_end_datetime = convert_stock_datetimes_to_local(
                    timezone, stock_timezone, 
                    dict_dates[key]['start_date'], 
                    dict_dates[key]['end_date']
                )
                # Exit the loop as the next valid trading day has been found.
                break
            # This comment explains that closed days (holidays) are being skipped.
            # Skip closed days (dates without trading hours)
        # If the loop finishes without finding a next trading day (e.g., at the end of the week).
        if trader_next_day_start_datetime is None:
            # Set the next day's times to the current day's end time to indicate no future session in the current data.
            trader_next_day_start_datetime = trader_end_datetime
            trader_next_day_end_datetime = trader_end_datetime
    else:
        # This block executes if the current time is already past the session at index 'i'.
        # Print a message indicating the search for the next session.
        print("The current trading session has ended. Looking for the next tradable session...")
        # Loop through subsequent keys to find the next valid session.
        for key in list(dict_dates.keys())[i+1:]:
            # Check if the entry represents a trading session.
            if isinstance(dict_dates[key], dict):
                # If found, this next session becomes the new "current" session. Convert its times.
                trader_next_day_start_datetime, trader_next_day_end_datetime = convert_stock_datetimes_to_local(
                    timezone, stock_timezone, 
                    dict_dates[key]['start_date'], 
                    dict_dates[key]['end_date']
                )
                # Exit the loop.
                break
            # This comment explains that closed days are being skipped.
            # Skip closed days
        # If no next trading day is found in the provided calendar data.
        if trader_next_day_start_datetime is None:
            # Set the next day's times to the current day's end time.
            trader_next_day_start_datetime = trader_end_datetime
            trader_next_day_end_datetime = trader_end_datetime
        # The session that was identified as the "next" one now becomes the "current" one for the calling function.
        trader_start_datetime = trader_next_day_start_datetime
        trader_end_datetime = trader_next_day_end_datetime

    # Print the identified next trading session's hours.
    print(f"The next tradable liquid hours will be {trader_next_day_start_datetime} and {trader_next_day_end_datetime}...")
    # Return a list containing the start and end times for both the current and the next trading session.
    return [trader_start_datetime, trader_end_datetime, trader_next_day_start_datetime, trader_next_day_end_datetime]
        
# Function to find the current and next valid trading sessions from a full calendar dictionary.
def get_closest_tradable_datetimes(dict_dates, now_, timezone, stock_timezone, data_frequency, 
                                   restart_hour, restart_minute, time_after_open, time_before_close):
    # Loop through the keys of the dates dictionary, which represents the trading calendar for the week.
    for i in range(len(dict_dates.keys())-1):
        # Check if the calendar entry for this day is a date object, which signifies a holiday or closed day.
        if type(dict_dates[list(dict_dates.keys())[i]]) is dt.date:
            # If it's a closed day, skip to the next iteration.
            continue
        # Check if the current time is already past the end of the session for this calendar day.
        elif now_ >= dict_dates[list(dict_dates.keys())[i]]['end_date']:
            # If so, skip to the next iteration to find the current or upcoming session.
            continue
        # Call the helper function to perform the detailed check and find the current and next sessions.
        dates = check_tradable_dates(dict_dates, i, now_, timezone, stock_timezone, data_frequency, 
                                        restart_hour, restart_minute, time_after_open, time_before_close)
        # Check if the helper function returned a valid list of dates.
        if isinstance(dates, list):
            # If a valid list is returned, it means the current and next sessions have been found, so return them immediately.
            return dates
        
# Function to dynamically load a Python file and list the functions defined within it.
def get_functions_from_file(filepath: str):
    # This comment explains the function's purpose and arguments.
    """
    Dynamically imports a Python module from a given file path
    and returns a list of the names of functions defined within it.

    Args:
        filepath: The absolute or relative path to the Python script (.py file).

    Returns:
        A list of function names found in the file, or None if the file
        cannot be loaded or processed.
    """
    # Check if the provided file path does not exist.
    if not os.path.exists(filepath):
        # If not, print an error message.
        print(f"Error: File not found at '{filepath}'")
        # Return None to indicate failure.
        return None
    # Check if the file does not have a '.py' extension.
    if not filepath.endswith(".py"):
        # If not, print an error message.
        print(f"Error: '{filepath}' is not a Python file (.py).")
        # Return None.
        return None

    # Create a unique module name from the base name of the file to avoid conflicts in sys.modules.
    module_name = os.path.splitext(os.path.basename(filepath))[0]
    # This is an alternative, more robust way to generate a unique name if needed.
    # A more robust way to generate a unique name if needed:
    # module_name = f"dynamic_module_{os.path.basename(filepath).replace('.', '_')}"

    # Create a module specification from the file path, which contains metadata for importing.
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    # Check if the specification or its loader could not be created.
    if spec is None or spec.loader is None:
        # If so, print an error message.
        print(f"Error: Could not create module spec for '{filepath}'")
        # Return None.
        return None

    # Create an empty module object from the specification.
    module = importlib.util.module_from_spec(spec)

    # Use a try...finally block to ensure cleanup code is executed even if errors occur.
    try:
        # Add the module's directory to the system path to handle relative imports within the script.
        # Add the module to sys.modules temporarily in case the loaded
        # script itself tries to import things relative to itself.
        # Also add the directory of the file to sys.path to help with imports.
        module_dir = os.path.dirname(os.path.abspath(filepath))
        # Check if the directory is not already in the system path.
        if module_dir not in sys.path:
            # If not, add it to the beginning of the path.
            sys.path.insert(0, module_dir)

        # Add the new module to the system's list of modules.
        sys.modules[module_name] = module
        # Execute the code within the file, which populates the empty module object.
        spec.loader.exec_module(module)

    # Catch any exception that occurs during the execution of the module's code.
    except Exception as e:
        # Print an error message with the exception details.
        print(f"Error executing module '{filepath}': {e}")
        # Begin cleanup if loading failed.
        # If the module was added to sys.modules, remove it.
        if module_name in sys.modules:
            del sys.modules[module_name]
        # If the directory was added to the path, remove it.
        if module_dir in sys.path and sys.path[0] == module_dir:
             sys.path.pop(0)
        # Return None to indicate failure.
        return None

    # Initialize an empty list to store the names of the functions found.
    function_names = []
    # Use a finally block to ensure cleanup happens after successful execution.
    try:
        # Get a list of all members (name, object) of the dynamically loaded module.
        # inspect.getmembers returns list of (name, member) tuples
        # inspect.isfunction checks if the member is a function
        for name, member in inspect.getmembers(module):
            # This condition checks if the member is a function AND was defined in this specific file
            # (not imported from another module).
            if inspect.isfunction(member) and member.__module__ == module_name:
                 # This commented-out line shows an optional filter to exclude private functions.
                 # if not name.startswith('_'):
                 # If it's a native function, add its name to the list.
                 function_names.append(name)
    finally:
        # --- Begin Cleanup ---
        # Remove the dynamically loaded module from the system's list of modules.
        # Remove the module from sys.modules after inspection
        if module_name in sys.modules:
            del sys.modules[module_name]
        # Remove the directory that was added to the system path.
        # Remove the path addition if we added it
        if module_dir in sys.path and sys.path[0] == module_dir:
             sys.path.pop(0)

    # Return the final list of function names.
    return function_names

# Function to determine the number of decimal places in a given tick size.
def get_num_decimals(tick_size):

    # Convert the tick_size number to a string and split it at the decimal point.
    decimal_part = str(tick_size).split('.')
    
    # Check if the resulting list has more than one element, which means a decimal point was present.
    if len(decimal_part) > 1:
        # If so, the number of decimals is the length of the string part after the decimal point.
        num_decimals = len(decimal_part[1])
    else:
        # If there was no decimal point, the number of decimals is 0.
        num_decimals = 0
        
    # Return the calculated number of decimals.
    return num_decimals

# Function to round a given price to the nearest valid multiple of the exchange's tick size.
def get_price_by_tick_size(number, tick_size):
    # Use the modulo operator to extract the decimal part of the input number.
    decimal_part = number % 1
    
    # Check if the tick size is not zero to avoid division by zero errors.
    if tick_size != 0.0:
        # This formula calculates the nearest valid decimal:
        # 1. Divide the decimal part by the tick size.
        # 2. Round the result to the nearest whole number.
        # 3. Multiply by the tick size again to get the closest valid multiple.
        multiple = round(decimal_part / tick_size) * tick_size
        
        # Combine the original integer part of the price with the newly calculated valid decimal part.
        # Get the integer part of the original price.
        integer_part = math.floor(number)
        # Add the integer part and the adjusted decimal part together.
        adjusted_number = integer_part + multiple
        
        # Return the final, adjusted price.
        return adjusted_number 

    else:
        # If the tick size is 0, simply round the number to the nearest whole number (0 decimal places).
        return round(number,0)
