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

def calculate_macd(df,short_period=12,long_period=26,signal_period=9):
	ema_short=df['Close'].ewm(span=short_period,adjust=False).mean()
	ema_long=df['Close'].ewm(span=long_period,adjust=False).mean()
	macd=ema_short-ema_long	
	signal=macd.ewm(span=signal_period,adjust=False).mean()
	histogram=macd-signal
	return macd,signal,histogram

def bollinger_bands(df,period=20):
	middle=df['Close'].rolling(window=period).mean()
	std=df['Close'].rolling(window=period).std()
	upper=middle+(2*std)
	lower=middle-(2*std)
	return upper,middle,lower

def calculate_moving_averages(df):
	sma_20=df['Close'].rolling(window=20).mean()
	sma_50=df['Close'].rolling(window=50).mean()
	sma_200=df['Close'].rolling(window=200).mean()
	ema_12=df['Close'].ewm(span=12,adjust=False).mean()
	ema_26=df['Close'].ewm(span=26,adjust=False).mean()
	return sma_20,sma_50,sma_200,ema_12,ema_26

tickers=["AAPL","GOOG","MSFT","AMZN","BTC-USD"]
if __name__ == "__main__":
    import yfinance as yf
    ticker = yf.Ticker("AAPL")
    df = ticker.history(period="1y")
    upper,middle,lower=bollinger_bands(df)
    print("UPPER:\n")
    print(upper.tail())
    print("MIDDLE:\n")
    print(middle.tail())
    print("LOWER:\n")
    print(lower.tail())

