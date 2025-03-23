import backtrader as bt
import math

from indicators.bar_strength import BarStrength
from indicators.k_line_market_phase import KlineMarketPhase
from indicators.pivot_market_phase import PivotMarketPhase
from indicators.pivots import Pivots

class MarketPhase(bt.Indicator):
    lines = ('phase',)
    plotinfo = dict(subplot=True)
    plotlines = dict(phase=dict(color='purple'))

    def __init__(self):
        self.kline_phase = KlineMarketPhase(self.data)
        self.pivot_phase = PivotMarketPhase(self.data)

    # def next(self):
    #     if self.kline_phase.lines.phase[0] != 0:
    #         self.lines.phase[0] = self.kline_phase.lines.phase[0]
    #     else:
    #         self.lines.phase[0] = self.pivot_phase.lines.phase[0]

class PhaseLength(bt.Indicator):
    lines = ('phase_length',)
    plotinfo = dict(subplot=True)
    plotlines = dict(phase_length=dict(color='red'))

    def __init__(self):
        self.phase_length = 0
        self.market_phase = MarketPhase(self.data)

    def next(self):
        if self.market_phase.lines.phase[0] == self.market_phase.lines.phase[-1]:
            self.phase_length += 1
        else:
            self.phase_length = 1
        self.lines.phase_length[0] = self.phase_length