// 与 src/nrt/model/entities.py 对应的 TypeScript 类型（种子 JSON 契约）

export interface Point {
  x: number
  y: number
}

export interface StoreProfile {
  store_id: string
  store_name: string
  store_size_sqm: number
  store_format: string
  island_region: string
  city: string
  latitude: number | null
  longitude: number | null
  target_sku_count: number
  sku_density: number | null
  fresh_ratio: number | null
  shelf_layers: number | null
  aisle_width_m: number | null
  qris_enabled: boolean
  supply_hub_distance_km: number | null
  lead_time_variance_days: number | null
  mudik_offset: number
}

export interface Zone {
  zone_id: string
  zone_name: string
  zone_type: string
  heat_value: number
  polygon: Point[]
}

export interface Fixture {
  fixture_id: string
  zone_id: string
  fixture_type: string
  fixture_label: string
  position_x: number
  position_y: number
  length_m: number
  height_m: number
  rotation_deg: number
}

export interface ShelfLevel {
  shelf_level_id: string
  fixture_id: string
  level_number: number
  height_from_floor_m: number
  is_eye_level: boolean
}

export interface Facing {
  facing_id: string
  shelf_level_id: string
  facing_index: number
  facing_width_m: number
  max_units: number
  sku_code: string | null
  planogram_version: number
}

export interface SKU {
  sku_id: string
  sku_code: string
  sku_name: string
  category_name: string
  subcategory: string
  brand: string
  unit_price: number
  unit_cost: number
  gross_margin: number | null
  shelf_life_days: number | null
  fresh_flag: boolean
  halal_certified: boolean
  local_content_ratio: number | null
  mudik_sensitive: boolean
  abc_class: string | null
}

export interface RamadanCalendar {
  ramadan_start: string
  lebaran_date: string
  peak_date: string
  mudik_peak_date: string
  pre_replenishment_windows: { round: number; start: string; end: string; scope: string }[]
}

export interface GenerationSummary {
  zones_count: number
  fixtures_count: number
  shelf_levels_count: number
  facings_count: number
  skus_count: number
  fresh_skus_count: number
  halal_certified_skus_count: number
  note: string
}

export interface SeedDoc {
  meta: { seed_version: string; generated_at: string; store_size_sqm: number; store_format: string; island_region: string; source: string }
  store_profile: StoreProfile
  zones: Zone[]
  fixtures: Fixture[]
  shelf_levels: ShelfLevel[]
  facings: Facing[]
  skus: SKU[]
  ramadan_calendar_2026: RamadanCalendar
  generation_summary: GenerationSummary
}

// 编辑器对单个 Facing 的本地修改
export interface FacingEdit {
  sku_code: string | null
  max_units: number
}
