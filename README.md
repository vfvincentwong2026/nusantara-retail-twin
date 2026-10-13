# nusantara-retail-twin
面向印尼与东南亚市场的零售空间数字孪生与智能补货模拟系统，融合 3D 平面图/货架图、SKU 去化、需求预测、舆情信号、节日季节因子、空间-存量优化与商品生命周期管理。
# Nusantara Retail Twin

> **Retail Space Digital Twin & Intelligent Replenishment Simulator for Indonesia and Southeast Asia**
>
> 面向印尼与东南亚市场的零售空间数字孪生与智能补货模拟系统

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Node 18+](https://img.shields.io/badge/node-18%2B-green.svg)](https://nodejs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B%20%2B%20PostGIS-336791.svg)](https://postgis.net/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Status](https://img.shields.io/badge/status-early%20development-orange.svg)](#roadmap)

---

## 目录

- [为什么做这个项目](#为什么做这个项目)
- [核心能力](#核心能力)
- [系统架构](#系统架构)
- [三档门店规模基准](#三档门店规模基准)
- [印尼市场适配层](#印尼市场适配层)
- [快速开始](#快速开始)
- [仓库结构](#仓库结构)
- [核心模块](#核心模块)
- [数据模型](#数据模型)
- [Roadmap](#roadmap)
- [技术栈](#技术栈)
- [贡献指南](#贡献指南)
- [许可证](#许可证)
- [致谢](#致谢)

---

## 为什么做这个项目

东南亚零售业正在经历一轮结构性的数字化升级。印尼作为区域最大市场，面临三个独特挑战：

1. **空间与存量脱节**：门店平面图、货架图与实时库存系统彼此独立，陈列面积无法驱动补货决策。
2. **节律非线性**：斋月与开斋节构成年度销售主轴，通用西方零售预测模型在印尼市场频繁失效。
3. **跨岛物流方差**：从 Java 到 Papua，提前期的不确定性远超均值本身，“平均提前期”是一个误导性指标。

**Nusantara Retail Twin** 将这三个问题放进同一个数字孪生框架：

> **空间即数据，数据即决策。**

该项目不是沃尔玛系统的复刻，而是一个面向群岛市场的、可组合、可拆分的开源模拟框架。

---

## 核心能力

| 能力域 | 说明 | 状态 |
|---|---|---|
| 3D 空间可视化 | 基于真实米制坐标的平面图与货架图，2D/3D 单一数据源驱动 | 设计中 |
| SKU 去化建模 | 按 Facings × 层数 × SKU 密度计算展示面积与存量上限 | 设计中 |
| 需求预测引擎 | 斋月/开斋节、Harbolnas、Mudik 返乡效应的季节性建模 | 设计中 |
| 智能补货 | 基于提前期方差的安全库存与再订货点计算 | 设计中 |
| 空间-存量优化 | MILP 求解货架空间分配，平衡单位面积利润与缺货风险 | 设计中 |
| 舆情信号接入 | 社交媒体热点与情感趋势作为外生需求变量 | 设计中 |
| 生命周期管理 | FEFO 批次分配、临期促销触发、清真认证链路 | 设计中 |
| 多规模门店模拟 | 500㎡ / 2,000㎡ / 5,000㎡ 三档基准，可扩展 | 设计中 |

---

## 系统架构

```text
+-----------------------------+
|         数据层              |
|  PostgreSQL + PostGIS       |
|  统一数据模型 / 门店种子     |
+--------------+--------------+
               |
               v
+-----------------------------+
|         计算层              |
|  需求预测 / 补货 / 空间优化  |
|  生命周期 / 舆情信号         |
+--------------+--------------+
               |
               v
+-----------------------------+
|         展示层              |
|  3D 数字孪生 / 控制塔仪表盘  |
+-----------------------------+
```

设计原则：空间、库存、销售、舆情四类数据通过 `store_id` + `sku_id` + `fixture_id` 三元组关联，任一层可独立替换。

---

## 三档门店规模基准

系统内置三档门店形态，覆盖印尼现代零售主流业态：

| 参数 | 500㎡ 社区店 | 2,000㎡ 标准店 | 5,000㎡ 大卖场 |
|---|---|---|---|
| 印尼对应业态 | Minimarket / Alfamidi 级 | Supermarket / Alfasupermarket 级 | Hypermarket / Hypermart 级 |
| SKU 数量 | 4,000 – 6,000 | 10,000 – 18,000 | 28,000 – 40,000 |
| 食品销售占比 | 85 – 90% | 70 – 80% | 55 – 65% |
| 生鲜面积占比 | 15 – 20% | 25 – 30% | 30 – 35% |
| 清真认证 SKU 覆盖率 | > 95% | > 90% | > 85% |
| 典型补货频率 | 每周 2–3 次 | 每周 3–5 次 | 每日 / 隔日 |
| 货架层数 | 4 – 5 层 | 5 – 6 层 | 6 – 7 层 |
| 主通道宽度 | 1.8 – 2.2 m | 2.5 – 3.5 m | 3 – 4 m |

三档种子数据位于 `data/seeds/`，可通过 CLI 一键生成：

```bash
nrt seed --store-size 2000 --region java --output ./workspace
```

---

## 印尼市场适配层

系统的印尼化不是语言翻译，而是**节律、物流、合规**三个维度的本地化。

### 节庆主轴

斋月与开斋节构成年度销售峰值。预测引擎的核心外生变量序列：

| 节日 | 影响窗口 | 权重 |
|---|---|---|
| 斋月 / 开斋节 | 6 周 | 极高 |
| Harbolnas（12.12） | 2 周 | 高 |
| 开斋节后返校季 | 4 周 | 高 |
| 独立日（8.17） | 1 周 | 中 |
| 年末假期 | 3 周 | 高 |

### 跨岛物流方差

补货引擎不以“平均提前期”为输入，而以 `LT_mean + k × σ_LT` 为有效提前期：

| 岛屿区域 | 系数 k | 含义 |
|---|---|---|
| Java | 0.5 | 供应链密集，方差小 |
| Sumatra / Kalimantan | 1.0 | 中等不确定性 |
| Sulawesi / Papua | 1.5 | 高方差，需冗余缓冲 |

### Mudik 返乡效应

开斋节前一周城市门店需求骤降，开斋节后外岛门店需求骤升。每个 `StoreProfile` 携带 `island_region` 与 `mudik_offset` 参数，预测时按区域独立偏移。

### 合规与认证

- `halal_certified`：印尼市场准入性字段，参与促销推荐与信任传递逻辑。
- `local_content_ratio`：受进口法规影响，影响采购与定价模型。
- QRIS 支付渗透：`qris_enabled` 门店赋予更高的促销弹性系数。

---

## 快速开始

### 前置依赖

- Python ≥ 3.10
- Node.js ≥ 18
- PostgreSQL ≥ 15 + PostGIS
- Docker（推荐）

### 一键启动

```bash
git clone https://github.com/YOUR_ORG/nusantara-retail-twin.git
cd nusantara-retail-twin

cp .env.example .env
docker compose up -d db

make install
make migrate
make seed
make dev
```

访问 `http://localhost:5173` 查看 3D 数字孪生视图。

### 生成一个 2,000㎡ 雅加达门店

```python
from nrt import StoreProfile, RetailTwin

store = StoreProfile(
    store_size_sqm=2000,
    island_region="java",
    target_sku_count=12000,
    fresh_ratio=0.28,
    qris_enabled=True,
)

twin = RetailTwin(store)
twin.load_planogram()
twin.forecast(horizon_days=30, include_ramadan=True)
twin.replenish()
twin.render_3d()
```

---

## 仓库结构

```text
nusantara-retail-twin/
├── data/
│   ├── schemas/
│   └── seeds/
│       ├── store_500sqm.json
│       ├── store_2000sqm.json
│       └── store_5000sqm.json
├── src/
│   ├── nrt/
│   │   ├── model/
│   │   ├── forecast/
│   │   ├── replenishment/
│   │   ├── space/
│   │   ├── lifecycle/
│   │   ├── sentiment/
│   │   └── calendar/
│   └── cli/
├── web/
│   ├── floorplan/
│   ├── three/
│   └── dashboard/
├── tests/
├── docs/
│   ├── architecture.md
│   ├── store-scale-benchmarks.md
│   ├── indonesia-market-notes.md
│   └── data-model.md
├── docker-compose.yml
├── Makefile
├── pyproject.toml
└── README.md
```

---

## 核心模块

### 3D 空间可视化

基于真实米制坐标而非像素，2D 平面图与 3D 视图共享同一份 JSON 文档。每个 `Zone` 携带 `heatValue` 字段，可对接去化速度数据实现热力图覆盖。

- 按 `store_size_sqm × sku_density × shelf_layers` 动态生成货架。
- 支持 Facings 粒度的缺货、临期、推荐补货量渲染。

### 需求预测引擎

- 特征工程：季节性、促销、价格、节庆、天气、滞后需求、舆情信号。
- 模型：Prophet + 梯度提升。
- 输出：按 Store × SKU 粒度的需求分布、安全库存、再订货点。

### 补货引擎

- 有效提前期：`LT_mean + k × σ_LT`。
- 斋月前置补货窗口：斋月前 6–8 周完成首轮，开斋节前 2 周完成次轮。
- 生鲜品类强制高频补货。

### 空间-存量优化

- 使用 MILP 求解货架空间分配。
- 目标函数：单位面积利润最大化 ↔ 缺货风险最小化。
- 输出回写 Planogram，作为预测引擎的约束条件。

### 生命周期管理

- FEFO 批次分配，剩余保质期驱动促销触发。
- 临期生鲜触发捆绑促销。
- 斋月前礼品装阶梯折扣。

### 舆情信号

- 聚合多平台热点与情感趋势。
- 输出品类级热度指数，作为预测引擎的外生变量。

---

## 数据模型

核心实体关系：

```text
Store
  └── Zone
        └── Fixture
              └── ShelfLevel
                    └── Facing
                          └── SKU
                                ├── InventoryBatch
                                ├── SalesEvent
                                └── DemandForecast

Store
  └── SentimentSignal
```

所有动态数据通过 `(store_id, sku_id, fixture_id)` 关联，确保空间位置可直接参与预测与补货计算。

---

## Roadmap

| 阶段 | 目标 | 状态 |
|---|---|---|
| v0.1 | 统一数据模型 + 三档门店种子数据 + 基础 3D 渲染 | 进行中 |
| v0.2 | 预测引擎接入 + 3D 视图叠加缺货风险层 | 计划中 |
| v0.3 | 补货引擎 + 空间-存量 MILP 优化 | 计划中 |
| v0.4 | 生命周期管理 + 舆情信号接入 | 计划中 |
| v0.5 | 合成消费者沙盒 | 计划中 |
| v1.0 | 端到端闭环 + 区域扩展 | 计划中 |

---

## 技术栈

- **后端**：Python · FastAPI · PostgreSQL · PostGIS · Prophet · OR-Tools
- **前端**：TypeScript · React · Three.js · Vite
- **基础设施**：Docker · Makefile · GitHub Actions
- **数据**：印尼节庆日历 · 门店种子 JSON · 舆情信号适配器

---

## 贡献指南

欢迎以任何形式参与：

- 提交 Issue 报告 Bug 或提出功能建议
- 贡献新的门店种子数据或区域适配
- 完善 `docs/` 下的架构与市场文档
- 帮助扩展至马来西亚、泰国、越南等市场

请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解提交流程。

---

## 许可证

本项目采用 [MIT License](LICENSE) 发布。

---

## 致谢

- 灵感来源于开源零售、供应链与数字孪生社区。
- 印尼市场参数参考 APPBI、公开财报与行业研究。
- 如果你正在东南亚零售业工作，欢迎分享实战反馈。

---

**Nusantara Retail Twin** · 空间即数据，数据即决策

Made with 🛒 for Indonesia & Southeast Asia
