import backtrader as bt

class BodyRatio(bt.Indicator):
    lines = ('body_ratio',)  # 现在有两个输出变量：当前的 body_ratio 和 最近 K 根K线的平均 body_ratio

    def next(self):
        # 获取当前K线的价格
        high = self.data.high[0]
        low = self.data.low[0]
        open = self.data.open[0]
        close = self.data.close[0]

        # 计算当前K线的 body_ratio
        body = abs(close - open)
        total = abs(high - low)

        self.lines.body_ratio[0] = body / total if total > 0 else 0  # 计算当前K线的 body_ratio
