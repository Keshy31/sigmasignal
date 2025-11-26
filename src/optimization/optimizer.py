import argparse
import pandas as pd
import itertools
from src.data.loader import fetch_data
from src.analysis.indicators import add_indicators
from src.analysis.signals import generate_signals
from src.engine.backtester import Backtester

class Optimizer:
    def __init__(self, ticker="NVDA", interval="5m", period="1mo"):
        self.ticker = ticker
        self.interval = interval
        self.period = period
        self.df = None
        self.results = []

    def load_data(self):
        """Fetch and prepare data once."""
        print(f"Fetching data for {self.ticker}...")
        df = fetch_data(self.ticker, interval=self.interval, period=self.period)
        if df.empty:
            raise ValueError("No data fetched.")
        
        print("Calculating indicators...")
        self.df = add_indicators(df)
        
    def run_grid_search(self):
        """
        Runs grid search over parameter combinations.
        """
        if self.df is None:
            self.load_data()
            
        # Parameter Grid
        # RSI Lower Thresholds (Upper will be 100 - Lower implicitly or explicitly set)
        # Note: In our current signal logic we use explicit upper/lower.
        # But commonly if we set lower=30, upper is 70.
        # Let's vary them symmetrically for now as per plan [20, 25, 30]
        # which means pairs (20, 80), (25, 75), (30, 70).
        rsi_params = [20, 25, 30]
        
        adx_params = [20, 25, 30]
        atr_sl_multipliers = [1.5, 2.0, 2.5]
        atr_tp_multipliers = [2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0]
        
        # Calculate total combinations
        combinations = list(itertools.product(rsi_params, adx_params, atr_sl_multipliers, atr_tp_multipliers))
        print(f"Starting grid search with {len(combinations)} combinations...")
        
        for rsi_low, adx_thresh, sl_mult, tp_mult in combinations:
            rsi_high = 100 - rsi_low
            
            # 1. Generate Signals
            # We use the median bandwidth as a baseline for all tests to isolate other variables
            # Or we could optimize bandwidth too, but let's stick to the plan.
            bw_threshold = self.df['Bandwidth'].median()
            
            df_sig = generate_signals(
                self.df, 
                bandwidth_threshold=bw_threshold, 
                adx_threshold=adx_thresh,
                rsi_lower_thresh=rsi_low,
                rsi_upper_thresh=rsi_high
            )
            
            # 2. Run Backtest
            engine = Backtester(atr_multiplier_sl=sl_mult, atr_multiplier_tp=tp_mult)
            trades = engine.run(df_sig)
            
            # 3. Calculate Metrics
            trade_count = len(trades)
            if trade_count > 0:
                total_pnl = trades['PnL'].sum()
                win_rate = len(trades[trades['PnL'] > 0]) / trade_count
                avg_pnl = trades['PnL'].mean()
            else:
                total_pnl = 0.0
                win_rate = 0.0
                avg_pnl = 0.0
                
            self.results.append({
                'RSI_Low': rsi_low,
                'RSI_High': rsi_high,
                'ADX_Thresh': adx_thresh,
                'ATR_SL': sl_mult,
                'ATR_TP': tp_mult,
                'Trades': trade_count,
                'Win_Rate': win_rate,
                'Total_PnL': total_pnl,
                'Avg_PnL': avg_pnl
            })
            
    def get_top_results(self, top_n=5, sort_by='Total_PnL'):
        """Returns the top N results sorted by metric."""
        results_df = pd.DataFrame(self.results)
        if results_df.empty:
            return results_df
            
        return results_df.sort_values(by=sort_by, ascending=False).head(top_n)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trinity Strategy Optimizer")
    parser.add_argument("--ticker", type=str, default="NVDA", help="Ticker to optimize (default: NVDA)")
    args = parser.parse_args()
    
    optimizer = Optimizer(ticker=args.ticker)
    optimizer.run_grid_search()
    
    print(f"\n--- Top 10 Optimization Results for {args.ticker} ---")
    top_results = optimizer.get_top_results(top_n=10)
    print(top_results.to_string(index=False))

