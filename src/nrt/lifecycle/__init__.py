"""生命周期管理（Phase 6，接口已预留）。

契约见 docs/architecture.md §4.4：FEFO 批次分配、临期触发捆绑促销
（剩余保质期 ≤ 2 天）、斋月前 4 周礼品装阶梯折扣（10–15% → 25–30%）、
清真认证 SKU 优先跨品类捆绑。
"""

from __future__ import annotations


class LifecycleManager:
    def __init__(self, store):
        self.store = store

    def run(self):
        raise NotImplementedError(
            "LifecycleManager 属 Phase 6（契约：docs/architecture.md §4.4）"
        )
