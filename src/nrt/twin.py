"""RetailTwin — 面向业务编排的入口门面。

README 快速开始中的用法：

    store = StoreProfile(...)
    twin = RetailTwin(store)
    twin.load_planogram()
    twin.forecast(horizon_days=30, include_ramadan=True)
    twin.replenish()
    twin.render_3d()

Phase 2 实现 load_planogram / 种子加载；预测、补货、优化、
渲染在对应子包实现后自动可用（方法已按 docs/architecture.md 契约预留）。
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Optional, Union

from nrt.model import StoreProfile, StoreSeed


class RetailTwin:
    def __init__(self, store: StoreProfile):
        self.store = store
        self.seed: Optional[StoreSeed] = None

    @classmethod
    def from_seed_file(cls, path: Union[str, Path]) -> "RetailTwin":
        """从种子文件直接构造（从 store_profile 恢复门店档案）。"""
        twin = cls.__new__(cls)
        twin.seed = None
        twin.load_seed(path)
        twin.store = twin.seed.store_profile
        return twin

    # ------------------------------------------------------------------
    # Phase 2：数据加载
    # ------------------------------------------------------------------
    def load_seed(self, path: Union[str, Path]) -> StoreSeed:
        """从 JSON 文件加载种子文档（全量或样例均可）。"""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        self.seed = StoreSeed.model_validate(data)
        return self.seed

    def load_planogram(self, path: Optional[Union[str, Path]] = None) -> StoreSeed:
        """加载货架图。未指定路径时按门店规模推断默认种子文件。

        对应架构文档「单一数据源」原则：2D 平面图与 3D 场景
        共享同一份种子文档。
        """
        if path is None:
            size = self.store.store_size_sqm
            path = Path(__file__).resolve().parents[3] / "data" / "seeds" / f"store_{size}sqm_full.json"
        return self.load_seed(path)

    # ------------------------------------------------------------------
    # Phase 4：需求预测
    # ------------------------------------------------------------------
    def forecast(
        self,
        horizon_days: int = 30,
        include_ramadan: bool = False,
        sku_count: int = 10,
        history_days: int = 150,
    ) -> list[dict]:
        """对种子目录中的前 N 个 SKU 运行基线预测引擎。

        返回严格遵循 docs/architecture.md §4.1 输出契约的 DemandForecast 列表。
        历史销售由 SalesHistorySimulator 合成，接入真实 POS 后替换数据源即可。
        """
        if self.seed is None or not self.seed.skus:
            raise RuntimeError("请先 load_planogram() / load_seed() 加载含 SKU 目录的种子")
        from nrt.forecast import ForecastEngine
        from nrt.forecast.history import SalesHistorySimulator

        targets = [s for s in self.seed.skus if s.abc_class and s.abc_class.value == "A"][:sku_count]
        engine = ForecastEngine(self.store)
        sim = SalesHistorySimulator(self.store, targets, seed=42)
        events = sim.generate(days=history_days)
        return [
            engine.predict(s, [e for e in events if e["sku_id"] == s.sku_id],
                           horizon_days=horizon_days, include_ramadan=include_ramadan)
            for s in targets
        ]

    def replenish(
        self,
        strategy: str = "auto",
        sku_count: int = 10,
        today: Optional[date] = None,
        seed: int = 42,
    ) -> dict:
        """预测 → 库存快照 → 补货决策的全链路编排。"""
        import random as _random

        if self.seed is None or not self.seed.skus:
            raise RuntimeError("请先 load_planogram() / load_seed() 加载含 SKU 目录的种子")
        from nrt.forecast import ForecastEngine
        from nrt.forecast.history import SalesHistorySimulator
        from nrt.replenishment import ReplenishmentEngine

        targets = [s for s in self.seed.skus if s.abc_class and s.abc_class.value == "A"][:sku_count]
        engine = ForecastEngine(self.store)
        events = SalesHistorySimulator(self.store, targets, seed=seed).generate(days=150, end_date=today)
        forecasts = {
            s.sku_id: engine.predict(
                s, [e for e in events if e["sku_id"] == s.sku_id],
                horizon_days=30, include_ramadan=True, today=today,
            )
            for s in targets
        }
        rng = _random.Random(seed)
        inventory = {
            s.sku_id: round(forecasts[s.sku_id]["reorder_point"] * rng.uniform(0.0, 1.3))
            for s in targets
        }
        return ReplenishmentEngine(self.store).run(targets, forecasts, inventory, strategy=strategy, today=today)

    def optimize_space(self, objective: str = "balanced") -> dict:
        """品类 → 面位 MILP 优化（需先加载种子）。"""
        if self.seed is None or not self.seed.skus:
            raise RuntimeError("请先 load_planogram() / load_seed() 加载含 SKU 目录的种子")
        from nrt.space import SpaceOptimizer

        abc_turnover = {"A": 12.0, "B": 6.0, "C": 2.5}
        cats: dict[str, dict] = {}
        for s in self.seed.skus:
            c = cats.setdefault(s.category_name, {"margins": [], "turnovers": [], "n": 0, "fresh": s.fresh_flag})
            c["n"] += 1
            c["margins"].append(s.gross_margin or 0.2)
            c["turnovers"].append(abc_turnover[s.abc_class.value if s.abc_class else "C"])
        categories = [
            {
                "category_id": name,
                "sku_count": c["n"],
                "avg_gross_margin": sum(c["margins"]) / len(c["margins"]),
                "avg_daily_turnover": sum(c["turnovers"]) / len(c["turnovers"]),
                "avg_facing_width_m": 0.2,
                "min_facings_required": max(6, round(c["n"] * 0.01)),
            }
            for name, c in cats.items()
        ]
        return SpaceOptimizer(self.store).solve(
            categories,
            total_facings=self.seed.generation_summary.facings_count,
            fresh_ratio_min=self.store.fresh_ratio or 0.0,
            fresh_categories={n for n, c in cats.items() if c["fresh"]},
            objective=objective,
        )
