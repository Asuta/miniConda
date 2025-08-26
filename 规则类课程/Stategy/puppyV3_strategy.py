import pandas as pd
import talib as ta
import numpy as np

# --- 第一部分：数据预处理 (与之前基本一致) ---
# 这部分主要是计算策略需要用到的各种技术指标，我们保持不变。
def preprocess_data(
    z_: pd.DataFrame,
    ret_periods: int = 24,
    vol_window: int = 24,
    atr_period: int = 14,
    sma_fast: int = 48,
    sma_slow: int = 200,
    adx_period: int = 14,
    breakout_lookback: int = 48, # breakout_lookback 在新版中可选使用
) -> pd.DataFrame:
    """
    V3 预处理（宽松版）：计算做多所需的趋势/波动/突破特征。
    """
    z = z_.copy()
    # 基础收益与波动
    z["ret"] = z["close"].pct_change().fillna(0)
    z["rolling_ret"] = z["close"].pct_change(periods=ret_periods).fillna(0)
    z["rolling_vol"] = z["ret"].rolling(window=vol_window).std().fillna(1e-6)
    z["signal_strength"] = z["rolling_ret"] / z["rolling_vol"]
    
    # 【修改点】之前的 signal_z 条件过于严格，这里我们直接使用原始的 signal_strength
    # 也可以选择完全不使用这个指标，在run_strategy中控制
    
    # 趋势与动量过滤指标 (保持不变)
    z["sma_fast"] = z["close"].rolling(sma_fast).mean()
    z["sma_slow"] = z["close"].rolling(sma_slow).mean()
    z["adx"] = ta.ADX(z["high"], z["low"], z["close"], timeperiod=adx_period)
    
    # ATR 与突破价 (保持不变)
    z["atr"] = ta.ATR(z["high"], z["low"], z["close"], timeperiod=atr_period)
    z["hh"] = z["high"].rolling(breakout_lookback).max().shift(1)
    
    # 初始化仓位和标记列
    z["position"] = 0.0
    z["flag"] = 0.0
    return z


# --- 第二部分：策略执行逻辑 (核心修改区域) ---
# 这里是我们的重头戏，放宽入场条件，增加交易频率。
def run_strategy(
    z: pd.DataFrame,
    # 【修改点】移除了 z_long，改为使用 signal_strength_min 或完全不用
    # signal_strength_min: float = 0.5, # 如果需要，可以启用这个动能门槛
    k_init: float = 2.0,  # 初始 ATR 止损倍数 (风控保持严格)
    k_trail: float = 2.5,  # 追踪 ATR 止损倍数 (风控保持严格)
    time_stop_hours: int = 24 * 10,  # 时间止损 (风控保持严格)
    cool_down_hours: int = 6,  # 【修改点】适当缩短冷却期，让策略更快恢复交易
    use_adx: bool = True,
    adx_min: float = 15.0, # ADX门槛可以保持或适当降低，这里保持15
    # 【修改点】增加开关，决定是否启用突破和动能条件
    require_breakout: bool = False, # 开关：是否要求突破前期高点 (改为False，极大放宽条件)
    require_momentum: bool = False, # 开关：是否要求动能强度 (改为False, 极大放宽条件)
) -> tuple:
    """
    V3 宽松版做多策略：
    核心入场条件：只保留最核心的趋势过滤（均线多头排列）。
    可选入场条件：突破、动能、ADX强度等都可以通过参数开关来控制。
    出场条件：保持原有的严格风控（ATR止损、追踪止损、时间止损、趋势失效）。
    """
    Buy, Sell = [], []
    
    # 确定需要计算指标的最小数据长度
    sma_slow = 200
    i_start = sma_slow + 5 # 保证所有指标都有值

    in_pos = False
    entry_price = 0.0
    entry_i = -(10**9)
    init_stop = None
    trail_stop = None
    highest_high = 0.0
    last_exit_i = -(10**9)

    for i in range(i_start, len(z)):
        idx = z.index[i]
        close = z["close"].iloc[i]
        high = z["high"].iloc[i]
        atr = z["atr"].iloc[i]

        # --- 入场条件修改核心区 ---
        # 1. 基础趋势过滤 (这是策略的灵魂，必须保留)
        regime_up = (z["sma_fast"].iloc[i] > z["sma_slow"].iloc[i]) and \
                    (close > z["sma_slow"].iloc[i])

        # 2. 【可选】ADX强度过滤
        if use_adx:
            regime_up = regime_up and (z["adx"].iloc[i] >= adx_min)

        # 默认沿用上一根K线的仓位
        prev_pos = z["position"].iloc[i - 1]
        z.at[idx, "position"] = prev_pos

        # 尝试开仓
        if (not in_pos) and (i - last_exit_i >= cool_down_hours):
            # 基础趋势条件满足后，检查可选的附加条件
            final_entry_condition = regime_up
            
            # 3. 【可选】动能过滤 (默认关闭)
            if require_momentum:
                # 使用 signal_strength 替代了之前苛刻的 signal_z
                # 这里可以设置一个阈值，例如 signal_strength_min
                cond_momentum = z["signal_strength"].iloc[i] > 0 # 只要求动能为正即可
                final_entry_condition = final_entry_condition and cond_momentum

            # 4. 【可选】突破过滤 (默认关闭)
            if require_breakout:
                cond_breakout = close > z["hh"].iloc[i]
                final_entry_condition = final_entry_condition and cond_breakout

            # 如果最终条件满足，则开仓
            if final_entry_condition:
                in_pos = True
                z.at[idx, "flag"] = 1
                z.at[idx, "position"] = 1
                entry_price = close
                entry_i = i
                highest_high = high
                init_stop = entry_price - k_init * atr
                trail_stop = highest_high - k_trail * atr
                Buy.append(
                    [idx, entry_price, f'开仓: 趋势确认, ATR={atr:.2f}']
                )
                print(idx, f'【V3开仓】价格={entry_price:.2f}, 初始止损={init_stop:.2f}')
                continue

        # --- 出场和持仓管理 (保持不变，风控是底线) ---
        if in_pos:
            highest_high = max(highest_high, high)
            trail_stop = max(trail_stop, highest_high - k_trail * atr)
            
            trend_invalid = not (
                (z["sma_fast"].iloc[i] > z["sma_slow"].iloc[i]) and \
                (close > z["sma_slow"].iloc[i])
            )
            
            stop_price = max(init_stop, trail_stop)
            hit_stop = close <= stop_price
            time_stop = (i - entry_i) >= time_stop_hours
            
            if hit_stop or time_stop or trend_invalid:
                in_pos = False
                z.at[idx, "flag"] = -1
                z.at[idx, "position"] = 0
                price_out = close
                reason = "止损" if hit_stop else ("时间止损" if time_stop else "趋势失效")
                Sell.append([idx, price_out, f"{reason}: stop={stop_price:.2f}"])
                last_exit_i = i
                print(idx, f"【V3平仓】{reason}，价格={price_out:.2f}")
                init_stop = trail_stop = highest_high = entry_price = 0.0 # 清理变量
    
    # 整理交易记录 (保持不变)
    p1 = pd.DataFrame(Buy, columns=["买入日期", "买入价格", "备注"])
    p2 = pd.DataFrame(Sell, columns=["卖出日期", "卖出价格", "备注"])
    transaction_v3 = pd.concat([p1.reset_index(drop=True), p2.reset_index(drop=True)], axis=1)
    
    # 计算净值曲线 (保持不变)
    z["ret"] = z["close"].pct_change().fillna(0)
    effective_position = z["position"].shift(1).fillna(0)
    z["nav"] = (1 + z["ret"] * effective_position).cumprod()
    z["benchmark"] = z["close"] / z["close"].iloc[0]
    
    return z, transaction_v3


# --- 第三部分：策略执行入口 ---
def execute_strategy(z: pd.DataFrame) -> tuple:
    """新版策略执行入口"""
    # 1. 数据预处理
    z_preprocessed = preprocess_data(z)
    
    # 2. 运行宽松版的策略逻辑
    # 你可以在这里调整开关来测试不同严格程度的策略
    data_price, transaction = run_strategy(
        z_preprocessed,
        require_breakout=False, # 设置为 False 来关闭突破要求
        require_momentum=False  # 设置为 False 来关闭动能要求
    )
    
    return data_price, transaction

