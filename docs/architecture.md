# Architecture

> Nusantara Retail Twin 的技术架构设计文档。
> 版本：v0.1 · 状态：设计中

---

## 1. 设计原则

Nusantara Retail Twin 的架构围绕四个核心原则展开：

**空间即数据**。门店平面图、货架图（Planogram）和 Facings 不是可视化附属品，而是补货决策的一等公民。每个 Facings 拥有独立的 `facing_id`，直接参与库存计算和预测输入。

**单一数据源**。2D 平面图与 3D 数字孪生共享同一份 JSON 文档。用户编辑 2D 平面时，3D 视图自动同步；货架图的变更直接写入 `planogram` 表，无需二次维护。

**可替换的预测层**。需求预测引擎通过标准化的 `DemandForecast` 接口与系统其余部分通信。当前实现基于 Prophet + LightGBM，但任何满足输入输出契约的模型都可以替换。

**方差优先于均值**。印尼跨岛物流的现实要求补货引擎以提前期方差（σ_LT）而非均值作为核心输入。这是与大多数西方零售补货系统的根本差异。

---

## 2. 分层架构总览

```text
┌─────────────────────────────────────────────────────────────┐
│                        展示层 (Presentation)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ 2D Floorplan │  │  3D Digital  │  │   Dashboard      │   │
│  │   Editor     │  │    Twin      │  │  (SKU Flow / ROI)│   │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘   │
│         │                 │                    │             │
│         └─────────────────┼────────────────────┘             │
│                           │ REST / WebSocket                 │
├───────────────────────────┼─────────────────────────────────┤
│                        服务层 (Service)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  Forecast    │  │ Replenishment│  │  Space Optimizer │   │
│  │   Engine     │  │   Engine     │  │    (MILP)        │   │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘   │
│         │                 │                    │             │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌────────┴─────────┐   │
│  │  Lifecycle   │  │  Sentiment   │  │  Calendar        │   │
│  │   Manager    │  │   Adapter    │  │  (ID Holidays)   │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
│                           │                                  │
├───────────────────────────┼─────────────────────────────────┤
│                        数据层 (Data)                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  PostgreSQL 15 + PostGIS                              │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌───────────┐  │   │
│  │  │ Spatial │ │Product  │ │Dynamic  │ │ Reference │  │   │
│  │  │ Entities│ │Catalog  │ │Data     │ │  Data     │  │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └───────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 数据流图

### 3.1 主数据流

```text
[门店种子数据 JSON] ──→ [PostgreSQL 入库]
                              │
                              ▼
                    ┌──────────────────┐
                    │  空间实体查询      │
                    │  Store → Zone →   │
                    │  Fixture → Facing │
                    └────────┬─────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  ▼
   ┌────────────┐    ┌────────────┐    ┌────────────┐
   │ 3D 渲染服务 │    │ 预测引擎   │    │ 空间优化器  │
   │ Three.js   │    │ Prophet +  │    │ MILP       │
   │            │    │ LightGBM   │    │            │
   └────────────┘    └─────┬──────┘    └─────┬──────┘
                           │                  │
                           ▼                  ▼
                    ┌────────────┐    ┌────────────┐
                    │DemandForecast│   │Planogram   │
                    │  (Store ×   │    │ Suggestion │
                    │   SKU)      │    │ (Facing →  │
                    └─────┬──────┘    │  SKU 映射) │
                          │           └─────┬──────┘
                          └───────┬─────────┘
                                  ▼
                         ┌────────────────┐
                         │  补货引擎       │
                         │  安全库存       │
                         │  再订货点       │
                         │  补货量建议     │
                         └────────┬───────┘
                                  │
                                  ▼
                         ┌────────────────┐
                         │  Replenishment │
                         │    Order       │
                         └────────────────┘
```

### 3.2 斋月期间的数据流增强

```text
[印尼节庆日历] ──┐
                │
[舆情信号] ──────┼──→ [预测引擎外生变量]
                │
[历史销售] ──────┘         │
                            ▼
              ┌─────────────────────────┐
              │ 斋月需求曲线生成          │
              │ - 城市门店：节前峰值      │
              │ - 外岛门店：节后峰值      │
              │ - Mudik 偏移参数          │
              └────────────┬────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │ 前置补货窗口计算          │
              │ - H-6~8 周：首轮         │
              │ - H-2 周：次轮           │
              └────────────┬────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │ 补货排程 + 库存约束检查   │
              └─────────────────────────┘
```

---

## 4. 模块契约

### 4.1 Forecast Engine

**输入**：

```json
{
  "store_id": "string",
  "sku_id": "string",
  "horizon_days": 30,
  "historical_sales": [
    { "date": "YYYY-MM-DD", "quantity": 12, "price": 15000, "promotion": false }
  ],
  "calendar_events": ["ramadan", "lebaran", "harbolnas"],
  "island_region": "java|sumatra|kalimantan|sulawesi|papua",
  "sentiment_signals": [
    { "category": "fashion", "heat_index": 0.72, "date": "YYYY-MM-DD" }
  ],
  "store_profile": {
    "store_size_sqm": 2000,
    "target_sku_count": 12000,
    "fresh_ratio": 0.28,
    "shelf_layers": 6
  }
}
```

**输出**：

```json
{
  "forecast_id": "uuid",
  "store_id": "string",
  "sku_id": "string",
  "generated_at": "ISO8601",
  "horizon": {
    "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD",
    "daily_forecast": [
      { "date": "YYYY-MM-DD", "demand_mean": 14.2, "demand_p90": 22.0 }
    ]
  },
  "safety_stock": 18,
  "reorder_point": 42,
  "suggested_order_quantity": 60,
  "confidence": 0.87,
  "model_version": "prophet-lgbm-v0.1"
}
```

**约束**：
- 预测粒度：Store × SKU × Day
- 最小历史数据要求：90 天
- 斋月窗口内自动启用节庆特征

### 4.2 Replenishment Engine

**输入**：

```json
{
  "store_id": "string",
  "sku_id": "string",
  "current_inventory": 8,
  "reorder_point": 42,
  "safety_stock": 18,
  "effective_lead_time_days": 7.5,
  "lead_time_variance_days": 2.3,
  "island_region": "sulawesi",
  "shelf_life_days": 5,
  "fresh_flag": true
}
```

**输出**：

```json
{
  "replenishment_id": "uuid",
  "store_id": "string",
  "sku_id": "string",
  "action": "ORDER|HOLD|URGENT",
  "order_quantity": 60,
  "priority": "HIGH",
  "reason": "stock_below_reorder_point_with_fresh_constraint",
  "suggested_delivery_window": "YYYY-MM-DD to YYYY-MM-DD",
  "promotion_trigger": null
}
```

**约束**：
- 有效提前期公式：`LT_eff = LT_mean + k × σ_LT`，k 由 `island_region` 决定
- 生鲜 SKU（`fresh_flag = true`）的 `order_quantity` 受 `shelf_life_days` 约束
- 斋月前 6–8 周自动提升节庆品类补货优先级

### 4.3 Space Optimizer (MILP)

**输入**：

```json
{
  "store_id": "string",
  "total_facings": 480,
  "categories": [
    {
      "category_id": "beverages",
      "sku_count": 240,
      "avg_gross_margin": 0.32,
      "avg_daily_turnover": 18.5,
      "avg_facing_width_m": 0.25,
      "min_facings_required": 20
    }
  ],
  "constraints": {
    "max_facings_per_category": { "beverages": 120 },
    "fresh_ratio_min": 0.25
  }
}
```

**输出**：

```json
{
  "planogram_id": "uuid",
  "store_id": "string",
  "generated_at": "ISO8601",
  "allocations": [
    {
      "category_id": "beverages",
      "allocated_facings": 96,
      "expected_daily_profit": 1250000,
      "stockout_risk": 0.03
    }
  ],
  "objective_value": 8450000,
  "solver_status": "OPTIMAL"
}
```

### 4.4 Lifecycle Manager

**输入**：

```json
{
  "store_id": "string",
  "inventory_batches": [
    {
      "batch_id": "uuid",
      "sku_id": "string",
      "quantity": 24,
      "expiry_date": "YYYY-MM-DD",
      "received_date": "YYYY-MM-DD",
      "facing_id": "string"
    }
  ],
  "today": "YYYY-MM-DD"
}
```

**输出**：

```json
{
  "actions": [
    {
      "batch_id": "uuid",
      "sku_id": "string",
      "action": "BUNDLE_PROMOTION|MARKDOWN|FEFO_PRIORITY|HOLD",
      "reason": "expires_in_2_days",
      "suggested_discount_pct": 15,
      "bundle_with_category": "vegetables"
    }
  ]
}
```

**约束**：
- 剩余保质期 ≤ 2 天 → 触发捆绑促销（非纯降价）
- 斋月前 4 周 → 礼品装 SKU 阶梯折扣（10–15% → 25–30%）
- 清真认证 SKU 优先跨品类捆绑

---

## 5. 技术选型

| 层级 | 组件 | 选型 | 理由 |
|---|---|---|---|
| 空间数据 | 数据库 | PostgreSQL 15 + PostGIS | 原生空间索引，支持 Zone/Fixture 几何查询 |
| 预测 | 时序模型 | Prophet | 原生 `yearly_seasonality` + `holiday` 组件 |
| 预测 | 梯度提升 | LightGBM | 处理节庆 × 价格 × 促销的非线性交互 |
| 空间优化 | 求解器 | OR-Tools (MILP) | 开源，支持整数规划与约束编程 |
| 3D 渲染 | 前端 | React Three Fiber + Drei | React 生态，声明式 3D 场景 |
| 2D 编辑 | 前端 | Konva / Fabric.js | Canvas 级平面图编辑，真实米制坐标 |
| 实时通信 | 后端 | WebSocket (ws) | 补货模拟与 3D 视图的实时同步 |
| 部署 | 托管 | Cloudflare Pages + Railway | 前端静态，后端按需伸缩 |

---

## 6. 数据一致性策略

**空间实体**：`Store → Zone → Fixture → ShelfLevel → Facing` 采用树形结构，通过 `parent_id` 关联。Facing 是叶子节点，携带 `sku_id` 外键。

**动态数据**：`InventoryBatch`、`SalesEvent`、`DemandForecast` 以 append-only 方式写入，通过 `(store_id, sku_id, facing_id)` 三元组关联到空间实体。

**版本控制**：Planogram 和 Forecast 均带 `version` 字段，便于回溯和 A/B 对比。

**冲突处理**：当同一 Facing 被多个 SKU 声明时，以最新 `updated_at` 为准，并在 `conflict_log` 中记录。
