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
    # Phase 3-6：按契约预留（子包实现后解除 NotImplementedError）
    # ------------------------------------------------------------------
    def forecast(self, horizon_days: int = 30, include_ramadan: bool = False):
        from nrt.forecast import ForecastEngine

        return ForecastEngine(self.store).predict(
            horizon_days=horizon_days, include_ramadan=include_ramadan
        )

    def replenish(self, strategy: str = "auto"):
        from nrt.replenishment import ReplenishmentEngine

        return ReplenishmentEngine(self.store).run(strategy=strategy)

    def optimize_space(self, objective: str = "balanced"):
        from nrt.space import SpaceOptimizer

        return SpaceOptimizer(self.store).solve(objective=objective)
