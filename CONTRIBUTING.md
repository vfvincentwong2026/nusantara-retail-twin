# Contributing to Nusantara Retail Twin

感谢你对 Nusantara Retail Twin 的关注。本文档说明如何参与贡献，包括环境搭建、代码规范、提交约定和 PR 流程。

---

## 1. 贡献方式

你可以通过以下方式参与：

| 方式 | 说明 | 入口 |
|---|---|---|
| 🐛 报告 Bug | 提交 Issue 描述问题 | [New Issue](https://github.com/YOUR_ORG/nusantara-retail-twin/issues/new) |
| 💡 功能建议 | 提交 Feature Request | [New Issue](https://github.com/YOUR_ORG/nusantara-retail-twin/issues/new) |
| 📖 完善文档 | 修正或补充 `docs/` | Pull Request |
| 🧩 贡献数据 | 新增门店种子或区域适配 | Pull Request |
| 🌏 区域扩展 | 帮助适配马来西亚/泰国/越南 | Issue + PR |
| 💻 代码贡献 | 修复 Bug 或实现新功能 | Pull Request |

> **重要**：在开始任何较大规模的工作之前，请先提交 Issue 讨论方案。这样可以避免你花时间实现的功能因不符合项目方向而被拒绝。

---

## 2. 开发环境搭建

### 2.1 前置依赖

| 依赖 | 版本要求 | 说明 |
|---|---|---|
| Python | ≥ 3.10 | 后端与预测引擎 |
| Node.js | ≥ 18 | 前端与 3D 渲染 |
| PostgreSQL | ≥ 15 + PostGIS | 空间数据存储 |
| Docker | 最新稳定版 | 容器化依赖服务 |
| Git | ≥ 2.30 | 版本控制 |

### 2.2 本地初始化

```bash
# 1. Fork 并克隆仓库
git clone https://github.com/YOUR_USERNAME/nusantara-retail-twin.git
cd nusantara-retail-twin

# 2. 添加上游远程
git remote add upstream https://github.com/YOUR_ORG/nusantara-retail-twin.git

# 3. 配置环境变量
cp .env.example .env

# 4. 启动数据库
docker compose up -d db

# 5. 安装依赖并初始化
make install
make migrate
make seed

# 6. 启动开发服务
make dev
```

### 2.3 验证环境

```bash
# 运行测试
make test

# 检查代码风格
make lint

# 验证种子数据生成
nrt seed --store-size 2000 --region java --output ./workspace/test
```

---

## 3. 代码规范

### 3.1 Python

- **格式化**：使用 `black`，行宽 100
- **导入排序**：使用 `isort`
- **Lint**：使用 `ruff`
- **类型检查**：使用 `mypy`（建议）

```bash
make format    # 自动格式化
make lint      # 检查
```

**命名约定**：

| 类型 | 规范 | 示例 |
|---|---|---|
| 模块 | snake_case | `replenishment_engine.py` |
| 类 | PascalCase | `ForecastEngine` |
| 函数 | snake_case | `calculate_safety_stock()` |
| 常量 | UPPER_SNAKE | `DEFAULT_LEAD_TIME_DAYS` |
| 私有 | 前缀 `_` | `_validate_input()` |

**类型注解**：所有公开函数必须包含完整的类型注解。

```python
def calculate_safety_stock(
    demand_std: float,
    lead_time_days: float,
    service_level: float = 0.95,
) -> int:
    """计算安全库存。

    Args:
        demand_std: 需求标准差。
        lead_time_days: 有效提前期（天）。
        service_level: 服务水平，默认 0.95。

    Returns:
        安全库存数量。
    """
```

### 3.2 TypeScript / React

- **格式化**：使用 Prettier
- **Lint**：使用 ESLint + `@typescript-eslint`
- **组件**：函数组件 + Hooks，禁止 class 组件
- **样式**：使用 Tailwind CSS，避免内联样式

**命名约定**：

| 类型 | 规范 | 示例 |
|---|---|---|
| 组件文件 | PascalCase | `FloorplanEditor.tsx` |
| Hook 文件 | camelCase | `useAgentFeed.ts` |
| 工具函数 | camelCase | `formatCurrency()` |
| 类型 | PascalCase | `FacingStatus` |
| 常量 | UPPER_SNAKE | `MAX_FACINGS` |

### 3.3 SQL

- 表名和列名使用 snake_case
- 主键统一 `{entity}_id` 格式
- 时间戳字段统一 `TIMESTAMPTZ`
- 必须为外键创建索引

### 3.4 文档

- 中文与英文之间加空格
- 代码块标注语言
- 表格对齐
- 标题层级不超过 4 级

---

## 4. Git 提交约定

### 4.1 提交信息格式

遵循 [Conventional Commits](https://www.conventionalcommits.org/)：

```text
<type>(<scope>): <subject>

<body>

<footer>
```

**Type 枚举**：

| type | 说明 |
|---|---|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档变更 |
| `style` | 代码格式（不影响逻辑） |
| `refactor` | 重构 |
| `test` | 测试相关 |
| `chore` | 构建/工具变更 |
| `data` | 种子数据/参数变更 |

**示例**：

```text
feat(forecast): add Ramadan demand multiplier

- Add ramadan_offset parameter to StoreProfile
- Implement pre-Ramadan replenishment window calculation
- Add unit tests for ramadan window logic

Closes #42
```

```text
docs(data-model): add replenishment_orders table DDL

- Add SQL DDL for replenishment_orders
- Document island_logistics_params reference table
```

### 4.2 分支命名

| 类型 | 格式 | 示例 |
|---|---|---|
| 功能 | `feat/<description>` | `feat/ramadan-forecast` |
| 修复 | `fix/<description>` | `fix/lead-time-calculation` |
| 文档 | `docs/<description>` | `docs/data-model-update` |
| 数据 | `data/<description>` | `data/store-500sqm-seed` |

### 4.3 提交纪律

- 每个提交做一件事，保持原子性
- 提交信息使用祈使句（“add” 而非 “added”）
- 不要在提交中包含密钥、凭证或大数据文件
- PR 提交前 squash 掉中间调试提交

---

## 5. Pull Request 流程

### 5.1 创建 PR 前检查

- [ ] 从最新 `main` 分支创建了功能分支
- [ ] 代码已格式化（`make format`）
- [ ] Lint 通过（`make lint`）
- [ ] 测试通过（`make test`）
- [ ] 新增功能有对应的测试
- [ ] 文档已更新（如有必要）
- [ ] 提交信息符合规范

### 5.2 PR 模板

创建 PR 时请填写以下内容：

```markdown
## 变更说明

简要描述这个 PR 做了什么。

## 关联 Issue

Closes #XX

## 变更类型

- [ ] 新功能
- [ ] Bug 修复
- [ ] 文档更新
- [ ] 数据/参数变更
- [ ] 重构

## 测试方式

描述如何验证这个变更。

## 检查清单

- [ ] 已运行 `make lint`
- [ ] 已运行 `make test`
- [ ] 已更新相关文档
- [ ] 已添加必要的测试

## 截图（如适用）

前端变更请附截图或 GIF。
```

### 5.3 审查标准

PR 审查关注以下维度：

| 维度 | 检查项 |
|---|---|
| **正确性** | 逻辑是否正确，边界条件是否覆盖 |
| **测试** | 是否有足够的测试覆盖 |
| **文档** | 公开接口是否有文档 |
| **性能** | 是否引入明显的性能退化 |
| **兼容性** | 是否破坏现有 API 或数据模型 |
| **风格** | 是否符合项目代码规范 |

### 5.4 合并要求

- 至少 **1 位维护者** Approve
- CI 全部通过
- 无未解决的 Review 评论
- 分支已 rebase 到最新 `main`

### 5.5 合并策略

使用 **Squash and Merge**，合并提交信息遵循 Conventional Commits 格式。

---

## 6. Issue 规范

### 6.1 Bug 报告

请包含以下信息：

```markdown
## 环境

- OS: 
- Python/Node 版本: 
- Nusantara Retail Twin 版本/Commit: 

## 复现步骤

1. 
2. 
3. 

## 期望行为

## 实际行为

## 日志/截图
```

### 6.2 功能请求

```markdown
## 功能描述

## 使用场景

## 建议实现方式（可选）

## 是否愿意提交 PR
- [ ] 是
- [ ] 否
```

---

## 7. 项目结构约定

```text
nusantara-retail-twin/
├── data/
│   ├── schemas/              # 数据模型定义
│   └── seeds/                # 门店种子数据
├── src/nrt/
│   ├── model/                # 实体与数据模型
│   ├── forecast/             # 需求预测
│   ├── replenishment/        # 补货引擎
│   ├── space/                # 空间优化
│   ├── lifecycle/            # 生命周期管理
│   ├── sentiment/            # 舆情信号
│   └── calendar/             # 印尼节庆日历
├── web/
│   ├── floorplan/            # 2D 平面图
│   ├── three/                # 3D 渲染
│   └── dashboard/            # 仪表盘
├── tests/
├── docs/
└── .github/workflows/
```

**新增模块时**：在 `src/nrt/` 下创建独立目录，包含 `__init__.py`、`engine.py` 和 `tests/`。

---

## 8. 数据贡献指南

### 8.1 新增门店种子

1. 在 `data/seeds/` 创建 JSON 文件
2. 遵循 `schemas/store_seed.schema.json` 格式
3. 在 PR 描述中说明数据来源
4. 运行 `nrt seed --validate` 验证

### 8.2 新增区域适配

1. 在 `src/nrt/calendar/` 添加区域日历模块
2. 在 `data/schemas/` 更新参考数据
3. 更新 `docs/indonesia-market-notes.md`
4. 添加对应的单元测试

### 8.3 数据来源要求

所有数据贡献必须标注来源，优先使用：

1. 上市公司财报 / 管理层演示
2. 官方运营资料
3. 行业法规
4. 学术研究
5. 行业媒体（需交叉验证）

---

## 9. 社区行为准则

- 尊重所有贡献者，不论经验水平
- 建设性反馈，对事不对人
- 使用中文或英文沟通，以对方使用的语言为准
- 不发布与项目无关的内容
- 遵守 [Contributor Covenant](https://www.contributor-covenant.org/) 行为准则

---

## 10. 联系方式

| 渠道 | 用途 |
|---|---|
| GitHub Issues | Bug 报告与功能建议 |
| GitHub Discussions | 技术讨论与方案设计 |
| Pull Requests | 代码与文档贡献 |

---

## 11. 更新日志

| 日期 | 版本 | 变更 |
|---|---|---|
| 2026-10 | v0.1 | 初始版本 |
