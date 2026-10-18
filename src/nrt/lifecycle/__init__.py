"""生命周期管理（Phase 6）。

对应 docs/architecture.md §4.4 契约：
- 剩余保质期 ≤ 2 天 → BUNDLE_PROMOTION（捆绑促销，非纯降价）
- 剩余保质期 ≤ 5 天 → MARKDOWN（折价出清）
- 斋月前 4 周 → 礼品装 SKU 阶梯折扣（10–15% → 25–30%）
- 清真认证 SKU 优先跨品类捆绑（信任传递）
- 批次出库遵循 FEFO（先到期先出）
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Optional

from nrt.model import SKU, StoreProfile

# 斋月礼品相关品类（ramadan-calendar-2026.md §4.2 节庆品）
GIFT_CATEGORIES = {"穆斯林服饰", "饼干", "零食", "咖啡", "茶"}
# 常见捆绑搭配（临期品类 → 搭档品类）
BUNDLE_PARTNER = {
    "蔬菜": "鲜肉", "水果": "乳制品", "鲜肉": "蔬菜", "海鲜": "蔬菜",
    "乳制品": "饼干", "鸡蛋": "方便面",
}


class LifecycleManager:
    def __init__(self, store: StoreProfile, calendar=None):
        self.store = store
        self.cal = calendar

    # ------------------------------------------------------------------
    def simulate_batches(
        self,
        sku: SKU,
        today: date,
        rng,
        batches_per_sku: int = 2,
    ) -> list[dict]:
        """为 SKU 生成合成库存批次（真实 WMS 接入前，Phase 8）。"""
        if not sku.shelf_life_days:
            return []
        batches = []
        for i in range(batches_per_sku):
            age = rng.randint(0, sku.shelf_life_days)
            expiry = today.toordinal() + (sku.shelf_life_days - age)
            batches.append(
                {
                    "batch_id": str(uuid.uuid4()),
                    "sku_id": sku.sku_id,
                    "sku_code": sku.sku_code,
                    "quantity": rng.randint(4, 48),
                    "received_date": date.fromordinal(max(today.toordinal() - age, 1)).isoformat(),
                    "expiry_date": date.fromordinal(expiry).isoformat(),
                    "facing_id": None,
                }
            )
        return batches

    def evaluate(self, sku: SKU, batch: dict, today: date, in_ramadan_pre: bool = False) -> dict:
        """单批次动作判定（§4.4 输出契约）。"""
        expiry = date.fromisoformat(batch["expiry_date"])
        remaining = (expiry - today).days
        action, reason, discount, partner = "HOLD", "shelf_life_ok", 0, None

        if remaining <= 2:
            action = "BUNDLE_PROMOTION"
            reason = "expires_in_2_days"
            partner = BUNDLE_PARTNER.get(sku.category_name, "零食")
            # 清真 SKU：优先跨品类捆绑（信任传递），搭档换高信任品类
            if sku.halal_certified:
                partner = "大米" if sku.category_name != "大米" else "食用油"
                reason = "expires_in_2_days_halal_bundle"
        elif remaining <= 5:
            action = "MARKDOWN"
            reason = "expires_in_5_days"
            discount = 15

        # 斋月前 4 周礼品装阶梯折扣（不与临期动作冲突）
        promotion_trigger = None
        if in_ramadan_pre and sku.category_name in GIFT_CATEGORIES and action == "HOLD":
            action = "MARKDOWN"
            reason = "ramadan_gift_stair_discount"
            weeks_to_ramadan = max(0, (self.cal.ramadan_start - today).days // 7)
            discount = 10 + max(0, 4 - weeks_to_ramadan) * 5  # 4 周前 10%，逐周 +5% 至 30%
            discount = min(discount, 30)
            promotion_trigger = "ramadan_stair_discount"

        return {
            "batch_id": batch["batch_id"],
            "sku_id": sku.sku_id,
            "sku_code": sku.sku_code,
            "sku_name": sku.sku_name,
            "action": action,
            "reason": reason,
            "remaining_shelf_life_days": remaining,
            "suggested_discount_pct": discount if action != "HOLD" else None,
            "bundle_with_category": partner,
            "promotion_trigger": promotion_trigger,
        }

    # ------------------------------------------------------------------
    def run(
        self,
        skus: list[SKU],
        today: Optional[date] = None,
        seed: int = 42,
        batches_per_sku: int = 2,
    ) -> dict:
        import random

        today = today or date.today()
        rng = random.Random(seed)
        in_ramadan_pre = False
        if self.cal:
            for w in self.cal.pre_replenishment_windows(self.store.island_region.value):
                if date.fromisoformat(w["start"]) <= today <= date.fromisoformat(w["end"]):
                    in_ramadan_pre = True

        sku_by_id = {s.sku_id: s for s in skus}
        actions = []
        batches_all = []
        for sku in skus:
            batches = self.simulate_batches(sku, today, rng, batches_per_sku)
            batches_all.extend(batches)
            # FEFO：按到期日排序，先到期先出（评估顺序即出库优先级）
            for b in sorted(batches, key=lambda x: x["expiry_date"]):
                actions.append(self.evaluate(sku, b, today, in_ramadan_pre))

        active = [a for a in actions if a["action"] != "HOLD"]
        return {
            "store_id": self.store.store_id,
            "date": today.isoformat(),
            "batches_checked": len(batches_all),
            "fefo_order": "expiry_date asc",
            "actions": actions,
            "summary": {
                "checked": len(actions),
                "bundle_promotions": sum(1 for a in active if a["action"] == "BUNDLE_PROMOTION"),
                "markdowns": sum(1 for a in active if a["action"] == "MARKDOWN"),
                "halal_bundles": sum(1 for a in active if "halal" in a["reason"]),
                "ramadan_stair": sum(1 for a in active if a["promotion_trigger"] == "ramadan_stair_discount"),
            },
        }


def fefo_allocate(batches: list[dict], quantity: int) -> list[dict]:
    """FEFO 出库分配：先到期先出，返回 [{batch_id, quantity}]。"""
    result = []
    remaining = quantity
    for b in sorted(batches, key=lambda x: x["expiry_date"]):
        if remaining <= 0:
            break
        take = min(b["quantity"], remaining)
        if take > 0:
            result.append({"batch_id": b["batch_id"], "quantity": take})
            remaining -= take
    return result
