import backtrader as bt
import backtrader.indicators as btind
import numpy as np
import math

from indicators.bar_strength import BarStrength
from indicators.linear_regression_slope_pct import LinearRegressionSlopePct
from indicators.natr import NormalizedATR

class StdDevRange(bt.Indicator):
    lines = ('is_consolidating',)
    params = (('period', 20), ('k', 2.3))
    plotinfo = dict(subplot=True)  # 在子图中显示

    def __init__(self):
        sma = btind.SMA(self.data.close, period=self.p.period)
        std = btind.StandardDeviation(self.data.close, period=self.p.period)

        self.upper = sma + self.p.k * std
        self.lower = sma - self.p.k * std

    def next(self):
        self.lines.is_consolidating[0] = 1 if self.lower[0] <= self.data.close[0] <= self.upper[0] else 0

class LinearRegressionTrend(bt.Indicator):
    lines = ('strong_trend',)
    params = (('period', 20), ('scale_factor', 0.3))
    plotinfo = dict(subplot=True)  # 在子图中显示

    def __init__(self):
        self.trend = LinearRegressionSlopePct(self.data.close, period=self.p.period)
        self.natr = NormalizedATR(self.data, period=self.p.period)

    def next(self):
        
        dynamic_threshold = self.natr[0] * self.p.scale_factor

        self.lines.strong_trend[0] = abs(self.trend[0]) > dynamic_threshold


class ConsolidationIndicator(bt.Indicator):
    lines = ('consol_upper', 'consol_lower')
    plotinfo = dict(subplot=False)

    def __init__(self):
        self.stddev_range = StdDevRange(self.data)
        self.linear_regression_trend = LinearRegressionTrend(self.data)
        self.consolidating_highs = []
        self.consolidating_lows = []
        self.prev_upper = np.nan  # 记录上一个震荡区间的上界
        self.prev_lower = np.nan  # 记录上一个震荡区间的下界

    def next(self):
        is_consolidating = self.stddev_range.is_consolidating[0] and not self.linear_regression_trend.strong_trend[0]
        if is_consolidating:  # 进入震荡状态
            # 如果上一个震荡区间存在，且当前价格仍在上一个区间内，则沿用
            if not np.isnan(self.prev_upper) and not np.isnan(self.prev_lower) and \
               self.prev_lower <= self.data.close[0] <= self.prev_upper:
                self.consolidating_highs.append(self.prev_upper)
                self.consolidating_lows.append(self.prev_lower)

            self.consolidating_highs.append(self.data.high[0])
            self.consolidating_lows.append(self.data.low[0])

            # 更新震荡区间的上下界
            self.prev_upper = max(self.consolidating_highs)
            self.prev_lower = min(self.consolidating_lows)

        else:  # 退出震荡状态，但保留之前的震荡区间
            self.consolidating_highs.clear()
            self.consolidating_lows.clear()

        # 设置当前 K 线的震荡区间（如果存在）
        if self.consolidating_highs and self.consolidating_lows:
            self.lines.consol_upper[0] = max(self.consolidating_highs)
            self.lines.consol_lower[0] = min(self.consolidating_lows)
        elif not np.isnan(self.prev_upper) and not np.isnan(self.prev_lower) \
            and self.data.high[0] <= self.prev_upper and self.data.low[0] >= self.prev_lower:
            self.lines.consol_upper[0] = self.prev_upper
            self.lines.consol_lower[0] = self.prev_lower
        else:
            # 沿用上一次的震荡区间，直到找到新的
            self.lines.consol_upper[0] = float('nan')
            self.lines.consol_lower[0] = float('nan')

class ConsolidationDuration(bt.Indicator):
    lines = ('duration',)
    plotinfo = dict(subplot=True)

    def __init__(self):
        self.consolidation_indicator = ConsolidationIndicator(self.data)
        self.counter = 0  # 记录震荡区间的持续时间

    def next(self):
        if not (math.isnan(self.consolidation_indicator.consol_upper[0]) or math.isnan(self.consolidation_indicator.consol_lower[0])):
            self.counter += 1
        else:
            self.counter = 0

        self.lines.duration[0] = self.counter

class BuySellSignal(bt.Indicator):
    lines = ('suspect_signal', 'confirm_signal')
    plotinfo = dict(subplot=True)
    
    params = (
        ('duration_threshold', 20),
        ('close_threshold', 0.5),
    )
    
    def __init__(self):
        self.consolidation_duration = ConsolidationDuration(self.data)
        self.consolidation_indicator = ConsolidationIndicator(self.data)
        self.bar_strength = BarStrength(self.data)
    
    def next(self):
        self.lines.suspect_signal[0] = 0
        self.lines.confirm_signal[0] = 0
        close = self.data.close[0]
        # 判断确认信号
        if self.lines.suspect_signal[-1] != 0:
            high = self.data.high[0]
            low = self.data.low[0]
            
            if self.lines.suspect_signal[-1] == 1 and close >= (high - (high - low) * (1 - self.p.close_threshold)):
                self.lines.confirm_signal[0] = 2
                return
            elif self.lines.suspect_signal[-1] == -1 and close <= (low + (high - low) * (1 - self.p.close_threshold)):
                self.lines.confirm_signal[0] = -2
                return
        
        # 过滤 ConsolidationDuration，前一个 K 线需要大于等于 20
        if self.consolidation_duration[-1] < self.p.duration_threshold:
            return
        
        # 当前 K 线是否仍处于震荡区间
        if not (math.isnan(self.consolidation_indicator.consol_upper[0]) or 
                math.isnan(self.consolidation_indicator.consol_lower[0])):
            return
        
        # 判断当前 K 线收盘价是否超出前一个 K 线的震荡区间
        prev_upper = self.consolidation_indicator.consol_upper[-1]
        prev_lower = self.consolidation_indicator.consol_lower[-1]
        if math.isnan(prev_upper) or math.isnan(prev_lower):
            return
        
        if close <= prev_upper and close >= prev_lower:
            return
        
        # 判断当前 K 线的强度是否大于 1
        if self.bar_strength[0] <= 1:
            return
        
        # 设置疑似信号标记
        if close > prev_upper:
            self.lines.suspect_signal[0] = 1
        elif close < prev_lower:
            self.lines.suspect_signal[0] = -1
        
        
