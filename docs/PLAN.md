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

**Status: Completed**

To improve the 0% Win Rate (observed in initial tests), we shifted from "Implementation" to "Quantitative Research". The goal was to filter low-quality signals and adapt to volatility.

### A. Dynamic Risk Management (ATR)
- **Implemented**: Stop Loss = $Entry - (k_1 \times ATR)$ and Take Profit = $Entry + (k_2 \times ATR)$
- **Result**: Moving from fixed % stops to ATR-based stops prevented premature stop-outs in high volatility.

### B. Regime Filtering (The "Traffic Light")
- **Implemented**: ADX filter to separate Trending vs. Ranging markets.
  - Trending (ADX > 25): Breakout Only.
  - Ranging (ADX < 25): Mean Reversion Only.

### C. Parameter Optimization (Grid Search)
- **Implemented**: `src/optimization/optimizer.py`
- **Findings**:
  - **Best Win Rate**: 50% (vs 0% initially).
  - **Best PnL**: +0.40% (vs -5% Buy & Hold drawdown).
  - **Optimal Parameters**:
    - RSI Thresholds: 30 / 70
    - ADX Threshold: 25
    - ATR Stop Loss: 2.0x
    - ATR Take Profit: 2.0x

### D. Extended Backtest
- **Action**: Optimized parameters have been applied to `main.py` as defaults.

## 9. Phase 3: Profit Maximization & Robustness (Planned)

To scale from "capital preservation" to "alpha generation", we will implement:

### A. Short Selling (The Biggest Lever)
- **Logic**: Allow the system to bet on price drops.
- **Impact**: In a bear market (like NVDA's recent -5% month), a shorting strategy transforms downside volatility into profit, potentially turning +0.4% into +5% or more.

### B. Dynamic Bandwidth
- **Current**: Static `median` bandwidth.
- **Improved**: Use a "percentile" approach (e.g., bandwidth < 10th percentile of last 100 bars). This adapts automatically to changing volatility regimes (e.g., earnings season vs. holiday chop).

### C. Data & Confidence
- **Current**: 1 month of data (~20 trading days).
- **Improved**: Expand to 3-6 months.
- **Goal**: Validate that the "low trade count" is a feature (precision) and not a bug (over-filtering). If trade frequency remains <5/month over 6 months, we may need to loosen filters.

### D. Refined Trend Capture
- **Observation**: While the system protected capital in NVDA (-5% vs +0.4%), it significantly underperformed GOOGL Buy & Hold (+20% vs +1.28%).
- **Diagnosis**: The system takes profit too early (2.0x ATR) in strong trends, missing the "fat tail" gains.
- **Solution**: Implement a **Trailing Stop** mechanism (e.g., Chandelier Exit or ATR Trailing Stop) instead of a fixed Take Profit target to let winning trades run.

