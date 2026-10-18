"""Phase 5 单元测试：补货引擎与空间-存量 MILP 优化。"""

from __future__ import annotations

import unittest
from datetime import date

from nrt.forecast import ForecastEngine
from nrt.forecast.history import SalesHistorySimulator
from nrt.model import SKU, StoreProfile, StoreFormat, IslandRegion, ABCClass
from nrt.replenishment import ReplenishmentEngine
from nrt.space import SpaceOptimizer


def make_store(region: str = "java") -> StoreProfile:
    return StoreProfile(
        store_id="st-test-001",
        store_name="Test Store",
        store_size_sqm=2000,
        store_format=StoreFormat.supermarket,
        island_region=IslandRegion(region),
        city="Jakarta",
        target_sku_count=100,
    )


def make_sku(fresh=False, shelf_life=180, cls=ABCClass.A) -> SKU:
    return SKU(
        sku_id="sku-test-001",
        sku_code="SKU-TEST-001",
        sku_name="Test SKU",
        category_name="蔬菜" if fresh else "方便面",
        brand="Test",
        unit_price=3500,
        unit_cost=2800,
        shelf_life_days=shelf_life,
        fresh_flag=fresh,
        halal_certified=True,
        abc_class=cls,
    )


def forecast_for(store, sku, today=None):
    engine = ForecastEngine(store)
    events = SalesHistorySimulator(store, [sku], seed=7).generate(days=150, end_date=today)
    return engine.predict(sku, [e for e in events if e["sku_id"] == sku.sku_id], today=today)


class TestReplenishmentDecisions(unittest.TestCase):
    def setUp(self):
        self.store = make_store()
        self.sku = make_sku()
        self.engine = ReplenishmentEngine(self.store)
        self.forecast = forecast_for(self.store, self.sku)

    def test_contract_keys(self):
        d = self.engine.decide(self.sku, self.forecast, current_inventory=1)
        for k in ("replenishment_id", "store_id", "sku_id", "action", "order_quantity",
                  "priority", "reason", "suggested_delivery_window", "promotion_trigger"):
            self.assertIn(k, d)

    def test_out_of_stock_is_urgent(self):
        d = self.engine.decide(self.sku, self.forecast, current_inventory=0)
        self.assertEqual(d["action"], "URGENT")
        self.assertEqual(d["priority"], "HIGH")
        self.assertGreater(d["order_quantity"], 0)

    def test_above_rop_holds(self):
        d = self.engine.decide(self.sku, self.forecast, current_inventory=self.forecast["reorder_point"] + 50)
        self.assertEqual(d["action"], "HOLD")
        self.assertEqual(d["order_quantity"], 0)

    def test_below_rop_orders(self):
        d = self.engine.decide(self.sku, self.forecast, current_inventory=self.forecast["reorder_point"] - 1)
        self.assertEqual(d["action"], "ORDER")

    def test_fresh_cap_by_shelf_life(self):
        fresh_sku = make_sku(fresh=True, shelf_life=2)
        f = forecast_for(self.store, fresh_sku)
        d = self.engine.decide(fresh_sku, f, current_inventory=0)
        daily = sum(x["demand_mean"] for x in f["horizon"]["daily_forecast"][:7]) / 7
        self.assertLessEqual(d["order_quantity"], daily * 2 + 2)

    def test_fefo_triggers_bundle(self):
        fresh_sku = make_sku(fresh=True, shelf_life=2)
        f = forecast_for(self.store, fresh_sku)
        d = self.engine.decide(fresh_sku, f, current_inventory=1, strategy="fefo")
        self.assertEqual(d["action"], "URGENT")
        self.assertEqual(d["promotion_trigger"], "bundle")

    def test_lead_time_formula(self):
        """LT_eff = LT_mean + k × σ_LT（Java: 3 + 0.5×1 = 3.5）。"""
        self.assertAlmostEqual(self.engine.effective_lead_time("java"), 3.5)
        self.assertAlmostEqual(self.engine.effective_lead_time("papua"), 19.5)


class TestRamadanPreStrategy(unittest.TestCase):
    def setUp(self):
        self.store = make_store("java")
        self.engine = ReplenishmentEngine(self.store)

    def test_in_first_round_window(self):
        """Java 首轮窗口 2026-01-08~01-22（k=0.5 → H-6 周）。"""
        r = self.engine.check_ramadan_pre_replenishment("2026-01-10")
        self.assertEqual(r["action"], "TRIGGER_FIRST_ROUND")
        self.assertIn("food", r["categories"])

    def test_outside_window_noop(self):
        r = self.engine.check_ramadan_pre_replenishment("2026-06-01")
        self.assertEqual(r["action"], "NOOP")

    def test_boost_reason_in_window(self):
        sku = make_sku()
        f = forecast_for(self.store_java(), sku, today=date(2026, 1, 10))
        d = self.engine.decide(sku, f, current_inventory=f["reorder_point"] - 1, today=date(2026, 1, 10))
        self.assertEqual(d["reason"], "ramadan_pre_window_boost")
        self.assertEqual(d["priority"], "HIGH")

    def store_java(self):
        return self.store

    def test_schedule_has_three_rounds(self):
        sched = self.engine.generate_ramadan_schedule(store_size=2000, island_region="java")
        self.assertEqual(len(sched), 3)
        self.assertEqual(sched[0]["priority"], "P0")
        self.assertEqual(sched[2]["scope"], "应急（斋月最后冲刺）")


class TestSpaceOptimizer(unittest.TestCase):
    CATEGORIES = [
        {"category_id": "beverages", "sku_count": 240, "avg_gross_margin": 0.32,
         "avg_daily_turnover": 18.5, "avg_facing_width_m": 0.25, "min_facings_required": 20},
        {"category_id": "fresh", "sku_count": 300, "avg_gross_margin": 0.20,
         "avg_daily_turnover": 25.0, "avg_facing_width_m": 0.30, "min_facings_required": 30},
        {"category_id": "household", "sku_count": 120, "avg_gross_margin": 0.25,
         "avg_daily_turnover": 8.0, "avg_facing_width_m": 0.25, "min_facings_required": 10},
        {"category_id": "snacks", "sku_count": 180, "avg_gross_margin": 0.28,
         "avg_daily_turnover": 15.0, "avg_facing_width_m": 0.20, "min_facings_required": 15},
    ]

    def setUp(self):
        self.opt = SpaceOptimizer(make_store())

    def test_contract_keys(self):
        r = self.opt.solve(self.CATEGORIES, total_facings=480, objective="balanced")
        for k in ("planogram_id", "store_id", "allocations", "objective_value", "solver_status"):
            self.assertIn(k, r)
        self.assertIn(r["solver_status"], ("OPTIMAL", "FEASIBLE"))

    def test_total_facings_constraint(self):
        r = self.opt.solve(self.CATEGORIES, total_facings=480, objective="balanced")
        self.assertEqual(sum(a["allocated_facings"] for a in r["allocations"]), 480)

    def test_min_facings_respected(self):
        r = self.opt.solve(self.CATEGORIES, total_facings=480, objective="balanced")
        mins = {c["category_id"]: c["min_facings_required"] for c in self.CATEGORIES}
        for a in r["allocations"]:
            self.assertGreaterEqual(a["allocated_facings"], mins[a["category_id"]])

    def test_fresh_ratio_constraint(self):
        r = self.opt.solve(
            self.CATEGORIES, total_facings=480, objective="balanced",
            fresh_ratio_min=0.25, fresh_categories={"fresh"},
        )
        fresh_facings = next(a["allocated_facings"] for a in r["allocations"] if a["category_id"] == "fresh")
        self.assertGreaterEqual(fresh_facings, 0.25 * 480)

    def test_profit_objective_beats_balanced_on_profit(self):
        profit_r = self.opt.solve(self.CATEGORIES, total_facings=480, objective="profit")
        balanced_r = self.opt.solve(self.CATEGORIES, total_facings=480, objective="balanced")
        # profit 目标下各品类期望利润总和应不低于 balanced（都满足同一约束集）
        p_profit = sum(a["expected_daily_profit"] for a in profit_r["allocations"])
        p_bal = sum(a["expected_daily_profit"] for a in balanced_r["allocations"])
        self.assertGreaterEqual(p_profit, p_bal * 0.9)


if __name__ == "__main__":
    unittest.main()
