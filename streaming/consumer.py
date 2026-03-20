from kafka import KafkaConsumer
import json
from data.db_connection import get_connection

conn=get_connection()
cursor=conn.cursor()
consumer=KafkaConsumer('stock-prices',bootstrap_servers='localhost:9092',
                       value_deserializer=lambda x: json.loads(x.decode('utf-8')
                    ))

for message in consumer:
    data=message.value
    cursor.execute("INSERT INTO stock_prices (time,symbol,close) values(%s,%s,%s) ON CONFLICT DO NOTHING",
                       (data['time'],data['symbol'],data['price']))
    conn.commit()
    print(f" Data for {data['symbol']} inserted successfully")

