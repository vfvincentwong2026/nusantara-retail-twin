"""舆情信号适配器（Phase 6，接口已预留）。

契约见 docs/data-model.md §4.5 sentiment_signals：聚合多平台热点与情感趋势，
输出品类级热度指数（heat_index 0–1）作为预测引擎外生变量；
清真认证 SKU 的情感信号赋予更高信任权重。
"""

from __future__ import annotations


class SentimentAdapter:
    def __init__(self, store=None):
        self.store = store

    def fetch(self, category: str | None = None):
        raise NotImplementedError(
            "SentimentAdapter 属 Phase 6（契约：docs/data-model.md §4.5）"
        )
