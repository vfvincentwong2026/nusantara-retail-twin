"""空间价值分析器（Phase 8 · 沃尔玛式货架科学下沉）。

回答店主三问：
1. 哪里最赚钱？—— 分区坪效榜（日毛利 / ㎡）
2. 哪个货架在浪费？—— 面位效率末位榜（单位宽度日毛利 vs 品类均值）
3. 挪一下多赚多少？—— what-if：末位面位换高潜未上架 SKU 的日毛利增量

销量用 ABC 速度代理（A=14/B=5.5/C=1.75 件/日，生鲜 ×1.15），
接入真实 POS 后由 ForecastEngine 替换（architecture.md §4.1 契约）。
"""

from __future__ import annotations

from nrt.model import StoreSeed

ABC_VELOCITY = {"A": 14.0, "B": 5.5, "C": 1.75}
FRESH_BUMP = 1.15


def _polygon_area_m2(polygon) -> float:
    """鞋带公式算多边形面积（㎡），兼容 pydantic Point 对象。"""
    pts = [(p.x, p.y) for p in polygon]
    s = 0.0
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        s += x1 * y2 - x2 * y1
    return abs(s) / 2


class SpaceAnalyzer:
    """从种子文档计算空间价值报告。"""

    def __init__(self, doc: StoreSeed):
        self.doc = doc
        self.sku_by_code = {s.sku_code: s for s in doc.skus}
        self.fixture_zone = {f.fixture_id: f.zone_id for f in doc.fixtures}
        self.level_fixture = {sl.shelf_level_id: sl.fixture_id for sl in doc.shelf_levels}
        self.zone_by_id = {z.zone_id: z for z in self.doc.zones}

    def _velocity(self, sku) -> float:
        cls = sku.abc_class.value if sku.abc_class else "C"
        return ABC_VELOCITY.get(cls, 1.75) * (FRESH_BUMP if sku.fresh_flag else 1.0)

    def _daily_margin(self, sku) -> float:
        margin_rate = sku.gross_margin
        if margin_rate is None:
            margin_rate = (sku.unit_price - sku.unit_cost) / sku.unit_price if sku.unit_price else 0
        return self._velocity(sku) * sku.unit_price * margin_rate

    def report(self, bottom_pct: float = 0.10, top_n: int = 3) -> dict:
        facing_rows = []
        for fc in self.doc.facings:
            if not fc.sku_code or fc.sku_code not in self.sku_by_code:
                continue
            sku = self.sku_by_code[fc.sku_code]
            fixture_id = self.level_fixture.get(fc.shelf_level_id)
            zone = self.zone_by_id.get(self.fixture_zone.get(fixture_id))
            daily_margin = self._daily_margin(sku)
            heat = zone.heat_value if zone else 0.5
            facing_rows.append({
                "facing_id": fc.facing_id,
                "sku_code": fc.sku_code,
                "sku_name": sku.sku_name,
                "category": sku.category_name,
                "zone_name": zone.zone_name if zone else "未分区",
                "heat": round(heat, 3),
                "width_m": fc.facing_width_m,
                "daily_margin_idr": round(daily_margin, 0),
                "margin_per_m_idr": round(daily_margin / max(fc.facing_width_m, 0.01), 0),
                "weighted_margin_idr": round(daily_margin * heat, 0),
            })

        # 1) 分区坪效榜
        zone_stats: dict[str, dict] = {}
        for r in facing_rows:
            z = zone_stats.setdefault(r["zone_name"],
                                      {"zone_name": r["zone_name"], "daily_margin_idr": 0.0, "facings": 0})
            z["daily_margin_idr"] += r["daily_margin_idr"]
            z["facings"] += 1
        areas = {z.zone_name: _polygon_area_m2(z.polygon) for z in self.doc.zones}
        zone_ranking = []
        for z in zone_stats.values():
            area = areas.get(z["zone_name"], 0.0)
            z["area_m2"] = round(area, 1)
            z["daily_margin_idr"] = round(z["daily_margin_idr"], 0)
            z["margin_per_m2_idr"] = round(z["daily_margin_idr"] / area, 0) if area > 0 else 0
            zone_ranking.append(z)
        zone_ranking.sort(key=lambda x: x["margin_per_m2_idr"], reverse=True)

        # 2) 面位效率末位榜（品类内 margin/m 相对均值）
        cat_vals: dict[str, list[float]] = {}
        for r in facing_rows:
            cat_vals.setdefault(r["category"], []).append(r["margin_per_m_idr"])
        cat_mean = {c: sum(v) / len(v) for c, v in cat_vals.items()}
        for r in facing_rows:
            m = cat_mean.get(r["category"], 1)
            r["efficiency_ratio"] = round(r["margin_per_m_idr"] / m, 2) if m > 0 else 1.0
        bottom_n = max(1, int(len(facing_rows) * bottom_pct))
        bottom_facings = sorted(facing_rows, key=lambda r: r["efficiency_ratio"])[:bottom_n]

        # 3) what-if：每个候选 SKU 配最优末位面位，按增量排序取 top_n
        placed = {r["sku_code"] for r in facing_rows}
        candidates = [s for s in self.doc.skus
                      if s.sku_code not in placed and s.abc_class and s.abc_class.value in ("A", "B")]
        candidates.sort(key=self._daily_margin, reverse=True)
        what_if = []
        used_targets: set[str] = set()
        for c in candidates:
            c_margin = self._daily_margin(c)
            best = None
            for target in bottom_facings:
                if target["facing_id"] in used_targets:
                    continue
                delta = c_margin * target["heat"] - target["weighted_margin_idr"]
                if best is None or delta > best[0]:
                    best = (delta, target)
            if best and best[0] > 0:
                used_targets.add(best[1]["facing_id"])
                what_if.append({
                    "action": "替换面位", "facing_id": best[1]["facing_id"],
                    "zone": best[1]["zone_name"], "from_sku": best[1]["sku_code"],
                    "to_sku": c.sku_code, "to_sku_name": c.sku_name,
                    "delta_daily_margin_idr": round(best[0], 0),
                })
        what_if.sort(key=lambda w: w["delta_daily_margin_idr"], reverse=True)
        what_if = what_if[:top_n]

        return {
            "store_id": self.doc.store_profile.store_id,
            "total_facing_daily_margin_idr": round(sum(r["daily_margin_idr"] for r in facing_rows), 0),
            "zone_ranking": zone_ranking,
            "bottom_facings": bottom_facings[:10],
            "what_if_top": what_if[:top_n],
        }
