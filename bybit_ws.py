import asyncio
import pybotters
import pandas as pd
from datetime import datetime


async def main(symbol: str, interval: int = 1):
    """
    DataFrameの中身
    buySumSize   -> Askの合計出来高
    sellSumSize　-> bidの合計出来高
    maxBuyPrice  -> Ask一番出来高の多いprice
    maxSellPrice -> bid一番出来高の多いprice
    :param symbol: str
    :param interval: int
    :return:
    """
    async with pybotters.Client(base_url='https://api.bybit.com') as client:
        store = pybotters.BybitDataStore()

        await client.ws_connect('wss://stream.bybit.com/realtime_public',
                                send_json={'op': 'subscribe', 'args': [
                                    f'orderBookL2_25.{symbol}',
                                    f'trade.{symbol}'
                                ]},
                                hdlr_json=store.onmessage,
                                )

        while not all([
            len(store.orderbook),
            len(store.trade)
        ]):
            await store.wait()

        df = pd.DataFrame()

        timer = 0
        while True:
            asyncio.create_task(store.wait())
            sec = datetime.utcnow().second

            if sec + 1 > timer or sec + 1 < timer:
                timer = sec + 1
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

            await store.wait()


if __name__ == '__main__':
    try:
        asyncio.run(main('BTCUSDT', interval=5))
    except KeyboardInterrupt:
        pass

'''
TO DO LIST
・日付更新したらcsv保存. DataFrame初期化
・途中で止めた場合もcsv保存する
・保存先がごちゃごちゃにならないように整理する
'''