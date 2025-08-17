"""
完整的加密货币数据处理和策略运行示例
这个脚本展示了如何使用下载的币安数据进行策略回测
"""

import crypto_process
from data_preprocess import preprocess_data, run_strategy
import pandas as pd
import matplotlib.pyplot as plt

def main():
    """主函数：完整的数据处理和策略运行流程"""
    
    print("=" * 60)
    print("加密货币策略回测系统")
    print("=" * 60)
    
    # 设置参数
    start_month = '2023-01'
    end_month = '2024-09'
    freq = '1d'
    
    print(f"数据时间范围: {start_month} 到 {end_month}")
    print(f"重采样频率: {freq}")
    print("-" * 40)
    
    try:
        # 第一步：加载原始数据
        print("第一步：加载原始数据...")
        z_original = crypto_process.load_data(start_month, end_month)
        print(f"原始数据形状: {z_original.shape}")
        
        # 第二步：重采样数据
        print("\n第二步：重采样数据...")
        z_resampled = crypto_process.resample_data(z_original, freq)
        print(f"重采样后数据形状: {z_resampled.shape}")
        
        # 第三步：数据预处理
        print("\n第三步：数据预处理...")
        z = preprocess_data(z_resampled)
        print(f"预处理后数据形状: {z.shape}")
        print(f"新增技术指标列: {[col for col in z.columns if col not in z_resampled.columns]}")
        
        # 第四步：运行策略
        print("\n第四步：运行策略...")
        data_price, transaction = run_strategy(z)
        
        # 第五步：分析结果
        print("\n第五步：策略结果分析")
        print("=" * 40)
        
        if len(transaction) > 0:
            # 计算策略表现
            buy_trades = transaction[transaction['action'].str.contains('开仓')]
            sell_trades = transaction[transaction['action'].str.contains('平仓')]
            
            print(f"总交易次数: {len(buy_trades)}")
            print(f"完成交易次数: {len(sell_trades)}")
            
            # 提取收益率
            profits = []
            for _, trade in sell_trades.iterrows():
                action_text = trade['action']
                if '收益=' in action_text:
                    profit_str = action_text.split('收益=')[1].replace('%', '')
                    profits.append(float(profit_str) / 100)
            
            if profits:
                total_return = sum(profits)
                win_rate = len([p for p in profits if p > 0]) / len(profits)
                avg_profit = sum(profits) / len(profits)
                
                print(f"总收益率: {total_return:.2%}")
                print(f"胜率: {win_rate:.2%}")
                print(f"平均每笔收益: {avg_profit:.2%}")
                print(f"最大单笔收益: {max(profits):.2%}")
                print(f"最大单笔亏损: {min(profits):.2%}")
            
            print("\n最近10笔交易:")
            print(transaction.tail(10).to_string(index=False))
            
        else:
            print("没有产生任何交易信号")
        
        # 保存结果
        print("\n第六步：保存结果...")
        z.to_csv('processed_data.csv')
        transaction.to_csv('transaction_records.csv', index=False)
        print("结果已保存到 processed_data.csv 和 transaction_records.csv")
        
        return z, transaction
        
    except Exception as e:
        print(f"运行失败: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def plot_results(z, transaction):
    """绘制策略结果图表"""
    try:
        import matplotlib.pyplot as plt
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
        
        # 绘制价格和交易信号
        ax1.plot(z.index, z['close'], label='Close Price', alpha=0.7)
        
        # 标记买入点
        buy_signals = z[z['flag'] == 1]
        if len(buy_signals) > 0:
            ax1.scatter(buy_signals.index, buy_signals['close'], 
                       color='green', marker='^', s=100, label='Buy Signal')
        
        # 标记卖出点
        sell_signals = z[z['flag'] == -1]
        if len(sell_signals) > 0:
            ax1.scatter(sell_signals.index, sell_signals['close'], 
                       color='red', marker='v', s=100, label='Sell Signal')
        
        ax1.set_title('BTCUSDT Price and Trading Signals')
        ax1.set_ylabel('Price (USDT)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 绘制信号强度
        ax2.plot(z.index, z['signal_strength'], label='Signal Strength', color='purple')
        ax2.axhline(y=0.5, color='green', linestyle='--', alpha=0.7, label='Buy Threshold')
        ax2.axhline(y=-0.3, color='red', linestyle='--', alpha=0.7, label='Sell Threshold')
        ax2.set_title('Signal Strength')
        ax2.set_ylabel('Signal Strength')
        ax2.set_xlabel('Date')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('strategy_results.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print("图表已保存为 strategy_results.png")
        
    except ImportError:
        print("matplotlib未安装，跳过图表绘制")
    except Exception as e:
        print(f"绘制图表失败: {e}")

if __name__ == "__main__":
    # 运行完整流程
    z, transaction = main()
    
    # 如果成功，尝试绘制图表
    if z is not None and transaction is not None:
        print("\n是否绘制结果图表？(需要matplotlib)")
        try:
            plot_results(z, transaction)
        except:
            print("绘制图表失败，但数据处理成功完成")
    
    print("\n" + "=" * 60)
    print("程序运行完成！")
    print("您现在可以在Jupyter notebook中使用以下代码:")
    print("""
# 导入模块
import crypto_process
from data_preprocess import preprocess_data, run_strategy

# 设置参数
start_month = '2023-01'
end_month = '2024-09'
freq = '1d'

# 运行完整流程
z_original = crypto_process.load_data(start_month, end_month)
z_resampled = crypto_process.resample_data(z_original, freq)
z = preprocess_data(z_resampled)
data_price, transaction = run_strategy(z)
    """)
    print("=" * 60)
