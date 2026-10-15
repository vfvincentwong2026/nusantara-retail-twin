"""统一数据模型实体。

对应 docs/data-model.md 的表结构。空间实体树：
Store → Zone → Fixture → ShelfLevel → Facing → SKU。
全量种子文档（StoreSeed）与样例种子文档（含 sample_facings / sample_skus）
共用同一组实体。
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class IslandRegion(str, Enum):
    java = "java"
    sumatra = "sumatra"
    kalimantan = "kalimantan"
    sulawesi = "sulawesi"
    papua = "papua"


class StoreFormat(str, Enum):
    minimarket = "minimarket"
    supermarket = "supermarket"
    hypermarket = "hypermarket"


class ZoneType(str, Enum):
    fresh = "fresh"
    ambient = "ambient"
    frozen = "frozen"
    household = "household"
    fashion = "fashion"
    promo = "promo"
    checkout = "checkout"


class FixtureType(str, Enum):
    shelf = "shelf"
    cooler = "cooler"
    freezer = "freezer"
    gondola = "gondola"
    # 生鲜 specialty 柜（样例种子使用）
    meat_counter = "meat_counter"
    seafood_counter = "seafood_counter"
    produce_rack = "produce_rack"
    bakery_counter = "bakery_counter"
    hot_food_counter = "hot_food_counter"


class ABCClass(str, Enum):
    A = "A"
    B = "B"
    C = "C"


class Point(BaseModel):
    x: float
    y: float


class StoreProfile(BaseModel):
    store_id: str
    store_name: str
    store_size_sqm: int
    store_format: StoreFormat
    island_region: IslandRegion
    city: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    target_sku_count: int = 0
    sku_density: Optional[float] = None
    fresh_ratio: Optional[float] = None
    shelf_layers: Optional[int] = None
    aisle_width_m: Optional[float] = None
    qris_enabled: bool = False
    supply_hub_distance_km: Optional[float] = None
    lead_time_variance_days: Optional[float] = None
    mudik_offset: int = 0


class Zone(BaseModel):
    zone_id: str
    zone_name: str
    zone_type: ZoneType
    heat_value: float = Field(ge=0, le=1)
    polygon: list[Point]


class Fixture(BaseModel):
    fixture_id: str
    zone_id: str
    fixture_type: FixtureType
    fixture_label: str = ""
    position_x: float
    position_y: float
    length_m: float
    height_m: float
    rotation_deg: float = 0


class ShelfLevel(BaseModel):
    shelf_level_id: str
    fixture_id: str
    level_number: int = Field(ge=1)
    height_from_floor_m: float
    is_eye_level: bool = False


class Facing(BaseModel):
    facing_id: str
    shelf_level_id: str
    facing_index: int = Field(ge=1)
    facing_width_m: float
    max_units: int = Field(ge=0)
    sku_code: Optional[str] = None
    planogram_version: int = 1


class SKU(BaseModel):
    sku_id: str
    sku_code: str
    sku_name: str
    category_name: str
    subcategory: str = ""
    brand: str = ""
    unit_price: float = Field(ge=0)
    unit_cost: float = Field(ge=0)
    gross_margin: Optional[float] = Field(default=None, ge=0, le=1)
    shelf_life_days: Optional[int] = None
    fresh_flag: bool = False
    halal_certified: bool = False
    local_content_ratio: Optional[float] = Field(default=None, ge=0, le=1)
    mudik_sensitive: bool = False
    abc_class: Optional[ABCClass] = None


class SeedMeta(BaseModel):
    seed_version: str = "0.2"
    generated_at: datetime
    store_size_sqm: int
    store_format: StoreFormat
    island_region: IslandRegion
    source: str = "nrt seed"


class GenerationSummary(BaseModel):
    zones_count: int
    fixtures_count: int
    shelf_levels_count: int
    facings_count: int
    skus_count: int
    fresh_skus_count: int
    halal_certified_skus_count: int
    note: str = ""


class RamadanCalendar(BaseModel):
    ramadan_start: str
    lebaran_date: str
    peak_date: str
    mudik_peak_date: str
    pre_replenishment_windows: list[dict]


class StoreSeed(BaseModel):
    """全量种子文档（nrt seed 生成）。

    兼容历史样例文档：若提供 sample_* 字段则视为样例。
    """

    meta: SeedMeta
    store_profile: StoreProfile
    zones: list[Zone]
    fixtures: list[Fixture]
    shelf_levels: list[ShelfLevel]
    facings: Optional[list[Facing]] = None
    skus: Optional[list[SKU]] = None
    sample_facings: Optional[list[Facing]] = None
    sample_skus: Optional[list[SKU]] = None
    ramadan_calendar_2026: RamadanCalendar
    generation_summary: GenerationSummary

    @property
    def is_sample(self) -> bool:
        return self.sample_facings is not None
