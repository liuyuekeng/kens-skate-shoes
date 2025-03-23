import backtrader as bt
import numpy as np

class LinearRegressionSlopePct(bt.Indicator):
    """
    计算最近 `period` 根 K 线的线性回归斜率，并转换为百分比变化
    """
    lines = ('slope_pct',)
    params = (('period', 20),)

    def __init__(self):
        self.addminperiod(self.p.period)

    def next(self):
        if len(self.data) < self.p.period:
            self.lines.slope_pct[0] = 0
            return

        # 取最近 period 根 K 线的索引（X）和收盘价（Y）
        x = np.arange(self.p.period)
        y = np.array(self.data.get(size=self.p.period))

        # 计算线性回归斜率
        A = np.vstack([x, np.ones(len(x))]).T
        m, _ = np.linalg.lstsq(A, y, rcond=None)[0]  # 线性回归求解斜率

        # 计算平均价格
        avg_price = np.mean(y)

        # 计算斜率的百分比变化
        self.lines.slope_pct[0] = (m / avg_price) * 100 if avg_price != 0 else 0
