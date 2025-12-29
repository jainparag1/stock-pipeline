from kafka import KafkaProducer
import json, random, time

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

tickers = ['AAPL', 'GOOG', 'MSFT', 'TSLA']

while True:
    data = {
        'ticker': random.choice(tickers),
        'price': round(random.uniform(100, 1500), 2),
        'volume': random.randint(100, 1000),
        'timestamp': time.time()
    }
    print(f"Sending: {data}")
    producer.send('stock-ticks', value=data)
    time.sleep(5)