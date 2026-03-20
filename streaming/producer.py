from kafka import KafkaProducer
import json
from datetime import datetime
import yfinance as yf
import time
producer=KafkaProducer(bootstrap_servers='localhost:9092',
                       value_serializer=lambda x: json.dumps(x).encode('utf-8')
)
tickers=["AAPL","GOOG","MSFT","AMZN","BTC-USD"]
while True:
    for ticker in tickers:
        tr=yf.Ticker(ticker)
        price=tr.fast_info.last_price
        producer.send('stock-prices',
                      value={'symbol':ticker,
                             'price':price,
                         'time':datetime.now().isoformat()
            })
    print("Data sent to Kafka topic:'stock-prices' ✅")
    time.sleep(1)
