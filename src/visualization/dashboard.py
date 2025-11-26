import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_dashboard(df: pd.DataFrame, trades: pd.DataFrame = None):
    """
    Creates an interactive Plotly dashboard for the Trinity Strategy.
    
    Layout:
    1. Main Chart: Candlestick, Bollinger Bands, Buy/Sell Markers.
    2. Subplot 1: RSI (14) with 30/70 levels.
    3. Subplot 2: MACD (Line, Signal, Hist).
    
    Args:
        df: DataFrame with OHLCV and Indicators.
        trades: DataFrame with trade log (Entry/Exit).
    
    Returns:
        plotly.graph_objects.Figure: The dashboard figure.
    """
    # Create Subplots
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.6, 0.2, 0.2],
        subplot_titles=('Price Action & Bollinger Bands', 'RSI (14)', 'MACD (12,26,9)')
    )
    
    # --- Row 1: Price & BB ---
    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='OHLC'
    ), row=1, col=1)
    
    # Bollinger Bands
    # Upper (Gray dashed?)
    fig.add_trace(go.Scatter(
        x=df.index, y=df['BBU'],
        line=dict(color='gray', width=1, dash='dash'),
        name='Upper BB'
    ), row=1, col=1)
    
    # Lower
    fig.add_trace(go.Scatter(
        x=df.index, y=df['BBL'],
        line=dict(color='gray', width=1, dash='dash'),
        name='Lower BB',
        fill='tonexty', # Fill between Upper and Lower? 
        # Plotly fills to previous trace. If we add Upper then Lower, it fills between.
        # But 'tonexty' fills to the trace before it.
        fillcolor='rgba(128, 128, 128, 0.1)'
    ), row=1, col=1)
    
    # Mid (Orange)
    fig.add_trace(go.Scatter(
        x=df.index, y=df['BBM'],
        line=dict(color='orange', width=1),
        name='Moving Avg (20)'
    ), row=1, col=1)
    
    # Trade Markers
    if trades is not None and not trades.empty:
        # Entries (Green Triangle Up)
        fig.add_trace(go.Scatter(
            x=trades['Entry Time'],
            y=trades['Entry Price'],
            mode='markers',
            marker=dict(symbol='triangle-up', color='green', size=12),
            name='Buy Signal'
        ), row=1, col=1)
        
        # Exits (Red Square or Triangle Down?)
        # Let's distinguish Profit vs Loss?
        # For MVP, just Red Square.
        fig.add_trace(go.Scatter(
            x=trades['Exit Time'],
            y=trades['Exit Price'],
            mode='markers',
            marker=dict(symbol='square', color='red', size=10),
            name='Sell/Exit'
        ), row=1, col=1)

    # --- Row 2: RSI ---
    fig.add_trace(go.Scatter(
        x=df.index, y=df['RSI'],
        line=dict(color='purple', width=2),
        name='RSI'
    ), row=2, col=1)
    
    # 30/70 Lines
    fig.add_hline(y=70, line_dash="dot", row=2, col=1, line_color="red")
    fig.add_hline(y=30, line_dash="dot", row=2, col=1, line_color="green")
    
    # --- Row 3: MACD ---
    # Histogram
    colors = ['green' if v >= 0 else 'red' for v in df['MACDh']]
    fig.add_trace(go.Bar(
        x=df.index, y=df['MACDh'],
        marker_color=colors,
        name='MACD Hist'
    ), row=3, col=1)
    
    # MACD Line (Blue)
    fig.add_trace(go.Scatter(
        x=df.index, y=df['MACD'],
        line=dict(color='blue', width=1.5),
        name='MACD Line'
    ), row=3, col=1)
    
    # Signal Line (Orange)
    fig.add_trace(go.Scatter(
        x=df.index, y=df['MACDs'],
        line=dict(color='orange', width=1.5),
        name='Signal Line'
    ), row=3, col=1)
    
    # Layout Updates
    fig.update_layout(
        title='Trinity Strategy Backtest Analysis',
        xaxis_rangeslider_visible=False,
        height=800,
        template='plotly_dark'
    )
    
    return fig

if __name__ == "__main__":
    # Test execution (Generate a dummy chart HTML)
    from src.data.loader import fetch_data
    from src.analysis.indicators import add_indicators
    from src.analysis.signals import generate_signals
    from src.engine.backtester import Backtester
    
    df = fetch_data("NVDA")
    df = add_indicators(df)
    median_bw = df['Bandwidth'].median()
    df = generate_signals(df, bandwidth_threshold=median_bw)
    
    engine = Backtester()
    trades = engine.run(df)
    
    fig = create_dashboard(df, trades)
    
    # Save to HTML
    output_path = "dashboard_test.html"
    fig.write_html(output_path)
    print(f"Dashboard saved to {output_path}")

