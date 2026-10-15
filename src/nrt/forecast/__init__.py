"""需求预测引擎（Phase 4，接口已预留）。

契约见 docs/architecture.md §4.1：输入历史销售 + 节庆日历 + 舆情信号 +
门店档案，输出 Store × SKU × Day 粒度的 DemandForecast。
计划实现：Prophet + LightGBM（docs/architecture.md §5）。
"""

from __future__ import annotations


class ForecastEngine:
    def __init__(self, store):
        self.store = store

    def predict(self, horizon_days: int = 30, include_ramadan: bool = False):
        raise NotImplementedError(
            "ForecastEngine 属 Phase 4：先完成 Prophet/LightGBM 实现"
            "（契约：docs/architecture.md §4.1）"
        )
