## Licensed under the Apache License, Version 2.0 (the "License").
- Copyright 2025 QuantInsti Quantitative Learnings Pvt Ltd.
- You may not use this file except in compliance with the License.
- You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
- Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

import datetime as dt
import yfinance as yf
import json
import pandas as pd
import numpy as np

# In a real deployment, you would have the 'graph' object from the LangGraph setup.
# This script is now structured to use it directly.
from langchain_core.messages import HumanMessage
from agent.graph import graph # This 'graph' object is crucial and comes from your LangGraph setup.

import warnings
warnings.filterwarnings("ignore")

# --- Script Configuration ---
# Set the parameters for the trading analysis here instead of using command-line arguments.
# These can be overridden by the 'app' object if passed from the main trading system.
INITIAL_QUERIES = 1
MAX_LOOPS = 1
REASONING_MODEL = "gemini-2.5-pro"
previous_period = dt.datetime.now() - dt.timedelta(minutes=3)


# --- Dynamic Prompt Generation ---
# Prompts are now functions to incorporate runtime arguments.

def get_news_gathering_prompt(asset_name, exchange, previous_period):
    """Generates the prompt for the news gathering agent."""
    return (
        f"Research the latest news from {previous_period} to now only. "
        f"Focus on news related to the asset '{asset_name}' on the {exchange} exchange. "
        "Search for news relevant to forming an opinion on how bearish or bullish the asset is."
    )

def get_sentiment_analysis_prompt(news_summaries):
    """Generates the prompt for the sentiment analysis agent."""
    return (
        "Based on the following news summaries, provide a sentiment score from -1 (very bearish) to +1 (very bullish). "
        f"Output only the numerical score. The news summaries are:\n\n{news_summaries}"
    )

def get_trading_strategy_prompt(asset_name, sentiment_score, volatility_index):
    """Generates the prompt for the final trading strategy decision."""
    return (
        "You are a trading strategy agent. Your task is to provide a trading recommendation "
        "based on a sentiment score and a market volatility index. "
        f"Analyze the following sentiment score and volatility index for {asset_name}. "
        "Provide your recommendation in a JSON format with three keys: "
        "'action' (string: 'BUY', 'SELL', or 'HOLD'), "
        "'confidence' (float: 0.0 to 1.0), and "
        "'reasoning' (string: your brief reasoning).\n\n"
        f"Sentiment Score: {sentiment_score}\n"
        f"Volatility Index (VIX): {volatility_index}"
    )


def extract_last_message_content(result, default_message=""):
    """Extracts content from the last message in the result."""
    messages = result.get("messages", [])
    if messages and hasattr(messages[-1], 'content'):
        return messages[-1].content
    return default_message

class NewsGathererAgent:
    """Agent for gathering news summaries."""
    def __init__(self, graph_instance, initial_queries, max_loops, reasoning_model):
        self.graph = graph_instance
        self.initial_queries = initial_queries
        self.max_loops = max_loops
        self.reasoning_model = reasoning_model

    def execute(self, asset_name, exchange):
        """Executes the news gathering task for a specific asset and exchange."""
        print(f"--- Step 1: Gathering News for {asset_name} ---")
        print(f'News Agent starts at {dt.datetime.now()}')
        prompt = get_news_gathering_prompt(asset_name, exchange, previous_period)
        state = {
            "messages": [HumanMessage(content=prompt)],
            "initial_search_query_count": self.initial_queries,
            "max_research_loops": self.max_loops,
            "reasoning_model": self.reasoning_model,
        }
        result = self.graph.invoke(state)
        news_summaries = extract_last_message_content(result, "No news summaries found.")
        print("News Summaries Obtained.")
        return news_summaries

class SentimentAnalyzerAgent:
    """Agent for analyzing the sentiment of news summaries."""
    def __init__(self, graph_instance, initial_queries, max_loops, reasoning_model):
        self.graph = graph_instance
        self.initial_queries = initial_queries
        self.max_loops = max_loops
        self.reasoning_model = reasoning_model

    def execute(self, news_summaries):
        """Executes the sentiment analysis task."""
        print("\n--- Step 2: Analyzing Sentiment ---")
        print(f'Sentiment Agent starts at {dt.datetime.now()}')
        if "No news summaries found." in news_summaries:
            print("No news to analyze.")
            return None

        question = get_sentiment_analysis_prompt(news_summaries)
        state = {
            "messages": [HumanMessage(content=question)],
            "initial_search_query_count": self.initial_queries,
            "max_research_loops": self.max_loops,
            "reasoning_model": self.reasoning_model,
        }
        result = self.graph.invoke(state)
        sentiment_score_str = extract_last_message_content(result, "0.0")
        try:
            sentiment_score = float(sentiment_score_str)
            print(f"Sentiment Score: {sentiment_score}")
            return sentiment_score
        except (ValueError, TypeError):
            print(f"Warning: Could not parse sentiment score '{sentiment_score_str}'. Defaulting to 0.0.")
            return 0.0


class MarketDataFetcher:
    """
    Agent to fetch live market data using the yfinance library.
    """
    def get_vix_index(self):
        """
        Fetches the most recent closing value for the CBOE Volatility Index (VIX).
        """
        print("\n--- Step 3: Fetching Market Volatility (VIX) ---")
        print(f'VIX Agent starts at {dt.datetime.now()}')
        try:
            vix_ticker = yf.Ticker("^VIX")
            hist = vix_ticker.history(period="5d")
            if hist.empty:
                print("Warning: Could not retrieve VIX data. It may be a non-trading day.")
                return None
            
            latest_vix = hist['Close'].iloc[-1]
            print(f"Successfully fetched VIX. Latest Close: {latest_vix:.2f}")
            return latest_vix
        except Exception as e:
            print(f"Error fetching VIX data from yfinance: {e}")
            return None


class TradingStrategyAgent:
    """Agent that combines sentiment and volatility to generate a trading signal."""
    def __init__(self, graph_instance, initial_queries, max_loops, reasoning_model):
        self.graph = graph_instance
        self.initial_queries = initial_queries
        self.max_loops = max_loops
        self.reasoning_model = reasoning_model

    def execute(self, asset_name, sentiment_score, volatility_index):
        """
        Executes the trading strategy analysis and returns a dictionary
        with action, confidence, and reasoning.
        """
        print("\n--- Step 4: Generating Trading Strategy ---")
        print(f'Trader Agent starts at {dt.datetime.now()}')
        default_response = {
            "action": "HOLD",
            "confidence": 0.5,
            "reasoning": "Could not determine a trading action."
        }
        
        if sentiment_score is None or volatility_index is None:
            print("Cannot generate strategy without sentiment and volatility data.")
            return default_response

        prompt = get_trading_strategy_prompt(asset_name, sentiment_score, volatility_index)
        state = {
            "messages": [HumanMessage(content=prompt)],
            "initial_search_query_count": self.initial_queries,
            "max_research_loops": self.max_loops,
            "reasoning_model": self.reasoning_model,
        }
        result = self.graph.invoke(state)
        recommendation_str = extract_last_message_content(result)

        try:
            # Clean the string to ensure it is valid JSON
            # The model might sometimes wrap the JSON in ```json ... ```
            if recommendation_str.strip().startswith("```json"):
                recommendation_str = recommendation_str.strip()[7:-3]

            recommendation_dict = json.loads(recommendation_str)
            
            # Ensure all keys are present
            recommendation_dict.setdefault('action', 'HOLD')
            recommendation_dict.setdefault('confidence', 0.5)
            recommendation_dict.setdefault('reasoning', 'No reasoning provided.')

            return recommendation_dict
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Warning: Could not parse JSON response. Error: {e}")
            print(f"Raw response was: {recommendation_str}")
            return default_response

# --- Functions from original strategy.py ---

def set_stop_loss_price(app):
    """
    Sets the stop-loss price based on the trading signal and fixed risk parameters.
    """  
    signal = app.signal
    last_value = app.last_value
    
    risk_management_target = 0.04
    stop_loss_multiplier = 1     

    order_price = last_value*(1-risk_management_target*stop_loss_multiplier)
        
    return order_price

def set_take_profit_price(app):
    """
    Sets the take-profit price based on the trading signal using fixed risk parameters.
    """
            
    signal = app.signal
    last_value = app.last_value
    
    risk_management_target = 0.04
    take_profit_multiplier = 1     

    order_price = last_value*(1+risk_management_target*take_profit_multiplier)
        
    return order_price

def prepare_base_df(historical_data, train_span=None):
    """
    Prepares a feature-engineered dataframe for model training.
    This function is intentionally emptied for AI_strategy.py as the multi-agent system
    does not rely on traditional feature engineering from historical data in this manner.
    """
    print("prepare_base_df in AI_strategy.py is empty and returns an empty DataFrame.")
    return pd.DataFrame(), []

def get_signal(app):
    """
    Generates a trading signal using the multi-agent system.
    """
    if not graph:
        print("Graph object not available. Exiting get_signal.")
        return 0, 0.0 # Return neutral signal and zero leverage

    # Use ASSET_NAME and EXCHANGE from app if available, otherwise use defaults
    asset_name = app.symbol
    exchange = app.exchange
    
    print(f'--- Running Multi-Agent System for {asset_name} ---')
    start_datetime = dt.datetime.now()

    # Initialize agents using the global configuration variables
    news_agent = NewsGathererAgent(graph, INITIAL_QUERIES, MAX_LOOPS, REASONING_MODEL)
    sentiment_agent = SentimentAnalyzerAgent(graph, INITIAL_QUERIES, MAX_LOOPS, REASONING_MODEL)
    market_data_fetcher = MarketDataFetcher()
    strategy_agent = TradingStrategyAgent(graph, INITIAL_QUERIES, MAX_LOOPS, REASONING_MODEL)

    # --- Execute the multi-step trading analysis ---
    news_summaries = news_agent.execute(asset_name, exchange)
    sentiment_score = sentiment_agent.execute(news_summaries)
    vix_index = market_data_fetcher.get_vix_index()
    final_recommendation = strategy_agent.execute(asset_name, sentiment_score, vix_index)

    action = final_recommendation.get('action')
    confidence = final_recommendation.get('confidence')
    reasoning = final_recommendation.get('reasoning')

    print(f"\n--- Final Recommendation for {asset_name} ---")
    print(f"Action: {action}")
    print(f"Confidence: {confidence}")
    print(f"Reasoning: {reasoning}")

    signal = 0 # Default to HOLD
    leverage = 0.0 # Default leverage

    if action == "BUY":
        signal = 1
        leverage = confidence
    else: # HOLD
        signal = 0
        leverage = 0.0

    print(f'AI Agents took the following time to complete all: {dt.datetime.now()-start_datetime}')
    
    return signal, leverage

# strategy_parameter_optimization function is simplified as it's not relevant for this AI-driven strategy.
def strategy_parameter_optimization():
    pass

