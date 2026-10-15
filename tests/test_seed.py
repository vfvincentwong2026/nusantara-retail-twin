"""Phase 2 单元测试：种子生成器、日历模块、数据模型。

运行：python -m unittest discover -s tests -v
"""

from __future__ import annotations

import unittest

from nrt.calendar import IndonesiaCalendar, ISLAND_LOGISTICS
from nrt.model import StoreSeed
from nrt.seed import SeedGenerator
from nrt.seed.catalog import SCALE_PARAMS


class TestSeedGenerator(unittest.TestCase):
    def setUp(self):
        # 用小规模参数加速测试（结构相同，数量级不同）
        self.gen = SeedGenerator(store_size=500, region="java", seed=42, sku_count=500)

    def test_generate_structure(self):
        doc = self.gen.generate()
        for key in ("meta", "store_profile", "zones", "fixtures", "shelf_levels",
                    "facings", "skus", "ramadan_calendar_2026", "generation_summary"):
            self.assertIn(key, doc)

    def test_facing_formula(self):
        """Facings 总数 = fixtures × layers × 6。"""
        doc = self.gen.generate()
        p = SCALE_PARAMS[500]
        self.assertEqual(len(doc["facings"]), p["fixtures"] * p["layers"] * 6)

    def test_facing_sku_references(self):
        doc = self.gen.generate()
        sku_codes = {s["sku_code"] for s in doc["skus"]}
        for fc in doc["facings"]:
            self.assertIn(fc["sku_code"], sku_codes)

    def test_spatial_references(self):
        doc = self.gen.generate()
        zone_ids = {z["zone_id"] for z in doc["zones"]}
        fixture_ids = {f["fixture_id"] for f in doc["fixtures"]}
        level_ids = {lv["shelf_level_id"] for lv in doc["shelf_levels"]}
        for f in doc["fixtures"]:
            self.assertIn(f["zone_id"], zone_ids)
        for lv in doc["shelf_levels"]:
            self.assertIn(lv["fixture_id"], fixture_ids)
        for fc in doc["facings"]:
            self.assertIn(fc["shelf_level_id"], level_ids)

    def test_reproducible(self):
        a = SeedGenerator(500, "java", 42, sku_count=500).generate()
        b = SeedGenerator(500, "java", 42, sku_count=500).generate()
        a["meta"]["generated_at"] = b["meta"]["generated_at"] = ""
        self.assertEqual(a, b)

    def test_seed_document_validates(self):
        doc = self.gen.generate()
        StoreSeed.model_validate(doc)


class TestScaleParams(unittest.TestCase):
    def test_targets_match_data_model_doc(self):
        """docs/data-model.md §7 的规模承诺。"""
        self.assertEqual(SCALE_PARAMS[500]["target_sku_count"], 5000)
        self.assertEqual(SCALE_PARAMS[2000]["target_sku_count"], 14000)
        self.assertEqual(SCALE_PARAMS[5000]["target_sku_count"], 34000)
        self.assertEqual(SCALE_PARAMS[500]["facings"], 1200)
        self.assertEqual(SCALE_PARAMS[2000]["facings"], 4320)
        self.assertEqual(SCALE_PARAMS[5000]["facings"], 10920)

    def test_facings_formula_holds_for_all_scales(self):
        for size, p in SCALE_PARAMS.items():
            self.assertEqual(p["facings"], p["fixtures"] * p["layers"] * 6, size)


class TestCalendar(unittest.TestCase):
    def setUp(self):
        self.cal = IndonesiaCalendar(year=2026)

    def test_official_dates(self):
        """政府官方日期：斋月 2/19，开斋节 3/21（docs/ramadan-calendar-2026.md §1）。"""
        self.assertEqual(self.cal.ramadan_start.isoformat(), "2026-02-19")
        self.assertEqual(self.cal.lebaran.isoformat(), "2026-03-21")

    def test_muhammadiyah_offset(self):
        cal = IndonesiaCalendar(year=2026, muhammadiyah_offset=-1)
        self.assertEqual(cal.ramadan_start.isoformat(), "2026-02-18")

    def test_mudik_offsets(self):
        self.assertEqual(self.cal.get_mudik_offset("java"), -7)
        self.assertEqual(self.cal.get_mudik_offset("sumatra"), 7)
        self.assertEqual(self.cal.get_mudik_offset("papua"), 3)

    def test_island_k_factors(self):
        """README：Java k=0.5，Sumatra/Kalimantan k=1.0，Sulawesi/Papua k=1.5。"""
        self.assertEqual(ISLAND_LOGISTICS["java"]["k_factor"], 0.5)
        self.assertEqual(ISLAND_LOGISTICS["sumatra"]["k_factor"], 1.0)
        self.assertEqual(ISLAND_LOGISTICS["papua"]["k_factor"], 1.5)

    def test_demand_multipliers_peak(self):
        mults = self.cal.get_demand_multipliers("java")
        peak = max(m["multiplier"] for m in mults)
        self.assertGreaterEqual(peak, 2.0)
        self.assertEqual(len(mults), 31)  # 2/19 ~ 3/21 含首尾

    def test_replenishment_windows_by_region(self):
        java = self.cal.pre_replenishment_windows("java")
        papua = self.cal.pre_replenishment_windows("papua")
        # k=1.5 的区域首轮更早启动
        self.assertLess(papua[0]["start"], java[0]["start"])


if __name__ == "__main__":
    unittest.main()
