"""
resample crypto数据
"""

import pandas as pd
import numpy as np
from datetime import datetime

def load_data(start_month:str,end_month:str) -> pd.DataFrame:
    start_month = datetime.strptime(start_month, '%Y-%m')
    end_month = datetime.strptime(end_month, '%Y-%m')

    # 币安K线数据的标准列名
    binance_columns = [
        'open_time',           # 开盘时间
        'open',                # 开盘价
        'high',                # 最高价
        'low',                 # 最低价
        'close',               # 收盘价
        'volume',              # 成交量
        'close_time',          # 收盘时间
        'quote_volume',        # 成交额
        'count',               # 成交笔数
        'taker_buy_volume',    # 主动买入成交量
        'taker_buy_quote_volume',  # 主动买入成交额
        'ignore'               # 忽略字段
    ]

    zs = []
    while start_month <= end_month:
        start_month = start_month.strftime('%Y-%m')
        file_path = f"D:/workspace/data/crypto/1min/BTCUSDT/BTCUSDT-1m-{start_month}.zip"

        try:
            # 读取CSV文件并设置列名
            z = pd.read_csv(file_path, header=None, names=binance_columns)
            print(f"成功加载 {file_path}, 数据形状: {z.shape}")
            zs.append(z)
        except FileNotFoundError:
            print(f"文件不存在: {file_path}")
        except Exception as e:
            print(f"加载文件失败 {file_path}: {e}")

        start_month = datetime.strptime(start_month, '%Y-%m')
        if start_month.month == 12:
            start_month = start_month.replace(year=start_month.year + 1, month=1)
        else:
            start_month = start_month.replace(month=start_month.month + 1)

    if not zs:
        raise ValueError("没有成功加载任何数据文件")

    z = pd.concat(zs, axis=0, ignore_index=True)
    print(f"合并后总数据形状: {z.shape}")

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