import os
import time
import requests
import pybotters
import numpy as np
import pandas as pd
from datetime import datetime, timedelta


def resample_ohlc(org_df, timeframe):
    df = org_df.resample(f'{timeframe * 60}S').agg(
        {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'})
    df['close'] = df['close'].fillna(method='ffill')
    df['open'] = df['open'].fillna(df['close'])
    df['high'] = df['high'].fillna(df['close'])
    df['low'] = df['low'].fillna(df['close'])
    return df


def trades_to_historical(df, period: str = '1S'):
    df_ohlcv = pd.concat([df["price"].resample(period).ohlc().ffill(),
                          df["size"].resample(period).sum(), ], axis=1)
    df_ohlcv.columns = ['open', 'high', 'low', 'close', 'volume']
    return df_ohlcv


def ftx_get_historical(start_ymd: str, end_ymd: str = None, symbol: str = 'BTC-PERP', resolution: int = 60,
                       output_dir: str = None, request_interval: float = 0.035, update: bool = True) -> None:
    if output_dir is None:
        output_dir = f'./csv/FTX/ohlcv/{resolution}s'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    path = f"{output_dir}/{symbol}.csv"

    if os.path.isfile(path) and update:
        print(f"Found old data --> {path}\nDifference update...\n")
        df_old = pd.read_csv(path, index_col='datetime', parse_dates=True)
        df_old.index = df_old.index
        start_dt = df_old.index[-1].timestamp() + 1
    else:
        start_ymd = start_ymd.replace('/', '-')
        start_dt = datetime.strptime(start_ymd, '%Y-%m-%d %H:%M:%S') + timedelta(hours=9)
        start_dt = int(start_dt.timestamp())

    if end_ymd is None:
        end_ymd = datetime.now()
    else:
        end_ymd = end_ymd.replace('/', '-')
        end_ymd = datetime.strptime(end_ymd, '%Y-%m-%d %H:%M:%S') + timedelta(hours=9)
    end_dt = int(end_ymd.timestamp())

    if start_dt > end_dt:
        raise ValueError(f'end_ymd{end_ymd} should be after start_ymd{start_ymd}.')

    params = dict(resolution=resolution, limit=5000, start_time=start_dt, end_time=end_dt)

    print(f'output dir: {output_dir}  save term: {start_ymd} -> {end_ymd:%Y-%m-%d %H:%M:%S}')

    r = requests.get(f'https://ftx.com/api/markets/{symbol}/candles', params=params)
    data = r.json()
    df = pd.DataFrame(data['result'])
    last_time = int(data['result'][0]['time'] / 1000) - 1
    while last_time >= start_dt:
        time.sleep(request_interval)
        temp_r = requests.get(f'https://ftx.com/api/markets/{symbol}/candles', params=dict(
            resolution=resolution, limit=5000, start_time=start_dt, end_time=last_time))
        temp_data = temp_r.json()
        try:
            last_time = int(temp_data['result'][0]['time'] / 1000) - 1
        except IndexError:
            print("Completed")
            break
        temp_df = pd.DataFrame(temp_data['result'])
        df = pd.concat([temp_df, df])
    df['time'] = df['time'] / 1000
    df.rename(columns={'time': 'datetime'}, inplace=True)
    df['datetime'] = pd.to_datetime(df['datetime'].astype(int), unit='s', utc=True, infer_datetime_format=True)
    df = df.set_index('datetime').reindex(columns=['open', 'high', 'low', 'close', 'volume'])
    df.index = df.index.tz_localize(None)
    if os.path.isfile(path) and update:
        df = pd.concat([df_old, df])
    df.to_csv(path)


def bf_get_historical(st_date: str, symbol: str = 'FX_BTC_JPY', period: str = 'm',
                      grouping: int = 1, output_dir: str = None) -> None:
    """ example
    bf_get_historical('2021/09/01')
    :param output_dir: str
    :param st_date: 2021/09/01
    :param symbol: FX_BTC_JPY, BTC_JPY, ETH_JPY
    :param period: m
    :param grouping: 1-30
    :return:
    """
    start = time.time()

    if output_dir is None:
        output_dir = f'csv/bf_ohlcv_{symbol}'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    path = f'{output_dir}_{period}.csv'
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    now = int(datetime.strptime(now_str, "%Y-%m-%d %H:%M").timestamp()) * 1000
    params = {'symbol': symbol, 'period': period, 'type': 'full', 'before': now, 'grouping': grouping}

    if os.path.isfile(path):
        print(f"Found old data --> {path}\nDifference update...\n")
        df_old = pd.read_csv(path, index_col='time', parse_dates=True)
        start_date = int(df_old.index[-1].timestamp() * 1000)
    else:
        df_old = None
        st_date = st_date.replace('/', '-')
        start_date = datetime.strptime(st_date, '%Y-%m-%d %H:%M:%S').timestamp() * 1000

    print(f'Until  --> {datetime.fromtimestamp(start_date / 1000)}')

    r = pybotters.get("https://lightchart.bitflyer.com/api/ohlc", params=params)
    data = r.json()
    last_time = data[-1][0] - params['grouping'] * 1000 * 2

    # while len(data) <= int(needTerm): ??????????????????????????????????????????(100?????????EMA??????????????????
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


def bf_get_trades(st_date: str, symbol: str = 'FX_BTC_JPY', output_dir: str = None) -> None:
    """ example
    bf_get_trades('2021/09/01')
    :param output_dir: str
    :param st_date: 2021/09/01
    :param symbol: FX_BTC_JPY, BTC_JPY, ETH_JPY
    :return:
    """

    start = time.time()

    if output_dir is None:
        output_dir = f'./bitflyer/{symbol}/trades/'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    path = f'{output_dir}/{symbol}.csv'

    if os.path.isfile(path):
        print(f"Found old data --> {path}\nDifference update...\n")
        df_old = pd.read_csv(path, index_col='exec_date', parse_dates=True)
        start_date = df_old.index[-1]
    else:
        df_old = None
        st_date = st_date.replace('/', '-')
        start_date = datetime.strptime(st_date, '%Y-%m-%d %H:%M:%S')

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


def bitfinex_get_trades(start_ymd: str, end_ymd: str = None, symbol: str = 'tBTCUSD',
                        output_dir: str = None, progress_info: bool = True, update: bool = True) -> None:
    """
    ????????????????????????????????????????????????.
    ??????????????????????????????????????????????????????
    :param progress_info:
    :param start_ymd:
    :param end_ymd:
    :param symbol:
    :param output_dir:
    :param update:
    :return:
    """
    start = time.time()

    if end_ymd is None:
        end_ymd = datetime.now()
    else:
        end_ymd = end_ymd.replace('/', '-')
        end_ymd = datetime.strptime(end_ymd, '%Y-%m-%d %H:%M:%S') + timedelta(hours=9)
    end_dt = int(end_ymd.timestamp()) * 1000

    if output_dir is None:
        output_dir = f'./csv/trades/bitfinex/{symbol}'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    path = f"{output_dir}/{end_ymd:%Y-%m-%d}.csv"

    if os.path.isfile(path) and update:
        print(f"Found old data --> {path}\nDifference update...\n")
        df_old = pd.read_csv(path, index_col='datetime', parse_dates=True)
        df_old.index = df_old.index
        start_dt = df_old.index[-1].timestamp() + 1
    else:
        start_ymd = start_ymd.replace('/', '-')
        start_ymd = datetime.strptime(start_ymd, '%Y-%m-%d %H:%M:%S') + timedelta(hours=9)
        start_dt = int(start_ymd.timestamp()) * 1000

    if start_dt > end_dt:
        raise ValueError(f'end_ymd{end_ymd} should be after start_ymd{start_ymd}.')

    print(f'output dir: {output_dir}  save term: {start_ymd-timedelta(hours=9)} -> {end_ymd-timedelta(hours=9)}')

    r = requests.get(f'https://api-pub.bitfinex.com/v2/trades/{symbol}/hist', params=dict(
        limit=10000, start=start_dt, end=end_dt, sort=-1))
    data = r.json()
    df = pd.DataFrame(data)[::-1]
    last_time = data[-1][1] - 1
    loop_time = 0
    counter = 1
    while last_time >= start_dt:
        start_loop_time = time.time()
        temp_r = requests.get(f'https://api-pub.bitfinex.com/v2/trades/{symbol}/hist', params=dict(
            limit=10000, start=start_dt, end=last_time, sort=-1))
        temp_data = temp_r.json()
        try:
            last_time = temp_data[-1][1] - 1
            if progress_info:
                print(f'process: {datetime.fromtimestamp(int(last_time/1000))}')
        except IndexError:
            print("completed!!")
            break

        temp_df = pd.DataFrame(temp_data)[::-1]
        df = pd.concat([temp_df, df])
        counter += 1
        loop_time += time.time() - start_loop_time
        if counter % 30 == 0:
            if progress_info:
                print(f'------ waiting {60-loop_time:.2f}sec ------')
            time.sleep(60-loop_time)
            loop_time = 0

    df.rename(columns={0: 'ID', 1: 'datetime', 2: 'size', 3: 'price'}, inplace=True)
    df['datetime'] = df['datetime'] / 1000
    df['datetime'] = pd.to_datetime(df['datetime'].astype(float), unit='s', utc=True, infer_datetime_format=True)
    df = df.set_index('datetime')
    df.index = df.index.tz_localize(None)
    if os.path.isfile(path) and update:
        df = pd.concat([df_old, df])
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


def binance_get_OI(st_date: str, symbol: str = 'BTCUSDT', period: str = '5m', output_dir: str = None) -> None:
    start = time.time()

    if output_dir is None:
        output_dir = f'csv/binance/OI/{symbol}'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    path = f'{output_dir}/{period}.csv'

    if os.path.isfile(path):
        print(f"Found old data --> {path}\nDiff update...\n")
        df_old = pd.read_csv(path, index_col='timestamp', parse_dates=True)
        start_date = int(df_old.index[-1].timestamp() * 1000)
    else:
        df_old = None
        st_date = st_date.replace('/', '-')
        start_date = int(datetime.strptime(st_date, '%Y-%m-%d %H:%M:%S').timestamp() * 1000)

    print(f'Until  --> {datetime.fromtimestamp(start_date / 1000)}')

    r = requests.get("https://fapi.binance.com/futures/data/openInterestHist",
                     params=dict(symbol=symbol,
                                 period=period,
                                 limit=500,
                                 startTime=start_date,
                                 endTime=int(time.time()) * 1000))
    data = r.json()
    last_time = data[0]['timestamp'] - 1
    df = pd.DataFrame(data)

    while last_time >= start_date:
        temp_r = requests.get("https://fapi.binance.com/futures/data/openInterestHist",
                              params=dict(symbol=symbol,
                                          period=period,
                                          limit=500,
                                          startTime=start_date,
                                          endTime=last_time))
        temp_data = temp_r.json()
        try:
            last_time = temp_data[0]['timestamp'] - 1
        except IndexError:
            if os.path.isfile(path):
                print("finish...")
            break
        temp_df = pd.DataFrame(temp_data)
        df = pd.concat([temp_df, df])
        time.sleep(0.2)

    df = df.set_index('timestamp')
    df.index = pd.to_datetime(df.index, unit='ms', utc=True).tz_localize(None)

    if os.path.isfile(path):
        df = pd.concat([df_old, df])
        df = df.drop_duplicates()

    df.to_csv(path)

    print(f'Output --> {path}')
    print(f'elapsed time: {time.time() - start:.2f}sec')


def binance_get_buy_sell_vol(st_date: str, symbol: str = 'BTCUSDT', period: str = '5m', output_dir: str = None) -> None:
    start = time.time()

    if output_dir is None:
        output_dir = f'csv/binance/volume/{symbol}'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    path = f'{output_dir}/{period}.csv'

    if os.path.isfile(path):
        print(f"Found old data --> {path}\nDiff update...\n")
        df_old = pd.read_csv(path, index_col='timestamp', parse_dates=True)
        start_date = int(df_old.index[-1].timestamp() * 1000)
    else:
        df_old = None
        st_date = st_date.replace('/', '-')
        start_date = int(datetime.strptime(st_date, '%Y-%m-%d %H:%M:%S').timestamp() * 1000)

    print(f'Until  --> {datetime.fromtimestamp(start_date / 1000)}')

    r = requests.get("https://fapi.binance.com/futures/data/takerlongshortRatio",
                     params=dict(symbol=symbol,
                                 period=period,
                                 limit=500,
                                 startTime=start_date,
                                 endTime=int(time.time()) * 1000))
    data = r.json()
    last_time = data[0]['timestamp'] - 1
    df = pd.DataFrame(data)

    while last_time >= start_date:
        temp_r = requests.get("https://fapi.binance.com/futures/data/takerlongshortRatio",
                              params=dict(symbol=symbol,
                                          period=period,
                                          limit=500,
                                          startTime=start_date,
                                          endTime=last_time))
        temp_data = temp_r.json()
        try:
            last_time = temp_data[0]['timestamp'] - 1
        except IndexError:
            if os.path.isfile(path):
                print("finish...")

        temp_df = pd.DataFrame(temp_data)
        df = pd.concat([temp_df, df])
        time.sleep(0.2)

    df = df.set_index('timestamp')
    df.index = pd.to_datetime(df.index, unit='ms', utc=True).tz_localize(None)

    if os.path.isfile(path):
        df = pd.concat([df_old, df])
        df = df.drop_duplicates()

    df.to_csv(path)

    print(f'Output --> {path}')
    print(f'elapsed time: {time.time() - start:.2f}sec')
