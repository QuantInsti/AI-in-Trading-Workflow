"""
## Licensed under the QuantInsti Open License (QOL) v1.1 (the "License").
- Copyright 2025 QuantInsti Quantitative Learning Pvt. Ltd.
- You may not use this file except in compliance with the License.
- You may obtain a copy of the License in LICENSE.md at the repository root or at https://www.quantinsti.com.
- Non-Commercial use only; see the License for permitted use, attribution, and restrictions.
"""

# For data manipulation
import pickle 
import numpy as np
import pandas as pd
from hmmlearn import hmm
from datetime import datetime
from sklearn.utils import check_random_state
from ibkr_stock import trading_functions as tf
import featuretools as ft
from featuretools.primitives import Month, Weekday, Hour
from ta import add_all_ta_features
from statsmodels.tsa.stattools import adfuller
from sklearn.ensemble import BaggingClassifier
from sklearn.ensemble import RandomForestClassifier as RFC
from sklearn.calibration import CalibratedClassifierCV as calibration

import warnings
warnings.filterwarnings("ignore")

def create_classifier_model(seed):
    """
    Creates a calibrated bagging classifier model with a Random Forest base estimator.

    This function constructs a classification model consisting of a BaggingClassifier that aggregates
    multiple RandomForestClassifier instances. The model is calibrated using isotonic regression to
    improve probability estimates.

    The base RandomForestClassifier is configured with 5 trees, all features considered for splits,
    and class weights adjusted per bootstrap sample. The BaggingClassifier ensembles 50 such random forests.
    Both components leverage parallel processing (n_jobs=-2). The final output is a calibrated model.

    Args:
        seed (int): Random seed for reproducibility. Controls randomness in the base estimator,
                   bagging process, and calibration.

    Returns:
        CalibratedClassifierCV: A classifier model wrapped with isotonic calibration. The model
                                combines bagged random forests and calibrated probabilities.

    Notes:
        - RandomForestClassifier uses "balanced_subsample" class weighting to handle imbalance.
        - n_jobs=-2 enables parallel processing using all except one CPU core.
        - Isotonic calibration fits a non-linear monotonic function to map probabilities to calibrated values.
    """
    
    # Create the model object
    model = calibration(BaggingClassifier(RFC(n_estimators=5, max_features=1.0, class_weight = "balanced_subsample",\
                                              n_jobs=-2, random_state=seed),
                                          n_estimators=50, random_state=seed, n_jobs=-2),
                        method='isotonic', n_jobs=-2)
    return model

def set_stop_loss_price(app):
    """
    Sets the stop-loss price based on the trading signal and fixed risk parameters.

    This function calculates the stop-loss price for a long or short position. For a long position (signal > 0),
    the stop loss is placed below the entry price. For a short position (signal < 0), it is placed above the entry price.
    The distance from the entry price is determined by fixed risk parameters: a 0.3% risk target and a multiplier of 1.

    Args:
        base_df (pd.DataFrame): Feature-engineered dataframe from `prepare_base_df`. Included for extensibility if needed for other stop-loss logic.
        signal (int/float): Trading signal indicating position direction. 
                            Positive values indicate long positions, negative values indicate short positions.
        last_value (float): The latest price or entry value of the asset.

    Returns:
        float: Stop-loss price rounded to 5 decimal places.

    Notes:
        - Long positions: stop_loss = last_value * (1 - 0.003)
        - Short positions: stop_loss = last_value * (1 + 0.003)
        - Rounding ensures practical price formatting for trading platforms.
        - Uses fixed risk parameters: 0.3% risk target and stop loss multiplier of 1.
    """  
    # Set the signal
    signal = app.signal
    # Set the last tick value of the Forex contract
    last_value = app.last_value
    
    # Set the risk management price return target
    risk_management_target = 0.04
    # Set the stop loss multiplier target
    stop_loss_multiplier = 1     

    # The stop loss price will be below the long position value
    order_price = last_value*(1-risk_management_target*stop_loss_multiplier)
        
    return order_price

def set_take_profit_price(app):
    """
    Sets the take-profit price based on the trading signal using fixed risk parameters.

    This function calculates the take-profit price for a long or short position using
    fixed parameters of 0.3% return target and 1x multiplier. For long positions (signal > 0),
    the take-profit is placed 0.3% above the entry price. For short positions (signal < 0),
    it is placed 0.3% below the entry price.

    Args:
        base_df (pd.DataFrame): Feature-engineered dataframe from `prepare_base_df`.
                               Included for potential future integration with alternative strategies.
        signal (int/float): Trading signal indicating position direction. 
                            Positive values indicate long positions, negative values indicate short positions.
        last_value (float): The latest price or entry value of the asset.

    Returns:
        float: Take-profit price rounded to 5 decimal places.

    Notes:
        - Long positions: take_profit = last_value * 1.003
        - Short positions: take_profit = last_value * 0.997
        - Uses fixed 0.3% (0.003) price target with 1x multiplier
        - Rounding ensures practical price formatting for trading platforms
        - base_df parameter is currently unused but available for future implementation extensions
    """
            
    # Set the signal
    signal = app.signal
    # Set the last tick value of the Forex contract
    last_value = app.last_value
    
    # Set the risk management price return target
    risk_management_target = 0.04
    # Set the stop loss multiplier target
    take_profit_multiplier = 1     

    # The stop loss price will be below the long position value
    order_price = last_value*(1+risk_management_target*take_profit_multiplier)
        
    return order_price

def prepare_base_df(historical_data, train_span=None):
    """
    Prepares a feature-engineered dataframe for model training, including technical indicators, 
    datetime features, and preprocessing.

    This function performs comprehensive feature engineering including:
    - Creation of target labels based on future returns
    - Generation of datetime features (month, weekday, hour dummies)
    - Calculation of technical indicators with multiple window sizes
    - Stationarity enforcement for features via ADF test
    - Feature normalization using rolling z-scores
    - Data cleaning and formatting for machine learning

    Args:
        historical_data (pd.DataFrame): Raw input dataframe with OHLC price data

    Returns:
        tuple: Contains three elements:
            - pd.DataFrame: Processed dataframe with features, targets, and cleaned data
            - list: Names of final input features for model training

    Notes:
        - Target variable 'y' has 2 labels: 1 (up) and -1 (down) based on next-period returns
        - Datetime features are one-hot encoded (month, weekday, hour) with Saturday (day_5) explicitly dropped
        - Technical indicators are calculated using the ta library with multiple window sizes
        - Features are made stationary using either percentage changes or differencing based on ADF test (p<0.05)
        - Includes volatility signals (MA crosses, STD thresholds) as additional features
        - Applies rolling z-score normalization with 30-period window to specified features
        - Handles missing/infinite values via forward-fill and dropna
    """
    
    # The maximum window to create the technical indicators
    max_window = 6

    df = historical_data.copy()
        
    if train_span is not None:
        # Subset the dataframe up to train_span observations
        df = df.iloc[-(train_span+500):,:].copy()
    
    ###############################################################################
    # Section 1: Creating the first model prediction feature
    
    # WARNING: IF YOU'RE TRADING OPEN_TO_CLOSE OR CLOSE_TO_OPEN YOU MIGHT WANT TO DEPLOY ANOTHER TYPE OF PREDICTION FEATURE
    
    ###############################################################################
    # Compute the close-to-close log returns
    df['cc_returns'] = np.log(df.Close/df.Close.shift(1))
    # Compute the prediction feature for the first model   
    df['y'] = np.where(df['cc_returns'].shift(-1)>0,1,0)
    # Drop the rows which have the prediction feature a label with very few observations
    df = tf.dropLabels(df)
    
    ###############################################################################
    # Section 2: Creating the datetime input features
    ###############################################################################
    # Set the name for the dates dataframe index
    for_features_index = 'index1'
    # Create a column based on the index datetime
    df[for_features_index] = df.index
    
    # Create an entityset to form the dates-based features
    es = ft.EntitySet('My EntitySet')
    es.add_dataframe(
        dataframe_name = 'main_data_table',
        index = 'index',
        dataframe = df[['Close', for_features_index]])#,
        # time_index = 'index1')#, 
        # make_index=True)
        
    # Set the frequency to be used to get the dates time series
    time_features = [Month, Weekday, Hour]
    #time_features = [Minute, Hour, Weekday, Month]
    
    # Create the time series based on the time frequencies' features from above
    fm, features = ft.dfs(
        entityset = es,
        target_dataframe_name = 'main_data_table',
        trans_primitives = time_features)
    
    # Set the fm index as the df.index is
    fm.set_index(df.index, inplace=True, drop=True)
    
    # A function to obtain the fm columns names
    def get_var_name(variable):
         for name, value in globals().items():
            if value is variable:
                return name
            
    # Set the time features names in a list
    time_features_columns = [get_var_name(el).upper()+ '('+for_features_index+')' for el in time_features]
    
    # Obtain the dummies from the months' time series
    months_dummies = pd.get_dummies(fm[time_features_columns[0]])
    # Rename the month's columns
    months_dummies.columns = ['month_'+ str(month) for month in months_dummies.columns.to_list()]
    # Obtain the dummies from the days' time series
    days_dummies = pd.get_dummies(fm[time_features_columns[1]])
    # Rename the days columns
    days_dummies.columns = ['day_'+ str(day) for day in days_dummies.columns.to_list()]
    # Drop the Saturday's column
    days_dummies.drop('day_5', axis=1, inplace=True)
    # Obtain the dummies from the hours' time series
    hours_dummies = pd.get_dummies(fm[time_features_columns[2]])
    # Rename the hour's columns
    hours_dummies.columns = ['hour_'+ str(hour) for hour in hours_dummies.columns.to_list()]
    
    # Save the datetime features in a single dataframe
    datetime_features = pd.concat([months_dummies, days_dummies, hours_dummies],axis=1)
    
    ###############################################################################
    # Section 3: Creating the technical indicators features
    ###############################################################################
    # Create a Volume column with zeros
    df['Volume'] = 0.0
    
    # Set the list of window sizes        
    if max_window<=15:
        windows = list(range(3,max_window))
    elif max_window>=16:
        windows = list(range(3,11))+list(range(15,(max_window+1),10))
    
    # Create the technical indicators dataframe
    technical_features_df = pd.DataFrame(index=df.index)
    
    # Obtain the long-memory stationary OHLC data based on the optimal "d" previously estimated
    df[['Open_dif','High_dif','Low_dif','Close_dif']] = df[['Open','High','Low','Close']].pct_change()
        
    ohlc_lags_list = ['Open_dif','High_dif','Low_dif','Close_dif']
    for lag in list(range(1,10)):
        df[[f'Open_dif_{lag}',f'High_dif_{lag}',f'Low_dif_{lag}',f'Close_dif_{lag}']] = df[['Open_dif','High_dif','Low_dif','Close_dif']].shift(lag)
        ohlc_lags_list.extend([f'Open_dif_{lag}',f'High_dif_{lag}',f'Low_dif_{lag}',f'Close_dif_{lag}'])
    
    # Drop Nan values
    df.dropna(inplace=True)
    
    # Get all the possible technical indicators for each window size
    for window in windows:
        # Obtain the technical indicators
        technical_features = (
            add_all_ta_features(
                df[['Open','High','Low','Close','Volume']].copy(), \
                    open="Open", high="High", low="Low", close="Close", volume="Volume"
            )
            .ffill()
        )
        
        # Drop the OHLCV columns
        technical_features.drop(['Open','High','Low','Close','Volume'], axis=1, inplace=True)
        # Save the names of the volume-based features as a list
        volume_indicators = technical_features.filter(like='volume', axis=1).columns.tolist()
        # Drop the volume-based features
        technical_features.drop(volume_indicators, axis=1, inplace=True)
        
        # Save the names of the volume-based features as a list
        volume_pvo_indicators = technical_features.filter(like='pvo', axis=1).columns.tolist()
        # Drop the volume-based features
        technical_features.drop(volume_pvo_indicators, axis=1, inplace=True)
        
        # Modify the dataframe columns to distinguish them from other features with different window sizes
        technical_features.columns = [f'{column}_{window}' for column in technical_features.columns.tolist()]
        # Concatenate these window-size-based technical indicators to the bigger dataframe
        technical_features_df.loc[technical_features.index, technical_features.columns.tolist()] = technical_features
        
    # Create a loop to make the technical indicators stationary
    for indicator in technical_features_df.columns:
        # If all observations are NaN values
        if technical_features_df[indicator].isna().all():
            # Drop the feature from the dataframe
            technical_features_df.drop(indicator, axis=1, inplace=True)  
            continue
        # If all observations are Infinite
        elif np.isinf(technical_features_df[indicator].values).all():
            # Drop the feature from the dataframe
            technical_features_df.drop(indicator, axis=1, inplace=True)  
            continue
        else:
            try:
                # Get the p-value of the adfuller applied to the technical indicator
                pvalue = adfuller(technical_features_df[indicator].dropna(), regression='c', autolag='AIC')[1]
                # If the p-value is higher than 0.05
                if pvalue > 0.05:
                    # Use the percentage returns of the technical indicator as the input feature
                    technical_features_df[indicator] = technical_features_df[indicator].pct_change()
                # If no p-value was obtained from the adfuller
                elif np.isnan(pvalue):
                    # Drop the feature from the dataframe
                    technical_features_df.drop(indicator, axis=1, inplace=True)
            except:
                # Drop the feature from the dataframe
                technical_features_df.drop(indicator, axis=1, inplace=True)
    
    # Creating more features
    ma_signal_names = [f'ma_signal_{i}' for i in windows]
    std_names = [f'std_{i}' for i in windows]
    std_mean_names = [f'std_mean_{i}' for i in windows]
    std_signal_names = [f'std_signal_{i1}_{i2}' for i1 in windows for i2 in windows]    
    df[ma_signal_names] = np.array([np.where(df['Close']>df['Close'].rolling(i).mean().values,1.0,-1.0) for i in windows]).T
    df[std_names] = np.array([df['Close'].rolling(i).std().values for i in windows]).T
    df[std_mean_names] = np.array([df[f'std_{i}'].rolling(i).mean() for i in windows]).T    
    df[std_signal_names] = np.array([np.where(df[f'std_{i1}']<df[f'std_mean_{i2}'],1.0,-1) for i1 in windows for i2 in windows]).T
    
    ###############################################################################
    # Section 4: Concatenating the necessary dataframes into a single dataframe
    ###############################################################################
    # Set the scalable features list
    scalable_features = technical_features_df.columns.tolist() + df[ohlc_lags_list].columns.tolist()
        
    # Create the base dataframe to be used for the ML model
    base_df = pd.concat([technical_features_df, df[ohlc_lags_list], datetime_features],axis=1)
    
    # Create the states' column to save the HMM-based regimes
    base_df['states'] = 0.0
    
    # Save the names of the final features as a list
    final_input_features = base_df.columns.tolist()
    
    # Create the dataframe to be used for estimating the model
    base_df = pd.concat([base_df, \
                         df[['y','cc_returns','Open','High','Low','Close']],\
                         df[ma_signal_names+std_signal_names]],axis=1) 
            
    # Add the relevant features to the final features
    final_input_features.extend(ma_signal_names)
    final_input_features.extend(std_signal_names)
    
    # Forward fill the NaN values
    base_df.ffill(inplace=True)  
    
    # Drop the NaN values
    base_df.dropna(inplace=True) 
    
    ###############################################################################
    # Section 5: Make the input features rolling-zscore-based
    ###############################################################################

    # Z-score the input features
    base_df, _ = tf.rolling_zscore_function(base_df, scalable_features, 30) 
        
    # Drop the Inf values
    base_df.replace([np.inf, -np.inf], np.nan, inplace=True)
    base_df.ffill(inplace=True) 
    
    # Return None for final_input_features in case you're not working with an ML-based strategy
    # return base_df, None
    return base_df, final_input_features

def get_signal(app): 
    """
    Generates a trading signal using a pre-trained model and HMM-based regime detection.

    This function loads serialized model objects (HMM and classifier) specific to the market open date,
    processes input data with purged k-fold cross-validation, updates regime states via HMM predictions,
    and returns a trading signal for the next period.

    Args:
        base_df (pd.DataFrame): Feature-engineered dataframe from `prepare_base_df`.
        purged_window_size (int): Number of periods to exclude around test splits to prevent look-ahead bias.
        embargo_period (int): Additional buffer period after purging to further avoid data leakage.
        model_datetime (datetime): Timestamp used to load date-specific model files (formats filenames as 
                                   'model_object_YYYY_MM_DD.pickle').
        final_input_features (list): Column names of features used for model prediction (must match the 
                                   trained model's expected features).

    Returns:
        float: Trading signal (-1, 0, or 1) indicating short, neutral, or long position.

    Notes:
        - Relies on pre-trained models stored in 'data/models/' with strict filename formatting:
            * HMM: hmm_model_YYYY_MM_DD.pickle
            * Classifier: model_object_YYYY_MM_DD.pickle
        - Splits the data into train and test dataframes in such a way that you purge and embargo the data.
        - HMM predicts market regimes using directional change events (theta=0.00002 threshold).
        - Transition matrix sampling forecasts the next regime state for the test period.
        - Embargo period ensures no overlapping information between train/test splits.
        - Models expect `model_datetime` to load the saved model objects.
    """
    
    # Set the features to be used 
    final_input_features = app.final_input_features
    # Set the feature-engineered dataframe
    base_df = app.base_df
    
    # The purged window and embargo period values
    purged_window_size = 1
    embargo_period = 1
    # Set the leverage for the trade size
    leverage = 0.02
    # Set the market open time
    model_datetime = app.model_datetime
    
    ''' Function to get the signal'''
    
    """ Change code from here """
    ###############################################################################
    # Section 1: Create the month and day strings to be used for calling the model objects
    ###############################################################################

    # Set the month and day strings to call the models
    month_string = str(model_datetime.month) if model_datetime.month>=10 else '0'+str(model_datetime.month)
    day_string = str(model_datetime.day) if (model_datetime.day)>=10 else '0'+str(model_datetime.day)

    ###############################################################################
    # Section 2: Split the data into train and test dataframes for the X and y features
    ###############################################################################

    # Create the input and prediction features
    X, y = tf.create_Xy(base_df, final_input_features, 'y')
    
    # Split the data
    X_train, X_test, y_train, _ = tf.train_test_split(X, y, 1, purged_window_size, embargo_period)
    
    ###############################################################################
    # Section 3: Create the HMM-based input feature
    ###############################################################################

    # Create the R indicator
    r_values = tf.directional_change_events(base_df.loc[X_train.index,['Close']], theta=0.00002, columns='R').dropna().values.reshape(-1,1)
    
    # Call the HMM model
    hmm_model = pickle.load(open(f'data/models/hmm_model_{model_datetime.year}_{month_string}_{day_string}.pickle', 'rb'))
        
    X_train['states'].iloc[-len(r_values):] = hmm_model.predict(r_values)
    
    # Forecast the next period state
    transmat_cdf = np.cumsum(hmm_model.transmat_, axis=1)
    random_state = check_random_state(hmm_model.random_state)
    X_test['states'].iloc[0] = (transmat_cdf[int(X_train['states'].iloc[-1])] > random_state.rand()).argmax()
    
    ###############################################################################
    # Section 4: Create the signal
    ###############################################################################
    # Call the random-forest first model object
    model_object = pickle.load(open(f'data/models/model_object_{model_datetime.year}_{month_string}_{day_string}.pickle', 'rb'))
    
    # Save the model test signal predictions
    signal = base_df.loc[X_test.index,'signal'] = float(model_object.predict(X_test[model_object.feature_names_in_.tolist()].astype("float32"))[0])
    
    """ Change code up to here """
    
    # If you set the leverage variable in the main file, you can just return the signal
    return signal , leverage

def strategy_parameter_optimization(seed, data_frequency,  
                                    base_df_address, 
                                    train_span, test_span, historical_data_address, model_datetime):

    """
    Optimizes trading strategy parameters through backtesting, feature selection, and model training.

    This end-to-end pipeline:
    1. Prepares feature-engineered data (`base_df`) from raw OHLC data
    2. Trains Hidden Markov Models (HMM) for regime detection
    3. Selects optimal features using Boruta-Shap algorithm
    4. Trains ensemble models with multiple random seeds
    5. Evaluates performance via Sharpe ratio
    6. Saves trained models and metadata to disk

    Args:
        seed (int): Random seed for reproducibility (HMM initialization, model training).
        data_frequency (str): Resampling frequency for raw data (e.g., '15min' for 15-minute bars).
        max_window (int): Maximum lookback window for technical indicator calculations.
        base_df_address (str): Path to save/load preprocessed `base_df` (feature-engineered data).
        purged_window_size (int): Number of periods to exclude around test splits to prevent look-ahead bias.
        embargo_period (int): Additional buffer periods after purging to avoid data leakage.
        train_span (int): Number of periods to use for training (None = use all available).
        test_span (int): Number of periods to reserve for testing (defaults to 5 trading days).
        model_datetime (datetime): Last datetime where the model was optimized timestamp used for:
                                   - Data resampling alignment
                                   - Model filename formatting (YYYY_MM_DD)

    Returns:
        None: Models and metadata are saved to disk rather than returned directly.

    Notes:
        - Saves 3 key artifacts to 'data/models/':
            1. HMM model: hmm_model_YYYY_MM_DD.pickle
            2. Classifier: model_object_YYYY_MM_DD.pickle 
            3. Feature importance: selected_features_YYYY_MM_DD.pickle
        - Uses 1M random seeds (subset to 3) for model diversity
        - Evaluates models on annualized Sharpe ratio of test period returns
        - Boruta-Shap feature selection uses 25 iterations with 80/20 train/validation split
        - Raw data preprocessing includes:
            * Mid-price calculation from OHLC
            * Frequency resampling aligned to market open time
            * Stationarity transformations
        - HMM configured with:
            * 2 hidden states (bull/bear regimes)
            * Diagonal covariance matrix
            * 100 EM algorithm iterations
    """

    # Set the month and day strings to save the model objects
    month_string = str(model_datetime.month) if model_datetime.month>=10 else '0'+str(model_datetime.month)
    day_string = str(model_datetime.day) if (model_datetime.day)>=10 else '0'+str(model_datetime.day)

    """ Change code from here """
    purged_window_size = embargo_period = 1
    ###############################################################################
    # Section 1: Prepare the base_df dataframe
    ###############################################################################
    start_time = datetime.now()
    
    # Number of random seeds to generate from the above seed to create the models
    random_seeds = list(np.random.randint(low = 1, high = 10000001, size = 1000000))[:3]

    print('='*100)
    print('='*100)
    print(f"- Preparing the base_df dataframe starts at {start_time}")
    
    # Get the trading periods per day
    periods_per_day = tf.get_periods_per_day(data_frequency)
    # Set the number of rows to be used for the test data
    if test_span is None:
        test_span = 5*periods_per_day
    
    # Import the data
    df = pd.read_csv(historical_data_address, index_col = 0)
    
    # Prepare the dataframe to be used for fitting the model
    # Return None for the final_input_features in case you're not working with an ML-based strategy
    base_df, final_input_features = prepare_base_df(df, train_span)
    
    # Save the final input features in case you're working with an ML-based strategy
    features_df = pd.DataFrame(data=final_input_features, columns=['final_features'], index=range(len(final_input_features)))
    features_df.to_excel('data/models/optimal_features_df.xlsx')
    
    start_time = datetime.now()
    print('='*100)
    print('='*100)
    print(f"- Backtesting starts at {start_time}")
    
    ###############################################################################
    # Section 2: Split the data into train and test dataframes for the X and y features
    ###############################################################################
    # Create the input and prediction features
    X, y = tf.create_Xy(base_df, final_input_features, 'y')
    
    # Split the data
    X_train, X_test, y_train, _ = tf.train_test_split(X, y, test_span, purged_window_size, embargo_period)
        
    ###############################################################################
    # Section 3: Create the HMM-based input feature
    ###############################################################################
    # Create the R indicator
    r_values = tf.directional_change_events(base_df.loc[X_train.index,['Close']], theta=0.00002, columns='R').values.reshape(-1,1)
    train_r_values = r_values[:-test_span]
    train_r_values = train_r_values[~np.isnan(train_r_values)].reshape(-1,1)
    test_r_values = r_values[-test_span:].reshape(-1,1)
    
    # Create an HMM object with two hidden states
    hmm_model = hmm.GaussianHMM(n_components = 2, covariance_type = "diag", n_iter = 100, random_state = seed)
    
    # Estimate the HMM model
    hmm_model.fit(train_r_values)
    
    # Use the Viterbi algorithm to find the fitted hidden states
    X_train['states'].iloc[(len(X_train)-len(train_r_values)):] = hmm_model.predict(train_r_values)
    
    # Compute the next state hidden state for the test data
    for i in range(len(train_r_values),(len(train_r_values)+len(test_r_values))):
        transmat_cdf = np.cumsum(hmm_model.transmat_, axis=1)
        random_state = check_random_state(hmm_model.random_state)
        if i == len(train_r_values):
            X_test['states'].iloc[(i-len(train_r_values))] = \
                (transmat_cdf[int(X_train['states'].iloc[-1])] > random_state.rand()).argmax()
        else:
            X_test['states'].iloc[(i-len(train_r_values))] = \
                (transmat_cdf[int(X_test['states'].iloc[(i-1-len(train_r_values))])] > random_state.rand()).argmax()
    
    ###############################################################################
    # Section 4: Do feature importance with the Boruta-Shap algorithm
    ###############################################################################
    # Set the date of train split to estimate the Boruta-Shap algorithm
    date_loc_split = X_train.index[int(len(X_train.index)*0.8)]
    
    # Select the best features based on the Boruta Shap algorithm
    print('Get the best features with the Boruta-Shap algorithm')
    selected_features = tf.library_boruta_shap(X_train, y_train.iloc[:,:], seed, 25, date_loc_split)
    print('The best features with the Boruta-Shap algorithm were obtained')
    
    ###############################################################################
    # Section 5: Estimate the models based on the list of seeds
    ###############################################################################
    # Set the start date of the backtesting seed loop
    loop_start_time = datetime.now()
    print('='*100)
    print(f"- Backtesting loop starts at {loop_start_time}")

    # A dictionary to save the model objects created per each seed
    model_objects = {}
    
    # A dictionary to save the test-data Sharpe ratios of each model
    models_sharpe = dict()

    # Annualize factor for the Sharpe ratio
    annualize_factor = 252*periods_per_day

    for i in range(len(random_seeds)):    
        print(f"\t- model number {i+1} estimation starts at {datetime.now()}")

        	# Create an random forest algo object
        model_objects[random_seeds[i]] = create_classifier_model(random_seeds[i]) 
        # Fit the model with the train data
        model_objects[random_seeds[i]].fit(X_train[selected_features].astype("float32"), y_train.astype("int32").values.ravel())
                
        	# Save the model train signal predictions
        base_df.loc[X_train.index,'signal'] = \
            model_objects[random_seeds[i]].predict(X_train[selected_features].astype("float32"))
            
        	# Save the model test signal predictions
        base_df.loc[X_test.index,'signal'] = \
            model_objects[random_seeds[i]].predict(X_test[selected_features].astype("float32"))
            
        # Compute the model's cumulative returns
        base_df.loc[X_train.index,'rets'] = base_df.loc[X_train.index,'cc_returns'] * \
            base_df.loc[X_train.index,'signal'].shift(1)
                                
        # Compute the model's cumulative returns
        base_df.loc[X_test.index,'rets'] = base_df.loc[X_test.index,'cc_returns'] * \
            base_df.loc[X_test.index,'signal'].shift(1)
                                
        # Compute the model's test data Sharpe ratio
        models_sharpe[random_seeds[i]] = np.round(base_df.loc[X_test.index,'rets'].mean() / \
                                                  base_df.loc[X_test.index,'rets'].std() * \
                                                  np.sqrt(annualize_factor),3)
                  
        print(f"\t\t- model number {i+1} with seed {random_seeds[i]} estimation ends at {datetime.now()}")
    
    loop_end_time = datetime.now()
    print('='*100)
    print(f"- Backtesting loop ends at {loop_end_time}")
    print(f"- Backtesting lasted {loop_end_time-start_time}")
      
    ###############################################################################
    # Section 6: Optimize the strategy based on the list of seeds
    ###############################################################################
    # Get the optimal model seed to trade the next month 
    optimal_seed = max(models_sharpe, key=models_sharpe.get)
            
    ###############################################################################
    # Section 7: Save all the model objects used while optimizating the strategy
    ###############################################################################
    # Save the HMM model
    with open(f'data/models/hmm_model_{model_datetime.year}_{month_string}_{day_string}.pickle', 'wb') as handle:
        pickle.dump(hmm_model, handle, protocol=pickle.HIGHEST_PROTOCOL)
    
    # Save the model object
    with open(f'data/models/model_object_{model_datetime.year}_{month_string}_{day_string}.pickle', 'wb') as handle:
        pickle.dump(model_objects[optimal_seed], handle, protocol=pickle.HIGHEST_PROTOCOL)

    """ Change code up to here """
    
    # Saving the base_df dataframe
    base_df.to_csv('data/'+base_df_address)    
