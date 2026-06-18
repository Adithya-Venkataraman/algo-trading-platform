import sys
sys.path.append('/home/jingv/algo-trading-platform')
import backtrader as bt
import pandas as pd
import joblib
import xgboost as xgb
import numpy as np
from sqlalchemy import create_engine
from trading.signal_generator import generate_signal

# ── LOAD MODEL ──
model_xgb = xgb.XGBClassifier()
model_xgb.load_model('models/training/xgboost_tuned.json')
scaler = joblib.load('models/training/scaler.pkl')
le = joblib.load('models/training/label_encoder.pkl')

# pre-compute all signals
print("Pre-computing signals...")
from sqlalchemy import create_engine
engine = create_engine(
    'postgresql://trading:trading123@localhost:5432/trading_db'
)

feature_query = """
    SELECT time, rsi, macd, macd_signal, macd_hist,
           bb_upper, bb_middle, bb_lower,
           sma_20, sma_50, sma_200, ema_12, ema_26
    FROM stock_features
    WHERE symbol = 'AAPL'
    AND rsi IS NOT NULL
    AND sma_200 IS NOT NULL
    ORDER BY time ASC
"""
features_df = pd.read_sql(feature_query, engine)
features_df['time'] = pd.to_datetime(
    features_df['time']).dt.tz_localize(None)
features_df.set_index('time', inplace=True)

# generate signal for each row
signals = {}
for idx, row in features_df.iterrows():
    X = row.values.reshape(1, -1)
    X_scaled = scaler.transform(X)
    proba = model_xgb.predict_proba(X_scaled)[0]
    pred = model_xgb.predict(X_scaled)[0]
    confidence = max(proba)
    signal = le.inverse_transform([pred])[0]
    
    if confidence < 0.65:
        signals[idx.date()] = 'FLAT'
    elif signal == 1:
        signals[idx.date()] = 'BUY'
    else:
        signals[idx.date()] = 'SELL'

print(f"Signals computed for {len(signals)} days! ✅")
# ── DRIFT STRATEGY ──
class DriftStrategy(bt.Strategy):
    
    def __init__(self):
        self.order = None
        
    def next(self):
        if self.order:
            return
    
    # lookup precomputed signal
        current_date = self.data.datetime.date(0)
        signal = signals.get(current_date, 'FLAT')
        confidence = 0.7  # default
    
        portfolio_value = self.broker.getvalue()
        position_size = portfolio_value * 0.05
    
        if signal == 'BUY' and not self.position:
            size = int(position_size / self.data.close[0])
            if size > 0:
                self.order = self.buy(size=size)
                print(f"BUY {size} @ ${self.data.close[0]:.2f}")
            
        elif signal == 'SELL' and self.position:
            self.order = self.sell(size=self.position.size)
            print(f"SELL @ ${self.data.close[0]:.2f}")

    def notify_order(self, order):
        if order.status in [order.Completed]:
            self.order = None

# ── FETCH AAPL DATA ──
engine = create_engine(
    'postgresql://trading:trading123@localhost:5432/trading_db'
)

query = """
    SELECT time, open, high, low, close, volume
    FROM stock_prices
    WHERE symbol = 'AAPL'
    ORDER BY time ASC
"""
df = pd.read_sql(query, engine, index_col='time', 
                 parse_dates=True)
df.columns = df.columns.str.capitalize()
df.index = pd.to_datetime(df.index, utc=True)
df.index = df.index.tz_localize(None) if df.index.tzinfo else df.index

# ── RUN BACKTEST ──
cerebro = bt.Cerebro()
cerebro.addstrategy(DriftStrategy)

data = bt.feeds.PandasData(dataname=df)
cerebro.adddata(data)

cerebro.broker.setcash(10000)
cerebro.broker.setcommission(commission=0.001)  # 0.1% commission

print(f"Starting Portfolio: ${cerebro.broker.getvalue():.2f}")
# add analyzers
cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')

results = cerebro.run()
strat = results[0]

start = 10000
end = cerebro.broker.getvalue()
total_return = ((end - start) / start) * 100
print(f"Total Return:       {total_return:.2f}%")
# print analysis
print(f"\n=== PERFORMANCE METRICS ===")
print(f"Total Return:    {total_return:.2f}%")
print(f"Sharpe Ratio:    {strat.analyzers.sharpe.get_analysis()['sharperatio']:.4f}")
print(f"Max Drawdown:    {strat.analyzers.drawdown.get_analysis()['max']['drawdown']:.2f}%")
trades = strat.analyzers.trades.get_analysis()
print(f"Total Trades:    {trades.total.total}")
print(f"Win Rate:        {trades.won.total/trades.total.total*100:.2f}%")
cerebro.run()
print(f"Final Portfolio:    ${cerebro.broker.getvalue():.2f}")

# calculate return
