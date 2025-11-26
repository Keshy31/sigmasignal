import os
import pandas as pd
import yfinance as yf

def fetch_data(ticker: str, interval: str = "5m", period: str = "1mo", data_dir: str = "data") -> pd.DataFrame:
    """
    Fetches OHLCV data for a given ticker.
    Checks local cache first; if not found, downloads from yfinance and caches it.

    Args:
        ticker: The stock symbol (e.g., 'NVDA').
        interval: Data granularity (default '5m').
        period: Data lookback period (default '1mo').
        data_dir: Directory to store cached CSVs.

    Returns:
        pd.DataFrame: Cleaned DataFrame with OHLCV data.
    """
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    # Sanitize inputs for filename
    safe_ticker = ticker.replace("^", "").replace("/", "-")
    cache_path = os.path.join(data_dir, f"{safe_ticker}_{interval}_{period}.csv")

    if os.path.exists(cache_path):
        print(f"Loading data from cache: {cache_path}")
        df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
    else:
        print(f"Downloading data for {ticker}...")
        try:
            df = yf.download(ticker, interval=interval, period=period, progress=False)
            
            # Handle MultiIndex columns (yfinance structure: Price, Ticker)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
        except Exception as e:
            print(f"Error downloading data: {e}")
            return pd.DataFrame()

        if df.empty:
            print(f"No data found for {ticker}")
            return pd.DataFrame()

        # Cache the raw data
        df.to_csv(cache_path)
        print(f"Data cached to {cache_path}")

    # Data Cleaning
    # 1. Drop NaNs
    df.dropna(inplace=True)

    # 2. Filter Zero Volume
    if 'Volume' in df.columns:
        df = df[df['Volume'] > 0]
    
    # Ensure index is DatetimeIndex and sorted
    if not isinstance(df.index, pd.DatetimeIndex):
         df.index = pd.to_datetime(df.index)
    
    df.sort_index(inplace=True)

    return df

if __name__ == "__main__":
    # Test execution
    data = fetch_data("NVDA")
    print(data.head())
    print(data.tail())
    print(f"Total Rows: {len(data)}")

