"""Croston-SBA：间歇性需求预测（C 类 SKU 分段选型，回测结论）。

非零需求间隔 p 与非零需求大小 z 分别做指数平滑（α=0.15），
SBA 修正因子 1 - α/2 抵消平滑偏差。对零膨胀的日销序列
（C 类长尾 SKU 典型形态）显著优于趋势/季节模型。
"""

from __future__ import annotations

import numpy as np


def croston_sba_forecast(series, horizon: int, alpha: float = 0.15) -> np.ndarray:
    """输入连续日销量序列（可含零），返回 horizon 天常数率预测。"""
    series = np.asarray(series, dtype=float)
    nonzero = series[series > 0]
    if len(nonzero) < 2:
        return np.full(horizon, float(nonzero[-1]) if len(nonzero) else 0.05)
    z = float(nonzero[0])
    p = 1.0
    last_idx = -1
    for i, v in enumerate(series):
        if v > 0:
            if last_idx >= 0:
                p = p + alpha * ((i - last_idx) - p)
            z = z + alpha * (v - z)
            last_idx = i
    rate = max((1 - alpha / 2) * z / max(p, 1.0), 0.05)
    return np.full(horizon, rate)
