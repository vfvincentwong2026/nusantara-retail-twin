"""三档门店全量种子数据生成器。

产出与 docs/data-model.md §7 规模承诺一致的全量数据：
500㎡ → 5,000 SKU / 1,200 Facings；2,000㎡ → 14,000 / 4,320；
5,000㎡ → 34,000 / 10,920。生成完全确定性（--seed 可复现）。

布局算法：门店 footprint 按区域切成横向 Zone 带，Zone 内按
货架长度 + 通道间距成行排布 Fixture，Fixture 按层数展开 ShelfLevel，
每层 6 个 Facing（6 × layers × fixtures = 目标 Facings 总数）。
"""

from __future__ import annotations

import random
from datetime import datetime, timezone, timedelta
from typing import Optional

from nrt.calendar import IndonesiaCalendar, ISLAND_LOGISTICS
from nrt.model import (
    ABCClass,
    Facing,
    Fixture,
    FixtureType,
    IslandRegion,
    Point,
    ShelfLevel,
    SKU,
    StoreFormat,
    StoreProfile,
    Zone,
    ZoneType,
)
from nrt.seed.catalog import (
    CATEGORIES,
    REGION_PROFILES,
    SCALE_PARAMS,
    STORE_NAME_SUFFIX,
    VARIANTS,
    ZONES,
)

FACINGS_PER_LEVEL = 6
ABC_WEIGHTS = (ABCClass.A, 0.20), (ABCClass.B, 0.30), (ABCClass.C, 0.50)


def _pick_abc(rng: random.Random) -> ABCClass:
    r = rng.random()
    return ABCClass.A if r < 0.20 else (ABCClass.B if r < 0.50 else ABCClass.C)


class SeedGenerator:
    def __init__(
        self,
        store_size: int = 2000,
        region: str = "java",
        seed: int = 42,
        sku_count: Optional[int] = None,
        fresh_ratio: Optional[float] = None,
    ):
        if store_size not in SCALE_PARAMS:
            raise ValueError(f"不支持的门店规模：{store_size}（可选 {sorted(SCALE_PARAMS)}）")
        if region not in ISLAND_LOGISTICS:
            raise ValueError(f"不支持的岛屿区域：{region}")
        self.p = SCALE_PARAMS[store_size]
        self.store_size = store_size
        self.region = region
        self.rng = random.Random(seed)
        self.target_sku = sku_count or self.p["target_sku_count"]
        self.fresh_ratio = fresh_ratio if fresh_ratio is not None else self.p["fresh_ratio"]
        self.cal = IndonesiaCalendar(year=2026)
        self._fmt = self.p["format"]
        self._size_code = store_size

    # ------------------------------------------------------------------
    def generate(self) -> dict:
        profile = self._store_profile()
        zones = self._zones()
        fixtures = self._fixtures(zones)
        shelf_levels = self._shelf_levels(fixtures)
        skus = self._skus()
        facings = self._facings(shelf_levels, fixtures, zones, skus)
        summary = {
            "zones_count": len(zones),
            "fixtures_count": len(fixtures),
            "shelf_levels_count": len(shelf_levels),
            "facings_count": len(facings),
            "skus_count": len(skus),
            "fresh_skus_count": sum(1 for s in skus if s.fresh_flag),
            "halal_certified_skus_count": sum(1 for s in skus if s.halal_certified),
            "note": "全量数据：facings 与 skus 为完整列表（Phase 2，nrt seed 生成）",
        }
        tz7 = timezone(timedelta(hours=7))
        return {
            "meta": {
                "seed_version": "0.2",
                "generated_at": datetime.now(tz7).isoformat(timespec="seconds"),
                "store_size_sqm": self.store_size,
                "store_format": self._fmt,
                "island_region": self.region,
                "source": f"nrt seed --store-size {self.store_size} --region {self.region}",
            },
            "store_profile": profile.model_dump(),
            "zones": [z.model_dump() for z in zones],
            "fixtures": [f.model_dump() for f in fixtures],
            "shelf_levels": [sl.model_dump() for sl in shelf_levels],
            "facings": [fc.model_dump() for fc in facings],
            "skus": [s.model_dump() for s in skus],
            "ramadan_calendar_2026": self.cal.ramadan_summary(self.region),
            "generation_summary": summary,
        }

    # ------------------------------------------------------------------
    # 门店档案
    # ------------------------------------------------------------------
    def _store_profile(self) -> StoreProfile:
        rp = REGION_PROFILES[self.region]
        city, lat, lng = self.rng.choice(rp["cities"])
        logistics = ISLAND_LOGISTICS[self.region]
        width, depth = self.p["footprint"]
        suffix = self.rng.choice(STORE_NAME_SUFFIX[self._fmt])
        return StoreProfile(
            store_id=f"st-{self._size_code}-{self.region}-001",
            store_name=f"{city} {self._fmt.capitalize()} {suffix}",
            store_size_sqm=self.store_size,
            store_format=StoreFormat(self._fmt),
            island_region=IslandRegion(self.region),
            city=city,
            latitude=lat + self.rng.uniform(-0.05, 0.05),
            longitude=lng + self.rng.uniform(-0.05, 0.05),
            target_sku_count=self.target_sku,
            sku_density=round(self.target_sku / self.store_size, 2),
            fresh_ratio=self.fresh_ratio,
            shelf_layers=self.p["layers"],
            aisle_width_m=self.p["aisle_width_m"],
            qris_enabled=True,
            supply_hub_distance_km=round(self.rng.uniform(*rp["hub_km"]), 1),
            lead_time_variance_days=logistics["lead_time_std_days"],
            mudik_offset=self.cal.get_mudik_offset(self.region),
        )

    # ------------------------------------------------------------------
    # 空间：Zone 带 → Fixture 网格 → ShelfLevel → Facing
    # ------------------------------------------------------------------
    def _zones(self) -> list[Zone]:
        width, depth = self.p["footprint"]
        zone_defs = ZONES[: self.p["zones"]]
        total_w = sum(z["weight"] for z in zone_defs)
        zones, y0 = [], 0.0
        for i, zd in enumerate(zone_defs, 1):
            band_h = depth * zd["weight"] / total_w
            zones.append(
                Zone(
                    zone_id=f"zn-{self._size_code}-{i:03d}",
                    zone_name=zd["name"],
                    zone_type=ZoneType(zd["type"]),
                    heat_value=round(self.rng.uniform(0.45, 0.95), 3),
                    polygon=[Point(x=0.0, y=round(y0, 2)), Point(x=float(width), y=round(y0, 2)),
                             Point(x=float(width), y=round(y0 + band_h, 2)), Point(x=0.0, y=round(y0 + band_h, 2))],
                )
            )
            y0 += band_h
        return zones

    def _zone_fixture_counts(self, zones: list[Zone]) -> dict[str, int]:
        """按 Zone 类型权重分配货架数，修正凑整到目标值。"""
        type_weights = {"fresh": 1.3, "frozen": 1.1, "promo": 0.8, "checkout": 0.5}
        raw = []
        for z in zones:
            w = type_weights.get(z.zone_type.value, 1.0) * (0.8 + z.heat_value)
            raw.append(w)
        total_raw = sum(raw)
        counts = [max(1, round(self.p["fixtures"] * w / total_raw)) for w in raw]
        diff = self.p["fixtures"] - sum(counts)
        order = sorted(range(len(counts)), key=lambda i: -counts[i])
        i = 0
        while diff != 0:
            j = order[i % len(order)]
            if diff > 0:
                counts[j] += 1
                diff -= 1
            elif counts[j] > 1:
                counts[j] -= 1
                diff += 1
            i += 1
        return {z.zone_id: c for z, c in zip(zones, counts)}

    def _fixtures(self, zones: list[Zone]) -> list[Fixture]:
        width, _ = self.p["footprint"]
        counts = self._zone_fixture_counts(zones)
        fixtures: list[Fixture] = []
        fx_no = 0
        for z in zones:
            n = counts[z.zone_id]
            y0, y1 = z.polygon[0].y, z.polygon[2].y
            band_h = y1 - y0
            # 按货架长度成行排布（长度 2.5–4m，间距 = 通道宽）
            length = 3.0 if self.store_size == 500 else 4.0
            gap = self.p["aisle_width_m"]
            per_row = max(1, int((width + gap) // (length + gap)))
            rows = (n + per_row - 1) // per_row
            row_h = band_h / max(rows, 1)
            for idx in range(n):
                row, col = divmod(idx, per_row)
                fx_no += 1
                ftype = {
                    "fresh": FixtureType.cooler,
                    "frozen": FixtureType.freezer,
                    "checkout": FixtureType.shelf,
                }.get(z.zone_type.value, FixtureType.gondola)
                fixtures.append(
                    Fixture(
                        fixture_id=f"fx-{self._size_code}-{fx_no:03d}",
                        zone_id=z.zone_id,
                        fixture_type=ftype,
                        fixture_label=f"F-{fx_no:03d}",
                        position_x=round(col * (length + gap) + length / 2, 2),
                        position_y=round(y0 + row_h * (row + 0.5), 2),
                        length_m=length,
                        height_m=1.8 if ftype == FixtureType.gondola else 2.0,
                        rotation_deg=0,
                    )
                )
        return fixtures

    def _shelf_levels(self, fixtures: list[Fixture]) -> list[ShelfLevel]:
        layers = self.p["layers"]
        eye = (layers + 1) // 2
        levels: list[ShelfLevel] = []
        for f in fixtures:
            for lv in range(1, layers + 1):
                levels.append(
                    ShelfLevel(
                        shelf_level_id=f"sl-{self._size_code}-{f.fixture_id.split('-')[-1]}-{lv}",
                        fixture_id=f.fixture_id,
                        level_number=lv,
                        height_from_floor_m=round(0.15 + (lv - 1) * 0.42, 2),
                        is_eye_level=(lv == eye),
                    )
                )
        return levels

    # ------------------------------------------------------------------
    # 商品：SKU 目录
    # ------------------------------------------------------------------
    def _skus(self) -> list[SKU]:
        rng = self.rng
        fresh_target = round(self.target_sku * self.fresh_ratio)
        fresh_cats = [c for c in CATEGORIES if c["fresh"]]
        ambient_cats = [c for c in CATEGORIES if not c["fresh"]]
        fw_total = sum(c["weight"] for c in fresh_cats)
        aw_total = sum(c["weight"] for c in ambient_cats)

        plan: list[tuple[dict, int]] = []
        remaining_fresh = fresh_target
        for c in fresh_cats[:-1]:
            n = round(fresh_target * c["weight"] / fw_total)
            plan.append((c, n))
            remaining_fresh -= n
        plan.append((fresh_cats[-1], remaining_fresh))
        for c in ambient_cats:
            plan.append((c, round((self.target_sku - fresh_target) * c["weight"] / aw_total)))

        skus: list[SKU] = []
        serial = 0
        for cat, n in plan:
            variants = VARIANTS[cat["key"]]
            for _ in range(max(n, 0)):
                serial += 1
                brand = rng.choice(cat["brands"])
                variant = rng.choice(variants)
                price = round(rng.uniform(*cat["price"]) / 100) * 100
                cost = round(price * rng.uniform(0.60, 0.85) / 100) * 100
                abc = _pick_abc(rng)
                skus.append(
                    SKU(
                        sku_id=f"sku-{serial:06d}",
                        sku_code=f"SKU-{cat['key'][:4].upper()}-{serial:05d}",
                        sku_name=f"{brand} {variant}",
                        category_name=cat["name"],
                        subcategory=variant,
                        brand=brand,
                        unit_price=price,
                        unit_cost=cost,
                        gross_margin=round((price - cost) / price, 3) if price else 0,
                        shelf_life_days=cat["shelf_life"],
                        fresh_flag=cat["fresh"],
                        halal_certified=rng.random() < cat["halal"],
                        local_content_ratio=round(rng.uniform(0.5, 0.99), 3),
                        mudik_sensitive=rng.random() < cat["mudik"],
                        abc_class=abc,
                    )
                )

        # 校准整体清真覆盖率到规模目标（docs/data-model.md §7：95%/90%/85%）。
        # 生鲜与食品品类默认高清真比例，缺口主要从非食品品类补齐/回退。
        target_halal = round(len(skus) * self.p["halal_ratio"])
        cat_halal = {c["name"]: c["halal"] for c in CATEGORIES}
        current = sum(1 for s in skus if s.halal_certified)
        if current < target_halal:
            candidates = sorted(
                (s for s in skus if not s.halal_certified),
                key=lambda s: -cat_halal.get(s.category_name, 0.5),
            )
            for s in candidates[: target_halal - current]:
                s.halal_certified = True
        elif current > target_halal:
            candidates = sorted(
                (s for s in skus if s.halal_certified),
                key=lambda s: cat_halal.get(s.category_name, 0.5),
            )
            for s in candidates[: current - target_halal]:
                s.halal_certified = False
        return skus

    # ------------------------------------------------------------------
    # Facing → SKU 映射：优先本 Zone 类型品类 + A/B 类
    # ------------------------------------------------------------------
    def _facings(
        self,
        levels: list[ShelfLevel],
        fixtures: list[Fixture],
        zones: list[Zone],
        skus: list[SKU],
    ) -> list[Facing]:
        rng = self.rng
        zone_by_id = {z.zone_id: z for z in zones}
        fixture_zone = {f.fixture_id: zone_by_id[f.zone_id] for f in fixtures}
        cat_by_name = {c["name"]: c for c in CATEGORIES}

        # 每个 zone_type 对应的 SKU 候选池（按 ABC 加权，A 类概率 ×3）
        pools: dict[str, list[str]] = {}
        for zt in ZoneType:
            names = [c["name"] for c in CATEGORIES if c["zone"] == zt.value]
            pool = []
            for s in skus:
                cat = cat_by_name.get(s.category_name)
                if cat and cat["zone"] == zt.value:
                    w = {"A": 3, "B": 2, "C": 1}[s.abc_class.value]
                    pool.extend([s.sku_code] * w)
            pools[zt.value] = pool
        all_pool = [s.sku_code for s in skus if s.abc_class != ABCClass.C] or [s.sku_code for s in skus]

        facings: list[Facing] = []
        no = 0
        for lv in levels:
            zt = fixture_zone[lv.fixture_id].zone_type.value
            pool = pools.get(zt) or all_pool
            fno = lv.fixture_id.split("-")[-1]
            for i in range(1, FACINGS_PER_LEVEL + 1):
                no += 1
                # eye level 面位更宽、容量更大
                eye = lv.is_eye_level
                width = round(rng.uniform(0.15, 0.30) + (0.05 if eye else 0), 2)
                facings.append(
                    Facing(
                        facing_id=f"fc-{self._size_code}-{fno}-{lv.level_number}-{i:02d}",
                        shelf_level_id=lv.shelf_level_id,
                        facing_index=i,
                        facing_width_m=width,
                        max_units=rng.randint(16, 48) if eye else rng.randint(8, 36),
                        sku_code=rng.choice(pool),
                        planogram_version=1,
                    )
                )
        return facings


def generate_seed(
    store_size: int = 2000,
    region: str = "java",
    seed: int = 42,
    sku_count: Optional[int] = None,
    fresh_ratio: Optional[float] = None,
) -> dict:
    """生成单店全量种子文档（纯 dict，可直接 json.dump）。"""
    return SeedGenerator(store_size, region, seed, sku_count, fresh_ratio).generate()
