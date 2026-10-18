<div align="center">

# 🏬 Nusantara Retail Twin
### 零售空间数字孪生与智能补货模拟平台
**Retail Space Digital Twin & Intelligent Replenishment Simulator**

<br />

<p>
  <img src="https://img.shields.io/badge/License-MIT-22C55E?style=flat-square&logo=opensourceinitiative&logoColor=white" alt="License" />
  <img src="https://img.shields.io/badge/PRs-Welcome-2563EB?style=flat-square&logo=github&logoColor=white" alt="PRs Welcome" />
  <img src="https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black" alt="React" />
  <img src="https://img.shields.io/badge/Three.js-r160-000000?style=flat-square&logo=three.js&logoColor=white" alt="Three.js" />
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/PostgreSQL-15+-336791?style=flat-square&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <a href="https://nusantara-retail-twin.pages.dev"><img src="https://img.shields.io/badge/Live_Demo-Cloudflare-F38020?style=flat-square&logo=cloudflare&logoColor=white" alt="Live Demo" /></a>
</p>

<p>
  <img src="./docs/assets/demo.gif" alt="Nusantara Retail Twin — 3D store digital twin, planogram heatmap, SKU flow, replenishment simulation, Ramadan demand curve" width="880" />
</p>

</div>

---

> 🛒 **500㎡ 社区店 · 2,000㎡ 标准店 · 5,000㎡ 大卖场**
> 一个面向印尼与东南亚市场的零售空间数字孪生平台。
> 从平面图到货架图，从 SKU 去化到斋月需求，从空间面积到补货决策，一站式模拟。
>
> *Multi-Scale 3D Digital Twin · SKU Decomposition · Ramadan-aware Forecast · Space-Inventory Optimization*

---

## 📖 项目简介 / Introduction

**Nusantara Retail Twin** 是一个开源的零售空间数字孪生与智能补货模拟平台。它将 3D 门店空间、货架图、SKU 库存、销售数据、需求预测、舆情信号与商品生命周期管理整合到同一套数据模型，让"货架展示面积"直接参与"补货决策"。

平台内置 **500㎡ / 2,000㎡ / 5,000㎡** 三档印尼主流门店形态，每档均配备 **2D 平面图**、**3D 数字孪生空间演示**、**SKU 去化视图**、**智能补货模拟器** 与 **空间-存量优化引擎**。

系统深度适配 **斋月 / 开斋节销售主轴**、**Mudik 返乡效应**、**跨岛物流方差** 与 **清真认证链路**，并预留与多智能体决策引擎的联动接口。

---

## 🌐 独立部署与矩阵生态 / Project Matrix

本项目独立部署于 Cloudflare Pages，与东南亚零售数字化生态中的其他开源项目形成"空间 + 决策"双子星矩阵。

| 项目名称 | 线上演示地址 | 核心定位 |
| :--- | :--- | :--- |
| **Nusantara Retail Twin** | [nusantara-retail-twin.pages.dev](https://nusantara-retail-twin.pages.dev) | 零售空间数字孪生、SKU 去化与智能补货模拟 |
| **Agent-Fleet-Spec** *(planned)* | *TBD* | 多智能体零售决策协议与事件总线 |

---

## 🏙 市场背景：为什么印尼需要零售数字孪生

在设计任何零售补货系统前，必须面对印尼市场的三个底层现实。它们决定了这套系统与西方零售模型必须不同。

### 🇮🇩 节律主轴：斋月与开斋节
- **核心事实**：斋月与开斋节构成年度销售峰值，APPBI 数据显示购物中心客流同比增长 **10–15%**，贡献了年度利润的极高比例。
- **系统响应**：需求预测引擎以斋月为绝对主轴，前置补货窗口提前 **6–8 周**，礼品装 SKU 在斋月前 4 周启动阶梯折扣。

### 🚚 跨岛物流：方差比均值更重要
- **核心事实**：从 Java 到 Papua，提前期的不确定性远超均值本身。Gorontalo 等外岛的补货延迟问题尤为突出。
- **系统响应**：补货引擎以 `LT_mean + k × σ_LT` 为有效提前期，Java `k=0.5`、Sumatra/Kalimantan `k=1.0`、Sulawesi/Papua `k=1.5`。

### ✅ 合规与信任：清真认证是准入线
- **核心事实**：清真认证（Halal）是印尼市场的准入性字段，覆盖率直接影响 SKU 可售范围与促销推荐。
- **系统响应**：`halal_certified` 参与预测与促销逻辑，滞销清真 SKU 优先与高周转品类跨品类捆绑，利用信任传递效应。

---

## 🎯 三种核心门店规模 / Core Store Scales

| 门店代号 | 印尼对应业态 | SKU 数量 | 生鲜占比 | 典型补货频率 | 最佳适配场景 |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **500㎡** | Minimarket / Alfamidi 级 | 4,000 – 6,000 | 15–20% | 每周 2–3 次 | 社区、办公区、加油站 |
| **2,000㎡** | Supermarket / Alfasupermarket 级 | 10,000 – 18,000 | 25–30% | 每周 3–5 次 | 购物中心、商圈 |
| **5,000㎡** | Hypermarket / Hypermart 级 | 28,000 – 40,000 | 30–35% | 每日 / 隔日 | 大型枢纽、郊区仓储 |

---

## 🗺 空间演示与平台模块

### 🚀 3D 数字孪生与平面图沙盘
- **双模视角**：支持室内卖场与户外停车场入口切换。
- **三档规模**：一键切换 500㎡ / 2,000㎡ / 5,000㎡ 门店布局。
- **全链路交互**：支持顾客动线、货架补货、临期促销、SKU 缺货高亮全动画演示。
- **热力覆盖**：Zone 级 `heatValue` 对接去化速度数据，高/低去化区域颜色直观呈现。

### 📊 核心功能模块
1. **门店规模选择器**：一键切换 3 档规模，直观对比 SKU 密度、货架层数、通道宽度。
2. **货架图编辑器**：2D 平面图与 3D 视图共享同一份 JSON，编辑一次双端同步。
3. **SKU 去化大屏**：实时监控 Facings 粒度库存、去化速度、缺货风险与补货建议。
4. **智能补货模拟器**：动态调整提前期方差、生鲜占比、节庆窗口，秒级输出补货方案。
5. **空间-存量优化器**：MILP 求解货架空间分配，平衡单位面积利润与缺货风险。
6. **生命周期看板**：FEFO 批次分配、临期促销触发、清真认证链路可视化。

---

## 🔮 需求预测引擎 / Forecast Engine

Nusantara Retail Twin 的预测引擎以 **斋月 / 开斋节** 为绝对主轴，构建印尼本地化特征工程。

### 📅 节庆外生变量

| 节日 | 影响窗口 | 权重 |
| :--- | :---: | :---: |
| 斋月 / 开斋节 | 6 周 | 🔴 极高 |
| Harbolnas（12.12） | 2 周 | 🟠 高 |
| 开斋节后返校季 | 4 周 | 🟠 高 |
| 独立日（8.17） | 1 周 | 🟡 中 |
| 年末假期 | 3 周 | 🟠 高 |

### 🔁 Mudik 返乡效应建模
开斋节前一周城市门店需求骤降，开斋节后外岛门店需求骤升。每个 `StoreProfile` 携带 `island_region` 与 `mudik_offset` 参数，预测时按区域独立偏移。

### 📡 舆情信号接入
聚合多平台热点与情感趋势，输出品类级热度指数，作为预测引擎的外生变量。清真认证 SKU 的情感信号赋予更高信任权重。

---

## 🧮 空间-存量优化 / Space-Inventory Optimization

Nusantara Retail Twin 的核心差异化能力：**让货架展示面积直接参与补货决策。**

| 输入 | 计算 | 输出 |
| :--- | :--- | :--- |
| `store_size_sqm` × `sku_density` | 货架数量与 Facings 数 | Planogram 建议 |
| `shelf_layers` × `facing_width_m` | 单 Facings 库存上限 | 补货量约束 |
| `fresh_ratio` × `shelf_life_days` | FEFO 触发阈值 | 促销建议 |
| `heatValue` × `turnover_rate` | 单位面积去化速度 | 货架分配权重 |

优化目标函数由 MILP 求解，在 **单位面积利润最大化** 与 **缺货风险最小化** 之间动态权衡。

---

## 🔗 多智能体联动 / Agent Integration

Nusantara Retail Twin 负责物理世界的 **空间、库存与预测**，预留接口对接多智能体决策引擎：

- 🤖 **需求预测 Agent**：基于历史销售、天气、节庆预测分时需求。
- 📦 **补货调度 Agent**：动态指派跨岛补货优先级与运输路径。
- 💰 **动态定价 Agent**：根据去化速度、剩余保质期、竞争价格自动调价。
- 📣 **促销触发 Agent**：临期生鲜触发捆绑，斋月前礼品装触发阶梯折扣。

**协议对齐 / Protocol alignment**：预留 Agent-Fleet-Spec 风格的 `STATE_EVENT` 信封接口，智能体身份采用 `agent://{trust-domain}/{fleet}/{role}/{instance}` URI。

---

## ☁️ Cloudflare Pages 部署 / Deployment

**方式一：GitHub Actions 自动部署（推荐）**

每次 push 到 `main` 自动构建并部署（`.github/workflows/deploy.yml`）：

1. Cloudflare Dashboard → **Manage Account → Account ID**，复制备用。
2. **My Profile → API Tokens → Create Token** → 模板选 **"Cloudflare Pages"**。
3. 仓库 **Settings → Secrets and variables → Actions** → 新建 `CLOUDFLARE_API_TOKEN`、`CLOUDFLARE_ACCOUNT_ID`。
4. Cloudflare Dashboard → **Pages → Create a project → Direct Upload**，项目名填 `nusantara-retail-twin`。

**方式二：Wrangler 手动部署**

```bash
cd web
npm ci && npm run build
npx wrangler pages deploy dist --project-name=nusantara-retail-twin
```

部署成功后可访问 `https://nusantara-retail-twin.pages.dev`。

---

## 🛠 技术栈 / Tech Stack

| 模块 / Module | 技术 / Technology |
|------|------|
| 3D 场景 / 3D Scene | React Three Fiber + Drei |
| 前端框架 / Frontend | React 18 + TypeScript + Vite |
| 空间数据 / Spatial Data | PostgreSQL + PostGIS |
| 需求预测 / Forecast | Prophet + LightGBM |
| 空间优化 / Optimization | OR-Tools (MILP) |
| 生命周期 / Lifecycle | Python + Pandas |
| 实时通信 / Real-time | WebSocket |
| 部署 / Deployment | Cloudflare Pages + GitHub Actions |

---

## 📁 项目结构 / Project Structure

```text
nusantara-retail-twin/
├── data/
│   ├── schemas/                  # 统一数据模型
│   └── seeds/                    # 三档门店种子数据
│       ├── store_500sqm.json
│       ├── store_2000sqm.json
│       └── store_5000sqm.json
├── src/
│   └── nrt/
│       ├── model/                # 实体与数据模型（pydantic，对应 docs/data-model.md）
│       ├── seed/                 # 全量种子数据生成器（nrt seed）
│       ├── calendar/             # 印尼节庆日历（2026 官方日期）
│       ├── twin.py               # RetailTwin 业务门面
│       ├── cli/                  # nrt 命令行工具（seed / validate / calendar）
│       ├── forecast/             # 需求预测引擎（Phase 4 接口预留）
│       ├── replenishment/        # 补货引擎（Phase 5 接口预留）
│       ├── space/                # 空间-存量优化（Phase 5 接口预留）
│       ├── lifecycle/            # FEFO / 促销触发（Phase 6 已落地）
│       └── sentiment/            # 舆情信号适配器（Phase 6 接口预留）
├── web/
│   ├── floorplan/                # 2D 平面图编辑器
│   ├── three/                    # 3D 数字孪生渲染
│   └── dashboard/                # SKU 去化大屏
├── tests/
├── docs/
│   ├── assets/                   # README 图像与 GIF
│   ├── architecture.md
│   ├── store-scale-benchmarks.md
│   ├── indonesia-market-notes.md
│   └── data-model.md
├── .github/workflows/            # 自动部署
├── docker-compose.yml
├── Makefile
└── README.md
```

---

## 🚀 快速开始 / Quick Start

### 环境要求 / Requirements

- Python ≥ 3.10
- Node.js ≥ 18
- PostgreSQL ≥ 15 + PostGIS
- Docker（推荐）

### 本地开发运行 / Local Development

```bash
# 1. 克隆仓库 / Clone
git clone https://github.com/YOUR_ORG/nusantara-retail-twin.git
cd nusantara-retail-twin

# 2. 安装并生成种子数据 / Install & seed
cp .env.example .env
make install
make seed          # 生成三档全量种子到 data/seeds/*_full.json（约 28MB，已 gitignore）

# 3. （可选）启动数据库 / Start database（Phase 3 起需要）
make db
# make migrate     # Phase 3 提供

# 4. 启动前后端 / Start frontend + backend
make dev           # Phase 4 提供 API；前端 Demo 见 Phase 3
```

校验种子数据一致性：

```bash
make validate      # nrt validate 全量 + 样例种子文件
```

### 生成一个 2,000㎡ 雅加达门店

```bash
nrt seed --store-size 2000 --region java --output ./data/seeds
```

```python
from nrt import RetailTwin
from nrt.model import StoreSeed

# 加载已生成的全量种子（单一数据源：2D 平面图与 3D 场景共用）
twin = RetailTwin.from_seed_file("./data/seeds/store_2000sqm_full.json")
seed: StoreSeed = twin.seed
print(seed.generation_summary)
# forecast / replenish / optimize_space：Phase 4–5 解锁
```

---

## 🗺 路线图 / Roadmap

| 阶段 / Phase | 内容 / Content | 状态 / Status |
|---|---|---|
| Phase 1 | 仓库初始化、README、统一数据模型 | ✅ 已完成 |
| Phase 2 | 三档门店种子数据、2D 平面图编辑器 | 🔄 进行中（全量种子生成器 + nrt CLI + 2D 平面图编辑器 ✅） |
| Phase 3 | 3D 数字孪生渲染（500 / 2000 / 5000㎡） | 🔄 进行中（R3F 沙盘 + 2D/3D 联动 ✅，户外场景/动效待做） |
| Phase 4 | 需求预测引擎（斋月 / Mudik / Harbolnas） | 🔄 进行中（基线引擎 + nrt forecast ✅，Prophet/LightGBM 待接） |
| Phase 5 | 补货引擎 + 空间-存量 MILP 优化 | 🔄 进行中（补货引擎 + nrt replenish + MILP 优化器 ✅） |
| Phase 6 | 生命周期管理 + 舆情信号接入 | 🔄 进行中（lifecycle/sentiment 引擎已落地） |
| Phase 7 | Cloudflare Pages 部署、文档完善 | ⏳ 计划中 |
| Phase 8 | 印尼试点、真实数据接入、区域扩展 | ⏳ 计划中 |

---

## 📊 门店运营速览 / Store Operations Quick View

以下表格基于印尼典型门店规模的公开数据与行业研究。

**500㎡ 社区店**

| 指标 | 数值 |
|---|---|
| SKU 数量 | 4,000 – 6,000 |
| 生鲜占比 | 15 – 20% |
| 货架层数 | 4 – 5 层 |
| 主通道宽度 | 1.8 – 2.2 m |
| 典型补货频率 | 每周 2–3 次 |

**2,000㎡ 标准店**

| 指标 | 数值 |
|---|---|
| SKU 数量 | 10,000 – 18,000 |
| 生鲜占比 | 25 – 30% |
| 货架层数 | 5 – 6 层 |
| 主通道宽度 | 2.5 – 3.5 m |
| 典型补货频率 | 每周 3–5 次 |

**5,000㎡ 大卖场**

| 指标 | 数值 |
|---|---|
| SKU 数量 | 28,000 – 40,000 |
| 生鲜占比 | 30 – 35% |
| 货架层数 | 6 – 7 层 |
| 主通道宽度 | 3 – 4 m |
| 典型补货频率 | 每日 / 隔日 |

**关键差异 / Key differences**：印尼现代零售的补货节律由斋月主导，而非西方零售的年末圣诞。500㎡ 店型的 SKU 密度显著高于中国同类社区店，因为印尼消费者在同一家店完成"日常 + 节庆"双场景采购。5,000㎡ 店型的生鲜占比高达 30–35%，因印尼消费者对新鲜肉类、蔬菜和海鲜需求极为突出。完整参数见 `docs/store-scale-benchmarks.md`。

---

## 📄 许可证 / License

MIT License

## 🙏 致谢 / Acknowledgements

- 视觉与展示范式参考：[ChargeNexus Showcase](https://github.com/vfvincentwong2026/charge-nexus-showcase)
- 印尼市场参数参考：APPBI 行业报告、Alfamidi / Alfasupermarket / Hypermart 公开数据
- 开源零售与供应链社区：Prophet、OR-Tools、React Three Fiber

---

Nusantara Retail Twin — 让每一个货架的展示面积都参与补货决策。
Nusantara Retail Twin — Let every shelf facing drive the replenishment decision.

</div>
