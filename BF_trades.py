import os
import time
import json
import requests
import pandas as pd
from datetime import datetime


def get_trades():
    r = requests.get('https://api.bitflyer.com/v1/getexecutions', params=dict(product_code=symbol, count=500))
    data = r.json()
    df = pd.DataFrame(data[::-1], dtype='float').set_index('exec_date')
    last_date = pd.to_datetime(df.index, utc=True).tz_localize(None)[-1]
    ID = data[-1]['id']
    count = 0
    while start_date <= last_date:
        if count % 500 == 0:
            print(last_date)
        count += 1
        temp_r = requests.get('https://api.bitflyer.com/v1/getexecutions',
                              params=dict(product_code=symbol, count=500, before=ID))
        temp_data = temp_r.json()
        temp_df = pd.DataFrame(temp_data[::-1], dtype='float').set_index('exec_date')
        last_date = pd.to_datetime(temp_df.index, utc=True).tz_localize(None)[-1]
        ID = int(temp_data[-1]['id'])
        df = pd.concat([temp_df, df])
        time.sleep(0.59)
    df.index = pd.to_datetime(df.index, utc=True).tz_localize(None)
    df = df.astype({'price': 'float', 'size': 'float'})
    if os.path.isfile(path):
        old_df = pd.read_csv(path, index_col='exec_date', parse_dates=True)
        df = pd.concat([old_df, df])
        df = df.drop_duplicates()
    df.to_csv(path)
    print(f'Output --> {path}')


if __name__ == '__main__':
    start = time.time()
    with open('config/bf_config.json', 'r', encoding="utf-8") as f:
        config = json.load(f)
    if not os.path.isdir("csv"):
        os.makedirs("csv")
    symbol = config['symbol']  # FX_BTC_JPY, BTC_JPY, ETH_JPY etc...
    path = f'csv/bf_trades_{symbol}.csv'
    if os.path.isfile(path):
        print(f"Found old data\nDiff update...\nMerge {path}")
        df_old = pd.read_csv(path, index_col='exec_date', parse_dates=True)
        start_date = df_old.index[-1]
    else:
        start_time_str = config['date']  # 例:2021-08-30 21:00:00
        start_date = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')

    print(f'Get bitflyer trades from {symbol}\nUntil --> {start_date}')
    try:
        get_trades()
        end_time = time.time() - start
        print(f'{end_time / 60:.2f}min')
    except KeyboardInterrupt:
        pass
