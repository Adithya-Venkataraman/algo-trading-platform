import sys
import warnings
warnings.filterwarnings('ignore')
sys.path.append('/home/jingv/algo-trading-platform')
import pandas as pd
from data.db_connection import get_connection
from data.features.indicators import (
    calculate_rsi,
    calculate_macd,
    bollinger_bands,
    calculate_moving_averages
)

def safe_float(series, index):
    try:
        val = series.loc[index]
        if isinstance(val, pd.Series):
            val = val.iloc[0]
        return float(val) if not pd.isna(val) else None
    except:
        return None

def calculate_features(symbol):
    conn = get_connection()
    cursor = conn.cursor()
    query = "select * from stock_prices where symbol=%s order by time"
    df = pd.read_sql(query, conn, params=(symbol,), index_col='time')
    
    rsi = calculate_rsi(df)
    macd, signal, histogram = calculate_macd(df)
    upper, middle, lower = bollinger_bands(df)
    sma_20, sma_50, sma_200, ema_12, ema_26 = calculate_moving_averages(df)
    
    for index, row in df.iterrows():
        cursor.execute("""
            INSERT into stock_features(time,symbol,rsi,macd,macd_signal,
            macd_hist,bb_upper,bb_middle,bb_lower,sma_20,sma_50,sma_200,
            ema_12,ema_26)
            values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT DO NOTHING
        """, (
            index,
            symbol,
            safe_float(rsi, index),
            safe_float(macd, index),
            safe_float(signal, index),
            safe_float(histogram, index),
            safe_float(upper, index),
            safe_float(middle, index),
            safe_float(lower, index),
            safe_float(sma_20, index),
            safe_float(sma_50, index),
            safe_float(sma_200, index),
            safe_float(ema_12, index),
            safe_float(ema_26, index),
        ))
    conn.commit()
    conn.close()
    print(f"Features calculated for {symbol} ✅")

if __name__ == "__main__":
    tickers = ["AAPL", "MSFT", "GOOG", "AMZN", "BTC-USD"]
    for ticker in tickers:
        calculate_features(ticker)