# --- Import necessary libraries ---
# os: For interacting with the operating system, used here to get environment variables.
import os
# smtplib: For sending emails using the Simple Mail Transfer Protocol.
import smtplib
# json: For working with JSON data, used here to format search results.
import json
# re: For regular expressions, used here to parse the data_frequency string.
import re
# pytz: For handling timezones to make the bot globally usable.
import pytz
# quantstats: For generating quantitative analytics and performance reports.
import numpy as np
import pyfolio as pf
# EmailMessage, MIMEApplication, MIMEMultipart: Classes for creating and managing email messages with attachments.
from email.message import EmailMessage
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
# TypedDict, List, Dict: For creating typed dictionaries and lists to define our state object clearly.
from typing import TypedDict, List, Dict, Optional
# load_dotenv: A function to load environment variables from a .env file.
from dotenv import load_dotenv
# datetime, timedelta: For working with dates and times, used to calculate data fetching periods.
from datetime import datetime, timedelta
# pandas: A powerful library for data manipulation and analysis.
import pandas as pd
# RandomForestClassifier: A machine learning model for classification tasks.
from sklearn.ensemble import RandomForestClassifier

# alpaca_trade_api: The official Python library for the Alpaca trading API.
import alpaca_trade_api as tradeapi
# TimeFrame, TimeFrameUnit: Enums from the Alpaca library to specify the data frequency.
from alpaca_trade_api.rest import TimeFrame, TimeFrameUnit

# ChatPromptTemplate: For creating structured prompts for the language model.
from langchain_core.prompts import ChatPromptTemplate
# ChatGoogleGenerativeAI: The LangChain integration for Google's Gemini models.
from langchain_google_genai import ChatGoogleGenerativeAI
# TavilySearchResults: The LangChain integration for the Tavily web search tool.
from langchain_tavily import TavilySearch
# StateGraph, END: Core components from LangGraph to build the state machine graph.
from langgraph.graph import StateGraph, END
import ta
import warnings
import matplotlib.pyplot as plt
import time
os.environ['MPLCONFIGDIR'] = os.getcwd() + "/configs/"


# --- 1. Load Environment Variables ---
# This line loads the variables from your .env file (e.g., API keys) into the environment.
load_dotenv()


def _describe_env_key(var_name: str) -> str:
    """Return a redacted description of an environment variable for debugging."""
    value = os.getenv(var_name)
    if not value:
        return "MISSING"
    tail = value[-4:]
    return f"set (len={len(value)}, endswith=***{tail})"

# --- 2. Define the Enhanced Graph State (with Timezone) ---
# This class defines the structure of our application's state.
# It's a dictionary that gets passed between all nodes in the graph.
class AgentState(TypedDict):
    # The list of stock tickers to be analyzed (e.g., ["AAPL", "MSFT"])
    tickers: List[str]
    # The frequency of the data to be fetched (e.g., "1D", "5Min")
    data_frequency: str
    # A dictionary holding the portfolio's state (cash, positions, history).
    portfolio: dict
    # A dictionary to store news search results, keyed by ticker.
    news_by_ticker: Dict[str, dict]
    # A dictionary to store the generated signals and market data for each ticker.
    signals_by_ticker: Dict[str, dict]
    # A dictionary to store the final portfolio weights, keyed by ticker.
    portfolio_weights: Dict[str, float]
    # The trader's local timezone string (e.g., "America/New_York").
    trader_timezone: str
    # The time window in minutes for news collection.
    news_lookback_minutes: int
    # The number of web links to use for news analysis.
    num_web_links: int
    # Optional dictionary for risk management specifications.
    risk_management_specs: Optional[dict]
    # A list of strings to log the actions and decisions taken by the agent.
    log: List[str]
    # A string to store the status of the final email notification.
    email_status: str

# --- 3. Create Tools and Helper Functions ---

# This function saves the current state of the portfolio to an Excel file.
def save_portfolio_state(portfolio: dict):
    """Saves the portfolio state to an Excel file with multiple sheets."""
    # Use pandas ExcelWriter to save multiple DataFrames to different sheets in one file.
    with pd.ExcelWriter("portfolio_state.xlsx", engine='openpyxl') as writer:
        # Save the current cash balance.
        pd.DataFrame([{"cash": portfolio.get("cash", 0)}]).to_excel(writer, sheet_name='Account', index=False)
        # Save the historical equity curve data.
        pd.DataFrame(portfolio.get("history", [])).to_excel(writer, sheet_name='EquityHistory', index=False)
        # Save a log of all submitted orders.
        pd.DataFrame(portfolio.get("orders", [])).to_excel(writer, sheet_name='Orders', index=False)
        # Save the current open positions.
        pd.DataFrame(portfolio.get("positions", [])).to_excel(writer, sheet_name='Positions', index=False)
        # Save a log of all trade executions.
        pd.DataFrame(portfolio.get("executions", [])).to_excel(writer, sheet_name='Executions', index=False)

# This function loads the portfolio state from the Excel file.
def load_portfolio_state() -> dict:
    """Loads the portfolio state from an Excel file."""
    # Check if the state file exists.
    if not os.path.exists("portfolio_state.xlsx"):
        # If not, return a default initial state.
        return {"cash": 100000, "history": [], "orders": [], "positions": [], "executions": []}
    
    # If the file exists, read each sheet into a pandas DataFrame.
    xls = pd.ExcelFile("portfolio_state.xlsx")
    # Construct the portfolio dictionary from the data in each sheet.
    portfolio = {
        "cash": pd.read_excel(xls, 'Account').iloc[0]['cash'],
        "history": pd.read_excel(xls, 'EquityHistory').to_dict('records'),
        "orders": pd.read_excel(xls, 'Orders').to_dict('records'),
        "positions": pd.read_excel(xls, 'Positions').to_dict('records'),
        "executions": pd.read_excel(xls, 'Executions').to_dict('records')
    }
    # Return the loaded portfolio state.
    return portfolio

# This function generates a detailed performance report.
def create_performance_report(portfolio_history: list, tickers: List[str]) -> str:
    """Generates a custom performance report using pyfolio metrics and matplotlib."""
    if not portfolio_history or len(portfolio_history) < 2:
        print("INFO: Not enough data to generate a performance report.")
        return None

    returns = pd.Series(
        [h['equity'] for h in portfolio_history],
        index=pd.to_datetime([h['timestamp'] for h in portfolio_history])
    ).pct_change().dropna()
    
    if returns.empty:
        print("INFO: Not enough data points to calculate returns. Skipping report.")
        return None

    # Ensure the index is timezone-naive for pyfolio compatibility
    returns.index = returns.index.tz_localize(None)

    report_path = f"performance_report_{'_'.join(tickers)}_{datetime.now().strftime('%Y%m%d')}.png"

    try:
        # --- 1. Calculate Metrics using Pyfolio ---
        perf_stats = pf.timeseries.perf_stats(returns)
        metrics_data = {
            "Annual return": f"{perf_stats.get('Annual return', 0):.2%}",
            "Cumulative returns": f"{perf_stats.get('Cumulative returns', 0):.2%}",
            "Annual volatility": f"{perf_stats.get('Annual volatility', 0):.2%}",
            "Sharpe ratio": f"{perf_stats.get('Sharpe ratio', 0):.2f}",
            "Max drawdown": f"{perf_stats.get('Max drawdown', 0):.2%}",
            "Calmar ratio": f"{perf_stats.get('Calmar ratio', 0):.2f}",
            "Sortino ratio": f"{perf_stats.get('Sortino ratio', 0):.2f}"
        }

        # --- 2. Create Plots and Table with Matplotlib ---
        fig = plt.figure(figsize=(12, 16))
        # Define a flexible grid: 2 plots, 1 table. If monthly plot is skipped, table takes its space.
        gs_rows = 3
        gs = fig.add_gridspec(gs_rows, 1, height_ratios=[2, 2, 1.5])

        # Ax 0: Cumulative Returns Plot
        ax0 = fig.add_subplot(gs[0])
        pf.plotting.plot_rolling_returns(returns, ax=ax0)
        ax0.set_title('Cumulative Returns', fontsize=14, fontweight='bold')
        ax0.tick_params(axis='x', labelrotation=0)

        # --- Conditional Monthly Returns Plot ---
        # Check if data spans more than one month
        if returns.index.to_period('M').nunique() > 1:
            ax1 = fig.add_subplot(gs[1])
            pf.plotting.plot_monthly_returns_heatmap(returns, ax=ax1)
            ax1.set_title('Monthly Returns (%)', fontsize=14, fontweight='bold')
            table_ax_index = 2 # Table goes in the third slot
        else:
            print("INFO: Data spans less than two months. Skipping monthly returns plot.")
            # If we skip the monthly plot, the table will take the second slot in a 2-row grid
            gs = fig.add_gridspec(2, 1, height_ratios=[2, 1.5])
            fig.axes[0].set_position(gs[0].get_position(fig)) # Reposition the first plot
            table_ax_index = 1

        # Ax for Table: Position is determined by the conditional logic above
        table_ax = fig.add_subplot(gs[table_ax_index])
        table_ax.axis('off') 
        table_ax.set_title('Performance Metrics', fontsize=14, fontweight='bold', y=0.8)

        # Create the table
        table_data = list(metrics_data.items())
        table = table_ax.table(
            cellText=table_data, 
            colLabels=["Metric", "Value"], 
            loc='center', 
            cellLoc='left',
            colWidths=[0.4, 0.3] # Adjust column widths
        )
        
        # Style the table for better rendering
        table.auto_set_font_size(False)
        table.set_fontsize(12)
        table.scale(1.1, 1.8) # Adjust cell height and width scaling
        
        # Style header
        for (i, j), cell in table.get_celld().items():
            if i == 0:
                cell.set_text_props(weight='bold', color='white')
                cell.set_facecolor('#40466e')
            if i > 0: # Style data cells
                cell.set_text_props(ha='left')

        # --- 3. Save and Finalize ---
        plt.tight_layout(pad=4.0, h_pad=5.0) # Add vertical padding
        fig.savefig(report_path, bbox_inches='tight')
        plt.close(fig)
        
        print(f"INFO: Custom performance report generated at {report_path}")
        return report_path

    except Exception as e:
        print(f"ERROR: Failed to generate custom performance report: {e}")
        if 'fig' in locals() and plt.fignum_exists(fig.number):
            plt.close(fig)
        return None

# This function checks the Alpaca API for the market schedule.
def get_market_schedule(num_days: int, trader_timezone: str) -> dict:
    """Gets the next N tradable days from the Alpaca API with open/close times."""
    # Print an informational message.
    print(f"INFO: Checking for the next {num_days} tradable days...")
    print(f"DEBUG: Trader timezone -> {trader_timezone}")
    print(
        "DEBUG: Alpaca credentials status -> ID {} | SECRET {}".format(
            _describe_env_key("APCA_API_KEY_ID"),
            _describe_env_key("APCA_API_SECRET_KEY")
        )
    )
    try:
        # Initialize the Alpaca API client.
        api = tradeapi.REST(os.getenv("APCA_API_KEY_ID"), os.getenv("APCA_API_SECRET_KEY"), base_url='https://paper-api.alpaca.markets')
        # Get today's date.
        today = datetime.now(pytz.timezone(trader_timezone)).date()
        # Set an end date for the calendar lookup, with a buffer.
        end_date = today + timedelta(days=num_days * 2)
        # Fetch the market calendar from Alpaca.
        calendar = api.get_calendar(start=today.isoformat(), end=end_date.isoformat())
        
        # Prepare timezone objects for conversion.
        ny_tz = pytz.timezone('America/New_York')
        user_tz = pytz.timezone(trader_timezone)
        
        # Create a dictionary to hold the market schedule.
        schedule = {}
        for day in calendar[:num_days]:
            # Combine the date with the open/close time strings.
            open_dt_str = f"{day.date.strftime('%Y-%m-%d')} {day.open}"
            close_dt_str = f"{day.date.strftime('%Y-%m-%d')} {day.close}"
            
            # Create timezone-aware datetime objects in the user's local timezone.
            open_dt = ny_tz.localize(datetime.strptime(open_dt_str, '%Y-%m-%d %H:%M:%S')).astimezone(user_tz)
            close_dt = ny_tz.localize(datetime.strptime(close_dt_str, '%Y-%m-%d %H:%M:%S')).astimezone(user_tz)
            
            # Store the open and close times in the schedule.
            schedule[day.date.date()] = {"open": open_dt, "close": close_dt}
            
        # Print the upcoming market schedule in a readable format.
        print("INFO: Upcoming market schedule (local time):")
        for date, times in schedule.items():
            open_time = times['open'].strftime('%I:%M %p')
            close_time = times['close'].strftime('%I:%M %p')
            print(f"  - {date.strftime('%A, %B %d, %Y')}: Open: {open_time}, Close: {close_time}")

        # Return the schedule.
        return schedule
    # Catch any exceptions during the API call.
    except Exception as e:
        # Print an error message.
        print(f"ERROR: Could not fetch calendar: {e}")
        print(f"DEBUG: Calendar exception type -> {type(e).__name__}")
        # Return an empty dictionary on failure.
        return {}

# This function fetches historical price data from Alpaca.
def fetch_historical_data(ticker: str, num_observations: int, data_frequency: str, trader_timezone: str) -> pd.DataFrame:
    """Fetches historical market data and returns a timezone-aware pandas DataFrame."""
    # Print an informational message.
    print(f"INFO: Fetching {num_observations} observations of {data_frequency} data for {ticker}...")
    try:
        # Initialize the Alpaca API client.
        api = tradeapi.REST(os.getenv("APCA_API_KEY_ID"), os.getenv("APCA_API_SECRET_KEY"), base_url='https://paper-api.alpaca.markets')
        # Use regex to parse the frequency string (e.g., "1D", "15Min").
        match = re.match(r"(\d+)(\w+)", data_frequency, re.IGNORECASE)
        # Extract the amount and unit, defaulting to 1 if not specified.
        amount, unit_str = (1, data_frequency) if not match else (int(match.groups()[0]), match.groups()[1])
        
        # Map the string unit to the Alpaca TimeFrameUnit enum.
        unit_map = {'min': TimeFrameUnit.Minute, 'h': TimeFrameUnit.Hour, 'd': TimeFrameUnit.Day}
        unit = next((u for s, u in unit_map.items() if s in unit_str.lower()), None)
        # Raise an error if the unit is invalid.
        if not unit: raise ValueError(f"Invalid time unit: {unit_str}")

        # Create the TimeFrame object required by the Alpaca API.
        timeframe = TimeFrame(amount, unit)
        # Get the current time in UTC to ensure a consistent reference point.
        today = datetime.now(pytz.utc)
        # Calculate a buffered number of observations to fetch to account for non-trading periods.
        buffered_obs = int(num_observations * 1.5)
        
        # Create a mapping to calculate the appropriate timedelta for the data fetch.
        delta_map = {TimeFrameUnit.Day: timedelta(days=buffered_obs), TimeFrameUnit.Hour: timedelta(hours=amount * buffered_obs), TimeFrameUnit.Minute: timedelta(minutes=amount * buffered_obs)}
        # Calculate the start date for the data fetch.
        start_date = today - delta_map[unit]
        
        # Call the Alpaca API to get the historical bars, with adjustment for splits and dividends.
        bars = api.get_bars(
            ticker, 
            timeframe,
            start=start_date.strftime('%Y-%m-%d'), 
            end=today.strftime('%Y-%m-%d'),
            adjustment='all', # This is the key change for adjusted data
            feed='iex' # Use IEX data feed for free stock data
        ).df
        
        # Convert the timestamp index from UTC to the trader's local timezone.
        # Then, remove the timezone information to make the datetime object "naive", which is easier for some libraries.
        bars.index = bars.index.tz_convert(trader_timezone).tz_localize(None)
        
        # Return only the requested number of recent observations.
        return bars.tail(num_observations)
    # Catch any exceptions.
    except Exception as e:
        # Print an error message.
        print(f"ERROR: Failed to fetch market data for {ticker}: {e}")
        # Return an empty DataFrame on failure.
        return pd.DataFrame()

# This function searches the web for news using Tavily within a specific time window.
def web_search_for_news(ticker: str, news_start_time: datetime, num_links: int) -> str:
    """Uses Tavily to search the web for recent financial news about a ticker since a given start time."""
    # Print an informational message.
    print(f"INFO: Searching web for {num_links} news links about {ticker} since {news_start_time.strftime('%Y-%m-%d %H:%M')}")
    try:
        # Initialize the Tavily search tool, now with a dynamic number of results.
        search_tool = TavilySearch(max_results=num_links, search_depth="advanced")
        # Modify the query to include the time constraint. This relies on the search engine's ability to understand time-based queries.
        query = f"latest financial news and analysis for {ticker} since {news_start_time.strftime('%Y-%m-%d %H:%M')}"
        # Invoke the tool with the specific query.
        results = search_tool.invoke(query)
        # Return the results as a JSON string.
        return json.dumps(results)
    # Catch any exceptions.
    except Exception as e:
        # Return an error message.
        return f"Failed to search for news: {e}"

# This function sends an email with an optional attachment.
def send_email_notification(subject: str, body: str, attachment_path: str = None):
    """Sends an email notification using Gmail, with an optional attachment."""
    try:
        # Get email credentials from environment variables.
        sender_email, app_password, recipient_email = (os.getenv(k) for k in ["SENDER_EMAIL", "GMAIL_APP_PASSWORD", "RECIPIENT_EMAIL"])
        # Check if all credentials are present.
        if not all([sender_email, app_password, recipient_email]): return "Email credentials not found."
        
        # Create a multipart message object.
        msg = MIMEMultipart()
        # Set the subject, from, and to fields.
        msg["Subject"], msg["From"], msg["To"] = subject, sender_email, recipient_email
        
        # Create the text body of the email.
        body_part = EmailMessage()
        body_part.set_content(body)
        # Attach the body to the main message.
        msg.attach(body_part)

        # Check if an attachment path is provided and if the file exists.
        if attachment_path and os.path.exists(attachment_path):
            # Open the file in binary read mode.
            with open(attachment_path, "rb") as f:
                # Create the attachment part.
                part = MIMEApplication(f.read(), Name=os.path.basename(attachment_path))
            # Add a header to make it an attachment.
            part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
            # Attach the file to the message.
            msg.attach(part)
        
        # Connect to Gmail's secure SMTP server.
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp_server:
            # Log in to the email account.
            smtp_server.login(sender_email, app_password)
            # Send the complete message.
            smtp_server.send_message(msg)
        # Return a success message.
        return "Email notification sent successfully."
    # Catch any exceptions.
    except Exception as e:
        # Return an error message.
        return f"Failed to send email: {e}"

# --- Define the Agent Nodes ---

# This node performs both qualitative and quantitative analysis for each stock.
def analysis_node(state: AgentState):
    """Gathers news and signals for each ticker individually."""
    # Get the list of tickers from the state.
    tickers = state["tickers"]
    # Get the trader's timezone from the state.
    trader_timezone = state["trader_timezone"]
    # Get the news time window from the state.
    news_lookback_minutes = state["news_lookback_minutes"]
    # Get the number of web links for news from the state.
    num_web_links = state["num_web_links"]
    # Get the log from the state.
    log = state.get("log", [])
    # Initialize dictionaries to hold results.
    news_by_ticker = {}
    signals_by_ticker = {}

    # Calculate the start time for the news search window.
    news_start_time = datetime.now(pytz.timezone(trader_timezone)) - timedelta(minutes=news_lookback_minutes)

    # Loop through each ticker to analyze it.
    for ticker in tickers:
        # Log the start of the analysis for the current ticker.
        log.append(f"--- Starting analysis for {ticker} ---")
        
        # Fetch historical data for the ticker.
        market_data = fetch_historical_data(ticker, num_observations=90, data_frequency=state["data_frequency"], trader_timezone=trader_timezone)
        # If data fetching fails, log it and skip to the next ticker.
        if market_data.empty:
            log.append(f"Analyst: Could not fetch market data for {ticker}. Skipping.")
            continue

        # --- Qualitative Analysis (Analyst Agent) ---
        # Search for news related to the ticker within the specified time window and link count.
        news = web_search_for_news(ticker, news_start_time, num_web_links)
        # Store the news results.
        news_by_ticker[ticker] = news
        # Initialize the Gemini LLM.
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0)
        
        # Create the prompt for the LLM to generate a signal from the news.
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a financial analyst. Based on the news, provide a signal (1 for BUY, 0 for HOLD). Respond with only the number."),
            ("human", "Ticker: {ticker}\nNews: {news}")
        ])
        # Create a LangChain chain.
        chain = prompt | llm
        # Invoke the chain with the news data.
        response = chain.invoke({"ticker": ticker, "news": news})
        
        # Try to parse the LLM's response as an integer.
        try:
            analyst_signal = int(response.content.strip())
        # If parsing fails, default to a HOLD signal.
        except ValueError:
            analyst_signal = 0
        
        # --- Quantitative Analysis (ML Agent) ---
        # Create a copy of the market data for manipulation.
        df = market_data.copy()
        # Check if there is enough data to create features.
        if not df.empty and len(df) >= 20:
            # Calculate technical indicators (SMA and RSI).
            df['SMA_14'] = ta.trend.sma_indicator(close=df['close'], window=14)
            df['RSI_14'] = ta.momentum.rsi(close=df['close'], window=14)
            # Create the target variable: 1 if the next day's close is higher, 0 otherwise.
            df['Target'] = (df['close'].shift(-1) > df['close']).astype(int)
            # Drop rows with missing values.
            df.dropna(inplace=True)
            
            # Check if there's still data after cleaning.
            if not df.empty:
                # Define features (X) and target (y).
                X = df[['SMA_14', 'RSI_14']]
                y = df['Target']
                # Initialize and train the Random Forest model.
                model = RandomForestClassifier(n_estimators=10, random_state=42)
                model.fit(X, y)
                # Get the most recent features to make a prediction.
                last_features = X.tail(1)
                # Predict the signal for the next period.
                ml_signal = int(model.predict(last_features)[0])
            # If no data remains, default to a HOLD signal.
            else:
                ml_signal = 0
        # If not enough initial data, default to a HOLD signal.
        else:
            ml_signal = 0

        # --- Trader's preliminary decision logic ---
        # The final signal is BUY only if the analyst (news) gives a BUY signal.
        final_signal = 1 if ((analyst_signal == 1) and (ml_signal == 1)) else 0
        
        # Store the results for this ticker.
        signals_by_ticker[ticker] = {
            "signal": final_signal,
            "market_data": market_data
        }
        # Log the preliminary decision.
        log.append(f"Preliminary decision for {ticker}: Signal={final_signal}")

    # Return the updated state.
    return {"log": log, "news_by_ticker": news_by_ticker, "signals_by_ticker": signals_by_ticker}

# This node determines the capital allocation for the portfolio.
def portfolio_agent_node(state: AgentState):
    """Determines portfolio weights based on news and signals."""
    # Get data from the state.
    log = state.get("log", [])
    news_by_ticker = state["news_by_ticker"]
    signals_by_ticker = state["signals_by_ticker"]
    # Get a list of tickers that have a BUY signal.
    tickers_with_buy_signal = [t for t, data in signals_by_ticker.items() if data["signal"] == 1]

    # Initialize weights for all tickers to zero.
    portfolio_weights = {ticker: 0.0 for ticker in state["tickers"]}

    # If no tickers have a BUY signal, do nothing.
    if not tickers_with_buy_signal:
        log.append("Portfolio Agent: No BUY signals. Allocating 0% to all tickers.")
        return {"log": log, "portfolio_weights": portfolio_weights}

    # Log the tickers that will be considered for allocation.
    log.append(f"Portfolio Agent: Allocating capital across: {tickers_with_buy_signal}")
    # Initialize the Gemini LLM for portfolio allocation.
    llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.5)
    
    # Create the prompt for the LLM to decide on weights.
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a portfolio manager. Based on the provided news summaries for several stocks, allocate portfolio weights. The stocks to allocate are: {tickers}. The weights must sum to 1.0. Respond with a JSON object where keys are ticker symbols and values are their weights (e.g., {{'AAPL': 0.6, 'MSFT': 0.4}})."),
        ("human", "News Summaries:\n{news}")
    ])
    # Create the LangChain chain.
    chain = prompt | llm
    
    # Format the news summaries for the LLM prompt.
    formatted_news = "\n\n".join([f"--- {ticker} ---\n{news_summary}" for ticker, news_summary in news_by_ticker.items() if ticker in tickers_with_buy_signal])
    
    # Invoke the chain to get the portfolio weights.
    response = chain.invoke({"tickers": ", ".join(tickers_with_buy_signal), "news": formatted_news})
    
    # Try to parse the JSON response from the LLM.
    try:
        weights = json.loads(response.content.strip())
        # Apply the weights, scaling them to 99% of the portfolio.
        for ticker, weight in weights.items():
            if ticker in portfolio_weights:
                portfolio_weights[ticker] = weight * 0.99
        log.append(f"Portfolio Agent: Assigned weights: {portfolio_weights}")
    # If parsing fails, fall back to an equal allocation strategy.
    except (json.JSONDecodeError, TypeError):
        log.append("Portfolio Agent: Failed to parse weights from LLM. Allocating equally.")
        equal_weight = 0.99 / len(tickers_with_buy_signal)
        for ticker in tickers_with_buy_signal:
            portfolio_weights[ticker] = equal_weight
            
    # Return the updated state with the new portfolio weights.
    return {"log": log, "portfolio_weights": portfolio_weights}

# This node executes the trades in the brokerage account.
def execution_node(state: AgentState):
    """Executes trades based on final signals, portfolio weights, and risk management specs."""
    # Get data from the state.
    log = state.get("log", [])
    portfolio = state["portfolio"]
    portfolio_weights = state["portfolio_weights"]
    trader_timezone = state["trader_timezone"]
    risk_management_specs = state.get("risk_management_specs") # Get optional RM specs
    signals_by_ticker = state["signals_by_ticker"]

    # Log the start of the execution phase.
    log.append("Execution Agent: Submitting real trades based on portfolio plan.")
    
    # Initialize the Alpaca API client.
    api = tradeapi.REST(os.getenv("APCA_API_KEY_ID"), os.getenv("APCA_API_SECRET_KEY"), base_url='https://paper-api.alpaca.markets')
    
    try:
        # Get the real-time cash balance from the account.
        account = api.get_account()
        initial_cash = float(account.cash)
        log.append(f"Execution: Fetched cash balance: ${initial_cash:.2f}")

        # First, submit an order to liquidate all existing positions to rebalance the portfolio.
        api.close_all_positions()
        log.append("Execution: Submitted orders to liquidate all existing positions.")

        # Second, submit new BUY orders based on the calculated portfolio weights.
        submitted_orders = []
        for ticker, weight in portfolio_weights.items():
            # Only place trades for stocks with a weight greater than zero.
            if weight > 0:
                # Calculate the dollar amount to invest in this ticker.
                investment_amount = initial_cash * weight
                
                # --- Prepare Order Parameters ---
                order_params = {
                    "symbol": ticker,
                    "notional": investment_amount,
                    "side": 'buy',
                    "type": 'market',
                    "time_in_force": 'day'
                }

                # --- Add Risk Management if specified ---
                if risk_management_specs:
                    # Use the last known price as an estimate for calculating SL/TP levels.
                    last_price = signals_by_ticker[ticker]["market_data"]['close'].iloc[-1]
                    
                    # Set order_class to 'bracket' for SL/TP orders.
                    order_params["order_class"] = 'bracket'
                    
                    # Calculate and add Take Profit parameter.
                    if 'take_profit' in risk_management_specs:
                        tp_spec = risk_management_specs['take_profit']
                        if tp_spec.get('type') == 'percentage':
                            tp_price = last_price * (1 + tp_spec['value'])
                            order_params['take_profit'] = {'limit_price': round(tp_price, 2)}
                            log.append(f"  - Attaching Take Profit at ${tp_price:.2f}")

                    # Calculate and add Stop Loss parameter.
                    if 'stop_loss' in risk_management_specs:
                        sl_spec = risk_management_specs['stop_loss']
                        if sl_spec.get('type') == 'percentage':
                            sl_price = last_price * (1 - sl_spec['value'])
                            order_params['stop_loss'] = {'stop_price': round(sl_price, 2)}
                            log.append(f"  - Attaching Stop Loss at ${sl_price:.2f}")
                
                # Submit the order with or without risk management parameters.
                order = api.submit_order(**order_params)
                
                # Add the submitted order object to a list for logging.
                submitted_orders.append(order)
                log.append(f"Execution: Submitted market order for ${investment_amount:.2f} of {ticker}.")
        
        # Update the portfolio state with the details of the submitted orders.
        for order in submitted_orders:
            portfolio["orders"].append({
                "id": order.id,
                "symbol": order.symbol,
                "qty": order.qty,
                "side": order.side,
                "type": order.type,
                "status": order.status,
                "submitted_at": pd.to_datetime(order.submitted_at).tz_convert(trader_timezone).isoformat()
            })

        # Update the portfolio history with the new real equity value from the account.
        updated_account = api.get_account()
        portfolio['account_summary'] = {
            "equity": float(updated_account.equity),
            "cash": float(updated_account.cash),
            "buying_power": float(updated_account.buying_power),
            "long_market_value": float(updated_account.long_market_value),
            "short_market_value": float(updated_account.short_market_value),
        }
        final_equity = portfolio['account_summary']['equity']
        local_now = datetime.now(pytz.timezone(trader_timezone))
        portfolio["history"].append({"timestamp": local_now.isoformat(), "equity": final_equity})
        
        # Get the list of current positions from the account.
        positions = api.list_positions()
        # Update the portfolio state with the new positions.
        portfolio["positions"] = [{"symbol": p.symbol, "qty": p.qty, "market_value": p.market_value} for p in positions]

        # For simplicity, we'll assume executions happen instantly for this log.
        # A more robust solution would use webhooks to get execution updates from the broker.
        portfolio["executions"] = portfolio["orders"]
        
    # Catch any exceptions during the execution phase.
    except Exception as e:
        log.append(f"ERROR in execution node: {e}")

    # Return the updated state.
    return {"log": log, "portfolio": portfolio}


# This node sends the final email report.
def email_notification_node(state: AgentState):
    """Prepares and sends the final email notification with performance report or account summary."""
    log = state.get("log", [])
    report_path = create_performance_report(state["portfolio"]["history"], state["tickers"])
    
    subject = f"Daily Trading Report for {datetime.now().strftime('%Y-%m-%d')}"
    
    # --- Create Email Body ---
    body = "Agentic system daily summary:\n\n"
    body += "--- Final Portfolio Weights ---" + "\n".join([f"{t}: {w:.2%}" for t, w in state["portfolio_weights"].items()]) + "\n\n"

    # If the report was not generated, include the account summary instead.
    if report_path is None:
        summary = state["portfolio"].get("account_summary", {})
        if summary:
            body += "--- Account Summary ---"
            body += f"Equity: ${summary.get('equity', 0):,.2f}\n"
            body += f"Cash: ${summary.get('cash', 0):,.2f}\n"
            body += f"Buying Power: ${summary.get('buying_power', 0):,.2f}\n"
            body += f"Long Market Value: ${summary.get('long_market_value', 0):,.2f}\n"
            body += f"Short Market Value: ${summary.get('short_market_value', 0):,.2f}\n\n"
    
    body += "--- Log ---" + "\n".join(log)
    
    # --- Send Email ---
    email_status = send_email_notification(subject, body, report_path)
    log.append(f"Notification: {email_status}")
    
    return {"log": log, "email_status": email_status}

# --- 5. Construct the Graph ---
# Initialize a new StateGraph with our AgentState structure.
workflow = StateGraph(AgentState)
# Add the functions as nodes in the graph.
workflow.add_node("analysis", analysis_node)
workflow.add_node("portfolio_allocator", portfolio_agent_node)
workflow.add_node("executor", execution_node)
workflow.add_node("email_notifier", email_notification_node)

# Set the entry point of the graph, which is the first node to be called.
workflow.set_entry_point("analysis")
# Define the sequence of operations by connecting the nodes with edges.
workflow.add_edge("analysis", "portfolio_allocator")
workflow.add_edge("portfolio_allocator", "executor")
workflow.add_edge("executor", "email_notifier")
# The final node connects to END, which signifies the end of the graph's execution.
workflow.add_edge("email_notifier", END)
# Compile the graph into a runnable application.
app = workflow.compile()

def format_seconds(seconds: float) -> str:
    """Converts seconds into a human-readable string (days, hours, minutes)."""
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds} second(s)"
    
    minutes, seconds = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes} minute(s)" if seconds == 0 else f"{minutes} minute(s) and {seconds} second(s)"
        
    hours, minutes = divmod(minutes, 60)
    if hours < 24:
        return f"{hours} hour(s)" if minutes == 0 else f"{hours} hour(s) and {minutes} minute(s)"
        
    days, hours = divmod(hours, 24)
    return f"{days} day(s)" if hours == 0 else f"{days} day(s) and {hours} hour(s)"

def parse_frequency_to_seconds(frequency: str) -> int:
    """Parses a frequency string (e.g., '5min', '1H', '1D') into seconds."""
    match = re.match(r"(\d+)(\w+)", frequency, re.IGNORECASE)
    if not match:
        raise ValueError(f"Invalid frequency format: {frequency}")
    
    amount, unit_str = int(match.groups()[0]), match.groups()[1].lower()
    
    if 'min' in unit_str:
        return amount * 60
    elif 'h' in unit_str:
        return amount * 3600
    elif 'd' in unit_str:
        return amount * 86400
    else:
        raise ValueError(f"Unsupported time unit in frequency: {unit_str}")

# --- 6. Create the Engine Loop and Run the System ---
# This function contains the main loop that runs the trading agent daily.
def engine_loop(tickers: List[str], data_frequency: str, num_observations: int, trader_timezone: str, news_lookback_minutes: int, num_web_links: int, risk_management_specs: Optional[dict] = None):
    """Main engine loop to run the agent continuously, waiting for market open."""
    
    while True:
        try:
            # Get schedule for the next 5 business days to handle weekends/holidays
            market_schedule = get_market_schedule(5, trader_timezone)
            local_tz = pytz.timezone(trader_timezone)
            local_now = datetime.now(local_tz)
            today = local_now.date()

            # Find the next market open time from the schedule
            next_market_open = None
            next_trading_day = None
            sorted_days = sorted(market_schedule.keys())
            
            for day in sorted_days:
                # Check for a trading day that is today or in the future
                if day >= today:
                    # If the market is already closed for today, skip to the next day
                    if day == today and local_now >= market_schedule[day]['close']:
                        continue
                    next_market_open = market_schedule[day]['open']
                    next_trading_day = day
                    break
            
            # If no upcoming market day is found, wait a full day and retry
            if not next_market_open:
                print("No upcoming trading day found in the schedule. Waiting for 1 day to check again...")
                print(f"DEBUG: market_schedule keys seen -> {sorted_days}")
                time.sleep(86400)
                continue

            # --- Wait until the next market open ---
            if local_now < next_market_open:
                wait_seconds = (next_market_open - local_now).total_seconds()
                print(f"Next market open is on {next_trading_day.strftime('%A, %B %d')} at {next_market_open.strftime('%H:%M:%S')}. Waiting for {format_seconds(wait_seconds)}...")
                print(f"DEBUG: Sleeping {wait_seconds:.0f} seconds awaiting market open")
                time.sleep(wait_seconds)

            # --- Main Trading Loop for the Day ---
            # At this point, the market is confirmed to be open
            market_close_time = market_schedule[next_trading_day]['close']
            print(f"\n--- Market is OPEN. Starting trading loop for {next_trading_day.isoformat()} until {market_close_time.strftime('%H:%M:%S')} ---")

            while datetime.now(local_tz) < market_close_time:
                print(f"\n--- Running Engine Iteration at {datetime.now(local_tz).strftime('%H:%M:%S')} ---")
                portfolio = load_portfolio_state()
                
                initial_state = {
                    "tickers": tickers,
                    "data_frequency": data_frequency,
                    "portfolio": portfolio,
                    "trader_timezone": trader_timezone,
                    "news_lookback_minutes": news_lookback_minutes,
                    "num_web_links": num_web_links,
                    "risk_management_specs": risk_management_specs,
                    "log": []
                }
                
                final_state = app.invoke(initial_state)
                save_portfolio_state(final_state["portfolio"])

                print("--- Iteration Complete ---")
                print(f"Email Status: {final_state.get('email_status')}")
                print("\n--- Execution Log ---")
                for entry in final_state.get('log', []):
                    print(entry)
                print("---------------------\n")

                # For daily frequency, break after one run.
                if 'd' in data_frequency.lower():
                    print("Daily frequency selected. Concluding trading for the day.")
                    break 
                
                # Wait for the specified interval before the next run.
                sleep_duration = parse_frequency_to_seconds(data_frequency)
                print(f"Waiting for {format_seconds(sleep_duration)} until the next run...")
                print(f"DEBUG: Sleeping {sleep_duration} seconds between iterations")
                time.sleep(sleep_duration)

            # --- End of Day ---
            print(f"Market closed at {market_close_time.strftime('%H:%M:%S')}. Preparing for the next trading session.")
            # The main loop will now restart and calculate the wait time to the next open.

        except Exception as e:
            print(f"An unexpected error occurred in the engine loop: {e}")
            print("Restarting the loop in 60 seconds...")
            time.sleep(60)
