"""补货引擎（Phase 5）。

对应 docs/architecture.md §4.2 契约：
- 有效提前期：LT_eff = LT_mean + k × σ_LT（k 由岛屿区域决定）
- 生鲜 SKU（fresh_flag=true）订货量受 shelf_life_days 约束
- 斋月前 6–8 周自动提升节庆品类补货优先级
- 动作：ORDER / HOLD / URGENT；优先级 HIGH / MEDIUM / LOW

策略（CLI-DESIGN.md §4.6）：
- reorder_point：经典再订货点
- fefo：生鲜批次临期优先（触发捆绑促销而非纯降价，§4.4）
- ramadan_pre：斋月前置补货窗口检查（首轮/次轮，区域差异化）
- auto：综合策略（默认）
"""

from __future__ import annotations

import math
import uuid
from datetime import date, timedelta
from typing import Optional

from nrt.calendar import IndonesiaCalendar, ISLAND_LOGISTICS
from nrt.model import SKU, StoreProfile
from nrt.forecast.history import CATEGORY_KEY

# 斋月前置补货的节庆品类（docs/ramadan-calendar-2026.md §4.2）
RAMADAN_PRE_CATEGORIES = {"food", "beverages", "fashion", "gift", "home_appliance"}

STRATEGIES = ("auto", "reorder_point", "fefo", "ramadan_pre")


class ReplenishmentEngine:
    def __init__(
        self,
        store: StoreProfile,
        calendar: Optional[IndonesiaCalendar] = None,
    ):
        self.store = store
        self.cal = calendar or IndonesiaCalendar(year=2026)

    # ------------------------------------------------------------------
    # 契约工具
    # ------------------------------------------------------------------
    def effective_lead_time(self, island_region: Optional[str] = None) -> float:
        """LT_eff = LT_mean + k × σ_LT。"""
        p = ISLAND_LOGISTICS[island_region or self.store.island_region.value]
        return p["lead_time_mean_days"] + p["k_factor"] * p["lead_time_std_days"]

    def decide(
        self,
        sku: SKU,
        forecast: dict,
        current_inventory: int,
        today: Optional[date] = None,
        strategy: str = "auto",
    ) -> dict:
        """单 SKU 补货决策，输出严格遵循 §4.2 输出契约。"""
        today = today or date.today()
        if strategy not in STRATEGIES:
            raise ValueError(f"未知策略：{strategy}（可选 {STRATEGIES}）")

        rop = forecast["reorder_point"]
        safety = forecast["safety_stock"]
        lt_eff = self.effective_lead_time()
        lt_std = ISLAND_LOGISTICS[self.store.island_region.value]["lead_time_std_days"]

        # ---- 动作判定 ----
        if current_inventory <= 0:
            action, priority, reason = "URGENT", "HIGH", "out_of_stock"
        elif current_inventory < safety:
            action, priority, reason = "URGENT", "HIGH", "stock_below_safety_stock"
        elif current_inventory < rop:
            action = "ORDER"
            reason = "stock_below_reorder_point"
            priority = "MEDIUM"
        else:
            action, priority, reason = "HOLD", "LOW", "stock_above_reorder_point"

        # ---- FEFO：生鲜临期升级（§4.4：临期触发捆绑，非纯降价）----
        promotion_trigger = None
        if sku.fresh_flag and sku.shelf_life_days is not None and action != "HOLD":
            if sku.shelf_life_days <= 3:
                action, priority = "URGENT", "HIGH"
                reason = "fresh_near_expiry_fefo"
                promotion_trigger = "bundle"
            elif strategy in ("fefo", "auto") and sku.shelf_life_days <= 5:
                priority = "HIGH"
                reason = "fresh_short_shelf_life"

        # ---- 斋月前置窗口：节庆品类升级（§4.2 约束 3）----
        if strategy in ("ramadan_pre", "auto") and self._in_ramadan_pre_window(today):
            cat = CATEGORY_KEY.get(sku.category_name)
            if cat in RAMADAN_PRE_CATEGORIES and action != "HOLD":
                priority = "HIGH"
                reason = "ramadan_pre_window_boost"
                promotion_trigger = promotion_trigger or "ramadan_stair_discount"

        # ---- 订货量 ----
        order_qty = 0
        if action in ("ORDER", "URGENT"):
            order_qty = max(forecast["suggested_order_quantity"], rop - current_inventory)
            if sku.fresh_flag and sku.shelf_life_days:
                # 生鲜：不超过 60% 保质期的需求量（§4.2 约束 2）
                daily_mean = _avg_daily(forecast)
                cap = max(2, math.ceil(daily_mean * min(sku.shelf_life_days * 0.6, 10)))
                order_qty = min(order_qty, cap)
            order_qty = max(order_qty, 1)

        window_start = today + timedelta(days=math.ceil(lt_eff - lt_std))
        window_end = today + timedelta(days=math.ceil(lt_eff + lt_std))
        return {
            "replenishment_id": str(uuid.uuid4()),
            "store_id": self.store.store_id,
            "sku_id": sku.sku_id,
            "sku_code": sku.sku_code,
            "action": action,
            "order_quantity": order_qty,
            "priority": priority,
            "reason": reason,
            "current_inventory": current_inventory,
            "reorder_point": rop,
            "safety_stock": safety,
            "suggested_delivery_window": f"{window_start.isoformat()} to {window_end.isoformat()}",
            "promotion_trigger": promotion_trigger,
            "strategy": strategy,
        }

    # ------------------------------------------------------------------
    # 斋月前置补货排程（docs/ramadan-calendar-2026.md §4 + §6.3）
    # ------------------------------------------------------------------
    def _in_ramadan_pre_window(self, today: date) -> bool:
        for w in self.cal.pre_replenishment_windows(self.store.island_region.value):
            if date.fromisoformat(w["start"]) <= today <= date.fromisoformat(w["end"]):
                return True
        return False

    def check_ramadan_pre_replenishment(
        self, today: str, store_size: Optional[int] = None, island_region: Optional[str] = None
    ) -> dict:
        """判断今天是否落在斋月前置补货窗口内。"""
        d = date.fromisoformat(today)
        region = island_region or self.store.island_region.value
        windows = self.cal.pre_replenishment_windows(region)
        for w in windows:
            if date.fromisoformat(w["start"]) <= d <= date.fromisoformat(w["end"]):
                return {
                    "action": "TRIGGER_FIRST_ROUND" if w["round"] == 1 else "TRIGGER_SECOND_ROUND",
                    "window_end": w["end"],
                    "scope": w["scope"],
                    "categories": sorted(RAMADAN_PRE_CATEGORIES),
                    "island_region": region,
                }
        return {
            "action": "NOOP",
            "next_window": windows[0] if d < date.fromisoformat(windows[0]["start"]) else None,
            "categories": [],
            "island_region": region,
        }

    def generate_ramadan_schedule(
        self,
        store_size: Optional[int] = None,
        island_region: Optional[str] = None,
        year: int = 2026,
    ) -> list[dict]:
        """生成斋月补货排程（首轮节庆品 → 次轮生鲜/即时 → 应急窗口）。"""
        region = island_region or self.store.island_region.value
        windows = self.cal.pre_replenishment_windows(region)
        schedule = []
        priority_map = {1: "P0", 2: "P0-P1"}
        categories_map = {
            1: sorted(RAMADAN_PRE_CATEGORIES),
            2: ["fresh", "food", "beverages"],
        }
        for w in windows:
            schedule.append(
                {
                    "round": w["round"],
                    "start": w["start"],
                    "end": w["end"],
                    "priority": priority_map[w["round"]],
                    "scope": w["scope"],
                    "categories": categories_map[w["round"]],
                }
            )
        # 应急窗口：斋月最后 5 天
        emergency_start = self.cal.lebaran - timedelta(days=10)
        schedule.append(
            {
                "round": 3,
                "start": emergency_start.isoformat(),
                "end": (self.cal.lebaran - timedelta(days=1)).isoformat(),
                "priority": "P0",
                "scope": "应急（斋月最后冲刺）",
                "categories": ["food", "gift", "fresh"],
            }
        )
        return schedule

    # ------------------------------------------------------------------
    def run(
        self,
        skus: list[SKU],
        forecasts: dict[str, dict],
        inventory: dict[str, int],
        strategy: str = "auto",
        today: Optional[date] = None,
    ) -> dict:
        """全店补货运行：返回决策列表 + 汇总。"""
        decisions = [
            self.decide(s, forecasts[s.sku_id], inventory.get(s.sku_id, 0), today=today, strategy=strategy)
            for s in skus
        ]
        need = [d for d in decisions if d["action"] in ("ORDER", "URGENT")]
        sku_cost = {s.sku_id: s.unit_cost for s in skus}
        sku_name = {s.sku_id: s.sku_name for s in skus}
        for d in decisions:
            d["sku_name"] = sku_name.get(d["sku_id"], "")
        total_cost = sum(d["order_quantity"] * sku_cost.get(d["sku_id"], 0) for d in need)
        return {
            "store_id": self.store.store_id,
            "strategy": strategy,
            "date": (today or date.today()).isoformat(),
            "decisions": decisions,
            "summary": {
                "checked": len(decisions),
                "need_replenishment": len(need),
                "urgent": sum(1 for d in need if d["action"] == "URGENT"),
                "total_order_quantity": sum(d["order_quantity"] for d in need),
                "estimated_cost_idr": round(total_cost, 2),
            },
        }


def _avg_daily(forecast: dict) -> float:
    days = forecast["horizon"]["daily_forecast"][:7]
    return sum(f["demand_mean"] for f in days) / max(len(days), 1)
