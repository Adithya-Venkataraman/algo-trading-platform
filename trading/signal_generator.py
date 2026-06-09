import mlflow
import pandas as pd
import numpy as np
import sys
import joblib
import xgboost as xgb
from sqlalchemy import create_engine

sys.path.append('/home/jingv/algo-trading-platform')


def kelly_criterion(win_prob, win_loss_ratio=1.5):
    loss_prob = 1 - win_prob
    kelly = (win_loss_ratio * win_prob - loss_prob) / win_loss_ratio
    return min(kelly, 0.05)


def get_latest_features(symbol):
    engine = create_engine(
        'postgresql://trading:trading123@localhost:5432/trading_db'
    )
    query = f"""
        SELECT rsi, macd, macd_signal, macd_hist,
               bb_upper, bb_middle, bb_lower,
               sma_20, sma_50, sma_200, ema_12, ema_26
        FROM stock_features 
        WHERE symbol = '{symbol}'
        AND rsi IS NOT NULL
        AND sma_200 IS NOT NULL
        ORDER BY time DESC 
        LIMIT 1
    """
    df = pd.read_sql(query, engine)
    return df


def generate_signal(symbol, model, scaler, le):
    df = get_latest_features(symbol)
    
    feature_cols = ['rsi', 'macd', 'macd_signal', 
                    'macd_hist', 'bb_upper', 'bb_middle',
                    'bb_lower', 'sma_20', 'sma_50', 
                    'sma_200', 'ema_12', 'ema_26']
    
    X = df[feature_cols]
    X_scaled = scaler.transform(X)
    
    proba = model.predict_proba(X_scaled)[0]
    pred = model.predict(X_scaled)[0]
    confidence = max(proba)
    
    signal = le.inverse_transform([pred])[0]
    signal_name = "BUY" if signal == 1 else "SELL"
    
    if confidence < 0.65:
        signal_name = "FLAT"
    
    position_size = kelly_criterion(confidence)
    
    return {
        "symbol": symbol,
        "signal": signal_name,
        "confidence": round(float(confidence), 4),
        "position_size": round(float(position_size), 4)
    }


def apply_risk_rules(signal, portfolio_drawdown, active_positions):
    if portfolio_drawdown > 0.10:
        return {"signal": "FLAT", "reason": "max drawdown exceeded!"}
    if active_positions >= 3:
        return {"signal": "FLAT", "reason": "max positions reached"}
    return signal


if __name__ == "__main__":
    # load model, scaler, label encoder
    model_xgb = xgb.XGBClassifier()
    model_xgb.load_model('models/training/xgboost_tuned.json')
    scaler = joblib.load('models/training/scaler.pkl')
    le = joblib.load('models/training/label_encoder.pkl')
    
    print("Models loaded! ✅")
    print(f"Kelly test: {kelly_criterion(0.57):.4f}")
    
    # generate signals for all tickers
    tickers = ["AAPL", "MSFT", "GOOG", "AMZN", "BTC-USD"]
    
    for ticker in tickers:
        signal = generate_signal(ticker, model_xgb, scaler, le)
        print(f"\n🚀 {ticker} Signal:")
        print(signal)