from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import backtrader as bt
import argparse
import os
import pandas as pd
from indicators import MarketPhase, PhaseLength
from indicators.k_means_range import KMeansRange
from indicators.market_phase import KlineMarketPhase, PivotMarketPhase
from indicators.pivots import Pivots

from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource

from indicators.range_zone import RangeZone, RangeZonePhaseIndicator
from indicators import StdDevRange, ConsolidationIndicator
from indicators.std_dev_histogram_range import StdDevHistogramRange
from indicators.std_dev_range import BuySellSignal, ConsolidationDuration, LinearRegressionTrend
from strategies import ConfirmSignalStrategy

class CSVData(bt.feeds.GenericCSVData):
    params = (
        ('dtformat', '%Y-%m-%d %H:%M:%S'),  # 解析标准时间格式
        ('datetime', 0),
        ('open', 1),
        ('high', 2),
        ('low', 3),
        ('close', 4),
        ('volume', 5),
        ('openinterest', -1),
    )

class MyStrategy(bt.Strategy):
    params = (
        ('period', 14),  # ATR 计算周期
    )

    def __init__(self):
        # self.pivots = Pivots(self.data)
        # self.pivot_market_phase = PivotMarketPhase(self.data)
        # self.kline_market_phase = KlineMarketPhase(self.data)
        # self.range_zone = RangeZone(self.data)
        # self.range_zone_phase = RangeZonePhaseIndicator(self.data);
        # self.std_dev_range = StdDevRange(self.data)
        # self.linear_regression_trend = LinearRegressionTrend(self.data)
        # self.consolidation_indicator = ConsolidationIndicator(self.data)
        # self.consolidation_duration = ConsolidationDuration(self.data)
        # self.buy_sell_signal = BuySellSignal(self.data)
        # self.k_means = KMeansRange(self.data)
        self.std_dev_histogram_range = StdDevHistogramRange(self.data)

    # def next(self):

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Backtrader回测程序')
    parser.add_argument('symbol', type=str, help='分析的交易对，例如 SOL-USDT')
    args = parser.parse_args()
    
    data_path = os.path.join('data', f'{args.symbol}_candlesticks.csv')
    if not os.path.exists(data_path):
        print(f'错误: {data_path} 文件不存在')
        exit(1)
    
    df = pd.read_csv(data_path)
    # df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], unit='ms')  # 仅转换为 datetime，不格式化
    df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], unit='ms').astype('datetime64[ns]')
    temp_path = os.path.join('data', f'temp_{args.symbol}_candlesticks.csv')
    df.to_csv(temp_path, index=False, date_format='%Y-%m-%d %H:%M:%S')  # 确保 CSV 保存时格式正确
    
    data_length = len(df)
    print(f'成功加载数据文件: {data_path}, 数据长度: {data_length}')
    
    cerebro = bt.Cerebro()
    cerebro.broker.setcommission(commission=0.0008,  # 例如 0.1% 佣金
                             commtype=bt.CommInfoBase.COMM_PERC)  # 按百分比计算

    cerebro.addstrategy(ConfirmSignalStrategy)
    # cerebro.addstrategy(MyStrategy)

    data = CSVData(dataname=temp_path)
    cerebro.adddata(data)
    cerebro.run()
    
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    
    cerebro.run()
    
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    cerebro.plot(style='candle', barup='green', bardown='red')

    #os.remove(temp_path)  # 运行结束后删除临时文件
