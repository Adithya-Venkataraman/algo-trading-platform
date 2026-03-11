import pandas
def calculate_rsi(df,period=14):
    delta=df['Close'].diff()
    gain=delta.where(delta>0,0)
    loss=-delta.where(delta<0,0)
    avg_gain=gain.ewm(com=period-1).mean()
    avg_loss=loss.ewm(com=period-1).mean()
    rs=avg_gain/avg_loss
    rsi=100-(100/(1+rs))
    return rsi

tickers=["AAPL","GOOG","MSFT","AMZN","BTC-USD"]
if __name__=="__main__":
    import yfinance as yf
    for ticker in tickers:
        t=yf.Ticker(ticker)
        df=t.history(period="1y")
        rsi=calculate_rsi(df)
        print(rsi.tail(10))