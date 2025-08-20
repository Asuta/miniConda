"""
resample crypto数据
"""

import pandas as pd
import numpy as np
from datetime import datetime

# 增加：自动识别 epoch 单位（s/ms/us/ns）的解析函数，兼容混合单位
def _parse_epoch_mixed(series: pd.Series) -> pd.Series:
    # 清洗并转换为数值
    s_str = series.astype(str).str.strip()
    s_num = pd.to_numeric(s_str, errors='coerce')
    lengths = s_str.str.len()
    # 预分配结果
    dt = pd.Series(pd.NaT, index=series.index, dtype='datetime64[ns]')
    # 19位及以上 → 纳秒 ns
    mask_ns = (lengths >= 19) & s_num.notna()
    if mask_ns.any():
        dt.loc[mask_ns] = pd.to_datetime(s_num.loc[mask_ns], unit='ns', errors='coerce')
    # 15-16位 → 微秒 us（常见：2025年数据如为微秒级）
    mask_us = (lengths.isin([15, 16])) & s_num.notna()
    if mask_us.any():
        dt.loc[mask_us] = pd.to_datetime(s_num.loc[mask_us], unit='us', errors='coerce')
    # 12-13位 → 毫秒 ms（常见历史数据）
    mask_ms = (lengths.isin([12, 13])) & s_num.notna()
    if mask_ms.any():
        dt.loc[mask_ms] = pd.to_datetime(s_num.loc[mask_ms], unit='ms', errors='coerce')
    # <=10位 → 秒 s
    mask_s = (lengths <= 10) & s_num.notna()
    if mask_s.any():
        dt.loc[mask_s] = pd.to_datetime(s_num.loc[mask_s], unit='s', errors='coerce')
    # 兜底：若仍有 NaT，尝试直接解析为字符串日期
    remain = dt.isna()
    if remain.any():
        try:
            dt.loc[remain] = pd.to_datetime(s_str.loc[remain], errors='coerce')
        except Exception:
            pass
    return dt

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

    # 处理时间戳：自动识别 s/ms/us/ns，直接保留为 datetime64[ns]
    z['open_time'] = _parse_epoch_mixed(z['open_time'])
    z['close_time'] = _parse_epoch_mixed(z['close_time'])

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