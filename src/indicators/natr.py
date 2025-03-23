import backtrader as bt

class NormalizedATR(bt.Indicator):
    lines = ('natr',)
    params = (('period', 14),)

    def __init__(self):
        self.atr = bt.indicators.ATR(self.data, period=self.p.period)

    def next(self):
        self.lines.natr[0] = (self.atr[0] / self.data.close[0]) * 100
