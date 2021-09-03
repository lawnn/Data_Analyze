import os
import sys
import time
import json
import requests
import pandas as pd
from datetime import datetime, timedelta


# 差分アップデート用関数.他から作るため後回し
def check(market_name, resolution, start_time_str):
    start_time_ux = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S').timestamp()
    path = 'csv/{}-{}min.csv'.format(market_name, int(resolution / 60))
    if os.path.isfile(path):
        print("古いデータが見つかりました.\n差分アップデートします.")
        df_old = pd.read_csv(path, index_col='time', parse_dates=True)
        df_old.index = df_old.index - timedelta(hours=9)
        start_time_ux = df_old.index[-1].timestamp() + 1

    params = dict(resolution=resolution, limit=5000, start_time=int(start_time_ux), end_time=int(time.time()))
    resolution_list = [15, 60, 300, 900, 3600, 14400, 86400]
    if resolution not in resolution_list:
        print("resolutionの値が異常です. {}の中から選んでください".format(resolution_list))
        sys.exit()
    print(f'Get historical data from {market_name}')
    get_trades(market_name, params, path)


def get_trades():
    r = requests.get('https://api.bitflyer.com/v1/getexecutions', params=dict(product_code=symbol, count=500))
    data = r.json()
    df = pd.DataFrame(data[::-1], dtype='float').set_index('exec_date')
    last_date = pd.to_datetime(df.index, utc=True).tz_convert('Asia/Tokyo').tz_localize(None)[-1]
    df.index = pd.to_datetime(df.index, utc=True).tz_convert('Asia/Tokyo').tz_localize(None)
    ID = data[-1]['id']
    while start_date <= last_date:
        temp_r = requests.get('https://api.bitflyer.com/v1/getexecutions',
                              params=dict(product_code=symbol, count=500, before=ID))
        temp_data = temp_r.json()
        temp_df = pd.DataFrame(temp_data[::-1], dtype='float').set_index('exec_date')
        last_date = pd.to_datetime(temp_df.index, utc=True).tz_convert('Asia/Tokyo').tz_localize(None)[-1]
        ID = int(temp_data[-1]['id'])
        df = pd.concat([temp_df, df])
        time.sleep(0.59)
    df.index = pd.to_datetime(df.index, utc=True).tz_convert('Asia/Tokyo').tz_localize(None)
    df = df.astype({'price': 'float', 'size': 'float'})
    df.to_csv(f'csv/bf_{symbol}_{start_date:%Y%m%d}.csv')


if __name__ == '__main__':
    start = time.time()
    with open('config/bf_config.json', 'r', encoding="utf-8") as f:
        config = json.load(f)
    if not os.path.isdir("csv"):
        os.makedirs("csv")
    symbol = config['symbol']  # FX_BTC_JPY, BTC_JPY, ETH_JPY etc...
    start_time_str = config['date']  # 例:2021-08-30 21:00:00
    start_date = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
    try:
        get_trades()
        print(f'{time.time() - start:.2f}sec')
    except KeyboardInterrupt:
        pass
