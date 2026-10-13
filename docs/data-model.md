# Data Model

> Nusantara Retail Twin 的统一数据模型定义。
> 数据库：PostgreSQL 15 + PostGIS

---

## 1. 实体关系总览

```text
Store (门店)
  │
  ├── Zone (区域：生鲜区、饮料区、日用品区...)
  │     │
  │     └── Fixture (货架/冷柜)
  │           │
  │           └── ShelfLevel (货架层)
  │                 │
  │                 └── Facing (陈列面位)
  │                       │
  │                       └── SKU (商品)
  │                             │
  │                             ├── InventoryBatch (库存批次)
  │                             ├── SalesEvent (销售事件)
  │                             └── DemandForecast (需求预测)
  │
  ├── SentimentSignal (舆情信号)
  └── ReplenishmentOrder (补货单)
```

---

## 2. 空间实体

### 2.1 stores

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `store_id` | UUID | PK | 门店唯一标识 |
| `store_name` | VARCHAR(128) | NOT NULL | 门店名称 |
| `store_size_sqm` | INTEGER | NOT NULL | 门店面积（㎡） |
| `store_format` | VARCHAR(32) | NOT NULL | minimarket / supermarket / hypermarket |
| `island_region` | VARCHAR(32) | NOT NULL | java / sumatra / kalimantan / sulawesi / papua |
| `city` | VARCHAR(64) | | 城市 |
| `latitude` | DECIMAL(9,6) | | 纬度 |
| `longitude` | DECIMAL(9,6) | | 经度 |
| `target_sku_count` | INTEGER | NOT NULL | 目标 SKU 数量 |
| `sku_density` | DECIMAL(6,2) | | SKU 密度（SKU/㎡） |
| `fresh_ratio` | DECIMAL(4,3) | | 生鲜 SKU 占比 |
| `shelf_layers` | SMALLINT | | 货架层数 |
| `aisle_width_m` | DECIMAL(4,2) | | 主通道宽度（米） |
| `qris_enabled` | BOOLEAN | DEFAULT false | 是否支持 QRIS |
| `supply_hub_distance_km` | DECIMAL(8,2) | | 到最近配送中心距离 |
| `lead_time_variance_days` | DECIMAL(4,2) | | 补货提前期方差 |
| `mudik_offset` | INTEGER | DEFAULT 0 | Mudik 返乡偏移天数 |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | DEFAULT now() | |

### 2.2 zones

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `zone_id` | UUID | PK | |
| `store_id` | UUID | FK → stores | |
| `zone_name` | VARCHAR(64) | NOT NULL | 区域名称 |
| `zone_type` | VARCHAR(32) | NOT NULL | fresh / ambient / frozen / household / fashion |
| `heat_value` | DECIMAL(4,3) | | 去化热力值 (0–1) |
| `polygon` | GEOMETRY(POLYGON, 4326) | | 区域几何边界 |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | |

### 2.3 fixtures

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `fixture_id` | UUID | PK | |
| `zone_id` | UUID | FK → zones | |
| `fixture_type` | VARCHAR(32) | NOT NULL | shelf / cooler / freezer / gondola |
| `fixture_label` | VARCHAR(32) | | 货架编号 |
| `position_x` | DECIMAL(6,2) | | X 坐标（米） |
| `position_y` | DECIMAL(6,2) | | Y 坐标（米） |
| `length_m` | DECIMAL(4,2) | | 货架长度（米） |
| `height_m` | DECIMAL(4,2) | | 货架高度（米） |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | |

### 2.4 shelf_levels

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `shelf_level_id` | UUID | PK | |
| `fixture_id` | UUID | FK → fixtures | |
| `level_number` | SMALLINT | NOT NULL | 层号（从下往上） |
| `height_from_floor_m` | DECIMAL(4,2) | | 离地高度（米） |
| `is_eye_level` | BOOLEAN | DEFAULT false | 是否黄金视线层 |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | |

### 2.5 facings

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `facing_id` | UUID | PK | |
| `shelf_level_id` | UUID | FK → shelf_levels | |
| `facing_index` | SMALLINT | NOT NULL | 面位序号（从左到右） |
| `facing_width_m` | DECIMAL(4,2) | NOT NULL | 面位宽度（米） |
| `max_units` | INTEGER | | 该面位最大存量 |
| `sku_id` | UUID | FK → skus | 当前陈列 SKU |
| `planogram_version` | INTEGER | DEFAULT 1 | 货架图版本 |
| `updated_at` | TIMESTAMPTZ | DEFAULT now() | |

---

## 3. 商品实体

### 3.1 skus

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `sku_id` | UUID | PK | |
| `sku_code` | VARCHAR(32) | UNIQUE | SKU 编码 |
| `sku_name` | VARCHAR(128) | NOT NULL | 商品名称 |
| `category_id` | UUID | FK → categories | |
| `subcategory` | VARCHAR(64) | | 子品类 |
| `brand` | VARCHAR(64) | | 品牌 |
| `unit_price` | DECIMAL(12,2) | | 单价（IDR） |
| `unit_cost` | DECIMAL(12,2) | | 成本价（IDR） |
| `gross_margin` | DECIMAL(4,3) | | 毛利率 |
| `shelf_life_days` | INTEGER | | 保质期（天） |
| `fresh_flag` | BOOLEAN | DEFAULT false | 是否生鲜 |
| `halal_certified` | BOOLEAN | DEFAULT false | 清真认证 |
| `local_content_ratio` | DECIMAL(4,3) | | 本地成分比例 |
| `mudik_sensitive` | BOOLEAN | DEFAULT false | 是否返乡携带品 |
| `abc_class` | CHAR(1) | | A / B / C |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | |

### 3.2 categories

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `category_id` | UUID | PK | |
| `category_name` | VARCHAR(64) | NOT NULL | 品类名称 |
| `parent_category_id` | UUID | FK → categories | 父品类 |
| `is_fresh` | BOOLEAN | DEFAULT false | 是否生鲜品类 |
| `seasonality_type` | VARCHAR(32) | | ramadan / harbolnas / none |

---

## 4. 动态数据

### 4.1 inventory_batches

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `batch_id` | UUID | PK | |
| `store_id` | UUID | FK → stores | |
| `sku_id` | UUID | FK → skus | |
| `facing_id` | UUID | FK → facings | |
| `quantity` | INTEGER | NOT NULL | 当前数量 |
| `expiry_date` | DATE | | 过期日期 |
| `received_date` | DATE | | 收货日期 |
| `batch_status` | VARCHAR(16) | DEFAULT 'active' | active / expired / quarantined |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | |

### 4.2 sales_events

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `event_id` | UUID | PK | |
| `store_id` | UUID | FK → stores | |
| `sku_id` | UUID | FK → skus | |
| `facing_id` | UUID | FK → facings | |
| `event_date` | DATE | NOT NULL | 销售日期 |
| `quantity_sold` | INTEGER | NOT NULL | 售出数量 |
| `unit_price` | DECIMAL(12,2) | | 成交单价 |
| `promotion_flag` | BOOLEAN | DEFAULT false | 是否促销 |
| `promotion_type` | VARCHAR(32) | | bundle / discount / none |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | |

### 4.3 demand_forecasts

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `forecast_id` | UUID | PK | |
| `store_id` | UUID | FK → stores | |
| `sku_id` | UUID | FK → skus | |
| `forecast_date` | DATE | NOT NULL | 预测日期 |
| `demand_mean` | DECIMAL(10,2) | | 需求均值 |
| `demand_p90` | DECIMAL(10,2) | | P90 需求 |
| `safety_stock` | INTEGER | | 安全库存 |
| `reorder_point` | INTEGER | | 再订货点 |
| `suggested_order_qty` | INTEGER | | 建议订货量 |
| `confidence` | DECIMAL(4,3) | | 置信度 |
| `model_version` | VARCHAR(32) | | 模型版本 |
| `generated_at` | TIMESTAMPTZ | DEFAULT now() | |

### 4.4 replenishment_orders

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `order_id` | UUID | PK | |
| `store_id` | UUID | FK → stores | |
| `sku_id` | UUID | FK → skus | |
| `order_quantity` | INTEGER | NOT NULL | 订货量 |
| `priority` | VARCHAR(16) | | HIGH / MEDIUM / LOW |
| `status` | VARCHAR(16) | DEFAULT 'pending' | pending / confirmed / shipped / received |
| `suggested_delivery_start` | DATE | | 建议交付开始 |
| `suggested_delivery_end` | DATE | | 建议交付结束 |
| `reason` | TEXT | | 补货原因 |
| `promotion_trigger` | VARCHAR(32) | | 触发的促销类型 |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | |

### 4.5 sentiment_signals

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `signal_id` | UUID | PK | |
| `store_id` | UUID | FK → stores | |
| `category_id` | UUID | FK → categories | |
| `signal_date` | DATE | NOT NULL | |
| `heat_index` | DECIMAL(4,3) | | 热度指数 (0–1) |
| `sentiment_score` | DECIMAL(4,3) | | 情感得分 (-1 到 1) |
| `source` | VARCHAR(32) | | tiktok / twitter / news |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | |

---

## 5. 参考数据

### 5.1 indonesia_holidays

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `holiday_id` | UUID | PK | |
| `holiday_name` | VARCHAR(64) | NOT NULL | 节日名称 |
| `holiday_date` | DATE | NOT NULL | 日期 |
| `holiday_type` | VARCHAR(32) | | religious / national / commercial |
| `impact_weight` | DECIMAL(4,3) | | 影响权重 (0–1) |
| `ramadan_relative_day` | INTEGER | | 相对斋月的天数 |

### 5.2 island_logistics_params

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `region_id` | VARCHAR(32) | PK | java / sumatra / kalimantan / sulawesi / papua |
| `region_name` | VARCHAR(64) | | |
| `lead_time_mean_days` | DECIMAL(4,2) | | 平均提前期 |
| `lead_time_std_days` | DECIMAL(4,2) | | 提前期标准差 |
| `k_factor` | DECIMAL(3,2) | | 安全系数 |
| `cold_chain_available` | BOOLEAN | | 冷链可用性 |
| `notes` | TEXT | | |

---

## 6. SQL DDL（核心表）

```sql
-- 启用 PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 门店
CREATE TABLE stores (
    store_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    store_name VARCHAR(128) NOT NULL,
    store_size_sqm INTEGER NOT NULL,
    store_format VARCHAR(32) NOT NULL CHECK (store_format IN ('minimarket','supermarket','hypermarket')),
    island_region VARCHAR(32) NOT NULL CHECK (island_region IN ('java','sumatra','kalimantan','sulawesi','papua')),
    city VARCHAR(64),
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    target_sku_count INTEGER NOT NULL,
    sku_density DECIMAL(6,2),
    fresh_ratio DECIMAL(4,3),
    shelf_layers SMALLINT,
    aisle_width_m DECIMAL(4,2),
    qris_enabled BOOLEAN DEFAULT false,
    supply_hub_distance_km DECIMAL(8,2),
    lead_time_variance_days DECIMAL(4,2),
    mudik_offset INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 区域
CREATE TABLE zones (
    zone_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    store_id UUID NOT NULL REFERENCES stores(store_id) ON DELETE CASCADE,
    zone_name VARCHAR(64) NOT NULL,
    zone_type VARCHAR(32) NOT NULL,
    heat_value DECIMAL(4,3),
    polygon GEOMETRY(POLYGON, 4326),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 货架
CREATE TABLE fixtures (
    fixture_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    zone_id UUID NOT NULL REFERENCES zones(zone_id) ON DELETE CASCADE,
    fixture_type VARCHAR(32) NOT NULL,
    fixture_label VARCHAR(32),
    position_x DECIMAL(6,2),
    position_y DECIMAL(6,2),
    length_m DECIMAL(4,2),
    height_m DECIMAL(4,2),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 货架层
CREATE TABLE shelf_levels (
    shelf_level_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fixture_id UUID NOT NULL REFERENCES fixtures(fixture_id) ON DELETE CASCADE,
    level_number SMALLINT NOT NULL,
    height_from_floor_m DECIMAL(4,2),
    is_eye_level BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (fixture_id, level_number)
);

-- 陈列面位
CREATE TABLE facings (
    facing_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    shelf_level_id UUID NOT NULL REFERENCES shelf_levels(shelf_level_id) ON DELETE CASCADE,
    facing_index SMALLINT NOT NULL,
    facing_width_m DECIMAL(4,2) NOT NULL,
    max_units INTEGER,
    sku_id UUID,
    planogram_version INTEGER DEFAULT 1,
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (shelf_level_id, facing_index)
);

-- SKU
CREATE TABLE skus (
    sku_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sku_code VARCHAR(32) UNIQUE,
    sku_name VARCHAR(128) NOT NULL,
    category_id UUID,
    subcategory VARCHAR(64),
    brand VARCHAR(64),
    unit_price DECIMAL(12,2),
    unit_cost DECIMAL(12,2),
    gross_margin DECIMAL(4,3),
    shelf_life_days INTEGER,
    fresh_flag BOOLEAN DEFAULT false,
    halal_certified BOOLEAN DEFAULT false,
    local_content_ratio DECIMAL(4,3),
    mudik_sensitive BOOLEAN DEFAULT false,
    abc_class CHAR(1) CHECK (abc_class IN ('A','B','C')),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 库存批次
CREATE TABLE inventory_batches (
    batch_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    store_id UUID NOT NULL REFERENCES stores(store_id),
    sku_id UUID NOT NULL REFERENCES skus(sku_id),
    facing_id UUID REFERENCES facings(facing_id),
    quantity INTEGER NOT NULL DEFAULT 0,
    expiry_date DATE,
    received_date DATE,
    batch_status VARCHAR(16) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 销售事件
CREATE TABLE sales_events (
    event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    store_id UUID NOT NULL REFERENCES stores(store_id),
    sku_id UUID NOT NULL REFERENCES skus(sku_id),
    facing_id UUID REFERENCES facings(facing_id),
    event_date DATE NOT NULL,
    quantity_sold INTEGER NOT NULL,
    unit_price DECIMAL(12,2),
    promotion_flag BOOLEAN DEFAULT false,
    promotion_type VARCHAR(32),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 需求预测
CREATE TABLE demand_forecasts (
    forecast_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    store_id UUID NOT NULL REFERENCES stores(store_id),
    sku_id UUID NOT NULL REFERENCES skus(sku_id),
    forecast_date DATE NOT NULL,
    demand_mean DECIMAL(10,2),
    demand_p90 DECIMAL(10,2),
    safety_stock INTEGER,
    reorder_point INTEGER,
    suggested_order_qty INTEGER,
    confidence DECIMAL(4,3),
    model_version VARCHAR(32),
    generated_at TIMESTAMPTZ DEFAULT now()
);

-- 补货单
CREATE TABLE replenishment_orders (
    order_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    store_id UUID NOT NULL REFERENCES stores(store_id),
    sku_id UUID NOT NULL REFERENCES skus(sku_id),
    order_quantity INTEGER NOT NULL,
    priority VARCHAR(16) CHECK (priority IN ('HIGH','MEDIUM','LOW')),
    status VARCHAR(16) DEFAULT 'pending',
    suggested_delivery_start DATE,
    suggested_delivery_end DATE,
    reason TEXT,
    promotion_trigger VARCHAR(32),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 索引
CREATE INDEX idx_facings_sku ON facings(sku_id);
CREATE INDEX idx_inventory_store_sku ON inventory_batches(store_id, sku_id);
CREATE INDEX idx_sales_store_date ON sales_events(store_id, event_date);
CREATE INDEX idx_forecast_store_sku_date ON demand_forecasts(store_id, sku_id, forecast_date);
CREATE INDEX idx_zones_polygon ON zones USING GIST(polygon);
```

---

## 7. 种子数据规模

三档门店的种子数据由 `nrt seed` 命令生成，核心参数：

| 参数 | 500㎡ | 2,000㎡ | 5,000㎡ |
|---|---|---|---|
| 门店面积 | 500 | 2000 | 5000 |
| 目标 SKU 数 | 5,000 | 14,000 | 34,000 |
| 货架数量 | 40 | 120 | 260 |
| 货架层数 | 5 | 6 | 7 |
| 总 Facings 数 | 1,200 | 4,320 | 10,920 |
| 生鲜占比 | 18% | 28% | 33% |
| 清真认证覆盖率 | 95% | 90% | 85% |

种子数据位于 `data/seeds/store_{size}sqm.json`，通过 `nrt seed --store-size {size} --region {region}` 一键生成。
