import backtrader as bt
from indicators.pivot_market_phase import PivotMarketPhase
from indicators.k_line_market_phase import KlineMarketPhase
from indicators.pivots import Pivots

class RangeZone(bt.Indicator):
    lines = ('range_high', 'range_low', 'phase_indicator')
    plotinfo = dict(subplot=False)
    plotlines = dict(
        range_high=dict(color='red', linestyle='dashed'),
        range_low=dict(color='blue', linestyle='dashed')
    )

    def __init__(self):
        self.pivot_phase = PivotMarketPhase(self.data)
        self.kline_phase = KlineMarketPhase(self.data)
        self.pivots = Pivots(self.data)
        self.atr = bt.indicators.ATR(self.data, period=14)  # 计算 ATR
        self.range_high = None
        self.range_low = None

    def next(self):
        pivot_phase = self.pivot_phase.lines.phase[0]
        kline_phase = self.kline_phase.lines.phase[0]
        last_phase = self.lines.phase_indicator[-1]
        phase = pivot_phase

        high, low = self.data.high[0], self.data.low[0]
        atr_value = self.atr[0] * 3  # 3 倍 ATR

        if phase == 0:  # 震荡区间
            if last_phase != 0 and self.range_high is not None and self.range_low is not None:
                # 如果上一阶段不是震荡区间，且当前K线仍在前一条区间内，则沿用前一条区间
                if self.range_low <= low <= self.range_high and self.range_low <= high <= self.range_high:
                    pass  # 直接沿用之前的 range，不做修改
                else:
                    self.range_high = None
                    self.range_low = None
            
            elif self.range_high is None or self.range_low is None:
                pivot_high, pivot_low = None, None
                for i in range(1, len(self.data)):
                    if pivot_high is None and not bt.math.isnan(self.pivots.lines.pivothigh[-i]):
                        pivot_high = self.pivots.lines.pivothigh[-i]
                    if pivot_low is None and not bt.math.isnan(self.pivots.lines.pivotlow[-i]):
                        pivot_low = self.pivots.lines.pivotlow[-i]
                    if pivot_high and pivot_low:
                        break
                
                # 检查 pivot 是否有效
                self.range_high = high if pivot_high is None or abs(pivot_high - high) > atr_value else pivot_high
                self.range_low = low if pivot_low is None or abs(pivot_low - low) > atr_value else pivot_low
            else:
                self.range_high = max(self.range_high, high)
                self.range_low = min(self.range_low, low)
        elif self.range_high is not None and self.range_low is not None:
            if high > self.range_high or low < self.range_low:
                self.range_high = self.range_low = None  # 进入趋势阶段后重置

        self.lines.range_high[0] = self.range_high if self.range_high is not None else float('nan')
        self.lines.range_low[0] = self.range_low if self.range_low is not None else float('nan')
        self.lines.phase_indicator[0] = phase


class RangeZonePhaseIndicator(bt.Indicator):
    lines = ('phase_indicator',)
    plotinfo = dict(subplot=True)
    plotlines = dict(phase_indicator=dict(color='green'))

    def __init__(self):
        self.range_zone = RangeZone(self.data)

    def next(self):
        self.lines.phase_indicator[0] = self.range_zone.lines.phase_indicator[0]
