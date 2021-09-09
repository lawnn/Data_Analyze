import os
import time
import requests
import pybotters
import numpy as np
import pandas as pd
from datetime import datetime, timedelta


def bf_get_historical(st_date: str, symbol: str = 'FX_BTC_JPY', period: str = 'm',
                      grouping: int = 1) -> None:
    """ example
    bf_get_historical('2021/09/01')
    :param st_date: 2021/09/01
    :param symbol: FX_BTC_JPY, BTC_JPY, ETH_JPY
    :param period: m
    :param grouping: 1-30
    :return:
    """
    start = time.time()

    if not os.path.isdir("csv"):
        os.makedirs("csv")

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    now = int(datetime.strptime(now_str, "%Y-%m-%d %H:%M").timestamp()) * 1000
    params = {'symbol': symbol, 'period': period, 'type': 'full', 'before': now, 'grouping': grouping}
    path = f'csv/bf_ohlcv_{symbol}_{period}.csv'

    if os.path.isfile(path):
        print(f"Found old data --> {path}\nDiff update...\n")
        df_old = pd.read_csv(path, index_col='time', parse_dates=True)
        start_date = int(df_old.index[-1].timestamp() * 1000)
    else:
        start_date = datetime.strptime(st_date, '%Y-%m-%d %H:%M:%S').timestamp() * 1000
    print(f'Until  --> {datetime.fromtimestamp(start_date / 1000)}')

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
        columns={0: 'time', 1: 'open', 2: 'high', 3: 'low', 4: 'close', 5: 'volume'}).set_index('time').replace(
        {'open': {'': np.nan}, 'high': {'': np.nan}, 'low': {'': np.nan}, 'close': {'': np.nan},
         'volume': {'': np.nan}}).dropna(how='any')
    df.index = pd.to_datetime(df.index, unit='ms', utc=True).tz_localize(None)

    if os.path.isfile(path):
        df = pd.concat([df_old, df])
        df = df.drop_duplicates()

    df.to_csv(path)

    print(f'Output --> {path}')
    print(f'elapsed time: {time.time() - start:.2f}sec')


def bf_get_trades(st_date: str, symbol: str = 'FX_BTC_JPY') -> None:
    """ example
    bf_get_trades('2021/09/01')
    :param st_date: 2021/09/01
    :param symbol: FX_BTC_JPY, BTC_JPY, ETH_JPY
    :return:
    """

    start = time.time()

    if not os.path.isdir("csv"):
        os.makedirs("csv")

    path = f'csv/bf_trades_{symbol}.csv'

    if os.path.isfile(path):
        print(f"Found old data --> {path}\nDiff update...\n\n")
        df_old = pd.read_csv(path, index_col='exec_date', parse_dates=True)
        start_date = df_old.index[-1]
    else:
        start_date = datetime.strptime(st_date, '%Y/%m/%d %H:%M:%S')

    print(f'Until  --> {start_date}')

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
        df = pd.concat([df_old, df])
        df = df.drop_duplicates()

    df.to_csv(path)

    print(f'Output --> {path}')
    print(f'elapsed time: {(time.time() - start) / 60:.2f}min')


def gmo_get_historical(start_ymd: str, end_ymd: str, symbol: str = 'BTC_JPY', interval: str = '1min',
                       output_dir: str = None, request_interval: float = 0.2, progress_info: bool = True) -> None:
    """ example
    gmo_get_historical('2021/09/01', '2021/09/08')
    :param start_ymd: 2021/09/01
    :param end_ymd: 2021/09/08
    :param symbol: BTC, BTC_JPY, ETH_JPY
    :param interval: 1min 5min 10min 15min 30min 1hour 4hour 8hour 12hour 1day 1week 1month
    :param output_dir: csv/hoge/huga/
    :param request_interval: 0
    :param progress_info: False
    :return:
    """
    if output_dir is None:
        output_dir = f'./gmo/{symbol}/ohlcv/{interval}/'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    start_dt = datetime.strptime(start_ymd, '%Y/%m/%d')
    end_dt = datetime.strptime(end_ymd, '%Y/%m/%d')
    if start_dt > end_dt:
        raise ValueError(f'end_ymd{end_ymd} should be after start_ymd{start_ymd}.')

    print(f'output dir: {output_dir}  save term: {start_dt:%Y/%m/%d} -> {end_dt:%Y/%m/%d}')

    cur_dt = start_dt
    total_count = 0
    while cur_dt <= end_dt:
        r = requests.get(f'https://api.coin.z.com/public/v1/klines',
                         params=dict(symbol=symbol, interval=interval, date=cur_dt.strftime('%Y%m%d')))
        data = r.json()
        df = pd.DataFrame(data['data'])
        df.rename(columns={'openTime': 'time'}, inplace=True)
        df = df.set_index('time')
        df.index = pd.to_datetime(df.index, unit='ms', utc=True).tz_localize(None)
        df.to_csv(f'{output_dir}/{cur_dt.strftime("%Y%m%d")}.csv')
        total_count += 1
        if progress_info:
            print(f'Completed output {cur_dt:%Y%m%d}.csv')

        cur_dt += timedelta(days=1)
        if request_interval > 0:
            time.sleep(request_interval)