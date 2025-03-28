import backtrader as bt
import numpy as np
import math

from indicators.bar_strength import BarStrength
from indicators.linear_regression_slope_pct import LinearRegressionSlopePct
from indicators.natr import NormalizedATR

class StdDevHistogramRange(bt.Indicator):
    lines = ('is_range', 'range_count')
    # plotlines = {
    #     'is_range': {'_plot': True, 'color': 'black', 'ls': '-', 'subplot': True},
    #     'range_count': {'_plot': True, 'color': 'blue', 'ls': '-', 'subplot': True}
    # }
    params = (('period', 50), ('density_threshold', 0.5), ('bins', 10), ('dynamic_factor', 2))

    def __init__(self):
        self.addminperiod(self.p.period)
        self.range_counter = 0

    def next(self):
        closes = np.array(self.data.close.get(size=self.p.period))
        
        # 计算过去 N 根 K 线的平均价格和标准差
        avg_price_last_n = np.mean(closes)
        std_price_last_n = np.std(closes)
        
        # 计算动态的 std_threshold（标准差阈值）
        # 通过历史的波动情况来设定阈值
        dynamic_std_threshold = self.p.dynamic_factor * std_price_last_n / avg_price_last_n
        # print(f"Dynamic Std Threshold: {dynamic_std_threshold * 100}%")  # 输出动态标准差阈值
        
        # 计算当前周期的标准差并转换为百分比
        std_price = std_price_last_n / avg_price_last_n
        # print(f"Std Price (Percentage): {std_price * 100}%")  # 输出当前标准差百分比
        
        # 计算价格密度直方图
        hist, bin_edges = np.histogram(closes, bins=self.p.bins, density=True)
        max_density = max(hist) if len(hist) > 0 else 0
        # print(f"Max Density: {max_density}")  # 输出最大密度
        
        # 判断是否进入震荡区间
        is_range = 1 if (std_price < dynamic_std_threshold and max_density > self.p.density_threshold) else 0
        # print(f"Is Range: {is_range}")  # 输出震荡区间标记
        
        self.lines.is_range[0] = is_range

        # 计算震荡区间的持续 K 线数
        if is_range:
            self.range_counter += 1
        else:
            self.range_counter = 0
        self.lines.range_count[0] = self.range_counter

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
        self.stddev_range = StdDevHistogramRange(self.data)
        self.linear_regression_trend = LinearRegressionTrend(self.data)
        self.consolidating_highs = []
        self.consolidating_lows = []
        self.prev_upper = np.nan  # 记录上一个震荡区间的上界
        self.prev_lower = np.nan  # 记录上一个震荡区间的下界

    def next(self):
        # is_consolidating = self.stddev_range.is_range[0]
        is_consolidating = self.stddev_range.is_range[0] and not self.linear_regression_trend.strong_trend[0]
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
        
        
