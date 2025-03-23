import backtrader as bt
from indicators.range_zone import RangeZone
from indicators.bar_strength import BarStrength

class BreakoutSignal(bt.Indicator):
    lines = ('buy_signal',)
    plotinfo = dict(subplot=True)
    plotlines = dict(
        buy_signal=dict(marker='^', markersize=8.0, color='green', fillstyle='full'),
    )

    def __init__(self):
        self.range_zone = RangeZone(self.data)
        self.bar_strength = BarStrength(self.data)

    def next(self):
        high, low, close = self.data.high[0], self.data.low[0], self.data.close[0]
        range_high, range_low = self.range_zone.lines.range_high[-1], self.range_zone.lines.range_low[-1]
        
        if not (bt.numutils.isnan(range_high) or bt.numutils.isnan(range_low)):
            if self.bar_strength.lines.strength[0] > 1 and close > range_high:  # 突破上沿
                self.lines.buy_signal[0] = 1
            else:
                self.lines.buy_signal[0] = 0
        else:
            self.lines.buy_signal[0] = 0
