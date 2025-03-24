import backtrader as bt
import math

from indicators.pivots import Pivots
from indicators.std_dev_range import BuySellSignal, ConsolidationDuration, ConsolidationIndicator

class ConfirmSignalStrategy(bt.Strategy):
    params = (
        ('risk_per_trade', 0.02),  # 单次交易最大风险占比
        ('lookback_bars', 3),  # 向前查找突破区间的最大K线数量
    )

    def log(self, txt):
        """ 输出日志信息 """
        print(f"K线索引={len(self)}, {txt}")

    def __init__(self):
        self.consolidation_indicator = ConsolidationIndicator(self.data)
        self.consolidation_duration = ConsolidationDuration(self.data)
        self.buy_sell_signal = BuySellSignal(self.data)
        self.confirm_signal = self.buy_sell_signal.lines.confirm_signal
        self.pivots = Pivots(self.data)
        self.pivot_high = self.pivots.lines.pivothigh
        self.pivot_low = self.pivots.lines.pivotlow
        self.consol_upper = self.consolidation_indicator.lines.consol_upper
        self.consol_lower = self.consolidation_indicator.lines.consol_lower

        self.orders = {}  # 记录所有订单，格式: {entry_order_ref: (stop_order_ref, limit_order_ref)}
    
    def has_open_position(self):
        return bool(self.orders)

    def find_breakout_zone(self):
        for i in range(-1, -self.p.lookback_bars - 1, -1):
            if not math.isnan(self.consol_upper[i]) and not math.isnan(self.consol_lower[i]):
                return self.consol_upper[i], self.consol_lower[i]
        return None, None
    
    def find_pivot_points(self):
        highs, lows = [], []
        i = -1
        while abs(i) <= len(self.data):  # 直到数据耗尽
            if not math.isnan(self.pivot_high[i]):
                highs.append(self.pivot_high[i])
            if not math.isnan(self.pivot_low[i]):
                lows.append(self.pivot_low[i])
            if highs and lows:
                break
            i -= 1
        return highs, lows

    def next(self):
        if self.has_open_position():
            return

        if self.confirm_signal[0] == 0:
            return

        upper, lower = self.find_breakout_zone()
        if upper is None or lower is None:
            return
        
        highs, lows = self.find_pivot_points()
        if not highs or not lows:
            return
        
        entry_price = self.data.high[0] + 0.01 if self.confirm_signal[0] > 0 else self.data.low[0] - 0.01
        stop_loss_price = min(lows) if self.confirm_signal[0] > 0 else max(highs)
        target_price = upper + (upper - lower) if self.confirm_signal[0] > 0 else lower - (upper - lower)
        
        risk = abs(entry_price - stop_loss_price)
        reward = abs(target_price - entry_price)
        
        if reward / risk < 1:
            return
        
        cash = self.broker.get_cash()
        size = (cash * self.p.risk_per_trade) / risk
        direction = "买入" if self.confirm_signal[0] > 0 else "卖出"
        
        self.log(f"设定入场订单: 价格={entry_price:.2f}, 方向={direction}, 金额={size * entry_price:.2f}")
        
        entry_order = self.buy(price=entry_price, size=size, exectype=bt.Order.Stop) if self.confirm_signal[0] > 0 \
                      else self.sell(price=entry_price, size=size, exectype=bt.Order.Stop)
        
        stop_order = self.sell(price=stop_loss_price, size=size, exectype=bt.Order.Stop, parent=entry_order) if self.confirm_signal[0] > 0 \
                     else self.buy(price=stop_loss_price, size=size, exectype=bt.Order.Stop, parent=entry_order)
        
        limit_order = self.sell(price=target_price, size=size, exectype=bt.Order.Limit, parent=entry_order) if self.confirm_signal[0] > 0 \
                      else self.buy(price=target_price, size=size, exectype=bt.Order.Limit, parent=entry_order)
        
        self.orders[entry_order.ref] = (stop_order.ref, limit_order.ref)
        
        self.log(f"设定止损订单: 价格={stop_loss_price:.2f}, 方向={'卖出' if self.confirm_signal[0] > 0 else '买入'}, 金额={size * stop_loss_price:.2f}")
        self.log(f"设定止盈订单: 价格={target_price:.2f}, 方向={'卖出' if self.confirm_signal[0] > 0 else '买入'}, 金额={size * target_price:.2f}")
    
    def notify_order(self, order):
        if order.status == bt.Order.Completed:
            order_type = "入场订单" if order.ref in self.orders else "止盈离场" if order.ref in [v[1] for v in self.orders.values()] else "止损离场"
            direction = "买入" if order.isbuy() else "卖出"
            self.log(f"订单成交 ({order_type}): 价格={order.executed.price:.2f}, 方向={direction}, 金额={order.executed.size * order.executed.price:.2f}")
            
            for entry_ref, (stop_ref, limit_ref) in list(self.orders.items()):
                if order.ref == stop_ref:
                    self.cancel(self.orders[entry_ref][1])  # 取消止盈订单
                    del self.orders[entry_ref]
                    break
                elif order.ref == limit_ref:
                    self.cancel(self.orders[entry_ref][0])  # 取消止损订单
                    del self.orders[entry_ref]
                    break
        
        elif order.status in [bt.Order.Canceled, bt.Order.Margin, bt.Order.Rejected]:
            for entry_ref in list(self.orders.keys()):
                if order.ref == entry_ref:
                    del self.orders[entry_ref]
