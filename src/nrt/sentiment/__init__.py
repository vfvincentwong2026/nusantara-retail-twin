"""舆情信号适配器（Phase 6）。

对应 docs/data-model.md §4.5：聚合多平台热点与情感趋势，输出品类级
热度指数（heat_index 0–1，sentiment_score -1..1），作为预测引擎外生变量。
真实多平台接入属 Phase 8；当前为确定性合成源（seed 可复现）。
清真认证 SKU 的情感信号赋予更高信任权重（§市场背景：信任传递）。
"""

from __future__ import annotations

import math
import random
from datetime import date, timedelta
from typing import Optional

from nrt.forecast.history import CATEGORY_KEY

SOURCES = ("tiktok", "twitter", "news")
TRUST_WEIGHT_HALAL = 1.5  # 清真品类情感信号信任权重
TRUST_WEIGHT_BASE = 1.0


class SentimentAdapter:
    def __init__(self, store=None, seed: int = 42):
        self.store = store
        self.rng = random.Random(seed)

    def fetch(self, category: str, days: int = 30, end_date: Optional[date] = None) -> list[dict]:
        """生成某品类近 N 天的合成舆情信号序列。"""
        end = end_date or date.today()
        cat_key = CATEGORY_KEY.get(category, "none")
        signals = []
        theta = self.rng.uniform(0, 2 * math.pi)
        for i in range(days):
            d = end - timedelta(days=days - 1 - i)
            wave = 0.5 + 0.5 * math.sin(2 * math.pi * i / 14 + theta)  # 双周话题周期
            spike = 0.35 if self.rng.random() < 0.06 else 0.0           # 偶发热点
            heat = min(1.0, 0.25 + 0.45 * wave + spike + self.rng.uniform(-0.08, 0.08))
            sentiment = max(-1.0, min(1.0, 0.25 + self.rng.uniform(-0.5, 0.5) + spike))
            signals.append(
                {
                    "signal_date": d.isoformat(),
                    "category": category,
                    "category_key": cat_key,
                    "heat_index": round(heat, 3),
                    "sentiment_score": round(sentiment, 3),
                    "source": self.rng.choice(SOURCES),
                }
            )
        return signals

    def aggregate(self, category: str, **kw) -> dict:
        """聚合为品类级单日信号（预测引擎外生变量格式）。"""
        signals = self.fetch(category, **kw)
        heat = sum(s["heat_index"] for s in signals) / len(signals)
        sent = sum(s["sentiment_score"] for s in signals) / len(signals)
        # 清真相关品类（食品/饮料/服饰）信号信任权重更高
        weight = TRUST_WEIGHT_HALAL if CATEGORY_KEY.get(category) in ("food", "beverages", "fashion") else TRUST_WEIGHT_BASE
        return {
            "category": category,
            "heat_index": round(heat, 3),
            "sentiment_score": round(sent, 3),
            "trust_weight": weight,
            "sample_size": len(signals),
        }

    def exogenous_multiplier(self, agg: dict) -> float:
        """外生乘数：热度 × 情感 × 信任权重，限制在 ±25% 内。"""
        raw = agg["heat_index"] * max(agg["sentiment_score"], 0) * agg["trust_weight"]
        return round(1.0 + min(max(raw * 0.35, -0.25), 0.25), 4)
