"""
resample crypto数据
"""

import pandas as pd
import numpy as np
from datetime import datetime

"""
将可能混合单位（秒/毫秒/微秒/纳秒）的 epoch 时间戳统一归一到毫秒，再安全解析为 datetime。
避免按字符串长度判断造成的单位误判，防止 OutOfBoundsDatetime。
"""
def _parse_epoch_mixed(series: pd.Series) -> pd.Series:
    s_raw_str = series.astype(str).str.strip()
    s_num = pd.to_numeric(s_raw_str, errors='coerce')

    # 统一到毫秒级别
    s_ms = pd.Series(np.nan, index=series.index, dtype='float64')
    # ns: >= 1e18（1970-01-01 之后，以纳秒为单位）
    mask_ns = s_num >= 1e18
    if mask_ns.any():
        s_ms.loc[mask_ns] = s_num.loc[mask_ns] / 1e6
    # us: [1e15, 1e18)
    mask_us = (s_num >= 1e15) & (s_num < 1e18)
    if mask_us.any():
        s_ms.loc[mask_us] = s_num.loc[mask_us] / 1e3
    # ms: [1e12, 1e15)
    mask_ms = (s_num >= 1e12) & (s_num < 1e15)
    if mask_ms.any():
        s_ms.loc[mask_ms] = s_num.loc[mask_ms]
    # s: valid seconds（< 1e12）
    mask_s = (s_num.notna()) & (s_num < 1e12)
    if mask_s.any():
        s_ms.loc[mask_s] = s_num.loc[mask_s] * 1e3

    # 先按毫秒安全转换；再对非数值或仍为 NaN 的尝试字符串解析
    # 使用四舍五入并转为 Pandas 可空整数，避免浮点误差
    s_ms_int = pd.Series(pd.NA, index=series.index, dtype='Int64')
    s_ms_int.loc[~pd.isna(s_ms)] = np.round(s_ms.loc[~pd.isna(s_ms)]).astype('int64')
    dt = pd.to_datetime(s_ms_int, unit='ms', errors='coerce')

    # 兜底：若仍有 NaT，尝试当作可读日期字符串解析
    remain = dt.isna()
    if remain.any():
        dt.loc[remain] = pd.to_datetime(s_raw_str.loc[remain], errors='coerce')

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


def clean_data(z: pd.DataFrame) -> pd.DataFrame:
    """
    使用前向填充（forward-fill）方法清洗数据中的NaN值。
    注意：如果数据开头的行存在NaN，'ffill'无法填充它们。
    
    Args:
        z (pd.DataFrame): 输入的DataFrame，可能包含NaN值。

    Returns:
        pd.DataFrame: 已填充NaN值后的DataFrame。
    """
    print("\n开始数据清洗：对NaN值进行前向填充...")
    nan_before = z.isnull().sum().sum()
    if nan_before == 0:
        print("数据中无NaN值，无需清洗。")
        return z
    
    z_cleaned = z.fillna(method='ffill')
    nan_after = z_cleaned.isnull().sum().sum()
    
    print(f"清洗前NaN值总数: {nan_before}")
    print(f"清洗后NaN值总数: {nan_after}")
    if nan_after > 0:
        print(f"警告：清洗后仍有 {nan_after} 个NaN值。这可能是因为数据开头的行包含NaN。")
        
    return z_cleaned


if __name__ == '__main__':
    start_month = '2023-01'
    end_month = '2024-09'
    freq = '5min'
    z = load_data(start_month,end_month)
    z = resample_data(z,freq)
    z = clean_data(z)
    print("\n数据清洗完成，预览处理后的数据：")
    print(z.head())