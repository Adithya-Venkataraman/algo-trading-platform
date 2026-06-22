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
    WHERE symbol = 'BTC-USD'
    AND rsi IS NOT NULL
    AND sma_200 IS NOT NULL
    ORDER BY time ASC
"""
features_df = pd.read_sql(feature_query, engine)
features_df['time'] = pd.to_datetime(
    features_df['time']).dt.tz_localize(None)
features_df['time']=features_df['time'].dt.date
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
    
    if confidence < 0.60:
        signals[idx] = 'FLAT'
    elif signal == 1:
        signals[idx] = 'BUY'
    else:
        signals[idx] = 'SELL'

print(f"Signals computed for {len(signals)} days! ✅")
print(f"Sample signals: {list(signals.items())[:5]}")
print(f"Total signals: {len(signals)}")
print(f"BUY signals: {list(signals.values()).count('BUY')}")
print(f"SELL signals: {list(signals.values()).count('SELL')}")
print(f"FLAT signals: {list(signals.values()).count('FLAT')}")


# ── DRIFT STRATEGY ──
class DriftStrategy(bt.Strategy):
    
    def __init__(self):
        self.order = None
    def next(self):
        if self.order:
            return
    
        current_date = self.data.datetime.date(0)
        signal = signals.get(current_date, 'NOT FOUND')
    
    # print every day to debug
        print(f"Day: {current_date} | Signal: {signal}")
    
    # remove the if len(self) < 4 check!
    # signals only start from 2021-09-24
    # backtest runs from 2021-06-15
    # first 100 days = FLAT (no signal) = normal! ✅
    
        if self.position:
            entry_price = self.position.price
            current_price = self.data.close[0]
            pnl_pct = (current_price - entry_price) / entry_price
        
            if pnl_pct < -0.02:
                self.order = self.sell(size=self.position.size)
                print(f"STOP LOSS @ ${current_price:.2f}")
                return
        
            if pnl_pct > 0.03:
                self.order = self.sell(size=self.position.size)
                print(f"TAKE PROFIT @ ${current_price:.2f}")
                return
    
        portfolio_value = self.broker.getvalue()
        position_size = portfolio_value * 0.10
    
        if signal == 'BUY' and not self.position:
    # use cash directly instead of shares
            cash = self.broker.getcash()
            size = (cash * 0.10) / self.data.close[0]  # fractional!
            if size > 0.001:  # minimum 0.001 BTC
                self.order = self.buy(size=size)
                print(f"BUY {size:.4f} BTC @ ${self.data.close[0]:.2f}")
        
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
    WHERE symbol = 'BTC-USD'
    ORDER BY time ASC
"""
df = pd.read_sql(query, engine, index_col='time', 
                 parse_dates=True)
df.columns = df.columns.str.capitalize()
# fix timezone
df.index = pd.to_datetime(df.index)
if df.index.tzinfo is not None:
    df.index = df.index.tz_convert(None)
# remove duplicates + sort
df = df[~df.index.duplicated(keep='first')]
df = df.sort_index()
print(f"df shape: {df.shape}")
print(f"df index sample: {df.index[:3]}")

# ── RUN BACKTEST ──
cerebro = bt.Cerebro()
cerebro.addstrategy(DriftStrategy)

data = bt.feeds.PandasData(dataname=df)
cerebro.adddata(data)

cerebro.broker.set_shortcash(False)
cerebro.broker.setcommission(commission=0.001)  # 0.1% commission

print(f"Starting Portfolio: ${cerebro.broker.getvalue():.2f}")
# add analyzers
cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
print(f"Data length: {len(df)}")
print(f"Cerebro data: {cerebro.datas[0]._name}")
print(df.head())
print(df.dtypes)
results = cerebro.run()
strat = results[0]

final_value = cerebro.broker.getvalue()
total_return = ((final_value - 10000) / 10000) * 100

print(f"\n=== PERFORMANCE METRICS ===")
print(f"Final Portfolio: ${final_value:.2f}")
print(f"Total Return:    {total_return:.2f}%")

# sharpe ratio
sharpe = strat.analyzers.sharpe.get_analysis().get('sharperatio')
print(f"Sharpe Ratio:    {f'{sharpe:.4f}' if sharpe else 'N/A'}")

# drawdown
drawdown = strat.analyzers.drawdown.get_analysis()
print(f"Max Drawdown:    {drawdown['max']['drawdown']:.2f}%")

# trades
trades = strat.analyzers.trades.get_analysis()
total = trades.get('total', {}).get('total', 0)
won = trades.get('won', {}).get('total', 0)
print(f"Total Trades:    {total}")
print(f"Win Rate:        {won/total*100:.2f}%" if total > 0 else "Win Rate: N/A")

# debug signals
print(f"\n=== SIGNAL DEBUG ===")
print(f"Total signals:   {len(signals)}")
print(f"BUY signals:     {list(signals.values()).count('BUY')}")
print(f"SELL signals:    {list(signals.values()).count('SELL')}")
print(f"FLAT signals:    {list(signals.values()).count('FLAT')}")

# check date formats
print(f"\nFirst signal date: {list(signals.keys())[0]}")
print(f"First signal type: {type(list(signals.keys())[0])}")
print(f"\nFirst price date: {df.index[0]}")
print(f"First price type: {type(df.index[0])}")