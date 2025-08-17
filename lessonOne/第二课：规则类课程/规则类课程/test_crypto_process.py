"""
测试修改后的crypto_process.py
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

import crypto_process

def test_load_data():
    """测试数据加载功能"""
    print("测试数据加载功能...")
    
    # 测试加载一个月的数据
    start_month = '2023-01'
    end_month = '2023-01'
    
    try:
        z_original = crypto_process.load_data(start_month, end_month)
        print(f"成功加载数据，形状: {z_original.shape}")
        print(f"列名: {list(z_original.columns)}")
        print("\n前5行数据:")
        print(z_original.head())
        
        return z_original
        
    except Exception as e:
        print(f"加载数据失败: {e}")
        return None

def test_resample_data(z_original):
    """测试数据重采样功能"""
    if z_original is None:
        print("原始数据为空，跳过重采样测试")
        return None
        
    print("\n\n测试数据重采样功能...")
    
    try:
        freq = '1d'  # 重采样为日线
        z_resampled = crypto_process.resample_data(z_original, freq)
        print(f"重采样后数据形状: {z_resampled.shape}")
        print(f"列名: {list(z_resampled.columns)}")
        print("\n前5行数据:")
        print(z_resampled.head())
        
        return z_resampled
        
    except Exception as e:
        print(f"重采样失败: {e}")
        return None

def main():
    """主测试函数"""
    print("开始测试crypto_process模块...")
    print("=" * 50)
    
    # 测试数据加载
    z_original = test_load_data()
    
    # 测试数据重采样
    z_resampled = test_resample_data(z_original)
    
    if z_resampled is not None:
        print("\n\n所有测试通过！")
        print("现在您可以在Jupyter notebook中使用以下代码:")
        print("""
start_month = '2023-01'
end_month = '2024-09'
freq = '1d'
z_original = crypto_process.load_data(start_month, end_month)
z_resampled = crypto_process.resample_data(z_original, freq)
        """)
    else:
        print("\n\n测试失败，请检查错误信息")

if __name__ == "__main__":
    main()
