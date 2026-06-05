import mlflow
import pandas as pd
import numpy as np
import sys
sys.path.append('/home/jingv/algo-trading-platform')


# 1. Kelly Criterion function
def kelly_criterion(win_prob, win_loss_ratio=1.5):
    loss_prob = 1 - win_prob
    kelly = (win_loss_ratio * win_prob - loss_prob) / win_loss_ratio
    return min(kelly, 0.05)  # cap at 5%

# 2. Load best model from MLflow
def load_model():
    model = mlflow.xgboost.load_model(
        "runs:/<your_run_id>/model"
    )
    return model

# 3. Get latest features from database
def get_latest_features(symbol):
    conn = get_connection()
    query = f"""
        SELECT * FROM stock_features 
        WHERE symbol = '{symbol}'
        ORDER BY time DESC 
        LIMIT 1
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# 4. Generate signal
def generate_signal(symbol, model, scaler, le):
    # get latest features
    df = get_latest_features(symbol)
    
    # prepare features
    feature_cols = ['rsi', 'macd', 'macd_signal', 
                    'macd_hist', 'bb_upper', 'bb_middle',
                    'bb_lower', 'sma_20', 'sma_50', 
                    'sma_200', 'ema_12', 'ema_26']
    
    X = df[feature_cols].values
    X_scaled = scaler.transform(X)
    
    # get prediction + confidence
    proba = model.predict_proba(X_scaled)[0]
    pred = model.predict(X_scaled)[0]
    confidence = max(proba)
    
    # decode label
    signal = le.inverse_transform([pred])[0]
    signal_name = "BUY" if signal == 1 else "SELL"
    
    # apply confidence filter
    if confidence < 0.65:
        signal_name = "FLAT"  # not confident enough
    
    # calculate position size
    position_size = kelly_criterion(confidence)
    
    return {
        "symbol": symbol,
        "signal": signal_name,
        "confidence": round(float(confidence), 4),
        "position_size": round(float(position_size), 4)
    }

# 5. Test it
if __name__ == "__main__":
    # we need to pass model, scaler, le from train.py
    # for now just test the kelly function
    import sys
import joblib
import xgboost as xgb
sys.path.append('/home/jingv/algo-trading-platform')
from data.db_connection import get_connection
import pandas as pd

# load model, scaler, label encoder
model_xgb = xgb.XGBClassifier()
model_xgb.load_model('models/training/xgboost_tuned.json')
scaler = joblib.load('models/training/scaler.pkl')
le = joblib.load('models/training/label_encoder.pkl')

# fetch latest features for AAPL

query = """
    SELECT rsi, macd, macd_signal, macd_hist,
           bb_upper, bb_middle, bb_lower,
           sma_20, sma_50, sma_200, ema_12, ema_26
    FROM stock_features
    WHERE symbol = 'AAPL'
    AND rsi IS NOT NULL
    AND sma_200 IS NOT NULL
    ORDER BY time DESC
    LIMIT 1
"""
from sqlalchemy import create_engine
engine = create_engine(
    'postgresql://trading:trading123@localhost:5432/trading_db'
)
latest_features = pd.read_sql(query, engine)
print(f"Rows fetched: {len(latest_features)}")
print(latest_features)
print(latest_features.shape)
# test query without filters
test_query = """
    SELECT * FROM stock_features 
    WHERE symbol = 'AAPL' 
    ORDER BY time DESC 
    LIMIT 5
"""
test_df = pd.read_sql(test_query, engine)
print(test_df)

print("Latest AAPL features fetched! ✅")

# generate signal
signal = generate_signal(latest_features, model_xgb, scaler, le)
print("\n🚀 AAPL Trading Signal:")
print(signal)