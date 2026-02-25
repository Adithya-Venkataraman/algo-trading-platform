
import yfinance as yf
tickers=["MSFT","AAPL","GOOG","AMZN","META"]
for ticker in tickers:
    t=yf.Ticker(ticker)
    df=t.history(period="1y")
    print(df.tail())
    print(f"{ticker} shape: {df.shape}")
    print(f"{ticker} date range: {df.index.min()} to {df.index.max()}")