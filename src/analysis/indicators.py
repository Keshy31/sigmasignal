import pandas as pd
import pandas_ta as ta

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds technical indicators to the DataFrame using pandas-ta.
    
    Indicators:
    1. Bollinger Bands (20, 2) -> BBL, BBM, BBU, Bandwidth
    2. RSI (14) -> RSI
    3. MACD (12, 26, 9) -> MACD, MACDs, MACDh
    
    Args:
        df: DataFrame with OHLCV data.
        
    Returns:
        pd.DataFrame: DataFrame with added indicator columns.
    """
    # Ensure we are working on a copy to avoid SettingWithCopy warnings
    df = df.copy()

    # pandas-ta requires 'close' column to be lowercase usually, or we specify it.
    # checking column names from yfinance (usually Capitalized 'Close')
    # pandas-ta can handle it but let's be explicit or just rely on its smarts.
    # It usually looks for 'close'.
    
    # 1. Bollinger Bands
    # Using direct call instead of Strategy class to avoid potential import issues
    df.ta.bbands(length=20, std=2.0, append=True)
    
    # 2. RSI
    df.ta.rsi(length=14, append=True)
    
    # 3. MACD
    df.ta.macd(fast=12, slow=26, signal=9, append=True)

    # Rename columns to standard names
    # We inspect columns to find the generated names
    # Expected pattern: BBL_20_2.0, RSI_14, MACD_12_26_9 etc.
    # But names might vary slightly (e.g. BBL_20_2.0_2.0)
    
    # Helper to find column starting with prefix
    def find_col(prefix):
        for c in df.columns:
            if c.startswith(prefix):
                return c
        return None

    # Mapping based on prefixes which are more stable
    col_map = {
        find_col('BBL_20'): 'BBL',
        find_col('BBM_20'): 'BBM',
        find_col('BBU_20'): 'BBU',
        find_col('BBB_20'): 'Bandwidth', # Bandwidth from pandas-ta if available
        find_col('RSI_14'): 'RSI',
        find_col('MACD_12'): 'MACD',
        find_col('MACDs_12'): 'MACDs',
        find_col('MACDh_12'): 'MACDh'
    }
    
    # Remove None keys
    col_map = {k: v for k, v in col_map.items() if k is not None}
    
    df.rename(columns=col_map, inplace=True)
    
    # If Bandwidth wasn't found/renamed, calculate it using standard names
    if 'Bandwidth' not in df.columns and 'BBU' in df.columns and 'BBL' in df.columns and 'BBM' in df.columns:
         df['Bandwidth'] = (df['BBU'] - df['BBL']) / df['BBM']
    
    return df

if __name__ == "__main__":
    # Test execution
    from src.data.loader import fetch_data
    
    df = fetch_data("NVDA")
    df_ind = add_indicators(df)
    
    print("Columns:", df_ind.columns)
    print(df_ind.tail())

