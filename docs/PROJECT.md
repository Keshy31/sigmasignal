# Project Spec: "The Trinity" Quantitative Backtest Engine

## 1. Executive Summary
**Objective:** To empirically validate the "Trinity" strategy (RSI + MACD + Bollinger Bands) by converting discretionary rules into deterministic code.
**Hypothesis:** Confluence of Volatility (BB), Momentum (RSI), and Trend (MACD) provides a statistical edge in predicting short-term price movements in high-beta assets (like NVDA).
**Scope (MVP):** 30 days of intraday data (e.g., 5-minute or 15-minute candles) for a single ticker.

---

## 2. The Quant Architecture (The "Stack")

A professional quant system is modular. We will build distinct "blocks" so we can swap parts out later (e.g., changing the data source without breaking the strategy logic).

### A. Data Ingestion Layer (The Feed)
* **Goal:** Fetch high-granularity OHLCV (Open, High, Low, Close, Volume) data.
* **The Quant Edge:** 30 days of *Daily* data is only 30 data points—statistically useless. We need **Intraday Data** (e.g., 5-minute intervals).
    * *Math:* 30 days $\times$ 6.5 trading hours $\times$ 12 intervals/hour = ~2,340 data points. This gives us enough sample size to test.
* **Tech:** `yfinance` (free, easy for MVP) or `interactive brokers API` (later).

### B. Feature Engineering Layer (The Math)
* **Goal:** Transform raw price data into the Trinity Indicators.
* **Library:** `pandas` (for vectorization) or `pandas-ta` (Technical Analysis library).
* **Calculations:**
    1.  **BB:** Rolling Mean (20) $\pm$ 2 Std Dev.
    2.  **RSI:** 14-period Wilder’s Smoothing.
    3.  **MACD:** EMA(12) - EMA(26) and Signal EMA(9).

### C. The Alpha Model (The Logic)
This is where we translate your obsidian notes into Boolean Logic. We define two distinct signals:

* **Signal_A (Mean Reversion):**
    `IF (Price < LowerBB) AND (RSI < 30) AND (MACD_Hist > Prev_MACD_Hist) -> BUY`
* **Signal_B (Breakout):**
    `IF (Bandwidth < Threshold) AND (Price > UpperBB) AND (RSI > 70) AND (MACD_Line > Signal_Line) -> BUY`

### D. The Execution Engine (The Simulation)
* **Goal:** Simulate what *would* have happened.
* **Logic:**
    * Iterate through the dataframe.
    * If `Signal == True`, open a "Virtual Position."
    * Track Entry Price, Stop Loss Price, and Take Profit Price.
    * Close position when Stop/Target is hit.
* **Output:** A list of trades with P&L.

### E. Visualization & Reporting (The Dashboard)
* **Goal:** Visual intuition. We don't just want a return number; we want to *see* the trade.
* **Tech:** `Plotly` (interactive charts).
* **Views:**
    * Price Chart with BB overlay.
    * Subplots for RSI and MACD.
    * **Markers:** Green triangles where the Algo bought, Red squares where it sold.

---

## 3. Development Roadmap (The "Sprints")

### Phase 1: Data & Features (Day 1-2)
* Set up Python environment.
* Download 30 days of 5-minute NVDA data.
* Calculate indicators and verify they match a TradingView chart (sanity check).

### Phase 2: The Signal Logic (Day 3)
* Write the Python functions for Scenario A and Scenario B.
* Create a "Signal Column" in the dataframe (0 = Do Nothing, 1 = Buy).

### Phase 3: The Vectorized Backtest (Day 4)
* Run the simulation.
* Calculate "naive" returns (assuming we buy on signal and close at end of day).

### Phase 4: Refinement & Visualization (Day 5)
* Add realistic exit rules (Stop Loss / Take Profit).
* Build the Plotly dashboard to zoom into specific days and see why a trade worked or failed.

---

## 4. Key Questions a Quant Would Ask (Pre-Mortem)

Before we write a line of code, a Two Sigma quant would ask these questions to avoid "Fool's Gold":

1.  **Look-Ahead Bias:** Are we calculating the signal using the *Close* price of the current bar? If so, we can't buy *at* that Close price (we'd have to buy at the *next* Open).
    * *Solution:* We will execute trades on `shift(-1)` (the next bar).
2.  **Overfitting:** Are we tweaking the parameters (e.g., RSI 14 to RSI 13) just to make the last 30 days look good?
    * *Solution:* Stick to standard settings (14, 20, 12/26/9) for the MVP.
3.  **Transaction Costs:** Scalping 5-minute candles generates lots of trades. Spreads and fees will eat profits.
    * *Solution:* We must factor in a "slippage" cost per trade in the final P&L.

---