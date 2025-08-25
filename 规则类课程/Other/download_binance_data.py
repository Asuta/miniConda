"""
从币安下载BTCUSDT历史数据的脚本
"""

import os
import requests
import zipfile
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path

def create_data_directory():
    """创建数据存储目录"""
    data_dir = Path("D:/workspace/data/crypto/1min/BTCUSDT")
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

def download_binance_data(symbol, interval, year, month, data_dir):
    """
    从币安下载指定月份的K线数据
    
    Args:
        symbol: 交易对，如 'BTCUSDT'
        interval: 时间间隔，如 '1m'
        year: 年份
        month: 月份
        data_dir: 数据存储目录
    """
    # 构建文件名
    filename = f"{symbol}-{interval}-{year}-{month:02d}.zip"
    
    # 币安历史数据下载URL
    base_url = "https://data.binance.vision/data/spot/monthly/klines"
    url = f"{base_url}/{symbol}/{interval}/{filename}"
    
    # 本地文件路径
    local_path = data_dir / filename
    
    # 检查文件是否已存在
    if local_path.exists():
        print(f"文件 {filename} 已存在，跳过下载")
        return True
    
    print(f"正在下载 {filename}...")
    
    try:
        # 下载文件
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # 保存文件
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"成功下载 {filename}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"下载 {filename} 失败: {e}")
        return False

def download_date_range(symbol, interval, start_date, end_date):
    """
    下载指定日期范围的数据
    
    Args:
        symbol: 交易对，如 'BTCUSDT'
        interval: 时间间隔，如 '1m'
        start_date: 开始日期，格式 'YYYY-MM'
        end_date: 结束日期，格式 'YYYY-MM'
    """
    # 创建数据目录
    data_dir = create_data_directory()
    
    # 解析日期
    start = datetime.strptime(start_date, '%Y-%m')
    end = datetime.strptime(end_date, '%Y-%m')
    
    current = start
    success_count = 0
    total_count = 0
    
    while current <= end:
        year = current.year
        month = current.month
        
        total_count += 1
        if download_binance_data(symbol, interval, year, month, data_dir):
            success_count += 1
        
        # 移动到下个月
        if month == 12:
            current = current.replace(year=year + 1, month=1)
        else:
            current = current.replace(month=month + 1)
    
    print(f"\n下载完成！成功下载 {success_count}/{total_count} 个文件")
    return success_count == total_count

def verify_data_format(data_dir, filename):
    """验证下载的数据格式"""
    file_path = data_dir / filename
    
    if not file_path.exists():
        print(f"文件 {filename} 不存在")
        return False
    
    try:
        # 读取zip文件中的CSV数据
        df = pd.read_csv(file_path)
        print(f"\n{filename} 数据格式验证:")
        print(f"数据形状: {df.shape}")
        print(f"列名: {list(df.columns)}")
        print(f"前5行数据:")
        print(df.head())
        return True
        
    except Exception as e:
        print(f"验证 {filename} 失败: {e}")
        return False

def main():
    """主函数"""
    symbol = "BTCUSDT"
    interval = "1m"
    start_date = "2023-01"
    end_date = "2024-09"
    
    print(f"开始下载 {symbol} {interval} 数据")
    print(f"时间范围: {start_date} 到 {end_date}")
    print("-" * 50)
    
    # 下载数据
    success = download_date_range(symbol, interval, start_date, end_date)
    
    if success:
        print("\n所有数据下载成功！")
        
        # 验证第一个文件的格式
        data_dir = create_data_directory()
        first_file = f"{symbol}-{interval}-2023-01.zip"
        verify_data_format(data_dir, first_file)
        
    else:
        print("\n部分数据下载失败，请检查网络连接或重试")

if __name__ == "__main__":
    main()
