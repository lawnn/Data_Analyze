import requests
import pandas as pd


symbol = 'BTC'
interval = '1min'
date = '20210417'

r = requests.get(f'https://api.coin.z.com/public/v1/klines', params=dict(symbol=symbol, interval=interval, date=date))
data = r.json()
df = pd.DataFrame(data['data'])
df.rename(columns={'openTime': 'time'}, inplace=True)
df = df.set_index('time')
df.index = pd.to_datetime(df.index, unit='ms', utc=True).tz_convert('Asia/Tokyo').tz_localize(None)
print(df)
