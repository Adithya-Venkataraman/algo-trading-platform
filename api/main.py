import sys
sys.path.append('/home/jingv/algo-trading-platform')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import joblib
import xgboost as xgb
from trading.signal_generator import generate_signal
from sqlalchemy import create_engine
import pandas as pd
from datetime import datetime

# initialize app
app = FastAPI(
    title="DRIFT Trading API",
    description="Algorithmic Trading Signal API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# load model
model_xgb = xgb.XGBClassifier()
model_xgb.load_model('models/training/xgboost_tuned.json')
scaler = joblib.load('models/training/scaler.pkl')
le = joblib.load('models/training/label_encoder.pkl')

engine = create_engine(
    'postgresql://trading:trading123@localhost:5432/trading_db'
)

# ── ENDPOINTS ──

@app.get("/")
def home():
    return {
        "name": "DRIFT Trading API",
        "version": "1.0.0",
        "status": "running ✅"
    }

@app.get("/signal/{symbol}")
def get_signal(symbol: str):
    signal_data = generate_signal(
        symbol.upper(), model_xgb, scaler, le)
    return {
        "symbol": symbol.upper(),
        "signal": signal_data['signal'],
        "confidence": signal_data['confidence'],
        "position_size": signal_data['position_size'],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/signals/all")
def get_all_signals():
    tickers = ["AAPL", "MSFT", "GOOG", "AMZN", "BTC-USD"]
    signals = {}
    for ticker in tickers:
        signals[ticker] = generate_signal(
            ticker, model_xgb, scaler, le)
    return {
        "signals": signals,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/prices/{symbol}")
def get_prices(symbol: str, days: int = 30):
    query = f"""
        SELECT time, close
        FROM stock_prices
        WHERE symbol = '{symbol.upper()}'
        AND time >= NOW() - INTERVAL '{days} days'
        ORDER BY time ASC
    """
    df = pd.read_sql(query, engine)
    return {
        "symbol": symbol.upper(),
        "prices": df.to_dict(orient='records')
    }

@app.get("/portfolio/performance")
def get_performance():
    return {
        "backtest_return": "21.81%",
        "win_rate": "51.91%",
        "max_drawdown": "9.54%",
        "sharpe_ratio": 0.42,
        "total_trades": 262,
        "best_model": "XGBoost (Optuna tuned)",
        "model_accuracy": "58%"
    }