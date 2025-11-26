import argparse
import pandas as pd
from src.data.loader import fetch_data
from src.analysis.indicators import add_indicators
from src.analysis.signals import generate_signals
from src.engine.backtester import Backtester
from src.visualization.dashboard import create_dashboard

def main():
    parser = argparse.ArgumentParser(description="Trinity Quantitative Backtest Engine")
    parser.add_argument("--ticker", type=str, default="NVDA", help="Stock Ticker (default: NVDA)")
    parser.add_argument("--interval", type=str, default="5m", help="Data Interval (default: 5m)")
    parser.add_argument("--period", type=str, default="1mo", help="Data Period (default: 1mo)")
    parser.add_argument("--tp", type=float, default=2.0, help="ATR Take Profit Multiplier (default: 2.0)")
    parser.add_argument("--sl", type=float, default=2.0, help="ATR Stop Loss Multiplier (default: 2.0)")
    parser.add_argument("--bandwidth", type=float, default=None, help="Bandwidth Threshold (default: median of data)")
    
    args = parser.parse_args()
    
    print(f"--- Starting Trinity Backtest for {args.ticker} ---")
    
    # 1. Data Ingestion
    print("Fetching Data...")
    df = fetch_data(args.ticker, interval=args.interval, period=args.period)
    if df.empty:
        print("No data found. Exiting.")
        return

    # 2. Feature Engineering
    print("Calculating Indicators...")
    df = add_indicators(df)
    
    # 3. Signal Generation
    print("Generating Signals...")
    # Determine bandwidth threshold
    bw_threshold = args.bandwidth
    if bw_threshold is None:
        bw_threshold = df['Bandwidth'].median()
        print(f"Using Median Bandwidth as Threshold: {bw_threshold:.4f}")
    
    df = generate_signals(df, bandwidth_threshold=bw_threshold)
    
    num_signals = df['Signal'].sum()
    print(f"Total Signals Generated: {num_signals}")
    
    # 4. Backtest Simulation
    print("Running Backtest...")
    engine = Backtester(atr_multiplier_tp=args.tp, atr_multiplier_sl=args.sl)
    trades = engine.run(df, verbose=True)
    
    if not trades.empty:
        total_pnl = trades['PnL'].sum()
        win_rate = len(trades[trades['PnL'] > 0]) / len(trades)
        print("\n--- Backtest Results ---")
        print(f"Total Trades: {len(trades)}")
        print(f"Total PnL: {total_pnl*100:.2f}%")
        print(f"Win Rate: {win_rate*100:.1f}%")
        print(trades[['Entry Time', 'Entry Price', 'Exit Time', 'Exit Price', 'PnL', 'Reason']].to_string())
    else:
        print("\nNo trades executed.")
    
    # 5. Visualization
    print("\nGenerating Dashboard...")
    fig = create_dashboard(df, trades)
    output_file = f"dashboard_{args.ticker}.html"
    fig.write_html(output_file)
    print(f"Dashboard saved to {output_file}")
    
    print("Done.")

if __name__ == "__main__":
    main()

