"""补货引擎（Phase 5，接口已预留）。

契约见 docs/architecture.md §4.2：有效提前期 LT_eff = LT_mean + k × σ_LT，
k 由岛屿区域决定（Java 0.5 / Sumatra·Kalimantan 1.0 / Sulawesi·Papua 1.5）；
生鲜 SKU 订货量受 shelf_life_days 约束；斋月前 6–8 周自动提升节庆品类优先级。
"""

from __future__ import annotations


class ReplenishmentEngine:
    def __init__(self, store):
        self.store = store

    def run(self, strategy: str = "auto"):
        raise NotImplementedError(
            "ReplenishmentEngine 属 Phase 5（契约：docs/architecture.md §4.2）"
        )

    def check_ramadan_pre_replenishment(self, today: str, store_size: int, island_region: str):
        raise NotImplementedError("ReplenishmentEngine 属 Phase 5")

    def generate_ramadan_schedule(self, store_size: int, island_region: str, year: int):
        raise NotImplementedError("ReplenishmentEngine 属 Phase 5")
