from agentic_AI_portfolio_manager import engine_loop

if __name__ == "__main__":
    # Define the risk management parameters. Set to None to disable.
    risk_specs = {
        "stop_loss": {"type": "percentage", "value": 0.02},  # 2% stop loss from entry
        "take_profit": {"type": "percentage", "value": 0.04} # 4% take profit from entry
    }
    
    # Call the engine_loop with the desired trading parameters.
    # Example for a trader in New York.
    engine_loop(
        tickers=["AAPL", "MSFT", "GOOG"],
        data_frequency="5min",
        num_observations=90,
        trader_timezone="America/Lima",
        news_lookback_minutes=10, # Look at news from the last 10 minutes
        num_web_links=10, # Use the top 5 web links for news analysis
        risk_management_specs=risk_specs
    )
