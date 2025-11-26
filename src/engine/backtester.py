import pandas as pd
from datetime import time

class Backtester:
    def __init__(self, atr_multiplier_sl=2.0, atr_multiplier_tp=3.0):
        self.atr_multiplier_sl = atr_multiplier_sl
        self.atr_multiplier_tp = atr_multiplier_tp
        self.trades = []
        
    def run(self, df: pd.DataFrame, verbose: bool = False) -> pd.DataFrame:
        """
        Runs the backtest simulation.
        
        Args:
            df: DataFrame with 'Signal' and OHLCV data.
            verbose: If True, prints trade details to console.
            
        Returns:
            pd.DataFrame: Trade log.
        """
        self.trades = []
        position = None # {'entry_time': ..., 'entry_price': ..., 'tp': ..., 'sl': ...}
        
        # We iterate until len(df) - 1 because we need i+1 for entry
        for i in range(len(df) - 1):
            curr_time = df.index[i]
            
            # Check for Exit if in position
            if position:
                # We are in a trade. Check current bar (High/Low) for TP/SL/Time limit.
                # Note: 'curr_row' here is the bar AFTER entry (or the entry bar itself if we just entered).
                # Wait, the loop step 'i' iterates through bars. 
                # If we entered at i (Open), we check i (High/Low) for exit?
                # Let's adjust logic. 
                # If we are in position, we monitor price.
                
                row = df.iloc[i]
                high = row['High']
                low = row['Low']
                close = row['Close']
                timestamp = df.index[i]
                
                exit_reason = None
                exit_price = None
                
                # Check SL first (Conservative)
                if low <= position['sl']:
                    exit_reason = 'Stop Loss'
                    exit_price = position['sl'] # Assuming fill at SL
                    # Realistically, it might gap, but for MVP we use SL level.
                    # Or use Close if Open < SL? Let's stick to SL level.
                
                # Check TP
                elif high >= position['tp']:
                    exit_reason = 'Take Profit'
                    exit_price = position['tp']
                    
                # Check EOD (Time Stop)
                # We close if the current bar is the last bar of the trading day.
                # Check if next bar's date is different from current bar's date.
                # If i is the last index of the dataframe, we can't check i+1, but loop range stops at len-1.
                # However, loop is range(len(df)-1), so i+1 is valid index up to len(df)-1.
                # Wait, if i is len(df)-2, i+1 is len(df)-1 (last bar).
                # If i is the last bar of the day, i+1 will be the first bar of next day.
                
                is_eod = False
                if i < len(df) - 1:
                    if df.index[i+1].date() > df.index[i].date():
                        is_eod = True
                else:
                    is_eod = True # Last bar of dataset
                    
                if is_eod:
                    exit_reason = 'EOD'
                    exit_price = close
                
                if exit_reason:
                    if verbose:
                        print(f"[EXIT] {timestamp} @ {exit_price:.2f} ({exit_reason}) | PnL: {(exit_price - position['entry_price'])/position['entry_price']*100:.2f}%")
                    self._close_trade(position, timestamp, exit_price, exit_reason)
                    position = None
                    continue # Trade closed, move to next bar (we can't re-enter same bar)
            
            # Check for Entry (if no position)
            # Signal at 'i' triggers entry at 'i+1' Open.
            if position is None:
                # We look at Signal of current completed bar 'i'.
                # But wait, if I am at 'i', I can see 'Signal'.
                # If Signal is 1, I set up to enter at 'i+1'.
                
                if df['Signal'].iloc[i] == 1:
                    # Execute entry at Next Open
                    next_open = df['Open'].iloc[i+1]
                    next_time = df.index[i+1]
                    atr_val = df['ATR'].iloc[i]  # Use ATR from signal generation time (current bar i)
                    
                    # Define Position with ATR-based SL/TP
                    # Long only for now
                    sl_price = next_open - (self.atr_multiplier_sl * atr_val)
                    tp_price = next_open + (self.atr_multiplier_tp * atr_val)
                    
                    # Identify signal type for logging
                    sig_type = "Unknown"
                    if 'Signal_MeanRev' in df.columns and df['Signal_MeanRev'].iloc[i] == 1:
                        sig_type = "Mean Reversion"
                    elif 'Signal_Breakout' in df.columns and df['Signal_Breakout'].iloc[i] == 1:
                        sig_type = "Breakout"
                    
                    if verbose:
                        print(f"[ENTRY] {next_time} ({sig_type}) @ {next_open:.2f} | SL: {sl_price:.2f} | TP: {tp_price:.2f} | ATR: {atr_val:.4f}")
                    
                    position = {
                        'entry_time': next_time,
                        'entry_price': next_open,
                        'tp': tp_price,
                        'sl': sl_price,
                        'signal_index': i # For debug
                    }
                    
                    # Note: We don't verify exit for 'i+1' here. 
                    # The loop will increment to 'i+1', and the "Check Exit" block will run for that bar.
                    # This correctly models entering at Open of i+1 and then checking High/Low of i+1 for exit.
        
        return pd.DataFrame(self.trades)

    def _close_trade(self, position, exit_time, exit_price, reason):
        pnl = (exit_price - position['entry_price']) / position['entry_price']
        trade = {
            'Entry Time': position['entry_time'],
            'Entry Price': position['entry_price'],
            'Exit Time': exit_time,
            'Exit Price': exit_price,
            'Reason': reason,
            'PnL': pnl,
            'Return %': pnl * 100
        }
        self.trades.append(trade)

if __name__ == "__main__":
    from src.data.loader import fetch_data
    from src.analysis.indicators import add_indicators
    from src.analysis.signals import generate_signals
    
    # Setup Data
    df = fetch_data("NVDA")
    df = add_indicators(df)
    
    # Use median bandwidth for test signals
    median_bw = df['Bandwidth'].median()
    df = generate_signals(df, bandwidth_threshold=median_bw)
    
    # Run Backtest
    # Using new ATR params: SL=2.0 ATR, TP=3.0 ATR
    engine = Backtester(atr_multiplier_sl=2.0, atr_multiplier_tp=3.0)
    results = engine.run(df)
    
    print("Backtest Results:")
    if not results.empty:
        print(results)
        print(f"\nTotal PnL: {results['PnL'].sum() * 100:.2f}%")
        print(f"Win Rate: {len(results[results['PnL'] > 0]) / len(results) * 100:.1f}%")
    else:
        print("No trades generated.")

