"""
数据预处理模块
"""

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
    """运行交易策略"""
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

            # 止损：价格从最高点回撤超过2倍ATR
            drawdown_from_peak = max_price - current_price
            stop_loss_threshold = 2 * atr_entry

            # 止盈：浮盈超过5%
            take_profit_threshold = 0.05

            # 信号反转：信号强度 < -0.3
            signal_reversal = signal < -0.3

            if (drawdown_from_peak > stop_loss_threshold or 
                floating_profit > take_profit_threshold or 
                signal_reversal):
                
                z.at[z.index[i], 'flag'] = -1
                z.at[z.index[i], 'position'] = 0
                date_out = z.index[i]
                price_out = z['close'][i]
                profit = (price_out - price_in) / price_in
                
                reason = ""
                if drawdown_from_peak > stop_loss_threshold:
                    reason = f"止损: 回撤{drawdown_from_peak:.2f} > {stop_loss_threshold:.2f}"
                elif floating_profit > take_profit_threshold:
                    reason = f"止盈: 浮盈{floating_profit:.2%}"
                elif signal_reversal:
                    reason = f"信号反转: signal={signal:.2f}"
                
                Sell.append([date_out, price_out, f'平仓: {reason}, 收益={profit:.2%}'])
                print(z.index[i], f'【平仓】{reason}，收益={profit:.2%}')
            else:
                z.at[z.index[i], 'position'] = 1

    # 构建交易记录
    transaction = pd.DataFrame(Buy + Sell, columns=['date', 'price', 'action'])
    transaction = transaction.sort_values('date').reset_index(drop=True)
    
    # 构建价格数据
    data_price = z[['close', 'position', 'flag']].copy()
    
    return data_price, transaction

if __name__ == "__main__":
    # 测试代码
    import crypto_process
    
    print("测试完整的数据处理和策略运行流程...")
    
    start_month = '2023-01'
    end_month = '2023-02'  # 先测试两个月的数据
    freq = '1d'
    
    try:
        # 加载和重采样数据
        z_original = crypto_process.load_data(start_month, end_month)
        z_resampled = crypto_process.resample_data(z_original, freq)
        
        # 数据预处理
        z = preprocess_data(z_resampled)
        print(f"预处理后数据形状: {z.shape}")
        print(f"新增列: {[col for col in z.columns if col not in z_resampled.columns]}")
        
        # 运行策略
        data_price, transaction = run_strategy(z)
        print(f"\n交易记录数量: {len(transaction)}")
        if len(transaction) > 0:
            print("交易记录:")
            print(transaction)
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
