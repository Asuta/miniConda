"""
resample crypto数据
"""

import pandas as pd
import numpy as np
from datetime import datetime

def load_data(start_month:str,end_month:str) -> pd.DataFrame:
    start_month = datetime.strptime(start_month, '%Y-%m')
    end_month = datetime.strptime(end_month, '%Y-%m')

    zs = []
    while start_month <= end_month:
        start_month_str = start_month.strftime('%Y-%m')
        file_path = f"D:/workspace/data/crypto/1min/BTCUSDT/BTCUSDT-1m-{start_month_str}.zip"

        try:
            # 指定列名，因为CSV文件没有header
            column_names = ['open_time', 'open', 'high', 'low', 'close', 'volume',
                          'close_time', 'quote_volume', 'count', 'taker_buy_volume',
                          'taker_buy_quote_volume', 'ignore']
            z = pd.read_csv(file_path, names=column_names, header=None)
            print(f"成功读取文件: {file_path}")
            print(f"列名: {z.columns.tolist()}")
            print(f"数据形状: {z.shape}")

            zs.append(z)
        except Exception as e:
            print(f"读取文件 {file_path} 时出错: {e}")
            continue

        # 更新到下一个月
        if start_month.month == 12:
            start_month = start_month.replace(year=start_month.year + 1, month=1)
        else:
            start_month = start_month.replace(month=start_month.month + 1)

    if not zs:
        raise ValueError("没有成功读取任何数据文件")

    z = pd.concat(zs, axis=0, ignore_index=True)
    print(f"合并后的数据形状: {z.shape}")
    print(f"合并后的列名: {z.columns.tolist()}")

    # 处理时间戳,变成年月日-时分秒格式
    z['open_time'] = pd.to_datetime(z['open_time'], unit='ms').dt.strftime('%Y-%m-%d %H:%M:%S')
    z['close_time'] = pd.to_datetime(z['close_time'], unit='ms').dt.strftime('%Y-%m-%d %H:%M:%S')

    return z

def resample_data(z:pd.DataFrame,freq:str) -> pd.DataFrame:
    z_ = z.copy()
    z_.index = pd.to_datetime(z_.open_time)
    z_rspled = z_.resample(freq).agg({'open_time':'first', 
                              'open':'first', 
                              'high':'max', 
                              'low':'min', 
                              'close':'last', 
                              'volume':'sum', 
                              'close_time':'last',
                              'quote_volume':'sum', 
                              'count':'sum', 
                              'taker_buy_volume':'sum', 
                              'taker_buy_quote_volume':'sum',
                              'ignore':'last'})
    z = z_rspled[['open','high','low','close','volume','quote_volume','count','taker_buy_volume','taker_buy_quote_volume']]
    return z


if __name__ == '__main__':
    start_month = '2023-01'
    end_month = '2024-09'
    freq = '5min'
    z = load_data(start_month,end_month)
    z = resample_data(z,freq)