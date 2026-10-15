"""空间-存量优化器（Phase 5，接口已预留）。

契约见 docs/architecture.md §4.3：MILP 求解货架空间分配，
在单位面积利润最大化与缺货风险最小化之间动态权衡。
计划实现：OR-Tools。
"""

from __future__ import annotations


class SpaceOptimizer:
    def __init__(self, store):
        self.store = store

    def solve(self, objective: str = "balanced"):
        raise NotImplementedError(
            "SpaceOptimizer 属 Phase 5：先完成 OR-Tools MILP 实现"
            "（契约：docs/architecture.md §4.3）"
        )
