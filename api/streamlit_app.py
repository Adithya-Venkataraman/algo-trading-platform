import sys
sys.path.append('/home/jingv/algo-trading-platform')
import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sqlalchemy import create_engine
from datetime import datetime

# page config
st.set_page_config(
    page_title="DRIFT Trading Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_URL = "http://localhost:8000"
engine = create_engine(
    'postgresql://trading:trading123@localhost:5432/trading_db'
)

# ── SIDEBAR ──
st.sidebar.title("⚙️ DRIFT Controls")
st.sidebar.divider()

selected_ticker = st.sidebar.selectbox(
    "📊 Select Ticker",
    ["AAPL", "MSFT", "GOOG", "AMZN", "BTC-USD"]
)

days = st.sidebar.slider("📅 Days of History", 7, 365, 90)

st.sidebar.divider()
st.sidebar.subheader("📈 Indicators")
show_rsi = st.sidebar.checkbox("RSI", value=True)
show_macd = st.sidebar.checkbox("MACD", value=True)
show_bb = st.sidebar.checkbox("Bollinger Bands", value=True)
show_sma = st.sidebar.checkbox("Moving Averages", value=True)

st.sidebar.divider()
if st.sidebar.button("🔄 Refresh All Data"):
    st.rerun()

# ── TITLE ──
st.title("📈 DRIFT — Algorithmic Trading Platform")
st.markdown("*Production-grade ML-powered trading signals*")
st.divider()

# ── PERFORMANCE METRICS ──
st.subheader("🏆 Backtest Performance (5 Years BTC-USD)")
perf = requests.get(f"{API_URL}/portfolio/performance").json()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Return", perf['backtest_return'], "vs Buy & Hold")
col2.metric("Win Rate", perf['win_rate'])
col3.metric("Max Drawdown", perf['max_drawdown'])
col4.metric("Sharpe Ratio", perf['sharpe_ratio'])
col5.metric("Model Accuracy", perf['model_accuracy'])

st.divider()

# ── LIVE SIGNALS ──
st.subheader("🚀 Live Trading Signals")
signals_resp = requests.get(f"{API_URL}/signals/all").json()
tickers = ["AAPL", "MSFT", "GOOG", "AMZN", "BTC-USD"]
cols = st.columns(5)

for i, ticker in enumerate(tickers):
    signal_data = signals_resp['signals'][ticker]
    signal = signal_data['signal']
    confidence = signal_data['confidence']
    position_size = signal_data['position_size']

    if signal == "BUY":
        color = "🟢"
        delta_color = "normal"
    elif signal == "SELL":
        color = "🔴"
        delta_color = "inverse"
    else:
        color = "⚪"
        delta_color = "off"

    with cols[i]:
        st.metric(
            label=f"**{ticker}**",
            value=f"{color} {signal}",
            delta=f"{confidence:.0%} confidence"
        )
        st.caption(f"Position: {position_size:.0%} of portfolio")

st.divider()

# ── FETCH DATA ──
@st.cache_data(ttl=300)
def fetch_price_data(ticker, days):
    query = f"""
        SELECT time, open, high, low, close, volume
        FROM stock_prices
        WHERE symbol = '{ticker}'
        AND time >= NOW() - INTERVAL '{days} days'
        ORDER BY time ASC
    """
    df = pd.read_sql(query, engine)
    df['time'] = pd.to_datetime(df['time'])
    return df

@st.cache_data(ttl=300)
def fetch_feature_data(ticker, days):
    query = f"""
        SELECT time, rsi, macd, macd_signal, macd_hist,
               bb_upper, bb_middle, bb_lower,
               sma_20, sma_50, sma_200, ema_12, ema_26
        FROM stock_features
        WHERE symbol = '{ticker}'
        AND rsi IS NOT NULL
        AND time >= NOW() - INTERVAL '{days} days'
        ORDER BY time ASC
    """
    df = pd.read_sql(query, engine)
    df['time'] = pd.to_datetime(df['time'])
    return df

price_df = fetch_price_data(selected_ticker, days)
feature_df = fetch_feature_data(selected_ticker, days)

# ── MAIN CHART ──
st.subheader(f"📊 {selected_ticker} — Technical Analysis")

# count how many subplots needed
num_plots = 1
if show_rsi: num_plots += 1
if show_macd: num_plots += 1

row_heights = [0.5] + [0.25] * (num_plots - 1)
subplot_titles = [f"{selected_ticker} Price"]
if show_rsi: subplot_titles.append("RSI")
if show_macd: subplot_titles.append("MACD")

fig = make_subplots(
    rows=num_plots, cols=1,
    shared_xaxes=True,
    subplot_titles=subplot_titles,
    row_heights=row_heights,
    vertical_spacing=0.05
)

# ── PRICE + BOLLINGER BANDS ──
if show_bb and not feature_df.empty:
    fig.add_trace(go.Scatter(
        x=feature_df['time'], y=feature_df['bb_upper'],
        name='BB Upper', line=dict(color='gray', dash='dash', width=1),
        opacity=0.5
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=feature_df['time'], y=feature_df['bb_lower'],
        name='BB Lower', line=dict(color='gray', dash='dash', width=1),
        fill='tonexty', fillcolor='rgba(128,128,128,0.1)',
        opacity=0.5
    ), row=1, col=1)

# candlestick
if not price_df.empty:
    fig.add_trace(go.Candlestick(
        x=price_df['time'],
        open=price_df['open'],
        high=price_df['high'],
        low=price_df['low'],
        close=price_df['close'],
        name=selected_ticker,
        increasing_line_color='#00ff88',
        decreasing_line_color='#ff4444'
    ), row=1, col=1)

# moving averages
if show_sma and not feature_df.empty:
    fig.add_trace(go.Scatter(
        x=feature_df['time'], y=feature_df['sma_20'],
        name='SMA 20', line=dict(color='yellow', width=1)
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=feature_df['time'], y=feature_df['sma_50'],
        name='SMA 50', line=dict(color='orange', width=1)
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=feature_df['time'], y=feature_df['sma_200'],
        name='SMA 200', line=dict(color='red', width=1)
    ), row=1, col=1)

# ── RSI ──
current_row = 2
if show_rsi and not feature_df.empty:
    fig.add_trace(go.Scatter(
        x=feature_df['time'], y=feature_df['rsi'],
        name='RSI', line=dict(color='purple', width=2)
    ), row=current_row, col=1)

    # overbought/oversold lines
    fig.add_hline(y=70, line_dash="dash",
                  line_color="red", opacity=0.5,
                  row=current_row, col=1)
    fig.add_hline(y=30, line_dash="dash",
                  line_color="green", opacity=0.5,
                  row=current_row, col=1)
    fig.add_hline(y=50, line_dash="dot",
                  line_color="gray", opacity=0.3,
                  row=current_row, col=1)

    current_row += 1

# ── MACD ──
if show_macd and not feature_df.empty:
    fig.add_trace(go.Scatter(
        x=feature_df['time'], y=feature_df['macd'],
        name='MACD', line=dict(color='blue', width=2)
    ), row=current_row, col=1)
    fig.add_trace(go.Scatter(
        x=feature_df['time'], y=feature_df['macd_signal'],
        name='Signal', line=dict(color='orange', width=2)
    ), row=current_row, col=1)
    fig.add_bar(
        x=feature_df['time'],
        y=feature_df['macd_hist'],
        name='Histogram',
        marker_color=feature_df['macd_hist'].apply(
            lambda x: '#00ff88' if x > 0 else '#ff4444'),
        row=current_row, col=1
    )

# layout
fig.update_layout(
    template='plotly_dark',
    height=800,
    showlegend=True,
    xaxis_rangeslider_visible=False,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    )
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── INDICATOR VALUES ──
st.subheader("📋 Current Indicator Values")

if not feature_df.empty:
    latest = feature_df.iloc[-1]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Momentum**")
        rsi_val = latest['rsi']
        rsi_status = "🔴 Overbought" if rsi_val > 70 else "🟢 Oversold" if rsi_val < 30 else "⚪ Neutral"
        st.metric("RSI (14)", f"{rsi_val:.2f}", rsi_status)

    with col2:
        st.markdown("**Trend**")
        st.metric("MACD", f"{latest['macd']:.4f}")
        st.metric("Signal Line", f"{latest['macd_signal']:.4f}")
        st.metric("Histogram", f"{latest['macd_hist']:.4f}")

    with col3:
        st.markdown("**Moving Averages**")
        st.metric("SMA 20", f"{latest['sma_20']:.2f}")
        st.metric("SMA 50", f"{latest['sma_50']:.2f}")
        st.metric("SMA 200", f"{latest['sma_200']:.2f}")

st.divider()

# ── TICKER COMPARISON ──
st.subheader("📊 Multi-Ticker Comparison")

comparison_query = f"""
    SELECT time, symbol, close
    FROM stock_prices
    WHERE symbol IN ('AAPL', 'MSFT', 'GOOG', 'AMZN')
    AND time >= NOW() - INTERVAL '{days} days'
    ORDER BY time ASC
"""
comp_df = pd.read_sql(comparison_query, engine)
comp_df['time'] = pd.to_datetime(comp_df['time'])

# normalize to percentage change
fig2 = go.Figure()
colors = ['#00ff88', '#ff9944', '#4488ff', '#ff44aa']

for i, ticker in enumerate(['AAPL', 'MSFT', 'GOOG', 'AMZN']):
    ticker_df = comp_df[comp_df['symbol'] == ticker].copy()
    if not ticker_df.empty:
        base = ticker_df['close'].iloc[0]
        ticker_df['pct_change'] = ((ticker_df['close'] - base) / base) * 100
        fig2.add_trace(go.Scatter(
            x=ticker_df['time'],
            y=ticker_df['pct_change'],
            name=ticker,
            line=dict(color=colors[i], width=2)
        ))

fig2.update_layout(
    template='plotly_dark',
    title=f"Normalized Returns (%) - Last {days} Days",
    yaxis_title="Return (%)",
    height=400,
    hovermode='x unified'
)
fig2.add_hline(y=0, line_dash="dash",
               line_color="white", opacity=0.3)

st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ── FOOTER ──
col1, col2 = st.columns(2)
col1.markdown(
    f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
)
col2.markdown(
    "*DRIFT — Because markets drift, and so do models.* 🌊"
)