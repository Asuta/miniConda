import pandas as pd
import talib as ta

def preprocess_data(z_: pd.DataFrame) -> pd.DataFrame:
    """数据预处理：计算收益率、波动率、ATR"""
    z = z_.copy()
    z['ret'] = z['close'].pct_change().fillna(0)
    # 波动率校正后的收益率，夏普比率的变形
    z['rolling_ret'] = z['close'].pct_change(periods=10).fillna(0)  # 滚动计算过去10个周期的ret
    z['rolling_vol'] = z['ret'].rolling(window=10).std().fillna(1e-6)  # 滚动计算过去10个周期的波动率
    z['signal_strength'] = z['rolling_ret'] / z['rolling_vol']
    z['atr'] = ta.ATR(z['high'], z['low'], z['close'], timeperiod=14)
    z['position'] = 0.0
    z['flag'] = 0.0
    return z

def run_strategy(z: pd.DataFrame) -> tuple:
    Buy, Sell = [], []
    max_price = 0
    atr_entry = 0
    price_in = 0

    for i in range(10, len(z)):
        signal = z['signal_strength'][i]

        # ✅ 开仓逻辑：信号强度 > 0.5
        if z['position'][i - 1] == 0 and signal > 0.5:
            z.at[z.index[i], 'flag'] = 1
            z.at[z.index[i], 'position'] = 1
            # TODO open价格开仓的局限性——股票
            price_in = z['close'][i]  # 记录开仓价格
            date_in = z.index[i]  # 记录开仓的时间
            atr_entry = z['atr'][i]
            max_price = z['close'][i]
            Buy.append([date_in, price_in, f'开仓: signal={signal:.2f}, ATR={atr_entry:.2f}'])
            print(z.index[i], f'【开仓】信号={signal:.2f}，ATR={atr_entry:.2f}')

        # ✅ 平仓逻辑（有仓位时）
        elif z['position'][i - 1] == 1:
            current_price = z['close'][i]
            max_price = max(max_price, current_price)
            floating_profit = (current_price - price_in) / price_in
            floating_drawdown = (max_price - current_price) / max_price  # 止盈用
            drawdown_atr = price_in - current_price  # ✅ 用于止损

            # ✅ 止损条件：开仓价 - 当前价 > 2ATR
            if drawdown_atr > 2 * atr_entry:
                z.at[z.index[i], 'flag'] = -1
                z.at[z.index[i], 'position'] = 0
                price_out = z['close'][i]
                date_out = z.index[i]
                Sell.append([date_out, price_out, f'止损: 跌幅={drawdown_atr:.2f} > 2ATR={2*atr_entry:.2f}'])
                print(z.index[i], f'【止损】当前价格较开仓价下跌{drawdown_atr:.2f} > 2ATR')

            # ✅ 止盈条件：从最高浮盈回撤超10%
            # 不跌破40日均线不离场
            # 仓位的逐步增减，盘中动量衰减，平掉1/3的仓位，利润回撤接近最大阈值，那么全平
            elif floating_profit > 0 and floating_drawdown > 0.10: 
                z.at[z.index[i], 'flag'] = -1
                z.at[z.index[i], 'position'] = 0
                price_out = z['close'][i]
                date_out = z.index[i]
                Sell.append([date_out, price_out, f'止盈: 回撤={floating_drawdown:.2%}'])
                print(z.index[i], f'【止盈】浮盈回撤={floating_drawdown:.2%} > 10%')

            else:
                z.at[z.index[i], 'position'] = z['position'][i - 1]
                print(z.index[i], f'持仓中，当前浮盈={floating_profit:.2%}')


    # 交易记录整理
    p1 = pd.DataFrame(Buy, columns=['买入日期', '买入价格', '备注'])
    p2 = pd.DataFrame(Sell, columns=['卖出日期', '卖出价格', '备注'])
    transaction = pd.concat([p1, p2], axis=1)

    # 净值计算
    z['ret'] = z['close'].pct_change().fillna(0)
    z['nav'] = 1 + (z['ret'] * z['position']).cumsum()  # 单利的计算
    z['benchmark'] = z['close'] / z['close'].iloc[0]

    return z, transaction


def execute_strategy(z: pd.DataFrame) -> tuple:
    z = preprocess_data(z)
    data_price, transaction = run_strategy(z)
    return data_price, transaction