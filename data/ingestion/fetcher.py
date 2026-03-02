import sys
sys.path.append('/home/jingv/algo-trading-platform')
from data.db_connection import get_connection
import yfinance as yf
conn=get_connection()
cursor = conn.cursor()
tickers=["AAPL"]

for ticker in tickers:
    t=yf.Ticker(ticker)
    df=t.history(period="1y")
    for index,row in df.iterrows():
        cursor.execute("INSERT INTO stock_prices(time,symbol,open,high,low,close,volume) values(%s,%s,%s,%s,%s,%s,%s)",
    (index, ticker, float(row['Open']), float(row['High']), float(row['Low']), float(row['Close']), int(row['Volume'])))
    conn.commit()
print("Data inserted Successfully")
conn.close()
    