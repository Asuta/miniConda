"""
检查币安下载数据的格式
"""

import pandas as pd
import zipfile

def check_binance_data_format():
    """检查币安数据格式"""
    file_path = "D:/workspace/data/crypto/1min/BTCUSDT/BTCUSDT-1m-2023-01.zip"
    
    # 读取zip文件
    df = pd.read_csv(file_path)
    
    print("原始数据格式:")
    print(f"数据形状: {df.shape}")
    print(f"列名: {list(df.columns)}")
    print("\n前5行数据:")
    print(df.head())
    
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
    
    # 重命名列
    df.columns = binance_columns
    
    print("\n\n重命名后的数据格式:")
    print(f"列名: {list(df.columns)}")
    print("\n前5行数据:")
    print(df.head())
    
    # 检查时间戳格式
    print(f"\n时间戳示例:")
    print(f"open_time: {df['open_time'].iloc[0]} (毫秒时间戳)")
    print(f"close_time: {df['close_time'].iloc[0]} (毫秒时间戳)")
    
    # 转换时间戳
    df['open_time_readable'] = pd.to_datetime(df['open_time'], unit='ms')
    df['close_time_readable'] = pd.to_datetime(df['close_time'], unit='ms')
    
    print(f"\n转换后的时间:")
    print(f"open_time: {df['open_time_readable'].iloc[0]}")
    print(f"close_time: {df['close_time_readable'].iloc[0]}")
    
    return df

if __name__ == "__main__":
    df = check_binance_data_format()
