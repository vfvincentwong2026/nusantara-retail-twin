# Store Scale Benchmarks

> Nusantara Retail Twin 三档门店规模参数基准的完整推导与数据来源。
> 版本：v0.1 · 最后更新：2026-10

---

## 1. 为什么需要基准参数

Nusantara Retail Twin 的核心能力是“让货架展示面积直接参与补货决策”。要让这个能力可复现、可对比，必须有标准化的门店规模基准。

三档门店（500㎡ / 2,000㎡ / 5,000㎡）覆盖印尼现代零售的主流业态：

| 规模 | 对应业态 | 对标品牌 | 核心场景 |
|---|---|---|---|
| 500㎡ | Minimarket | Alfamidi、Indomaret、Alfamart | 社区、办公区、加油站 |
| 2,000㎡ | Supermarket | Alfamidi Super、Super Indo | 购物中心、商圈 |
| 5,000㎡ | Hypermarket | Hypermart、Transmart、Lotte Mart | 大型枢纽、郊区仓储 |

---

## 2. 数据来源与推导方法

### 2.1 来源优先级

参数来源按可信度排序：

| 优先级 | 来源类型 | 示例 | 说明 |
|---|---|---|---|
| 1 | 上市公司财报 / 管理层演示 | MIDI Management Presentation | 经审计，口径一致 |
| 2 | 官方加盟资料 | Alfamidiku.com | 运营商自披露 |
| 3 | 行业法规 | Perpres No. 112/2007 | 法定分类标准 |
| 4 | 学术研究 | ITS / UI 零售业态论文 | 方法论可验证 |
| 5 | 行业媒体 | ANTARA、Kontan | 单点数据，需交叉验证 |
| 6 | 第三方报告 | WWF Indonesia Retail Ecosystem | 调研汇总 |

### 2.2 交叉验证方法

每个参数至少两个来源交叉验证。当数据冲突时，优先采用上市公司披露数据，其次采用法规定义。

---

## 3. 500㎡ Minimarket 基准

### 3.1 SKU 数量

| 来源 | 数值 | 备注 |
|---|---|---|
| MIDI Management Presentation 2023 Q2 | ~7,000 SKU | Alfamidi 标准店 |
| Alfamidiku.com 加盟资料 | ~7,000 SKU（200-400㎡） | 官方披露 |
| 印尼上市公司年报 | ~6,000 SKU（60 型）| 200-250㎡ |
| 学术论文（ITS Repository） | 3,000-4,000 SKU | Minimarket 定义 |
| Harian Haluan 行业报道 | ~3,000 item | 小规模 Minimarket |

**基准采用值：4,000-6,000 SKU。**

推导逻辑：Alfamidi 作为印尼 Minimarket 头部品牌，其 200-400㎡ 门店的 SKU 约 7,000，但 500㎡ 门店并非所有品牌都达到该密度。学术定义中 Minimarket 的 SKU 上限为 5,000。取 4,000-6,000 作为区间，覆盖从基础 Minimarket 到 Alfamidi 级门店的跨度。

### 3.2 生鲜面积占比

| 来源 | 数值 | 备注 |
|---|---|---|
| MIDI Management Presentation 2023 Q2 | ~25% | Alfamidi / Alfamidi Super |
| Alfamidiku.com 加盟资料 | 20-25㎡ Fresh / 600-650㎡ 总面积 | 约 3-4% |
| 学术研究 | 印尼 Minimarket 生鲜占比受限 | 受冷链成本约束 |

**基准采用值：15-20%。**

推导逻辑：Alfamidi 官方披露的生鲜面积占比为 25% 销售面积，但这是品牌差异化策略的结果。学术研究和 WWF 报告指出，许多 Minimarket（如 Alfamart、Borma）因空间和冷链限制不销售新鲜蔬果。基准值取 15-20%，反映行业平均而非头部品牌水平。

### 3.3 货架与 Facings

基于 Perpres No. 112/2007 对 Minimarket 的定义（最大 400㎡），500㎡ 门店已超出法定 Minimarket 上限，属于“大型 Minimarket”或“小型 Supermarket”范畴。

| 参数 | 推导值 | 推导方法 |
|---|---|---|
| 货架数量 | 40-50 | 面积 / 单货架占地 ≈ 500 / 12 |
| 货架层数 | 4-5 层 | 受天花板高度和视线约束 |
| 单货架 Facings | 25-30 | 货架长度 3m / Facings 宽度 0.10-0.12m |
| 总 Facings | 1,000-1,500 | 货架数 × 单货架 Facings |

---

## 4. 2,000㎡ Supermarket 基准

### 4.1 SKU 数量

| 来源 | 数值 | 备注 |
|---|---|---|
| MIDI Management Presentation 2022 Q4 | ~12,000 SKU | Alfamidi Super（≥500㎡） |
| MIDI Management Presentation 2023 Q2 | ~10,000 SKU | Alfamidi Super |
| Alfamidiku.com 加盟资料 | ~12,000 SKU | 600-650㎡ Supermarket 型 |
| 学术论文（ITS Repository） | 15,000-60,000 SKU | Supermarket 定义 |
| Perpres No. 112/2007 | 5,000-25,000 item | Supermarket 法定范围 |

**基准采用值：10,000-18,000 SKU。**

推导逻辑：Alfamidi Super 的官方披露在 10,000-12,000 SKU 区间，但该品牌门店面积仅略超 500㎡，远小于 2,000㎡。2,000㎡ 门店的 SKU 容量应显著高于 500㎡ 级。学术定义中 Supermarket 的 SKU 上限为 60,000，但印尼市场的实际运营密度低于欧美。取 10,000-18,000 作为区间，覆盖从 Alfamidi Super 级到大型 Super Indo 的跨度。

### 4.2 生鲜面积占比

| 来源 | 数值 | 备注 |
|---|---|---|
| MIDI Management Presentation 2023 Q2 | ~25% | Alfamidi Super |
| WWF Indonesia 报告 | 50%（Nanakam Fresh Market） | 定位高端鲜食 |
| WWF Indonesia 报告 | 40%+ 收入来自 Fresh（Ranch Market）| 高端进口超市 |
| 行业惯例 | 25-35% | 标准 Supermarket |

**基准采用值：25-30%。**

推导逻辑：25% 是印尼现代超市生鲜面积的锚点（Alfamidi Super 官方数据）。WWF 报告显示高端定位门店（Nanakam、Ranch Market）可达 40-50%，但基准应反映行业主流而非高端特例。取 25-30% 覆盖标准 Supermarket 到偏鲜食定位门店。

### 4.3 货架与 Facings

| 参数 | 推导值 | 推导方法 |
|---|---|---|
| 货架数量 | 110-130 | 面积 / 单货架占地 ≈ 2000 / 16 |
| 货架层数 | 5-6 层 | Supermarket 标准 |
| 单货架 Facings | 30-36 | 货架长度 4m / Facings 宽度 0.11-0.13m |
| 总 Facings | 3,500-4,700 | 货架数 × 单货架 Facings |

---

## 5. 5,000㎡ Hypermarket 基准

### 5.1 SKU 数量

| 来源 | 数值 | 备注 |
|---|---|---|
| Hypermart Ketapang（ANTARA 2015） | 30,000 SKU / 4,500㎡ | 单店披露 |
| Hypermart Sampit（Kontan 2013） | 45,000 SKU / 5,000㎡ | 单店披露 |
| Hypermart Balikpapan（ANTARA 2015） | 35,000 SKU / 3,200㎡ | 单店披露 |
| Hypermart 官网 | >30,000 SKU | 品牌整体 |
| Hypermart 战略调整 | 50,000-60,000 → 目标 2,800-3,000㎡ | 投资者报道 |
| Perpres No. 112/2007 | >25,000 item | Hypermarket 法定下限 |

**基准采用值：28,000-40,000 SKU。**

推导逻辑：Hypermart 单店披露数据集中在 30,000-45,000 SKU（面积 3,200-5,000㎡）。Hypermart 官网声明品牌整体 >30,000 SKU。投资者报道显示品牌历史上 SKU 曾达 50,000-60,000，但正在战略缩减。取 28,000-40,000 作为区间，反映当前运营状态而非历史峰值。

### 5.2 生鲜面积占比

| 来源 | 数值 | 备注 |
|---|---|---|
| WWF Indonesia 报告 | 30-35% | Hypermarket 生鲜区 |
| Hypermart 门店描述 | 水果、蔬菜、鲜肉、海鲜 | 多品类覆盖 |
| 行业惯例 | 30-40% | 大型卖场 |

**基准采用值：30-35%。**

推导逻辑：Hypermarket 的生鲜占比通常高于 Supermarket，因面积充裕且客群更广泛。WWF 报告显示印尼 Hypermarket 的生鲜区约占 30-35%。Hypermart 门店描述确认覆盖水果、蔬菜、鲜肉、海鲜等多品类。

### 5.3 货架与 Facings

| 参数 | 推导值 | 推导方法 |
|---|---|---|
| 货架数量 | 240-280 | 面积 / 单货架占地 ≈ 5000 / 19 |
| 货架层数 | 6-7 层 | Hypermarket 标准 |
| 单货架 Facings | 36-42 | 货架长度 5m / Facings 宽度 0.12-0.14m |
| 总 Facings | 9,000-12,000 | 货架数 × 单货架 Facings |

---

## 6. 三档对比总览

| 参数 | 500㎡ | 2,000㎡ | 5,000㎡ |
|---|---|---|---|
| 印尼对应业态 | Minimarket | Supermarket | Hypermarket |
| SKU 数量 | 4,000-6,000 | 10,000-18,000 | 28,000-40,000 |
| SKU 密度 (SKU/㎡) | 8-12 | 5-9 | 6-8 |
| 食品销售占比 | 85-90% | 70-80% | 55-65% |
| 生鲜面积占比 | 15-20% | 25-30% | 30-35% |
| 清真认证覆盖率 | >95% | >90% | >85% |
| 货架数量 | 40-50 | 110-130 | 240-280 |
| 货架层数 | 4-5 | 5-6 | 6-7 |
| 总 Facings | 1,000-1,500 | 3,500-4,700 | 9,000-12,000 |
| 主通道宽度 | 1.8-2.2m | 2.5-3.5m | 3-4m |
| 典型补货频率 | 每周 2-3 次 | 每周 3-5 次 | 每日/隔日 |

**关键差异说明**：

- **SKU 密度**：500㎡ 门店的 SKU 密度最高（8-12/㎡），因为小面积门店需要更高的坪效。5,000㎡ 门店密度最低（6-8/㎡），因大量面积分配给生鲜、通道和体验区。
- **生鲜占比**：从 Minimarket 到 Hypermarket 递增，反映面积和冷链能力对生鲜品类的约束。
- **清真认证覆盖率**：规模越小，覆盖率越高（>95%），因为小门店的 SKU 集中于标准化包装食品，清真认证更易覆盖。

---

## 7. 种子数据生成

三档门店的种子数据由 `nrt seed` 命令生成：

```bash
nrt seed --store-size 500 --region java --output ./workspace
nrt seed --store-size 2000 --region java --output ./workspace
nrt seed --store-size 5000 --region java --output ./workspace
```

生成的 JSON 文件位于 `data/seeds/`，包含：

```json
{
  "store_profile": { "store_size_sqm": 2000, "island_region": "java", ... },
  "zones": [ { "zone_name": "生鲜区", "zone_type": "fresh", "heat_value": 0.85 } ],
  "fixtures": [ { "fixture_label": "F-001", "position_x": 2.5, "position_y": 10.0 } ],
  "shelf_levels": [ { "level_number": 1, "is_eye_level": false } ],
  "facings": [ { "facing_index": 1, "facing_width_m": 0.12, "sku_code": "SKU-001" } ]
}
```

---

## 8. 参考来源

| 来源 | 类型 | 引用参数 |
|---|---|---|
| MIDI Management Presentation 2023 Q2 | 上市公司披露 | Alfamidi SKU 7,000，Alfamidi Super SKU 10,000-12,000 |
| MIDI Management Presentation 2022 Q4 | 上市公司披露 | Alfamidi Super SKU 12,000 |
| Alfamidiku.com 加盟资料 | 官方运营资料 | Supermarket 型 12,000 SKU，600-650㎡ |
| Hypermart Ketapang（ANTARA 2015） | 行业媒体 | 4,500㎡ / 30,000 SKU |
| Hypermart Sampit（Kontan 2013） | 行业媒体 | 5,000㎡ / 45,000 SKU |
| Hypermart Balikpapan（ANTARA 2015） | 行业媒体 | 3,200㎡ / 35,000 SKU |
| ITS Repository 学术论文 | 学术研究 | Minimarket 3,000-4,000 SKU，Supermarket 15,000-60,000 SKU |
| WWF Indonesia Retail Ecosystem Report | 第三方调研 | 生鲜面积占比，门店运营实践 |
| Perpres No. 112/2007 | 法规 | Minimarket / Supermarket / Hypermarket 分类标准 |

---

## 9. 更新日志

| 日期 | 版本 | 变更 |
|---|---|---|
| 2026-10 | v0.1 | 初始版本，覆盖三档门店的参数推导与来源 |
