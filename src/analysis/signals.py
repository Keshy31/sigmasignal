import pandas as pd

def generate_signals(df: pd.DataFrame, bandwidth_threshold: float = 0.02, adx_threshold: float = 25.0) -> pd.DataFrame:
    """
    Generates trading signals based on Trinity Strategy.
    
    Signals:
    1. Mean Reversion (Signal A):
       - Price < Lower BB
       - RSI < 30
       - MACD Histogram > Previous MACD Histogram (Momentum improving)
       - Regime: ADX < Threshold (Ranging)
       
    2. Squeeze Breakout (Signal B):
       - Price > Upper BB
       - RSI > 70
       - MACD Line > Signal Line
       - Bandwidth < Threshold (Low Volatility / Squeeze)
       - Regime: ADX > Threshold (Trending)
       
    Args:
        df: DataFrame with indicators (BBL, BBU, RSI, MACD, MACDs, MACDh, Bandwidth, ADX).
        bandwidth_threshold: Threshold for Bandwidth to consider it a squeeze. 
                             Default 0.02 (2%) might be tight for intraday, adjust as needed.
        adx_threshold: Threshold for ADX to distinguish between Trending and Ranging regimes.
                             Default 25.0.
                             
    Returns:
        pd.DataFrame: DataFrame with 'Signal' column (1 for Buy, 0 for None).
                      Also adds 'Signal_MeanRev' and 'Signal_Breakout' for debugging.
    """
    df = df.copy()
    
    # Ensure required columns exist
    required_cols = ['Close', 'BBL', 'BBU', 'RSI', 'MACD', 'MACDs', 'MACDh', 'Bandwidth', 'ADX']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns for signal generation: {missing}")
    
    # --- Regime Filter ---
    # ADX > Threshold -> Trending
    # ADX < Threshold -> Ranging
    is_trending = df['ADX'] > adx_threshold
    is_ranging = df['ADX'] < adx_threshold
    
    # --- Signal A: Mean Reversion ---
    # Buy the dip in Ranging Market
    # Condition 1: Price < LowerBB (Rumble Strip)
    cond_a_1 = df['Close'] < df['BBL']
    
    # Condition 2: RSI < 30 (Oversold)
    cond_a_2 = df['RSI'] < 30
    
    # Condition 3: MACD Histogram Rising (Momentum turning up)
    # We compare current hist with previous hist
    cond_a_3 = df['MACDh'] > df['MACDh'].shift(1)
    
    # Combine with Regime
    df['Signal_MeanRev'] = (cond_a_1 & cond_a_2 & cond_a_3 & is_ranging).astype(int)
    
    # --- Signal B: Squeeze Breakout ---
    # Buy the explosion in Trending Market
    # Condition 1: Price > UpperBB
    cond_b_1 = df['Close'] > df['BBU']
    
    # Condition 2: RSI > 70 (Strong Momentum)
    cond_b_2 = df['RSI'] > 70
    
    # Condition 3: MACD Bullish
    cond_b_3 = df['MACD'] > df['MACDs']
    
    # Condition 4: Bandwidth was low (Squeeze)
    # Note: If price breaks out, bandwidth might start expanding immediately.
    # We can check current bandwidth or previous bandwidth. 
    # Let's check if it IS low (indicating the move is starting from a squeeze).
    cond_b_4 = df['Bandwidth'] < bandwidth_threshold
    
    df['Signal_Breakout'] = (cond_b_1 & cond_b_2 & cond_b_3 & cond_b_4 & is_trending).astype(int)
    
    # --- Combined Signal ---
    # Priority: If both true (rare), we buy. 
    # 1 = Buy, 0 = Hold/None
    df['Signal'] = (df['Signal_MeanRev'] | df['Signal_Breakout']).astype(int)
    
    return df

if __name__ == "__main__":
    from src.data.loader import fetch_data
    from src.analysis.indicators import add_indicators
    
    df = fetch_data("NVDA")
    df = add_indicators(df)
    
    # Inspect Bandwidth to set a reasonable threshold for testing
    print("Bandwidth Stats:")
    print(df['Bandwidth'].describe())
    
    # Use median as threshold for testing to get some signals
    median_bw = df['Bandwidth'].median()
    print(f"Using median bandwidth {median_bw:.4f} as threshold for test")
    
    df = generate_signals(df, bandwidth_threshold=median_bw)
    
    print("\nSignal Counts:")
    print(df['Signal'].value_counts())
    print("\nMean Reversion Counts:", df['Signal_MeanRev'].sum())
    print("Breakout Counts:", df['Signal_Breakout'].sum())
    
    # Show some rows with signals
    print("\nSample Trades:")
    print(df[df['Signal'] == 1].tail())

