
import pandas as pd
import talib as ta
import numpy as np

def preprocess_data(
    z_: pd.DataFrame,
    ret_periods: int = 24,
    vol_window: int = 24,
    atr_period: int = 14,
) -> pd.DataFrame:
    """数据预处理：计算收益率、波动率、ATR（小时级可调）"""
    z = z_.copy()
    z["ret"] = z["close"].pct_change().fillna(0)
    # 小时级：默认用近1天(24小时)的动量与波动率衡量信号强度
    z["rolling_ret"] = z["close"].pct_change(periods=ret_periods).fillna(0)
    z["rolling_vol"] = z["ret"].rolling(window=vol_window).std().fillna(1e-6)
    z["signal_strength"] = z["rolling_ret"] / z["rolling_vol"]
    z["atr"] = ta.ATR(z["high"], z["low"], z["close"], timeperiod=atr_period)
    z["position"] = 0.0
    z["flag"] = 0.0
    return z

def preprocess_data(
    z_: pd.DataFrame,
    ret_periods: int = 24,
    vol_window: int = 24,
    atr_period: int = 14,
    sma_fast: int = 48,
    sma_slow: int = 200,
    adx_period: int = 14,
    breakout_lookback: int = 48,
) -> pd.DataFrame:
    """V2 预处理：仅做多所需的趋势/波动/突破特征。
    要求输入为 1 小时 K 线 DataFrame，至少包含: ['open','high','low','close']，索引为时间。
    """
    z = z_.copy()
    # 基础收益与波动
    z["ret"] = z["close"].pct_change().fillna(0)
    z["rolling_ret"] = z["close"].pct_change(periods=ret_periods).fillna(0)
    z["rolling_vol"] = z["ret"].rolling(window=vol_window).std().fillna(1e-6)
    z["signal_strength"] = z["rolling_ret"] / z["rolling_vol"]
    # 信号 zscore（长期均值/方差）
    _mean = z["signal_strength"].rolling(240).mean()
    _std = z["signal_strength"].rolling(240).std().replace(0, 1)
    z["signal_z"] = ((z["signal_strength"] - _mean) / _std).fillna(0)
    # 趋势与动量过滤
    z["sma_fast"] = z["close"].rolling(sma_fast).mean()
    z["sma_slow"] = z["close"].rolling(sma_slow).mean()
    z["adx"] = ta.ADX(z["high"], z["low"], z["close"], timeperiod=adx_period)
    # ATR 与突破价
    z["atr"] = ta.ATR(z["high"], z["low"], z["close"], timeperiod=atr_period)
    z["hh"] = (
        z["high"].rolling(breakout_lookback).max().shift(1)
    )  # 上一根之前 N 小时最高
    # 初始化列（与 V1 保持一致）
    z["position"] = 0.0
    z["flag"] = 0.0
    return z

def run_strategy(
    z: pd.DataFrame,
    z_long: float = 0.8,  # 入场信号强度阈值（z-score）
    k_init: float = 2.0,  # 初始 ATR 止损倍数
    k_trail: float = 2.5,  # 追踪 ATR 止损倍数
    time_stop_hours: int = 24 * 10,  # 时间止损（持仓最久小时数）
    cool_down_hours: int = 24,  # 冷却期：平仓后 N 小时内不再开新仓
    use_adx: bool = True,
    adx_min: float = 15.0,
) -> tuple:
    """V2 仅做多、全仓、无费率版本。
    入场：趋势过滤(仅多头)，signal_z > z_long，且收盘上破过去 N 小时高点。
    出场：初始 ATR 止损 + 追踪 ATR 止损 + 时间止损 + 趋势失效（SMA48 下穿 SMA200）。
    结果列：position_v2、flag_v2、nav_v2、benchmark。
    返回: (DataFrame, 交易记录DataFrame)
    """
    Buy, Sell = [], []
    # 需要的最小起始索引
    sma_fast = int(
        z.get("sma_fast").rolling(1).window
        if hasattr(z.get("sma_fast"), "rolling")
        else 48
    )  # 兜底
    sma_slow = 200
    atr_period = 14
    breakout_lookback = 48
    i_start = max(240, sma_slow, breakout_lookback, atr_period)
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
        # 趋势过滤（仅多头）
        regime_up = (close > z["sma_slow"].iloc[i]) and (
            z["sma_fast"].iloc[i] > z["sma_slow"].iloc[i]
        )
        if use_adx:
            regime_up = regime_up and (z["adx"].iloc[i] >= adx_min)
        # 默认沿用上一根仓位
        prev_pos = z["position"].iloc[i - 1]
        z.at[idx, "position"] = prev_pos
        # 尝试开仓
        if (not in_pos) and (i - last_exit_i >= cool_down_hours):
            cond_signal = z["signal_z"].iloc[i] > z_long
            cond_breakout = close > z["hh"].iloc[i]
            if regime_up and cond_signal and cond_breakout:
                in_pos = True
                z.at[idx, "flag"] = 1
                z.at[idx, "position"] = 1
                entry_price = close
                entry_i = i
                highest_high = high
                init_stop = entry_price - k_init * atr
                trail_stop = highest_high - k_trail * atr
                Buy.append(
                    [
                        idx,
                        entry_price,
                        f'开仓: z={z["signal_z"].iloc[i]:.2f}, ATR={atr:.2f}',
                    ]
                )
                print(
                    idx,
                    f'【V2开仓】z={z["signal_z"].iloc[i]:.2f}, 价格={entry_price:.2f}, 初始止损={init_stop:.2f}',
                )
                continue
        # 管理持仓
        if in_pos:
            highest_high = max(highest_high, high)
            # 动态追踪止损
            trail_stop = max(trail_stop, highest_high - k_trail * atr)
            # 趋势失效
            trend_invalid = not (
                (z["sma_fast"].iloc[i] > z["sma_slow"].iloc[i])
                and (close > z["sma_slow"].iloc[i])
            )
            # 触发任何离场条件
            stop_price = max(init_stop, trail_stop)
            hit_stop = close <= stop_price
            time_stop = (i - entry_i) >= time_stop_hours
            if hit_stop or time_stop or trend_invalid:
                in_pos = False
                z.at[idx, "flag"] = -1
                z.at[idx, "position"] = 0
                price_out = close
                reason = (
                    "止损" if hit_stop else ("时间止损" if time_stop else "趋势失效")
                )
                Sell.append([idx, price_out, f"{reason}: stop={stop_price:.2f}"])
                last_exit_i = i
                print(idx, f"【V2平仓】{reason}，价格={price_out:.2f}")
                # 清空变量以防误用
                init_stop = None
                trail_stop = None
                highest_high = 0.0
                entry_price = 0.0
    # 交易记录
    p1 = pd.DataFrame(Buy, columns=["买入日期", "买入价格", "备注"])
    p2 = pd.DataFrame(Sell, columns=["卖出日期", "卖出价格", "备注"])
    transaction = pd.concat([p1, p2], axis=1)
    # 净值（V2）
    z["ret"] = z["close"].pct_change().fillna(0)
    effective_position = z["position"].shift(1).fillna(0)
    z["nav"] = (1 + z["ret"] * effective_position).cumprod()
    z["benchmark"] = z["close"] / z["close"].iloc[0]
    return z, transaction

def execute_strategy(z: pd.DataFrame) -> tuple:
    z = preprocess_data(z)
    data_price, transaction = run_strategy(z)
    return data_price, transaction