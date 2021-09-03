import os
import json
import time
import pybotters
import pandas as pd
from datetime import datetime


def get_historical():
    r = pybotters.get("https://lightchart.bitflyer.com/api/ohlc", params=params)
    data = r.json()
    last_time = data[-1][0] - params['grouping'] * 1000 * 2
    # while len(data) <= int(needTerm): 必要な期間が必要な時の実用例(100期間のEMAが欲しいなど
    while start_date <= last_time:
        temp_r = pybotters.get("https://lightchart.bitflyer.com/api/ohlc", params=dict(
            symbol=params['symbol'], period=params['period'], before=last_time, grouping=params['grouping']))
        temp_data = temp_r.json()
        data.extend(temp_data)
        last_time = temp_data[-1][0] - params['grouping'] * 1000 * 2
    df = pd.DataFrame(data, dtype='object')[::-1]
    df = df.drop(columns={6, 7, 8, 9}).rename(
        columns={0: 'time', 1: 'open', 2: 'high', 3: 'low', 4: 'close', 5: 'volume'}).set_index('time')
    df.index = pd.to_datetime(df.index, unit='ms', utc=True).tz_convert('Asia/Tokyo').tz_localize(None)
    df.to_csv(f'csv/bf_ohlcv_{symbol}_{period}.csv')


def now_bf():
    u"""
    bitflyer用　現在時刻(秒切り捨て)
    datetime --> str --> datetime --> int
    :return: int
    """
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    return int(datetime.strptime(now_str, "%Y-%m-%d %H:%M").timestamp()) * 1000


if __name__ == '__main__':
    start = time.time()
    with open('config/bf_config.json', 'r', encoding="utf-8") as f:
        config = json.load(f)
    if not os.path.isdir("csv"):
        os.makedirs("csv")
    grouping = config['grouping']  # 1 - 30
    symbol = config['symbol']  # ETH_JPY, BTC_JPY etc...
    period = config['period']  # m, h, d
    now = now_bf()
    params = {'symbol': symbol, 'period': period, 'type': 'full', 'before': now, 'grouping': grouping}
    start_time_str = config['date']  # 2021-08-30 21:00:00
    start_date = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S').timestamp() * 1000
    try:
        get_historical()
        print(f'{time.time() - start:.2f}sec')
    except KeyboardInterrupt:
        pass