Plan: Trinity Quantitative Backtest Engine
1. Project Initialization & Architecture
Set up a modular Python project structure to support the "systems trading desk" vision.

Structure:
src/: Source code
data/: Data ingestion
analysis/: Indicators and signals
engine/: Backtesting logic
visualization/: Plotly dashboard
data/: Local storage for cached CSVs
notebooks/: For exploratory analysis
main.py: Entry point
2. Data Ingestion (The Feed)
Implement the data fetcher using yfinance.

Module: src/data/loader.py
Key Features:
Fetch intraday data (e.g., 5m interval) for last 30 days.
Basic cleaning: Drop NaNs, zero-volume filtering.
Caching: Save fetched data to data/ to prevent API rate limits/redundant calls during dev.
3. Feature Engineering (The Math)
Implement technical indicators using pandas-ta.

Module: src/analysis/indicators.py
Calculations:
Bollinger Bands: Length=20, Std=2 (Columns: BBL, BBM, BBU, Bandwidth).
RSI: Length=14 (Column: RSI).
MACD: Fast=12, Slow=26, Signal=9 (Columns: MACD, MACDs, MACDh).
4. Alpha Model (The Logic)
Translate the Trinity strategy into boolean signals.

Module: src/analysis/signals.py
Signals:
Signal_A (Mean Reversion): Buy when Price < LowerBB AND RSI < 30 AND MACD Hist rising.
Signal_B (Breakout): Buy when Price > UpperBB AND RSI > 70 AND MACD Bullish AND Bandwidth < Threshold.
Output: Boolean columns or a combined Signal column (1 for Buy, 0 for None).
5. Execution Engine (The Simulation)
Build the backtester with "Next-Bar" execution to avoid look-ahead bias.

Module: src/engine/backtester.py
Logic:
Iterate through DataFrame (or vectorized approach where possible).
Entry: If Signal at $T_0$, Buy at Open of $T_{+1}$.
Exit Rules:
Take Profit: +2%
Stop Loss: -1%
End of Day Close.
Reporting: Generate a trade log (Entry Time/Price, Exit Time/Price, P&L).
6. Visualization (The Dashboard)
Create interactive charts for analysis.

Module: src/visualization/dashboard.py
Components:
Row 1: Candlestick + BB + Buy/Sell Markers.
Row 2: RSI with 30/70 lines.
Row 3: MACD Histogram.
Tech: plotly.graph_objects.
7. Integration
Script: main.py
Flow: Load Data -> Add Indicators -> Generate Signals -> Run Backtest -> Show Dashboard.