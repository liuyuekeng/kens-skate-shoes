import backtrader as bt
from indicators.bar_strength import BarStrength


class KlineMarketPhase(bt.Indicator):
    lines = ('phase',)
    plotinfo = dict(subplot=True)
    plotlines = dict(phase=dict(color='green'))

    def __init__(self):
        self.bar_strength = BarStrength(self.data)
        self.current_phase = 0

    def next(self):
        if len(self.data) < 5:
            self.lines.phase[0] = 0
            return

        prev_phase = self.lines.phase[-1]
        if prev_phase in (3, -3):
            same_direction = ((self.data.close[0] >= self.data.open[0]) == (prev_phase == 3)) or ((self.data.close[0] <= self.data.open[0]) == (prev_phase == -3))
            if same_direction:
                self.current_phase = prev_phase
            else:
                if all(((self.data.close[-i] >= self.data.open[-i]) == (prev_phase == 3)) or ((self.data.close[-i] <= self.data.open[-i]) == (prev_phase == -3)) for i in range(1, 3)):
                    if self.bar_strength.lines.strength[0] < 2:
                        self.current_phase = prev_phase
                    else:
                        self.current_phase = 0
                else:
                    self.current_phase = 0
        else:
            same_direction_count = 1
            for i in range(1, 5):
                if (self.data.close[-i] > self.data.open[-i]) == (self.data.close[0] > self.data.open[0]):
                    same_direction_count += 1
                else:
                    break

            if same_direction_count >= 3 and all(self.bar_strength.lines.strength[-i] >= 3 for i in range(3)):
                self.current_phase = 3 if self.data.close[0] > self.data.open[0] else -3
            elif same_direction_count >= 4:
                self.current_phase = 3 if self.data.close[0] > self.data.open[0] else -3
            else:
                self.current_phase = 0

        self.lines.phase[0] = self.current_phase