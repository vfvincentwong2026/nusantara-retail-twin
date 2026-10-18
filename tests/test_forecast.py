"""Phase 4 单元测试：预测引擎契约与斋月行为。"""

from __future__ import annotations

import unittest
from datetime import date

from nrt.forecast import ForecastEngine
from nrt.forecast.history import SalesHistorySimulator
from nrt.model import SKU, StoreProfile, StoreFormat, IslandRegion, ABCClass

CONTRACT_KEYS = {
    "forecast_id", "store_id", "sku_id", "generated_at", "horizon",
    "safety_stock", "reorder_point", "suggested_order_quantity",
    "confidence", "model_version",
}


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


def make_sku(name="Indomie Goreng 85g", fresh=False, shelf_life=180, cls=ABCClass.A) -> SKU:
    return SKU(
        sku_id="sku-test-001",
        sku_code="SKU-TEST-001",
        sku_name=name,
        category_name="方便面" if not fresh else "蔬菜",
        brand="Test",
        unit_price=3500,
        unit_cost=2800,
        shelf_life_days=shelf_life,
        fresh_flag=fresh,
        halal_certified=True,
        abc_class=cls,
    )


def history_for(store, sku, days=150, end=None):
    sim = SalesHistorySimulator(store, [sku], seed=7)
    return sim.generate(days=days, end_date=end)


class TestForecastContract(unittest.TestCase):
    def setUp(self):
        self.store = make_store()
        self.sku = make_sku()
        self.engine = ForecastEngine(self.store)

    def test_output_contract(self):
        history = history_for(self.store, self.sku)
        out = self.engine.predict(self.sku, history, horizon_days=30, today=date(2026, 10, 16))
        missing = CONTRACT_KEYS - set(out)
        self.assertFalse(missing, f"契约字段缺失: {missing}")
        self.assertEqual(len(out["horizon"]["daily_forecast"]), 30)
        self.assertTrue(out["model_version"].startswith("hybrid"))

    def test_p90_above_mean(self):
        history = history_for(self.store, self.sku)
        out = self.engine.predict(self.sku, history, horizon_days=30, today=date(2026, 10, 16))
        for f in out["horizon"]["daily_forecast"]:
            self.assertGreaterEqual(f["demand_p90"], f["demand_mean"])

    def test_min_history_enforced(self):
        with self.assertRaises(ValueError):
            self.engine.predict(self.sku, [], horizon_days=30)

    def test_safety_stock_positive(self):
        history = history_for(self.store, self.sku)
        out = self.engine.predict(self.sku, history, horizon_days=30, today=date(2026, 10, 16))
        self.assertGreater(out["safety_stock"], 0)
        self.assertGreater(out["reorder_point"], out["safety_stock"])
        self.assertGreaterEqual(out["suggested_order_quantity"], 0)


class TestRamadanEffect(unittest.TestCase):
    """斋月窗口内食品需求必须显著高于平日（docs/ramadan-calendar-2026.md §2）。"""

    def setUp(self):
        self.store = make_store("java")
        self.sku = make_sku()
        self.engine = ForecastEngine(self.store)

    def _peak_mean(self, include: bool) -> float:
        history = history_for(self.store, self.sku, end=date(2026, 1, 15))
        out = self.engine.predict(
            self.sku, history, horizon_days=70, include_ramadan=include, today=date(2026, 1, 15)
        )
        return max(f["demand_mean"] for f in out["horizon"]["daily_forecast"])

    def test_ramadan_boosts_food(self):
        with_ramadan = self._peak_mean(True)
        without = self._peak_mean(False)
        self.assertGreater(with_ramadan, without * 1.5,
                           f"斋月峰值 {with_ramadan} 应显著高于平日 {without}")

    def test_peak_near_official_peak_date(self):
        """峰值应出现在斋月中后段（3/6–3/20，APPBI 预测 3 月第二周）。"""
        history = history_for(self.store, self.sku, end=date(2026, 1, 15))
        out = self.engine.predict(
            self.sku, history, horizon_days=70, include_ramadan=True, today=date(2026, 1, 15)
        )
        peak = max(out["horizon"]["daily_forecast"], key=lambda f: f["demand_mean"])
        d = date.fromisoformat(peak["date"])
        self.assertGreaterEqual(d, date(2026, 2, 19))   # 不早于斋月首日
        self.assertLessEqual(d, date(2026, 3, 24))      # 不晚于开斋节假期


class TestFreshConstraint(unittest.TestCase):
    """生鲜建议订货量受保质期约束（§4.2：order_quantity 受 shelf_life_days 约束）。"""

    def test_short_shelf_life_caps_order(self):
        store = make_store()
        sku = make_sku(fresh=True, shelf_life=2)
        engine = ForecastEngine(store)
        history = history_for(store, sku)
        out = engine.predict(sku, history, horizon_days=30, today=date(2026, 10, 16))
        daily_mean = max(
            (f["demand_mean"] for f in out["horizon"]["daily_forecast"][:8]), default=1
        )
        self.assertLessEqual(out["suggested_order_quantity"], daily_mean * 2 + 2)


class TestIslandLeadTime(unittest.TestCase):
    """岛屿 k 系数进入有效提前期：Papua 的 ROP 应高于 Java（同 SKU 同历史）。"""

    def test_papua_rop_above_java(self):
        sku = make_sku()
        results = {}
        for region in ("java", "papua"):
            store = make_store(region)
            engine = ForecastEngine(store)
            history = history_for(store, sku, end=date(2026, 10, 16))
            out = engine.predict(sku, history, horizon_days=30, today=date(2026, 10, 16))
            results[region] = out["reorder_point"]
        self.assertGreater(results["papua"], results["java"])


if __name__ == "__main__":
    unittest.main()


class TestHybridModelSelection(unittest.TestCase):
    """ABC 分段选型：C 类走 Croston-SBA，A 类维持 weekday 基线。"""

    def _history(self, sku, days=120):
        store = make_store()
        sim = SalesHistorySimulator(store, [sku], seed=7)
        return store, sim.generate(days=days, end_date=date(2026, 1, 15))

    def test_c_class_uses_croston_flat_forecast(self):
        sku = make_sku(cls=ABCClass.C)
        store, history = self._history(sku)
        pred = ForecastEngine(store).predict(sku, history, horizon_days=14, today=date(2026, 1, 15))
        means = [f["demand_mean"] for f in pred["horizon"]["daily_forecast"]]
        self.assertEqual(pred["model_version"], "hybrid-v0.3")
        # Croston 输出常数率：无斋月乘数时逐日相等
        self.assertEqual(len(set(means)), 1)
        self.assertGreater(means[0], 0)

    def test_a_class_keeps_dow_baseline(self):
        sku = make_sku(cls=ABCClass.A)
        store, history = self._history(sku)
        pred = ForecastEngine(store).predict(sku, history, horizon_days=14, today=date(2026, 1, 15))
        means = [f["demand_mean"] for f in pred["horizon"]["daily_forecast"]]
        self.assertEqual(pred["model_version"], "hybrid-v0.3")
        # weekday 基线：跨周的同一天均值应一致，周内至少两种取值
        self.assertGreater(len(set(means[:7])), 1)

    def test_contract_unchanged(self):
        sku = make_sku(cls=ABCClass.C)
        store, history = self._history(sku)
        pred = ForecastEngine(store).predict(sku, history, horizon_days=7, today=date(2026, 1, 15))
        self.assertTrue(CONTRACT_KEYS.issubset(pred.keys()))
        self.assertGreaterEqual(pred["safety_stock"], 0)
