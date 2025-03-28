import backtrader as bt
import numpy as np
from sklearn.cluster import KMeans

class KMeansRange(bt.Indicator):
    lines = ('is_range', 'range_count')
    # plotlines = {
    #     'is_range': {'_plot': True, 'color': 'black', 'ls': '-', 'subplot': True},
    #     'range_count': {'_plot': True, 'color': 'blue', 'ls': '-', 'subplot': True}
    # }
    params = (('period', 50), ('k_max', 5), ('threshold', 0.03))  # 50根K线, 最大5个聚类, 震荡阈值 3%

    def __init__(self):
        self.addminperiod(self.p.period)
        self.range_counter = 0  # 震荡区间计数器

    def optimal_k(self, data_points):
        """使用肘部法则动态选择最佳 K 值"""
        sse = []
        k_range = range(2, self.p.k_max + 1)
        
        for k in k_range:
            kmeans = KMeans(n_clusters=k, n_init=10, random_state=42)
            kmeans.fit(data_points)
            sse.append(kmeans.inertia_)  # SSE: 簇内平方误差
        
        # 计算SSE的变化率，找到下降变缓的位置
        sse_diff = np.diff(sse)
        sse_diff2 = np.diff(sse_diff)
        optimal_k = k_range[np.argmin(sse_diff2) + 1]  # 选择拐点处的 K 值
        
        return max(2, optimal_k)  # K 至少为 2

    def next(self):
        highs = np.array(self.data.high.get(size=self.p.period))
        lows = np.array(self.data.low.get(size=self.p.period))
        closes = np.array(self.data.close.get(size=self.p.period))
        
        data_points = np.column_stack((highs, lows, closes))
        
        # 计算最优 K 值
        best_k = self.optimal_k(data_points)
        
        # 运行 K-Means
        kmeans = KMeans(n_clusters=best_k, n_init=10, random_state=42)
        kmeans.fit(data_points)
        centers = np.sort(kmeans.cluster_centers_[:, 2])  # 按收盘价排序
        
        # 计算聚类中心的范围
        range_width = abs(centers[-1] - centers[0]) / centers[0]  # 归一化震荡幅度
        
        # 标记是否为震荡区间
        is_range = 1 if range_width < self.p.threshold else 0
        self.lines.is_range[0] = is_range
        
        # 计算震荡区间的持续K线数
        if is_range:
            self.range_counter += 1
        else:
            self.range_counter = 0
        self.lines.range_count[0] = self.range_counter
