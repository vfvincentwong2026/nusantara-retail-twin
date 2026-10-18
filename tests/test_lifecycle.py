"""Phase 6 生命周期管理测试。"""

from __future__ import annotations

import unittest
from datetime import date, timedelta

from nrt.calendar import IndonesiaCalendar
from nrt.lifecycle import LifecycleManager, fefo_allocate
from nrt.model import SKU, StoreProfile, StoreFormat, IslandRegion, ABCClass


def make_store() -> StoreProfile:
    return StoreProfile(
        store_id="st-test-001", store_name="T", store_size_sqm=2000,
        store_format=StoreFormat.supermarket, island_region=IslandRegion.java, city="Jakarta",
        target_sku_count=100,
    )


def make_sku(cat="蔬菜", fresh=True, halal=True, shelf_life=5):
    return SKU(
        sku_id="sku-t", sku_code="SKU-T", sku_name="Test", category_name=cat,
        brand="B", unit_price=5000, unit_cost=4000, shelf_life_days=shelf_life,
        fresh_flag=fresh, halal_certified=halal, abc_class=ABCClass.A,
    )


def batch(expiry_offset: int, qty: int = 10) -> dict:
    today = date(2026, 3, 1)
    return {
        "batch_id": f"b-{expiry_offset}", "sku_id": "sku-t", "sku_code": "SKU-T",
        "quantity": qty,
        "received_date": (today - timedelta(days=3)).isoformat(),
        "expiry_date": (today + timedelta(days=expiry_offset)).isoformat(),
        "facing_id": None,
    }


class TestLifecycle(unittest.TestCase):
    def setUp(self):
        self.mgr = LifecycleManager(make_store(), calendar=IndonesiaCalendar(year=2026))
        self.today = date(2026, 3, 1)

    def test_expires_in_2_days_bundles(self):
        a = self.mgr.evaluate(make_sku(halal=False), batch(2), self.today)
        self.assertEqual(a["action"], "BUNDLE_PROMOTION")
        self.assertEqual(a["reason"], "expires_in_2_days")
        self.assertIsNotNone(a["bundle_with_category"])

    def test_halal_bundle_priority(self):
        a = self.mgr.evaluate(make_sku(halal=True), batch(1), self.today)
        self.assertIn("halal", a["reason"])
        self.assertIn(a["bundle_with_category"], ("大米", "食用油"))

    def test_expires_in_5_days_markdown(self):
        a = self.mgr.evaluate(make_sku(), batch(5), self.today)
        self.assertEqual(a["action"], "MARKDOWN")
        self.assertEqual(a["suggested_discount_pct"], 15)

    def test_fresh_ok_holds(self):
        a = self.mgr.evaluate(make_sku(), batch(20), self.today)
        self.assertEqual(a["action"], "HOLD")

    def test_ramadan_gift_stair_discount(self):
        """斋月前 4 周（2026-01-22）礼品装应触发阶梯折扣，且临期动作优先。"""
        sku = make_sku(cat="穆斯林服饰", fresh=False, shelf_life=1095)
        a = self.mgr.evaluate(sku, batch(300), date(2026, 1, 22), in_ramadan_pre=True)
        self.assertEqual(a["action"], "MARKDOWN")
        self.assertEqual(a["promotion_trigger"], "ramadan_stair_discount")
        self.assertGreaterEqual(a["suggested_discount_pct"], 10)
        self.assertLessEqual(a["suggested_discount_pct"], 30)

    def test_fefo_allocate(self):
        batches = [batch(10, 5), batch(2, 8), batch(5, 6)]
        alloc = fefo_allocate(batches, 10)
        self.assertEqual(alloc[0]["batch_id"], "b-2")  # 最先到期先出
        self.assertEqual(sum(x["quantity"] for x in alloc), 10)

    def test_run_summary(self):
        skus = [make_sku(), make_sku(cat="水果")]
        result = self.mgr.run(skus, today=self.today, seed=1)
        self.assertIn("summary", result)
        self.assertEqual(result["summary"]["checked"], result["batches_checked"])


if __name__ == "__main__":
    unittest.main()
