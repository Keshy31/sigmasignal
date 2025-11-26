# Plan: Trinity Quantitative Backtest Engine

## 1. Project Initialization & Architecture

Set up a modular Python project structure to support the "systems trading desk" vision.

- **Structure**:
    - `src/`: Source code
    - `data/`: Data ingestion
    - `analysis/`: Indicators and signals
    - `engine/`: Backtesting logic
    - `visualization/`: Plotly dashboard
    - `data/`: Local storage for cached CSVs
    - `notebooks/`: For exploratory analysis
    - `main.py`: Entry point

## 2. Data Ingestion (The Feed)

Implement the data fetcher using `yfinance`.

- **Module**: `src/data/loader.py`
- **Key Features**:
    - Fetch intraday data (e.g., 5m interval) for last 30 days.
    - Basic cleaning: Drop NaNs, zero-volume filtering.
    - **Caching**: Save fetched data to `data/` to prevent API rate limits/redundant calls during dev.

## 3. Feature Engineering (The Math)

Implement technical indicators using `pandas-ta`.

- **Module**: `src/analysis/indicators.py`
- **Calculations**:
    - **Bollinger Bands**: Length=20, Std=2 (Columns: `BBL`, `BBM`, `BBU`, `Bandwidth`).
    - **RSI**: Length=14 (Column: `RSI`).
    - **MACD**: Fast=12, Slow=26, Signal=9 (Columns: `MACD`, `MACDs`, `MACDh`).
    - **ATR** (Phase 2): Length=14 (Column: `ATR`).
    - **ADX** (Phase 2): Length=14 (Columns: `ADX`, `DMP`, `DMN`).

## 4. Alpha Model (The Logic)

Translate the Trinity strategy into boolean signals.

- **Module**: `src/analysis/signals.py`
- **Signals**:
    - **Signal_A (Mean Reversion)**: Buy when Price < LowerBB AND RSI < 30 AND MACD Hist rising.
    - **Signal_B (Breakout)**: Buy when Price > UpperBB AND RSI > 70 AND MACD Bullish AND Bandwidth < Threshold.
    - **Regime Filter** (Phase 2):
        - If `ADX > 25` (Trending): Prioritize Signal_B. Block Signal_A.
        - If `ADX < 25` (Ranging): Prioritize Signal_A. Block Signal_B.
- **Output**: Boolean columns or a combined `Signal` column (1 for Buy, 0 for None).

## 5. Execution Engine (The Simulation)

Build the backtester with "Next-Bar" execution to avoid look-ahead bias.

- **Module**: `src/engine/backtester.py`
- **Logic**:
    - Iterate through DataFrame (or vectorized approach where possible).
    - **Entry**: If Signal at $T_0$, Buy at Open of $T_{+1}$.
    - **Exit Rules**:
        - **Phase 1 (Fixed)**: Take Profit +2%, Stop Loss -1%.
        - **Phase 2 (Dynamic)**:
            - Stop Loss = $Entry - (k_1 \times ATR)$
            - Take Profit = $Entry + (k_2 \times ATR)$
    - End of Day Close.
- **Reporting**: Generate a trade log (Entry Time/Price, Exit Time/Price, P&L).

## 6. Visualization (The Dashboard)

Create interactive charts for analysis.

- **Module**: `src/visualization/dashboard.py`
- **Components**:
    - Row 1: Candlestick + BB + Buy/Sell Markers.
    - Row 2: RSI with 30/70 lines.
    - Row 3: MACD Histogram.
- **Tech**: `plotly.graph_objects`.

## 7. Integration

- **Script**: `main.py`
- **Flow**: Load Data -> Add Indicators -> Generate Signals -> Run Backtest -> Show Dashboard.

## 8. Phase 2: Alpha Optimization (Quant Refinement)

To improve the 0% Win Rate (observed in initial tests), we shift from "Implementation" to "Quantitative Research". The goal is to filter low-quality signals and adapt to volatility.

### A. Dynamic Risk Management (ATR)

- **Hypothesis**: Fixed 1% SL is likely getting stopped out by random noise in high-beta stocks like NVDA.
- **Solution**: Use **Average True Range (ATR)** for dynamic stops.
    - Stop Loss = $Entry - (k_1 \times ATR)$
    - Take Profit = $Entry + (k_2 \times ATR)$

### B. Regime Filtering (The "Traffic Light")

- **Hypothesis**: Mean Reversion strategies fail in strong trends; Breakout strategies fail in chop.
- **Solution**: Implement **ADX (Average Directional Index)**.
    - **Strong Trend (ADX > 25)**: ONLY take Breakout signals. Block Mean Reversion.
    - **Ranging (ADX < 25)**: ONLY take Mean Reversion signals. Block Breakout.

### C. Parameter Optimization (Grid Search)

- **Hypothesis**: "Median Bandwidth" and RSI 30/70 are arbitrary.
- **Solution**: Build `src/optimization/optimizer.py`.
- Systematically test combinations of:
    - RSI Thresholds: [20, 25, 30]
    - ATR Multipliers: [1.5, 2.0, 2.5]
    - ADX Threshold: [20, 25, 30]
- **Metric**: Maximize **Sharpe Ratio** or **Total PnL**.

### D. Extended Backtest

- **Action**: Expand data window beyond 1 month (if API permits) or test on multiple tickers to ensure statistical significance.
