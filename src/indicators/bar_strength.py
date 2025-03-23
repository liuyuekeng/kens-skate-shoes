import backtrader as bt

class BarStrength(bt.Indicator):
    lines = ('strength',)  # 只输出一个强度分数

    params = (
        ('period', 20),  # 用于计算 ATR 的周期
        ('close_percent', 0.8),  # 80% 收盘价位置的阈值
    )

    def __init__(self):
        # 使用 ATR 指标计算振幅
        self.atr = bt.indicators.AverageTrueRange(self.data, period=self.p.period)

    def next(self):
        # 获取当前K线的价格
        high = self.data.high[0]
        low = self.data.low[0]
        open = self.data.open[0]
        close = self.data.close[0]

        # 计算当前K线的强度分数
        strength_score = 0
        if (high - low) > self.atr[0]:
            strength_score += 1  # 振幅大于 ATR，增加分数

        body_ratio = abs(close - open) / (high - low) if (high - low) > 0 else 0
        if body_ratio > 0.5:
            strength_score += 1  # body_ratio 大于 0.5，增加分数

        if close > open:  # 阳线
            if close >= (high - (high - low) * (1 - self.p.close_percent)):  # 收盘接近最高价
                strength_score += 1
        else:  # 阴线
            if close <= (low + (high - low) * (1 - self.p.close_percent)):  # 收盘接近最低价
                strength_score += 1

        self.lines.strength[0] = strength_score  # 设置最终的强度值