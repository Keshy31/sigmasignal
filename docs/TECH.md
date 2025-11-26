# Technical Overview: The Trinity Backtest Engine

## 1\. System Architecture

The system follows a linear **ETL (Extract, Transform, Load)** pipeline pattern adapted for quantitative research. It is designed to be stateless and vectorized for maximum performance.

```mermaid
graph TD
    A[Data Ingestion<br/>(yfinance)] -->|Raw OHLCV| B[Data Processing<br/>(Pandas)]
    B -->|Cleaned DataFrame| C[Feature Engineering<br/>(pandas-ta)]
    C -->|Indicators Added| D[Signal Generation<br/>(Vectorized Logic)]
    D -->|Boolean Signals| E[Execution Simulator<br/>(Backtest Engine)]
    E -->|Trade Logs| F[Visualization<br/>(Plotly)]
```

-----

## 2\. Technology Stack

| Component | Technology | Rationale |
| :--- | :--- | :--- |
| **Core Language** | **Python 3.10+** | Industry standard for financial research and data science. |
| **Data Source** | **`yfinance`** | Low-latency access to Yahoo Finance API for granular intraday data (1m, 5m). |
| **Data Structure** | **Pandas DataFrame** | In-memory, columnar storage allowing for vectorized operations (SIMD-like speed). |
| **Math Library** | **`pandas-ta`** | Standardized, tested implementations of technical indicators (prevents calculation errors). |
| **Visualization** | **Plotly Graph Objects** | Interactive HTML5 charts allowing zoom/pan/hover for specific candle inspection. |

-----

## 3\. Data Model & Ingestion

**Scope:** 30 Days of 5-minute Intraday Data.
**Schema:**

| Column | Type | Description |
| :--- | :--- | :--- |
| `Datetime` | `datetime64[ns]` | Index. UTC converted to Market Time (EST). |
| `Open` | `float64` | Opening price of the 5-min bar. |
| `High` | `float64` | Highest price during the 5-min bar. |
| `Low` | `float64` | Lowest price during the 5-min bar. |
| `Close` | `float64` | Closing price of the 5-min bar. |
| `Volume` | `int64` | Total shares traded. |

**Data Cleaning Protocols:**

1.  **Drop NaN:** Remove rows with missing price data.
2.  **Zero-Volume Filter:** Exclude pre-market/after-hours noise if liquidity is zero.

-----

## 4\. Feature Engineering (The Indicator Logic)

We utilize `pandas-ta` to append the following columns to the main DataFrame:

### A. Bollinger Bands

  * **Settings:** Length=20, StdDev=2.
  * **Outputs:** `BBL_20_2.0` (Lower), `BBM_20_2.0` (Mid), `BBU_20_2.0` (Upper).
  * **Derived Feature:** `Bandwidth = (Upper - Lower) / Mid` (Used to detect Squeezes).

### B. RSI (Relative Strength Index)

  * **Settings:** Length=14.
  * **Method:** Wilder’s Smoothing (Standard).
  * **Output:** `RSI_14`.

### C. MACD

  * **Settings:** Fast=12, Slow=26, Signal=9.
  * **Outputs:** `MACD_12_26_9` (Line), `MACDs_12_26_9` (Signal), `MACDh_12_26_9` (Histogram).

-----

## 5\. Algorithmic "Alpha" Logic

The strategy is codified into Boolean masks.

### Signal Generation Rules

#### Scenario A: Mean Reversion (Long)

*Logic: Buy the dip in a ranging market.*

```python
condition_1 = df['Close'] < df['BBL_20_2.0']       # Price touches Rumble Strip
condition_2 = df['RSI_14'] < 30                    # Momentum is Oversold
condition_3 = df['Bandwidth'] > threshold          # Ensure bands aren't squeezing (optional)

Signal_Reversion = condition_1 & condition_2 & condition_3
```

#### Scenario B: Squeeze Breakout (Long)

*Logic: Buy the explosion.*

```python
condition_1 = df['Close'] > df['BBU_20_2.0']       # Price breaks Upper Band
condition_2 = df['RSI_14'] > 70                    # Momentum is strong (not overbought)
condition_3 = df['MACD_12_26_9'] > df['MACDs_12_26_9'] # Trend is Bullish
condition_4 = df['Bandwidth'] < squeeze_threshold  # Volatility was low previously

Signal_Breakout = condition_1 & condition_2 & condition_3 & condition_4
```

-----

## 6\. Execution & Simulation Model

### The "Look-Ahead" Guardrail

To ensure scientific integrity, we strictly adhere to **Next-Bar Execution**.

  * **Problem:** We calculate indicators using the `Close` of $T_{0}$. We cannot buy at $T_{0}$ `Close` because the candle has closed.
  * **Solution:** If `Signal == True` at index $i$, we enter the trade at `Open` price of index $i+1$.

### Trade Lifecycle

1.  **Entry:** `df['Open'].shift(-1)` where Signal is True.
2.  **Exit (MVP):**
      * *Take Profit:* +2% movement.
      * *Stop Loss:* -1% movement.
      * *Time Stop:* Close at End-of-Day (Intraday constraint).

-----

## 7\. Visualization Outputs

The dashboard will render a stacked subplot chart:

1.  **Row 1 (Main):** Candlestick Price Chart + Bollinger Bands overlay + Buy/Sell Markers.
2.  **Row 2:** RSI Oscillator with 30/70 horizontal lines.
3.  **Row 3:** MACD Histogram and Signal Lines.