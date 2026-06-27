import sys
sys.path.append('/home/jingv/algo-trading-platform')
import os
import alpaca_trade_api as tradeapi
from dotenv import load_dotenv
import joblib
import xgboost as xgb
import time
from trading.signal_generator import generate_signal
from datetime import datetime

load_dotenv()
API_KEY=os.getenv('ALPACA_API_KEY')
SECRET_KEY=os.getenv('ALPACA_SECRET_KEY')
BASE_URL=os.getenv('ALPACA_BASE_URL')

print(f"API Key loaded: {API_KEY[:8] if API_KEY else 'NOT FOUND'}...")
print(f"Secret loaded: {SECRET_KEY[:8] if SECRET_KEY else 'NOT FOUND'}...")
print(f"Base URL: {BASE_URL}")

api=tradeapi.REST(API_KEY,SECRET_KEY,BASE_URL)
model_xgb=xgb.XGBClassifier()
model_xgb.load_model('models/training/xgboost_tuned.json')
scaler=joblib.load('models/training/scaler.pkl')
le=joblib.load('models/training/label_encoder.pkl')

TICKERS=['AAPL','MSFT','GOOG','AMZN']
POSITION_SIZE=0.05

def get_portfolio_value():
    account=api.get_account()
    return float(account.portfolio_value)

def get_current_position(symbol):
    try:
        position=api.get_position(symbol)
        return float(position.qty)
    except:
        return 0

def place_buy_order(symbol, confidence):
    portfolio_value = get_portfolio_value()
    position_value = portfolio_value * POSITION_SIZE
    
    # get current price
    quote = api.get_latest_trade(symbol)
    current_price = quote.price
    
    qty = int(position_value / current_price)
    
    if qty > 0:
        api.submit_order(
            symbol=symbol,
            qty=qty,
            side='buy',
            type='market',
            time_in_force='day'
        )
        print(f"✅ BUY {qty} {symbol} @ ~${current_price:.2f} | confidence: {confidence:.2f}")

def place_sell_order(symbol):
    qty = get_current_position(symbol)
    if qty > 0:
        api.submit_order(
            symbol=symbol,
            qty=qty,
            side='sell',
            type='market',
            time_in_force='day'
        )
        print(f"🔴 SELL {qty} {symbol}")

def run_paper_trader():
    print(f"\n{'='*50}")
    print(f"DRIFT Paper Trader - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")
    
    # check account
    account = api.get_account()
    print(f"Portfolio Value: ${float(account.portfolio_value):,.2f}")
    print(f"Cash Available:  ${float(account.cash):,.2f}")
    print(f"{'='*50}\n")
    
    for ticker in TICKERS:
        try:
            # generate signal
            signal_data = generate_signal(
                ticker, model_xgb, scaler, le)
            signal = signal_data['signal']
            confidence = signal_data['confidence']
            
            print(f"{ticker}: {signal} (confidence: {confidence:.2f})")
            
            # get current position
            current_qty = get_current_position(ticker)
            
            # execute trade
            if signal == 'BUY' and current_qty == 0:
                place_buy_order(ticker, confidence)
                
            elif signal == 'SELL' and current_qty > 0:
                place_sell_order(ticker)
                
            else:
                print(f"{ticker}: No action (position: {current_qty})")
                
        except Exception as e:
            print(f"Error with {ticker}: {e}")
    
    print(f"\n{'='*50}")
    print("Paper trading run complete! ✅")

if __name__ == "__main__":
    run_paper_trader()

