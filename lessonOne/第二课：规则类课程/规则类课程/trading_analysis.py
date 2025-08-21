import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def comprehensive_trading_analysis(transactions: pd.DataFrame, price_data: pd.DataFrame = None) -> dict:
    """
    综合交易分析函数
    
    参数:
    transactions: DataFrame, 包含交易记录，应有以下列:
        - 买入日期
        - 买入价格
        - 卖出日期
        - 卖出价格
        - 备注 (可选)
    price_data: DataFrame, 包含价格数据，应有close列 (可选，用于计算持仓时间)
    
    返回:
    dict: 包含各种分析指标的字典
    """
    
    # 检查交易数据是否有效
    if transactions.empty:
        return {"error": "没有交易记录"}
    
    # 确保必要的列存在
    required_columns = ['买入日期', '买入价格', '卖出日期', '卖出价格']
    missing_cols = [col for col in required_columns if col not in transactions.columns]
    if missing_cols:
        return {"error": f"缺少必要的列: {missing_cols}"}
    
    # 创建交易分析结果的字典
    analysis_results = {}
    
    # 1. 基础交易统计
    analysis_results['交易总次数'] = len(transactions)
    
    # 2. 胜率分析
    profits = transactions['卖出价格'] - transactions['买入价格']
    win_trades = profits > 0
    analysis_results['盈利交易次数'] = win_trades.sum()
    analysis_results['亏损交易次数'] = len(transactions) - win_trades.sum()
    analysis_results['胜率'] = win_trades.mean()
    
    # 3. 利润率分析
    profit_rates = profits / transactions['买入价格']
    analysis_results['总利润率'] = profit_rates.sum()
    analysis_results['平均利润率'] = profit_rates.mean()
    analysis_results['最大单笔利润率'] = profit_rates.max()
    analysis_results['最大单笔亏损率'] = profit_rates.min()
    
    # 4. 盈亏比分析
    winning_trades = profit_rates[profit_rates > 0]
    losing_trades = profit_rates[profit_rates < 0]
    
    if len(winning_trades) > 0 and len(losing_trades) > 0:
        avg_win = winning_trades.mean()
        avg_loss = abs(losing_trades.mean())
        analysis_results['盈亏比'] = avg_win / avg_loss if avg_loss > 0 else float('inf')
    else:
        analysis_results['盈亏比'] = np.nan
    
    # 5. 持仓时间分析
    if '买入日期' in transactions.columns and '卖出日期' in transactions.columns:
        try:
            # 确保日期格式正确
            transactions['买入日期'] = pd.to_datetime(transactions['买入日期'])
            transactions['卖出日期'] = pd.to_datetime(transactions['卖出日期'])
            
            # 计算持仓时间
            holding_times = transactions['卖出日期'] - transactions['买入日期']
            holding_hours = holding_times.dt.total_seconds() / 3600  # 转换为小时
            
            analysis_results['平均持仓时间(小时)'] = holding_hours.mean()
            analysis_results['平均持仓时间(天)'] = holding_hours.mean() / 24
            analysis_results['最短持仓时间(小时)'] = holding_hours.min()
            analysis_results['最长持仓时间(小时)'] = holding_hours.max()
            
            # 按持仓时间分类统计
            short_trades = holding_hours[holding_hours <= 24]  # 1天内
            medium_trades = holding_hours[(holding_hours > 24) & (holding_hours <= 168)]  # 1-7天
            long_trades = holding_hours[holding_hours > 168]  # 超过7天
            
            analysis_results['短期交易占比'] = len(short_trades) / len(holding_hours)
            analysis_results['中期交易占比'] = len(medium_trades) / len(holding_hours)
            analysis_results['长期交易占比'] = len(long_trades) / len(holding_hours)
            
        except Exception as e:
            analysis_results['持仓时间计算错误'] = str(e)
    
    # 6. 连续盈利/亏损分析
    consecutive_wins = 0
    consecutive_losses = 0
    max_consecutive_wins = 0
    max_consecutive_losses = 0
    
    for is_win in win_trades:
        if is_win:
            consecutive_wins += 1
            consecutive_losses = 0
            max_consecutive_wins = max(max_consecutive_wins, consecutive_wins)
        else:
            consecutive_losses += 1
            consecutive_wins = 0
            max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
    
    analysis_results['最大连续盈利次数'] = max_consecutive_wins
    analysis_results['最大连续亏损次数'] = max_consecutive_losses
    
    # 7. 交易频率分析
    if len(transactions) >= 2 and '买入日期' in transactions.columns:
        try:
            transactions['买入日期'] = pd.to_datetime(transactions['买入日期'])
            time_span = transactions['买入日期'].iloc[-1] - transactions['买入日期'].iloc[0]
            total_days = time_span.days
            
            if total_days > 0:
                analysis_results['日均交易次数'] = len(transactions) / total_days
                analysis_results['周均交易次数'] = len(transactions) / (total_days / 7)
                analysis_results['月均交易次数'] = len(transactions) / (total_days / 30)
        except Exception as e:
            analysis_results['交易频率计算错误'] = str(e)
    
    # 8. 资金利用率分析
    if price_data is not None and 'close' in price_data.columns:
        try:
            total_capital = transactions['买入价格'].sum()
            if total_capital > 0:
                analysis_results['总投入资金'] = total_capital
                analysis_results['资金周转率'] = total_capital / (transactions['卖出价格'].sum() / 2)  # 假设平均持仓资金
        except Exception as e:
            analysis_results['资金利用率计算错误'] = str(e)
    
    # 9. 交易类型分析 (如果备注信息包含交易类型)
    if '备注' in transactions.columns:
        try:
            # 从备注中提取交易类型信息
            buy_notes = transactions[transactions['买入价格'].notna()]['备注']
            sell_notes = transactions[transactions['卖出价格'].notna()]['备注']
            
            # 这里可以根据实际备注格式进行解析
            # 示例：统计不同类型的交易
            analysis_results['交易类型备注'] = {
                '开仓备注示例': buy_notes.dropna().tolist()[:3],  # 显示前3个例子
                '平仓备注示例': sell_notes.dropna().tolist()[:3]
            }
        except Exception as e:
            analysis_results['交易类型分析错误'] = str(e)
    
    # 10. 风险调整收益指标
    if len(profit_rates) > 0:
        analysis_results['收益标准差'] = profit_rates.std()
        analysis_results['变异系数'] = profit_rates.std() / abs(profit_rates.mean()) if profit_rates.mean() != 0 else np.nan
        
        # 计算索提诺比率 (Sortino Ratio)
        downside_returns = profit_rates[profit_rates < 0]
        if len(downside_returns) > 0 and downside_returns.std() > 0:
            excess_returns = profit_rates.mean()  # 假设无风险收益率为0
            downside_deviation = downside_returns.std()
            analysis_results['索提诺比率'] = excess_returns / downside_deviation
        else:
            analysis_results['索提诺比率'] = np.nan
    
    # 11. 交易分布统计
    if len(profit_rates) > 0:
        # 将利润率分为几个区间
        profit_bins = [-np.inf, -0.1, -0.05, 0, 0.05, 0.1, np.inf]
        profit_labels = ['严重亏损(<-10%)', '较大亏损(-10%~-5%)', '小亏损(-5%~0%)', 
                        '小盈利(0%~5%)', '较大盈利(5%~10%)', '大盈利(>10%)']
        
        profit_distribution = pd.cut(profit_rates, bins=profit_bins, labels=profit_labels).value_counts()
        analysis_results['利润率分布'] = profit_distribution.to_dict()
    
    # 12. 综合评分 (0-100分)
    score = 0
    if analysis_results['胜率'] > 0.5:
        score += analysis_results['胜率'] * 20
    else:
        score += analysis_results['胜率'] * 10
    
    if analysis_results['平均利润率'] > 0:
        score += min(analysis_results['平均利润率'] * 200, 20)
    else:
        score += analysis_results['平均利润率'] * 100
    
    if analysis_results['盈亏比'] > 1:
        score += min(analysis_results['盈亏比'] * 10, 20)
    else:
        score += analysis_results['盈亏比'] * 5
    
    if analysis_results['最大连续盈利次数'] > analysis_results['最大连续亏损次数']:
        score += 15
    else:
        score += 5
    
    if analysis_results['最大回撤'] < 0.1 if '最大回撤' in analysis_results else False:
        score += 15
    
    analysis_results['综合评分'] = min(max(score, 0), 100)
    
    return analysis_results

def print_trading_analysis(analysis_results: dict):
    """
    打印交易分析结果
    
    参数:
    analysis_results: comprehensive_trading_analysis函数返回的分析结果字典
    """
    print("=" * 80)
    print("交易策略综合分析报告")
    print("=" * 80)
    
    # 基础统计
    print("\n【基础交易统计】")
    print(f"交易总次数: {analysis_results.get('交易总次数', 0)}")
    print(f"盈利交易次数: {analysis_results.get('盈利交易次数', 0)}")
    print(f"亏损交易次数: {analysis_results.get('亏损交易次数', 0)}")
    print(f"胜率: {analysis_results.get('胜率', 0):.2%}")
    
    # 利润率分析
    print("\n【利润率分析】")
    print(f"总利润率: {analysis_results.get('总利润率', 0):.2%}")
    print(f"平均利润率: {analysis_results.get('平均利润率', 0):.2%}")
    print(f"最大单笔利润率: {analysis_results.get('最大单笔利润率', 0):.2%}")
    print(f"最大单笔亏损率: {analysis_results.get('最大单笔亏损率', 0):.2%}")
    print(f"盈亏比: {analysis_results.get('盈亏比', 0):.2f}")
    
    # 持仓时间分析
    if '平均持仓时间(小时)' in analysis_results:
        print("\n【持仓时间分析】")
        print(f"平均持仓时间: {analysis_results.get('平均持仓时间(小时)', 0):.1f} 小时 ({analysis_results.get('平均持仓时间(天)', 0):.1f} 天)")
        print(f"最短持仓时间: {analysis_results.get('最短持仓时间(小时)', 0):.1f} 小时")
        print(f"最长持仓时间: {analysis_results.get('最长持仓时间(小时)', 0):.1f} 小时")
        print(f"短期交易占比: {analysis_results.get('短期交易占比', 0):.1%}")
        print(f"中期交易占比: {analysis_results.get('中期交易占比', 0):.1%}")
        print(f"长期交易占比: {analysis_results.get('长期交易占比', 0):.1%}")
    
    # 连续性分析
    print("\n【连续性分析】")
    print(f"最大连续盈利次数: {analysis_results.get('最大连续盈利次数', 0)}")
    print(f"最大连续亏损次数: {analysis_results.get('最大连续亏损次数', 0)}")
    
    # 交易频率
    if '日均交易次数' in analysis_results:
        print("\n【交易频率分析】")
        print(f"日均交易次数: {analysis_results.get('日均交易次数', 0):.2f}")
        print(f"周均交易次数: {analysis_results.get('周均交易次数', 0):.2f}")
        print(f"月均交易次数: {analysis_results.get('月均交易次数', 0):.2f}")
    
    # 风险指标
    print("\n【风险指标】")
    print(f"收益标准差: {analysis_results.get('收益标准差', 0):.2%}")
    print(f"变异系数: {analysis_results.get('变异系数', 0):.2f}")
    print(f"索提诺比率: {analysis_results.get('索提诺比率', 0):.2f}")
    
    # 利润率分布
    if '利润率分布' in analysis_results:
        print("\n【利润率分布】")
        for category, count in analysis_results['利润率分布'].items():
            print(f"  {category}: {count} 次")
    
    # 综合评分
    print("\n【综合评估】")
    print(f"综合评分: {analysis_results.get('综合评分', 0):.1f}/100")
    
    # 评估等级
    score = analysis_results.get('综合评分', 0)
    if score >= 80:
        grade = "优秀"
    elif score >= 60:
        grade = "良好"
    elif score >= 40:
        grade = "一般"
    elif score >= 20:
        grade = "较差"
    else:
        grade = "很差"
    print(f"评估等级: {grade}")
    
    print("=" * 80)

# 使用示例
if __name__ == "__main__":
    # 示例数据 - 您可以用实际的数据替换
    example_transactions = pd.DataFrame({
        '买入日期': ['2023-01-01 10:00', '2023-01-02 14:30', '2023-01-03 09:15', 
                    '2023-01-04 11:45', '2023-01-05 16:20'],
        '买入价格': [100, 102, 98, 105, 110],
        '卖出日期': ['2023-01-01 15:30', '2023-01-03 10:00', '2023-01-03 16:45',
                    '2023-01-05 13:15', '2023-01-06 11:30'],
        '卖出价格': [105, 100, 102, 108, 115],
        '备注': ['开仓: signal=0.35', '开仓: signal=0.42', '止损: 跌幅=2.5',
                '开仓: signal=0.38', '止盈: 回撤=4.5%']
    })
    
    # 运行分析
    results = comprehensive_trading_analysis(example_transactions)
    
    # 打印结果
    print_trading_analysis(results)