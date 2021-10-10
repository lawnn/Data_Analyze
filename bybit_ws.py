import os
import asyncio
import pybotters
import pandas as pd
from datetime import datetime


async def main(symbol: str = 'BTCUSDT', interval: float = 1.0, output_dir=None):
    """
    DataFrameの中身
    buySumSize   -> Askの厚み
    sellSumSize　-> bidの厚み
    maxBuyPrice  -> Askで一番厚みがある価格
    maxSellPrice -> bidで一番厚みがある価格
    :param output_dir: str
    :param symbol: str
    :param interval: float
    :return:
    """
    async with pybotters.Client() as client:
        store = pybotters.BybitDataStore()

        await client.ws_connect('wss://stream.bybit.com/realtime_public',
                                send_json={'op': 'subscribe', 'args': [f'orderBookL2_25.{symbol}']},
                                hdlr_json=store.onmessage,)

        await store.wait()

        if output_dir is None:
            output_dir = f'./bybit/{symbol}/orderBook/'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        df = pd.DataFrame()

        timer = 0
        while True:
            obtask = asyncio.create_task(store.orderbook.wait())
            dt_now = datetime.utcnow()
            sec = dt_now.second

            if sec + 1 > timer or sec + 1 < timer:
                timer = sec + 1

                # 00:00:00でCSV保存. df初期化
                if dt_now.strftime('%H%M%S') == '000000':
                    df.to_csv(f'{output_dir}{datetime.utcnow().strftime("%Y%m%d")}.csv')
                    df = pd.DataFrame()

                if sec % interval == 0:
                    now = datetime.utcnow()
                    ob = pd.DataFrame(store.orderbook.find())
                    ob_buy = ob.query('side == "Buy"').sort_values('price', ascending=False)
                    maxBuyPrice = ob_buy.price[ob_buy['size'].idxmax]
                    buySumSize = ob_buy['size'].sum()
                    ob_sell = ob.query('side == "Sell"').sort_values('price', ascending=True)
                    maxSellPrice = ob_sell.price[ob_sell['size'].idxmax]
                    sellSumSize = ob_sell['size'].sum()
                    temp_df = pd.DataFrame({'buySumSize': [buySumSize], 'sellSumSize': [sellSumSize],
                                            'maxBuyPrice': [maxBuyPrice], 'maxSellPrice': [maxSellPrice]},
                                           index=[now])
                    df = pd.concat([df, temp_df])
                    print(df)

            await obtask


if __name__ == '__main__':
    try:
        if os.name == 'nt':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main(interval=1))
    except KeyboardInterrupt:
        pass
    finally:
        print("stop")
