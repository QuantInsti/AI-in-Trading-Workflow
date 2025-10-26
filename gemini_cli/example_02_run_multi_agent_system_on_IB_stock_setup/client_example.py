import datetime as dt
import yfinance as yf
import json

# In a real deployment, you would have the 'graph' object from the LangGraph setup.
# This script is now structured to use it directly.
from langchain_core.messages import HumanMessage
from agent.graph import graph


# --- Script Configuration ---
# Set the parameters for the trading analysis here instead of using command-line arguments.
ASSET_NAME = 'TSLA'  # Asset symbol to research (e.g., 'AAPL', 'GOOG', 'TSLA')
EXCHANGE = 'NASDAQ'   # Exchange where the asset is traded (e.g., 'NASDAQ', 'NYSE')
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


def main():
    """Run the multi-agent system using the configuration set at the top of the file."""
    if not graph:
        print("Graph object not available. Exiting.")
        return
    
    start_datetime = dt.datetime.now()
    print(f'Start datetime is {start_datetime}')

    # Initialize agents using the global configuration variables
    news_agent = NewsGathererAgent(graph, INITIAL_QUERIES, MAX_LOOPS, REASONING_MODEL)
    sentiment_agent = SentimentAnalyzerAgent(graph, INITIAL_QUERIES, MAX_LOOPS, REASONING_MODEL)
    market_data_fetcher = MarketDataFetcher()
    strategy_agent = TradingStrategyAgent(graph, INITIAL_QUERIES, MAX_LOOPS, REASONING_MODEL)

    # --- Execute the multi-step trading analysis ---
    news_summaries = news_agent.execute(ASSET_NAME, EXCHANGE)
    sentiment_score = sentiment_agent.execute(news_summaries)
    vix_index = market_data_fetcher.get_vix_index()
    final_recommendation = strategy_agent.execute(ASSET_NAME, sentiment_score, vix_index)

    # --- Use the separated output variables ---
    action = final_recommendation.get('action')
    confidence = final_recommendation.get('confidence')
    reasoning = final_recommendation.get('reasoning')

    print(f"\n--- Final Recommendation for {ASSET_NAME} ---")
    print(f"Action: {action}")
    print(f"Confidence: {confidence}")
    print(f"Reasoning: {reasoning}")
    
    # You can now use these variables for any downstream logic,
    # such as placing an order or logging the decision.
    print("\n--- Example of Downstream Logic ---")
    if action == "BUY" and confidence > 0.50:
        print(f"Decision: High-confidence BUY signal detected for {ASSET_NAME}. Triggering order placement logic.")
    elif action == "SELL" and confidence > 0.50:
        print(f"Decision: High-confidence SELL signal detected for {ASSET_NAME}. Triggering order placement logic.")
    else:
        print(f"Decision: No high-confidence action for {ASSET_NAME}. Monitoring position.")

    print(f'End datetime is {dt.datetime.now()}')
    print(f'AI Agents took the following time to complete all: {dt.datetime.now()-start_datetime}')

if __name__ == "__main__":
    main()
