import backtrader as bt
import math

from indicators.pivots import Pivots
from indicators.std_dev_range import BuySellSignal, ConsolidationDuration, ConsolidationIndicator

class ConfirmSignalStrategy(bt.Strategy):
    params = (
        ('risk_per_trade', 0.02),  # 单次交易最大风险占比
        ('lookback_bars', 3),  # 向前查找突破区间的最大K线数量
    )

    def log(self, txt, dt=None):
        """ 输出日志信息 """
        dt = dt or self.datas[0].datetime.datetime(0)
        print(f"{dt.strftime('%Y-%m-%d %H:%M:%S')}, {txt}")

    def __init__(self):
        self.consolidation_indicator = ConsolidationIndicator(self.data)
        self.consolidation_duration = ConsolidationDuration(self.data)
        self.buy_sell_signal = BuySellSignal(self.data)
        self.confirm_signal = self.buy_sell_signal.lines.confirm_signal
        self.pivots = Pivots(self.data)
        self.pivot_high = self.pivots.lines.pivothigh  # 修改这里
        self.pivot_low = self.pivots.lines.pivotlow    # 修改这里
        self.consol_upper = self.consolidation_indicator.lines.consol_upper
        self.consol_lower = self.consolidation_indicator.lines.consol_lower
        
        self.entry_order = None  # 记录入场订单
        self.stop_order = None   # 记录止损订单
        self.limit_order = None  # 记录止盈订单
    
    def has_open_position(self):
        return self.entry_order and self.entry_order.status in [bt.Order.Accepted, bt.Order.Completed]

    def find_breakout_zone(self):
        for i in range(-1, -self.p.lookback_bars - 1, -1):
            if not math.isnan(self.consol_upper[i]) and not math.isnan(self.consol_lower[i]):
                return self.consol_upper[i], self.consol_lower[i]
        return None, None
    
    def find_pivot_points(self):
        highs, lows = [], []
        for i in range(-1, -self.p.lookback_bars * 2 - 1, -1):
            if not math.isnan(self.pivot_high[i]):  # 关键高点
                highs.append(self.pivot_high[i])
            if not math.isnan(self.pivot_low[i]):  # 关键低点
                lows.append(self.pivot_low[i])
            if highs and lows:
                break
        return highs, lows

    
    def next(self):
        if self.has_open_position():
            return  # 如果已有仓位，跳过

        if self.confirm_signal[0] == 0:
            return  # 没有交易信号

        self.log("信号！")
        
        upper, lower = self.find_breakout_zone()
        if upper is None or lower is None:
            return  # 没找到突破区间
        self.log("信号！111")
        
        highs, lows = self.find_pivot_points()
        if not highs or not lows:
            return  # 没找到足够的关键点
        self.log("信号！222")
        
        entry_price = self.data.high[0] + 0.01 if self.confirm_signal[0] > 0 else self.data.low[0] - 0.01
        stop_loss = min(lows) if self.confirm_signal[0] > 0 else max(highs)
        target_price = upper + (upper - lower) if self.confirm_signal[0] > 0 else lower - (upper - lower)
        
        risk = abs(entry_price - stop_loss)
        reward = abs(target_price - entry_price)
        
        if reward / risk < 1:
            return  # 盈亏比不足 1，不交易
        self.log("信号！333")
        
        if (self.confirm_signal[0] > 0 and self.data.close[0] > target_price) or \
           (self.confirm_signal[0] < 0 and self.data.close[0] < target_price):
            return  # TODO: 突破过强，暂时跳过
        self.log("信号！444")
        
        cash = self.broker.get_cash()
        size = (cash * self.p.risk_per_trade) / risk
        
        self.entry_order = self.buy(exectype=bt.Order.Stop, price=entry_price, size=size) if self.confirm_signal[0] > 0 \
                          else self.sell(exectype=bt.Order.Stop, price=entry_price, size=size)
    
    def notify_order(self, order):
        if order.status == bt.Order.Completed:
            if order == self.entry_order:
                stop_loss_price = order.executed.price - abs(order.executed.price - min(self.find_pivot_points()[1]))
                target_price = order.executed.price + abs(order.executed.price - self.find_breakout_zone()[0])
                
                self.stop_order = self.sell(exectype=bt.Order.Stop, price=stop_loss_price, size=order.executed.size) if order.isbuy() \
                                 else self.buy(exectype=bt.Order.Stop, price=stop_loss_price, size=order.executed.size)
                
                self.limit_order = self.sell(exectype=bt.Order.Limit, price=target_price, size=order.executed.size) if order.isbuy() \
                                  else self.buy(exectype=bt.Order.Limit, price=target_price, size=order.executed.size)
            
        elif order.status in [bt.Order.Canceled, bt.Order.Margin, bt.Order.Rejected]:
            if order == self.entry_order:
                self.entry_order = None
