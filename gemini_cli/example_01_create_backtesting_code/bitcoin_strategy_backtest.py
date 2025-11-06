import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from fpdf import FPDF
import itertools
from tqdm import tqdm
import os
import sys
import datetime as dt

# 1. Data Download
ticker = 'BTC-USD'
start_date = '2014-01-01'
end_date = dt.datetime.now().date().strftime('%Y-%m-%d')

# Ensure the ticker is valid and the date range is appropriate
if not ticker or not isinstance(start_date, str) or not isinstance(end_date, str):
    raise ValueError("Invalid ticker or date range provided.")
if start_date >= end_date:
    raise ValueError("Start date must be earlier than end date.")

# Download historical data
try:
    data = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=False, group_by='tickers')[ticker]
    if data.empty:
        raise ValueError('No data downloaded. Check ticker or date range.')
    data['Returns'] = data['Adj Close'].pct_change()
    print(f'Data downloaded successfully for {ticker}')
    print('Data from:', data.index.min().date(), 'to', data.index.max().date())
    print(data.head())
except Exception as e:
    print(f'Error downloading data: {e}')
    sys.exit(1)

# 2. Strategy Optimization (90% of data)
# Calculate the split point for 90% of the data
split_point = int(len(data) * 0.9)
optimization_data = data.iloc[:split_point].copy()
short_windows = range(3, 21)
long_windows = range(5, 31)

# Ensure long window is always greater than short window
param_grid = [(s, l) for s in short_windows for l in long_windows if l > s]
print(f'{len(param_grid)} parameter combinations to test.')

def calculate_sortino_ratio(returns, risk_free_rate=0):
    target_return = 0
    downside_returns = returns[returns < target_return].dropna()
    if len(downside_returns) == 0:
        return 0.0
    
    expected_return = returns.mean()
    downside_std = downside_returns.std()
    
    if downside_std == 0:
        return np.inf if expected_return > risk_free_rate else 0.0
        
    # Annualize
    sortino_ratio = (expected_return * 252 - risk_free_rate) / (downside_std * np.sqrt(252))
    return sortino_ratio

def run_optimization_backtest(data, short_window, long_window):
    df = data.copy()
    df['short_mavg'] = df['Adj Close'].rolling(window=short_window).mean()
    df['long_mavg'] = df['Adj Close'].rolling(window=long_window).mean()
    df.dropna(inplace=True)

    df['signal'] = 0
    df['signal'] = np.where(df['short_mavg'] > df['long_mavg'], 1, 0)
    df['position'] = df['signal'].diff()

    # This is a simplified backtest for optimization speed, not event-driven
    strategy_returns = df['position'].shift(1) * df['Returns']
    return strategy_returns

results = []
for short_window, long_window in tqdm(param_grid, desc="Optimizing..."):
    strategy_returns = run_optimization_backtest(optimization_data, short_window, long_window)
    sortino = calculate_sortino_ratio(strategy_returns)
    results.append({
        'short_window': short_window,
        'long_window': long_window,
        'sortino_ratio': sortino
    })

results_df = pd.DataFrame(results)
best_params = results_df.loc[results_df['sortino_ratio'].idxmax()]
print("Best Parameters Found:")
print(best_params)

# 3. Event-Driven Backtest (10% of data)
backtest_data = data.iloc[split_point:].copy()
short_window = int(best_params['short_window'])
long_window = int(best_params['long_window'])
stop_loss_pct = 0.02
take_profit_pct = 0.04

# Add MAs to backtest data, ensuring enough prior data is included for calculation
ma_context_data = data.loc[data.index < backtest_data.index[0]].tail(long_window - 1)
full_backtest_data = pd.concat([ma_context_data, backtest_data])
full_backtest_data['short_mavg'] = full_backtest_data['Adj Close'].rolling(window=short_window).mean()
full_backtest_data['long_mavg'] = full_backtest_data['Adj Close'].rolling(window=long_window).mean()
backtest_data_with_ma = full_backtest_data.loc[backtest_data.index]

if backtest_data_with_ma.isnull().values.any():
    print('Warning: NaNs present in moving averages. Backtest may be inaccurate.')
    backtest_data_with_ma.dropna(inplace=True)

portfolio = {'cash': 100000, 'position_size': 0, 'entry_price': 0}
equity_curve = []
trades = []
position = 'out' # 'in' or 'out'

for i in range(1, len(backtest_data_with_ma)):
    current_price = backtest_data_with_ma['Adj Close'].iloc[i]
    date = backtest_data_with_ma.index[i]

    # Check for stop loss or take profit
    if position == 'in':
        pnl = (current_price - portfolio['entry_price']) / portfolio['entry_price']
        if pnl <= -stop_loss_pct or pnl >= take_profit_pct:
            portfolio['cash'] += portfolio['position_size'] * current_price
            trades.append({'date': date, 'type': 'sell', 'price': current_price, 'pnl': pnl})
            position = 'out'
            portfolio['position_size'] = 0

    # Check for entry signal (Golden Cross)
    if position == 'out':
        if backtest_data_with_ma['short_mavg'].iloc[i-1] < backtest_data_with_ma['long_mavg'].iloc[i-1] and \
           backtest_data_with_ma['short_mavg'].iloc[i] > backtest_data_with_ma['long_mavg'].iloc[i]:
            portfolio['position_size'] = portfolio['cash'] / current_price
            portfolio['entry_price'] = current_price
            portfolio['cash'] = 0
            position = 'in'
            trades.append({'date': date, 'type': 'buy', 'price': current_price, 'pnl': np.nan})

    # Check for exit signal (Death Cross)
    elif position == 'in':
        if backtest_data_with_ma['short_mavg'].iloc[i-1] > backtest_data_with_ma['long_mavg'].iloc[i-1] and \
           backtest_data_with_ma['short_mavg'].iloc[i] < backtest_data_with_ma['long_mavg'].iloc[i]:
            portfolio['cash'] += portfolio['position_size'] * current_price
            pnl = (current_price - portfolio['entry_price']) / portfolio['entry_price']
            trades.append({'date': date, 'type': 'sell', 'price': current_price, 'pnl': pnl})
            position = 'out'
            portfolio['position_size'] = 0

    # Update equity
    current_equity = portfolio['cash'] + portfolio['position_size'] * current_price
    equity_curve.append({'date': date, 'equity': current_equity})

equity_df = pd.DataFrame(equity_curve).set_index('date')
trades_df = pd.DataFrame(trades).set_index('date') if trades else pd.DataFrame(columns=['type', 'price', 'pnl'])

print("Backtest Complete. Final Equity:", equity_df['equity'].iloc[-1])

# --- Buy-and-hold equity curve calculation ---
# Use the same initial value as the strategy
initial_value = equity_df['equity'].iloc[0]
# Align buy-and-hold to the same dates as the strategy equity curve
buyhold_prices = backtest_data_with_ma.loc[equity_df.index, 'Adj Close']
buyhold_equity = initial_value * (buyhold_prices / buyhold_prices.iloc[0])
equity_df['buyhold_equity'] = buyhold_equity

# 4. Results Analysis and PDF Report
# Calculate Metrics
total_return = (equity_df['equity'].iloc[-1] / equity_df['equity'].iloc[0]) - 1
equity_df['returns'] = equity_df['equity'].pct_change()
sharpe_ratio = (equity_df['returns'].mean() * np.sqrt(252)) / equity_df['returns'].std() if equity_df['returns'].std() != 0 else 0
sortino_ratio_final = calculate_sortino_ratio(equity_df['returns'])

# Max Drawdown
equity_df['peak'] = equity_df['equity'].cummax()
equity_df['drawdown'] = (equity_df['equity'] - equity_df['peak']) / equity_df['peak']
max_drawdown = equity_df['drawdown'].min()

# Win Rate
sell_trades = trades_df[trades_df['type'] == 'sell']
wins = sell_trades[sell_trades['pnl'] > 0]
win_rate = len(wins) / len(sell_trades) if len(sell_trades) > 0 else 0

metrics = {
    "Total Return": f"{total_return:.2%}",
    "Sharpe Ratio": f"{sharpe_ratio:.2f}",
    "Sortino Ratio": f"{sortino_ratio_final:.2f}",
    "Max Drawdown": f"{max_drawdown:.2%}",
    "Win Rate": f"{win_rate:.2%}",
    "Total Trades": len(sell_trades)
}

backtest_start_date = backtest_data.index.min().date()
backtest_end_date = backtest_data.index.max().date()
backtest_period_str = f"{backtest_start_date} to {backtest_end_date}"

metrics_df = pd.DataFrame([metrics])
print(f"Backtest Metrics ({backtest_period_str}):")
print(metrics_df.to_string())

# Plot Equity Curve (with Buy-and-Hold)
plt.style.use('seaborn-v0_8-darkgrid')
fig, ax1 = plt.subplots(figsize=(12, 6))
ax1.plot(equity_df.index, equity_df['equity'], label='Strategy Equity', color='blue')
ax1.plot(equity_df.index, equity_df['buyhold_equity'], label='Buy & Hold', color='orange', linestyle='--')
ax1.set_title(f'Equity Curve ({backtest_period_str})')
ax1.set_xlabel('Date')
ax1.set_ylabel('Portfolio Value ($)')

# Overlay trades
buy_signals = trades_df[trades_df['type']=='buy']
sell_signals = trades_df[trades_df['type']=='sell']
ax1.plot(buy_signals.index, equity_df.loc[buy_signals.index]['equity'], '^', markersize=10, color='g', label='Buy Signal')
ax1.plot(sell_signals.index, equity_df.loc[sell_signals.index]['equity'], 'v', markersize=10, color='r', label='Sell Signal')
ax1.legend()
equity_curve_path = 'equity_curve.png'
plt.savefig(equity_curve_path)
# plt.show()

# Plot Drawdown
fig, ax2 = plt.subplots(figsize=(12, 6))
ax2.plot(equity_df.index, equity_df['drawdown']*100, label='Drawdown', color='red')
ax2.fill_between(equity_df.index, equity_df['drawdown']*100, 0, color='red', alpha=0.3)
ax2.set_title(f'Portfolio Drawdown ({backtest_period_str})')
ax2.set_xlabel('Date')
ax2.set_ylabel('Drawdown (%)')
ax2.legend()
drawdown_path = 'drawdown.png'
plt.savefig(drawdown_path)
# plt.show()

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Bitcoin Crossover Strategy Report', 0, 1, 'C')

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

pdf = PDF()
pdf.add_page()

# Title
pdf.set_font('Arial', 'B', 16)
pdf.cell(0, 10, f'Backtest Results for {backtest_period_str}', 0, 1, 'L')
pdf.ln(5)

# Best Parameters
pdf.set_font('Arial', 'B', 12)
pdf.cell(0, 10, 'Optimized Parameters:', 0, 1, 'L')
pdf.set_font('Arial', '', 10)
pdf.cell(0, 8, f"- Short Window: {short_window}", 0, 1, 'L')
pdf.cell(0, 8, f"- Long Window: {long_window}", 0, 1, 'L')
pdf.cell(0, 8, f"- Stop Loss: {stop_loss_pct:.0%}", 0, 1, 'L')
pdf.cell(0, 8, f"- Take Profit: {take_profit_pct:.0%}", 0, 1, 'L')
pdf.ln(10)

# Metrics Table
pdf.set_font('Arial', 'B', 12)
pdf.cell(0, 10, 'Performance Metrics:', 0, 1, 'L')
pdf.set_font('Arial', 'B', 10)
pdf.cell(45, 10, 'Metric', 1, 0, 'C')
pdf.cell(45, 10, 'Value', 1, 1, 'C')
pdf.set_font('Arial', '', 10)
for metric, value in metrics.items():
    pdf.cell(45, 10, metric, 1, 0, 'L')
    pdf.cell(45, 10, str(value), 1, 1, 'R')
pdf.ln(10)

# Plots
pdf.add_page()
pdf.set_font('Arial', 'B', 12)
pdf.cell(0, 10, 'Equity Curve', 0, 1, 'L')
if os.path.exists(equity_curve_path):
    pdf.image(equity_curve_path, x=10, y=None, w=180)
pdf.ln(5)

pdf.cell(0, 10, 'Drawdown', 0, 1, 'L')
if os.path.exists(drawdown_path):
    pdf.image(drawdown_path, x=10, y=None, w=180)

pdf_output_path = 'backtest_report.pdf'
try:
    pdf.output(pdf_output_path)
    print(f"PDF report generated at: {os.path.abspath(pdf_output_path)}")
except Exception as e:
    print(f'Error generating PDF: {e}')