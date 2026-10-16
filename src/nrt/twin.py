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

    def replenish(self, strategy: str = "auto"):
        from nrt.replenishment import ReplenishmentEngine

        return ReplenishmentEngine(self.store).run(strategy=strategy)

    def optimize_space(self, objective: str = "balanced"):
        from nrt.space import SpaceOptimizer

        return SpaceOptimizer(self.store).solve(objective=objective)
