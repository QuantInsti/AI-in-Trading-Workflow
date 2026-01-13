import datetime as dt
import yfinance as yf
import json
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

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
REASONING_MODEL = "gemini-2.0-flash" # Update this model as per Google's available models
previous_period = dt.datetime.now() - dt.timedelta(minutes=3)


# --- Dynamic Prompt Generation ---
# Prompts are now functions to incorporate runtime arguments.

def get_news_gathering_prompt(asset_name, exchange, previous_period):
    """Generates the prompt for the news gathering agent."""
    return (
        f"Research the latest news from {previous_period} to now only. "
        f"Focus on news related to the asset '{asset_name}' on the {exchange} exchange. "
        "For each news article, provide the title and the author. If the author is not available, state 'Author: N/A'. "
        "Search for news relevant to forming an opinion on how bearish or bullish the asset is."
    )

def get_sentiment_analysis_prompt(news_summaries):
    """Generates the prompt for the sentiment analysis agent."""
    return (
        f"Based on the following news (including titles, authors, and summaries), provide a sentiment score from -1 (very bearish) to +1 (very bullish). "
        f"Focus on the summary to determine the sentiment. Ignore any links or URLs in the text. Output only the numerical score. For example, if the sentiment is neutral, you should output `0.0`. Remember, the score must be between -1.0 and 1.0. The news is:\n\n{news_summaries}"
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
        f"Sentiment Score: {sentiment_score:.2f}\n"
        f"Volatility Index (VIX): {volatility_index:.2f}"
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
            # Use regex to find the first floating point number in the string
            import re
            match = re.search(r"[-+]?\d*\.\d+|\d+", sentiment_score_str)
            if match:
                sentiment_score = float(match.group())
                # Normalize sentiment score if it's outside the -1 to +1 range, assuming a 0-100 scale
                if sentiment_score > 1.0 or sentiment_score < -1.0:
                    if sentiment_score >= 0 and sentiment_score <= 100:
                        # Assuming a 0-100 scale, convert to -1 to +1
                        sentiment_score = (sentiment_score / 50.0) - 1.0
                    else:
                        print(f"Warning: Sentiment score {sentiment_score} is outside expected -1 to +1 range and not a 0-100 scale. Defaulting to 0.0.")
                        sentiment_score = 0.0

                print(f"Sentiment Score: {sentiment_score}")
                return sentiment_score
            else:
                print(f"Warning: Could not parse sentiment score from '{sentiment_score_str}'. Defaulting to 0.0.")
                return 0.0
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


def generate_markdown_report(asset_name, exchange, final_recommendation, news_summaries, sentiment_score, vix_index):
    """Generates a Markdown report summarizing the agent's analysis."""
    
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    md_file_name = f"{asset_name}_trading_report_{timestamp}.md"
    pdf_file_name = f"{asset_name}_trading_report_{timestamp}.pdf"

    # --- Construct Markdown Content ---
    report_content = f"# Trading Analysis Report: {asset_name}\n\n"
    report_content += f"**Report Generated:** {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    report_content += "## Executive Summary\n"
    summary_text = (
        f"The multi-agent system recommends a '{final_recommendation.get('action', 'N/A')}' "
        f"action for {asset_name} with a confidence score of {final_recommendation.get('confidence', 0.0):.2f}. "
        f"Reasoning: {final_recommendation.get('reasoning', 'No reasoning provided.')}"
    )
    report_content += f"{summary_text}\n\n"

    report_content += "## Input Parameters\n"
    report_content += f"**Asset:** {asset_name}\n"
    report_content += f"**Exchange:** {exchange}\n"
    report_content += f"**Sentiment Score:** {sentiment_score:.2f}\n"
    report_content += f"**Volatility Index (VIX):** {vix_index:.2f}\n\n"

    report_content += "## Agent Contributions (Chain of Thought)\n"
    
    report_content += "### 1. News Gatherer Agent\n"
    report_content += "**Summary of Findings:**\n"
    report_content += f"{news_summaries}\n\n"

    report_content += "### 2. Sentiment Analyzer Agent\n"
    report_content += f"**Sentiment Score:** {sentiment_score:.2f}\n\n"

    report_content += "### 3. Market Data Fetcher\n"
    report_content += f"**Latest VIX Close:** {vix_index:.2f}\n\n"

    report_content += "### 4. Trading Strategy Agent\n"
    report_content += "**Final Recommendation:**\n"
    report_content += f"**Action:** {final_recommendation.get('action', 'N/A')}\n"
    report_content += f"**Confidence:** {final_recommendation.get('confidence', 0.0):.2f}\n"
    report_content += f"**Reasoning:** {final_recommendation.get('reasoning', 'N/A')}\n\n"

    report_content += "---\n"
    report_content += "## Disclaimer\n"
    disclaimer_text = (
        "This report is generated by an AI-driven multi-agent system and is for informational purposes only. "
        "It is not financial advice. Trading financial markets involves substantial risk. "
        "Always conduct your own research and risk assessment before making any investment decisions."
    )
    report_content += f"{disclaimer_text}\n"

    with open(md_file_name, 'w') as f:
        f.write(report_content)
        
    print(f"\n--- Markdown Report Generated ---")
    print(f"Successfully saved trading analysis to '{md_file_name}'")
    
    return md_file_name, pdf_file_name


def generate_pdf_from_cleaned_content(pdf_file_name, content):
    """Generates a PDF report from cleaned markdown content."""
    import re
    
    doc = SimpleDocTemplate(pdf_file_name, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    lines = content.split('\n')
    for line in lines:
        # BOLD conversion
        line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)

        if line.startswith('# '):
            story.append(Paragraph(line[2:], styles['h1']))
        elif line.startswith('## '):
            story.append(Paragraph(line[3:], styles['h2']))
        elif line.startswith('### '):
            story.append(Paragraph(line[4:], styles['h3']))
        elif line.strip() == '---':
            story.append(PageBreak())
        else:
            story.append(Paragraph(line, styles['BodyText']))
        story.append(Spacer(1, 0.1*inch))

    doc.build(story)
    print(f"\n--- PDF Report Generated ---")
    print(f"Successfully saved trading analysis to '{pdf_file_name}'")


def remove_links(text):
    """Removes markdown-style links and raw URLs from a string."""
    import re
    # Replace markdown links, allowing whitespace/newlines between parts.
    text = re.sub(r'\[([^\]]+)\]\s*\((.*?)\)', r'\1', text, flags=re.DOTALL)
    # Remove bare URLs that may remain after model-generated line wrapping.
    text = re.sub(r'https?://\S+', '', text)
    return text

def clean_news_summaries(news_summaries_text):
    """Removes specific conversational messages from news summaries."""
    import re
    # Regex to match the specific sentence about missing titles and authors
    pattern = r"Titles and Authors:Unfortunately, the summaries provided do not consistently include the titles and authors of the news\narticles. Where available, the source is cited\." 
    cleaned_text = re.sub(pattern, "", news_summaries_text, flags=re.IGNORECASE)
    return cleaned_text.strip()

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
    news_summaries = clean_news_summaries(news_summaries)
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
    
    # --- Generate and save the PDF report ---
    if vix_index is not None and sentiment_score is not None:
        md_file, pdf_file = generate_markdown_report(ASSET_NAME, EXCHANGE, final_recommendation, news_summaries, sentiment_score, vix_index)
        
        with open(md_file, 'r') as f:
            content = f.read()
            
        cleaned_content = remove_links(content)
        
        generate_pdf_from_cleaned_content(pdf_file, cleaned_content)
        
        os.remove(md_file)

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
