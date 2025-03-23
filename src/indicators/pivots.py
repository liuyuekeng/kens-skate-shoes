import backtrader as bt

class Pivots(bt.Indicator):
    lines = ('pivothigh', 'pivotlow')
    params = (('lookback', 3),)  # 移除 threshold 参数

    plotinfo = dict(subplot=False)  # 让指标绘制在主图
    plotlines = dict(
        pivothigh=dict(marker='v', markersize=5.0, color='red', fillstyle='full'),
        pivotlow=dict(marker='^', markersize=5.0, color='blue', fillstyle='full'),
    )

    def __init__(self):
        self.addminperiod(self.p.lookback * 2 + 1)
        self.last_pivot_high_idx = None  # 记录上一个高点的索引
        self.last_pivot_low_idx = None   # 记录上一个低点的索引

        # 让关键点跟随 K 线主图绘制
        self.plotinfo.plotmaster = self.data

    def next(self):
        lookback = self.p.lookback
        idx = len(self.data) - 1

        if idx < lookback:
            return

        try:
            high_vals = [self.data.high[-i] for i in range(lookback, -lookback - 1, -1)]
            low_vals = [self.data.low[-i] for i in range(lookback, -lookback - 1, -1)]
        except IndexError:
            return

        mid_high = self.data.high[0]
        mid_low = self.data.low[0]

        # **局部高点**
        if mid_high == max(high_vals):  # 最高点判断
            if self.last_pivot_high_idx is None or (idx - self.last_pivot_high_idx > lookback):
                self.lines.pivothigh[0] = mid_high
                self.last_pivot_high_idx = idx  # 记录最新的高点索引
            else:
                self.lines.pivothigh[0] = float('nan')
        else:
            self.lines.pivothigh[0] = float('nan')

        # **局部低点**
        if mid_low == min(low_vals):  # 最低点判断
            if self.last_pivot_low_idx is None or (idx - self.last_pivot_low_idx > lookback):
                self.lines.pivotlow[0] = mid_low
                self.last_pivot_low_idx = idx  # 记录最新的低点索引
            else:
                self.lines.pivotlow[0] = float('nan')
        else:
            self.lines.pivotlow[0] = float('nan')