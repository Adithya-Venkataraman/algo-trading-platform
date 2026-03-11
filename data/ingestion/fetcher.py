import sys
sys.path.append('/home/jingv/algo-trading-platform')
from data.db_connection import get_connection
import yfinance as yf
conn=get_connection()
cursor = conn.cursor()
tickers=["AAPL","GOOG","MSFT","AMZN","BTC-USD"]

for ticker in tickers:
    try:
        t=yf.Ticker(ticker)
        df=t.history(period="1y")
        for index,row in df.iterrows():
            cursor.execute("INSERT INTO stock_prices(time,symbol,open,high,low,close,volume) values(%s,%s,%s,%s,%s,%s,%s)",
            (index, ticker, float(row['Open']), float(row['High']), float(row['Low']), float(row['Close']), int(row['Volume'])))
        conn.commit()
        print(f"Data for {ticker} inserted successfully")
    except Exception as e:
        print(f"Error inserting data for {ticker}: {e}")
conn.close()
    