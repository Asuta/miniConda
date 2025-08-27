import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# 设置matplotlib支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 指定默认字体
plt.rcParams['axes.unicode_minus'] = False  # 解决保存图像是负号'-'显示为方块的问题

def generate_detailed_report(data_price: pd.DataFrame, transaction: pd.DataFrame, risk_free_rate: float = 0.02, trading_days_per_year: int = 365):
    """
    根据策略回测结果（data_price）和交易记录（transaction），生成一份详细的绩效分析报告。

    Args:
        data_price (pd.DataFrame): 包含净值曲线(nav)、收益率(ret)、持仓(position)等时间序列数据的DataFrame。
        transaction (pd.DataFrame): 包含每笔交易明细的DataFrame。
        risk_free_rate (float, optional): 年化无风险利率. Defaults to 0.02.
        trading_days_per_year (int, optional): 每年的交易天数（加密货币通常是365天）. Defaults to 365.
    """
    
    print("==================================================")
    print("==========    详细策略回测绩效报告    ==========")
    print("==================================================")
    
    # --- 1. 整体表现指标 (基于 data_price) ---
    print("\n--- [1] 整体表现指标 ---")
    
    # 总收益率
    total_return = data_price['nav'].iloc[-1] - 1
    print(f"总收益率: {total_return:.2%}")

    # 年化收益率
    total_days = (data_price.index[-1] - data_price.index[0]).days
    annual_return = (1 + total_return) ** (trading_days_per_year / total_days) - 1
    print(f"年化收益率: {annual_return:.2%}")

    # 策略日收益率
    strategy_returns = data_price['ret'] * data_price['position'].shift(1).fillna(0)

    # 年化波动率
    annual_volatility = strategy_returns.std() * np.sqrt(trading_days_per_year)
    print(f"年化波动率: {annual_volatility:.2%}")

    # 夏普比率
    sharpe_ratio = (annual_return - risk_free_rate) / annual_volatility if annual_volatility != 0 else 0
    print(f"夏普比率 (Sharpe Ratio): {sharpe_ratio:.2f}")

    # 最大回撤
    drawdown = 1 - data_price['nav'] / data_price['nav'].cummax()
    max_drawdown = drawdown.max()
    print(f"最大回撤 (Max Drawdown): {max_drawdown:.2%}")

    # 卡玛比率 (年化收益 / 最大回撤)
    calmar_ratio = annual_return / max_drawdown if max_drawdown != 0 else 0
    print(f"卡玛比率 (Calmar Ratio): {calmar_ratio:.2f}")

    # --- 2. 交易统计指标 (基于 transaction) ---
    print("\n--- [2] 交易统计指标 ---")
    
    if transaction.empty or '卖出价格' not in transaction.columns or '买入价格' not in transaction.columns:
        print("交易记录为空或不完整，无法计算交易统计指标。")
        return

    num_trades = len(transaction)
    print(f"总交易次数: {num_trades}")

    # 计算每笔交易的收益
    transaction['pnl'] = transaction['卖出价格'] - transaction['买入价格']
    transaction['pnl_pct'] = (transaction['卖出价格'] / transaction['买入价格']) - 1

    # 胜率
    winning_trades = transaction[transaction['pnl'] > 0]
    num_winning_trades = len(winning_trades)
    win_rate = num_winning_trades / num_trades if num_trades > 0 else 0
    print(f"胜率: {win_rate:.2%}")

    # 盈亏比
    losing_trades = transaction[transaction['pnl'] <= 0]
    num_losing_trades = len(losing_trades)
    average_profit = winning_trades['pnl'].mean()
    average_loss = abs(losing_trades['pnl'].mean())
    profit_loss_ratio = average_profit / average_loss if average_loss != 0 else np.inf
    print(f"平均盈亏比: {profit_loss_ratio:.2f}")
    
    print(f"  - 盈利交易平均利润: {average_profit:.4f}")
    print(f"  - 亏损交易平均亏损: {average_loss:.4f}")

    # 最大单笔盈利/亏损
    max_profit = transaction['pnl_pct'].max()
    max_loss = transaction['pnl_pct'].min()
    print(f"最大单笔盈利: {max_profit:.2%}")
    print(f"最大单笔亏损: {max_loss:.2%}")
    
    # 平均持仓时间
    transaction['holding_period'] = transaction['卖出日期'] - transaction['买入日期']
    average_holding_period = transaction['holding_period'].mean()
    print(f"平均持仓时间: {average_holding_period}")


    # --- 3. 可视化图表 ---
    print("\n--- [3] 生成可视化图表 ---")
    
    fig, axes = plt.subplots(3, 1, figsize=(16, 12), sharex=True, gridspec_kw={'height_ratios': [3, 1, 1]})
    fig.suptitle('策略表现详细分析', fontsize=16)

    # 图1: 净值曲线 vs. 基准
    ax1 = axes[0]
    ax1.plot(data_price.index, data_price['nav'], label='策略净值 (NAV)', color='r')
    ax1.plot(data_price.index, data_price['benchmark'], label='基准 (Benchmark)', color='b', alpha=0.7)
    ax1.set_title('策略净值曲线 vs. 基准')
    ax1.set_ylabel('累计收益')
    ax1.legend()
    ax1.grid(True)

    # 标记买卖点
    buy_signals = data_price[data_price['flag'] == 1]
    sell_signals = data_price[data_price['flag'] == -1]
    ax1.scatter(buy_signals.index, data_price.loc[buy_signals.index]['benchmark'], marker='^', color='darkred', s=100, label='买入点')
    ax1.scatter(sell_signals.index, data_price.loc[sell_signals.index]['benchmark'], marker='v', color='darkgreen', s=100, label='卖出点')

    # 图2: 回撤曲线
    ax2 = axes[1]
    ax2.fill_between(drawdown.index, 0, -drawdown, color='orange', alpha=0.7)
    ax2.set_title('回撤曲线 (Drawdown)')
    ax2.set_ylabel('回撤')
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: f"{-x:.0%}"))
    ax2.grid(True)
    
    # 图3: 仓位变化
    ax3 = axes[2]
    ax3.plot(data_price.index, data_price['position'].shift(1).fillna(0), label='仓位')
    ax3.set_title('仓位变化')
    ax3.set_ylabel('仓位')
    ax3.set_xlabel('日期')
    ax3.set_yticks([0, 1])
    ax3.set_yticklabels(['空仓', '持仓'])
    ax3.grid(True)
    
    # 格式化x轴日期
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.xticks(rotation=45)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()

    # 图4: 单笔交易收益分布
    fig2, ax4 = plt.subplots(figsize=(10, 6))
    ax4.hist(transaction['pnl_pct'], bins=30, color='skyblue', edgecolor='black')
    ax4.axvline(0, color='grey', linestyle='--')
    ax4.set_title('单笔交易收益率分布')
    ax4.set_xlabel('收益率')
    ax4.set_ylabel('交易次数')
    ax4.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: f"{x:.1%}"))
    plt.grid(True)
    plt.show()


if __name__ == '__main__':
    # --- 使用示例 ---
    # 在实际使用中，您需要先从您的策略回测脚本（如run_strategy.ipynb）中
    # 获取`data_price`和`transaction`这两个DataFrame。
    
    print("这是一个分析脚本，请在其他文件中调用 `generate_detailed_report` 函数。")
    print("使用方法示例：")
    print("1. from detailed_analysis import generate_detailed_report")
    print("2. # 假设你已经通过运行策略得到了 data_price 和 transaction")
    print("3. generate_detailed_report(data_price, transaction)")

    # # 创建一个虚拟的data_price和transaction用于演示
    # dates = pd.to_datetime(pd.date_range(start='2023-01-01', periods=200, freq='D'))
    # price = 100 * (1 + np.random.randn(200).cumsum() / 100)
    # mock_data_price = pd.DataFrame({'close': price}, index=dates)
    # mock_data_price['ret'] = mock_data_price['close'].pct_change().fillna(0)
    # mock_data_price['position'] = np.random.randint(0, 2, 200)
    # mock_data_price['nav'] = (1 + mock_data_price['ret'] * mock_data_price['position'].shift(1)).cumprod()
    # mock_data_price['benchmark'] = mock_data_price['close'] / mock_data_price['close'].iloc[0]
    # mock_data_price['flag'] = 0

    # mock_transaction = pd.DataFrame({
    #     '买入日期': pd.to_datetime(['2023-01-10', '2023-03-15', '2023-05-20']),
    #     '买入价格': [102, 105, 110],
    #     '卖出日期': pd.to_datetime(['2023-02-20', '2023-04-25', '2023-06-30']),
    #     '卖出价格': [108, 103, 115]
    # })

    # generate_detailed_report(mock_data_price, mock_transaction)