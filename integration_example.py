# 在您现有的 run_strategy.ipynb 中使用 comprehensive_trading_analysis 的示例

# 在您现有的代码中，在 transaction 数据生成后，添加以下代码：

# 1. 首先导入交易分析模块
import trading_analysis

# 2. 在您运行策略后，transaction 数据已经生成
# 假设这是您现有的代码：
# data_price, transaction = run_strategy(z, **params)

# 3. 添加交易分析代码
# 方法一：直接调用函数并打印结果
analysis_results = trading_analysis.comprehensive_trading_analysis(transaction, data_price)
trading_analysis.print_trading_analysis(analysis_results)

# 方法二：如果您想要将分析结果保存到变量中
# detailed_analysis = trading_analysis.comprehensive_trading_analysis(transaction, data_price)

# 方法三：如果您想要只获取特定的分析指标
# basic_stats = {
#     '交易总次数': analysis_results['交易总次数'],
#     '胜率': analysis_results['胜率'],
#     '平均利润率': analysis_results['平均利润率'],
#     '平均持仓时间(小时)': analysis_results.get('平均持仓时间(小时)', 0),
#     '盈亏比': analysis_results.get('盈亏比', 0)
# }

# 打印基础统计信息
# print("基础统计信息:")
# for key, value in basic_stats.items():
#     if isinstance(value, float):
#         print(f"{key}: {value:.2f}")
#     else:
#         print(f"{key}: {value}")

# 在您的 Jupyter notebook 中的完整使用示例：

"""
# 在现有的 run_strategy.ipynb 中添加以下代码单元：

# 导入交易分析模块
import trading_analysis

# 运行您的策略（这行代码您已经有了）
# data_price, transaction = run_strategy(z, **params)

# 进行全面的交易分析
print("=== 交易策略全面分析 ===")
analysis_results = trading_analysis.comprehensive_trading_analysis(transaction, data_price)
trading_analysis.print_trading_analysis(analysis_results)

# 如果您想要对比不同参数下的策略表现，可以这样：
# params_list = [
#     {'signal_threshold': 0.3, 'atr_stop_mult': 1.5, 'tp_drawdown_pct': 0.05},
#     {'signal_threshold': 0.4, 'atr_stop_mult': 2.0, 'tp_drawdown_pct': 0.08},
#     {'signal_threshold': 0.2, 'atr_stop_mult': 1.2, 'tp_drawdown_pct': 0.03}
# ]

# for i, params in enumerate(params_list):
#     print(f"\\n=== 参数组合 {i+1} 分析 ===")
#     data_price_temp, transaction_temp = run_strategy(z, **params)
#     results_temp = trading_analysis.comprehensive_trading_analysis(transaction_temp, data_price_temp)
#     trading_analysis.print_trading_analysis(results_temp)
"""

# 如果您想要将分析结果保存到 CSV 文件：
def save_analysis_to_csv(analysis_results, filename="trading_analysis_results.csv"):
    """将分析结果保存到CSV文件"""
    import pandas as pd
    
    # 将字典转换为DataFrame
    df = pd.DataFrame.from_dict(analysis_results, orient='index', columns=['值'])
    
    # 保存到CSV
    df.to_csv(filename, encoding='utf-8-sig')  # utf-8-sig 支持中文
    print(f"分析结果已保存到: {filename}")

# 使用方法：
# save_analysis_to_csv(analysis_results)