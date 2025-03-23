import math
import backtrader as bt
from indicators.pivots import Pivots


class PivotMarketPhase(bt.Indicator):
    lines = ('phase',)
    plotinfo = dict(subplot=True)
    plotlines = dict(phase=dict(color='blue'))

    def __init__(self):
        self.pivots = Pivots(self.data)
        self.current_phase = 0

    def next(self):
        idx = len(self.data) - 1
        highs, lows = [], []
        lookback_idx = 1

        while len(highs) < 3 or len(lows) < 3:
            if idx - lookback_idx < 0:
                break
            high_val = self.pivots.pivothigh[-lookback_idx]
            low_val = self.pivots.pivotlow[-lookback_idx]
            if not math.isnan(high_val):
                highs.append(high_val)
            if not math.isnan(low_val):
                lows.append(low_val)
            lookback_idx += 1

        if len(highs) < 3 or len(lows) < 3:
            self.lines.phase[0] = 0
            return

        new_phase = 0
        if all(x > y for x, y in zip(highs, highs[1:])) and all(x > y for x, y in zip(lows, lows[1:])):
            new_phase = 3
        elif all(x < y for x, y in zip(highs, highs[1:])) and all(x < y for x, y in zip(lows, lows[1:])):
            new_phase = -3
        else:
            new_phase = 0

        self.current_phase = new_phase
        self.lines.phase[0] = self.current_phase