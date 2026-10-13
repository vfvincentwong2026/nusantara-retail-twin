# src/cli/ — 命令行工具设计

> Nusantara Retail Twin 的命令行接口定义、命令契约与实现规范。
> 版本：v0.1

---

## 1. 设计原则

**命令即契约**。每个 CLI 命令对应一个可独立调用的系统能力，输入输出明确，可被脚本、CI、Agent 消费。

**配置分层**。CLI 参数 > 环境变量 > 配置文件（`nrt.config.yaml`）> 默认值。

**幂等优先**。`nrt seed`、`nrt migrate` 等命令重复执行结果一致，不产生副作用。

**可组合**。命令输出支持 `--format json`，可直接管道给 `jq` 或其他工具。

---

## 2. 命令总览

```text
nrt <command> [options]

命令列表：
  nrt init              初始化工作区
  nrt seed              生成门店种子数据
  nrt validate          校验种子数据与数据模型
  nrt migrate           执行数据库迁移
  nrt forecast          运行需求预测
  nrt replenish         运行补货引擎
  nrt optimize          运行空间-存量优化
  nrt simulate          运行完整模拟链路
  nrt serve             启动 API 服务
  nrt export            导出数据（JSON / CSV / Parquet）
  nrt calendar          查询印尼节庆日历
  nrt doctor            环境诊断
```

---

## 3. 全局选项

所有命令共享以下选项：

| 选项 | 简写 | 说明 | 默认值 |
|---|---|---|---|
| `--config` | `-c` | 配置文件路径 | `./nrt.config.yaml` |
| `--workspace` | `-w` | 工作区目录 | `./workspace` |
| `--format` | `-f` | 输出格式：`table` / `json` / `csv` | `table` |
| `--verbose` | `-v` | 详细日志 | `false` |
| `--quiet` | `-q` | 静默模式 | `false` |
| `--no-color` | | 禁用彩色输出 | `false` |
| `--help` | `-h` | 显示帮助 | |
| `--version` | `-V` | 显示版本 | |

**环境变量**：

```bash
NRT_CONFIG=./nrt.config.yaml
NRT_WORKSPACE=./workspace
NRT_DATABASE_URL=postgresql://user:pass@localhost:5432/nrt
NRT_LOG_LEVEL=info
NRT_NO_COLOR=false
```

---

## 4. 命令详细定义

### 4.1 `nrt init`

**职责**：初始化工作区，创建目录结构与默认配置。

**用法**：

```bash
nrt init [options]
```

**选项**：

| 选项 | 说明 | 默认值 |
|---|---|---|
| `--template` | 模板：`minimal` / `full` / `demo` | `minimal` |
| `--force` | 覆盖已有文件 | `false` |

**输出**：

```text
workspace/
├── nrt.config.yaml
├── data/
│   ├── seeds/
│   ├── calendar/
│   └── exports/
├── logs/
└── .gitignore
```

**示例**：

```bash
nrt init --template full
# ✓ 工作区已初始化：./workspace
# ✓ 配置文件：./workspace/nrt.config.yaml
# ✓ 目录结构：data/ logs/
```

---

### 4.2 `nrt seed`

**职责**：生成三档门店的种子数据。

**用法**：

```bash
nrt seed [options]
```

**选项**：

| 选项 | 简写 | 说明 | 默认值 |
|---|---|---|---|
| `--store-size` | `-s` | 门店面积：`500` / `2000` / `5000` / `all` | `all` |
| `--region` | `-r` | 岛屿区域：`java` / `sumatra` / `kalimantan` / `sulawesi` / `papua` | `java` |
| `--output` | `-o` | 输出目录 | `./data/seeds` |
| `--sku-count` | | 覆盖 SKU 数量 | 按规模默认 |
| `--fresh-ratio` | | 覆盖生鲜占比 | 按规模默认 |
| `--seed` | | 随机种子（保证可复现） | `42` |
| `--validate` | | 生成后校验 | `false` |

**输出**：

```text
data/seeds/
├── store_500sqm.json
├── store_2000sqm.json
└── store_5000sqm.json
```

**示例**：

```bash
# 生成全部三档
nrt seed --store-size all --region java

# 生成单个门店
nrt seed --store-size 2000 --region java --output ./workspace/data/seeds

# 生成后可复现
nrt seed --store-size 2000 --seed 12345

# JSON 输出
nrt seed --store-size 2000 --format json | jq '.[0].store_profile'
```

**退出码**：

| 码 | 含义 |
|---|---|
| 0 | 成功 |
| 1 | 参数错误 |
| 2 | 生成失败 |
| 3 | 校验失败 |

---

### 4.3 `nrt validate`

**职责**：校验种子数据与数据模型的一致性。

**用法**：

```bash
nrt validate [options] [files...]
```

**选项**：

| 选项 | 说明 | 默认值 |
|---|---|---|
| `--schema` | 指定 Schema 文件 | `./data/schemas/store_seed.schema.json` |
| `--strict` | 严格模式，警告即失败 | `false` |

**示例**：

```bash
nrt validate ./data/seeds/store_2000sqm.json

# 输出：
# ✓ store_2000sqm.json
#   - zones: 8
#   - fixtures: 13
#   - facings: 4320
#   - skus: 14000
#   - 校验通过
```

**校验项**：

- JSON Schema 合规性
- `store_size_sqm` 与 `store_format` 匹配
- `island_region` 在枚举范围内
- `sku_density` 与 `target_sku_count` 一致性
- `fresh_ratio` 在 0–1 之间
- Facings 与 SKU 引用完整性
- 清真认证覆盖率合理

---

### 4.4 `nrt migrate`

**职责**：执行数据库迁移。

**用法**：

```bash
nrt migrate [options]
```

**选项**：

| 选项 | 说明 | 默认值 |
|---|---|---|
| `--up` | 执行迁移 | `true` |
| `--down` | 回滚 | `false` |
| `--to` | 迁移到指定版本 | 最新 |
| `--dry-run` | 仅打印 SQL | `false` |

**示例**：

```bash
nrt migrate --up
# → 应用迁移：001_init_schema
# → 应用迁移：002_add_ramadan_tables
# ✓ 数据库已更新到 v0.2.0

nrt migrate --dry-run --to 001
# 打印将回滚的 SQL，不执行
```

---

### 4.5 `nrt forecast`

**职责**：运行需求预测引擎。

**用法**：

```bash
nrt forecast [options]
```

**选项**：

| 选项 | 简写 | 说明 | 默认值 |
|---|---|---|---|
| `--store` | `-s` | 门店 ID | 必填 |
| `--sku` | | SKU ID（可多次） | 全部 |
| `--horizon` | `-h` | 预测天数 | `30` |
| `--include-ramadan` | | 启用斋月特征 | `false` |
| `--model` | | 模型版本 | `prophet-lgbm-v0.1` |
| `--output` | `-o` | 输出文件 | stdout |

**示例**：

```bash
# 单 SKU 预测
nrt forecast --store st-2000-java-001 --sku sku-001 --horizon 30

# 斋月窗口预测
nrt forecast --store st-2000-java-001 --include-ramadan --horizon 60

# JSON 输出
nrt forecast --store st-2000-java-001 --format json | jq '.horizon.daily_forecast[0]'
```

**输出示例**（table）：

```text
Store: st-2000-java-001
SKU:   sku-001 (Indomie Goreng 85g)
模型:  prophet-lgbm-v0.1
置信度: 0.87

日期        需求均值  P90    斋月
2026-10-14  14.2      22.0   -
2026-10-15  13.8      21.5   -
...
2026-11-13  15.1      23.2   -

安全库存: 18
再订货点: 42
建议订货: 60
```

---

### 4.6 `nrt replenish`

**职责**：运行补货引擎。

**用法**：

```bash
nrt replenish [options]
```

**选项**：

| 选项 | 简写 | 说明 | 默认值 |
|---|---|---|---|
| `--store` | `-s` | 门店 ID | 必填 |
| `--strategy` | | `reorder_point` / `fefo` / `ramadan_pre` / `auto` | `auto` |
| `--date` | | 模拟日期 | 今天 |
| `--lead-time` | | 覆盖有效提前期 | 按区域计算 |
| `--output` | `-o` | 输出文件 | stdout |

**示例**：

```bash
# 标准补货
nrt replenish --store st-2000-java-001

# 斋月前置补货
nrt replenish --store st-2000-java-001 --strategy ramadan_pre --date 2026-01-01

# FEFO 生鲜补货
nrt replenish --store st-2000-java-001 --strategy fefo
```

**输出示例**：

```text
Store: st-2000-java-001
策略:  auto
日期:  2026-10-14

Facings  F-001-3-01  SKU-001  Indomie Goreng
  当前: 8  ROP: 42  安全库存: 18
  动作: ORDER  数量: 60  优先级: HIGH
  原因: stock_below_reorder_point

汇总：
  检查 Facings: 120
  需补货:       18
  总订货量:     840
  预估成本:     IDR 12,500,000
```

---

### 4.7 `nrt optimize`

**职责**：运行空间-存量优化（MILP）。

**用法**：

```bash
nrt optimize [options]
```

**选项**：

| 选项 | 简写 | 说明 | 默认值 |
|---|---|---|---|
| `--store` | `-s` | 门店 ID | 必填 |
| `--objective` | | `profit` / `stockout_min` / `balanced` | `balanced` |
| `--total-facings` | | 覆盖总 Facings 数 | 按门店 |
| `--output` | `-o` | 输出 Planogram | stdout |

**示例**：

```bash
nrt optimize --store st-2000-java-001 --objective balanced

# 输出：
# 目标函数值: 8,450,000
# 求解状态:   OPTIMAL
#
# 品类          分配 Facings  日利润     缺货风险
# beverages     96            1,250,000  0.03
# fresh         128           2,100,000  0.05
# household     72            620,000    0.02
# ...
```

---

### 4.8 `nrt simulate`

**职责**：运行完整模拟链路（seed → forecast → replenish → optimize）。

**用法**：

```bash
nrt simulate [options]
```

**选项**：

| 选项 | 说明 | 默认值 |
|---|---|---|
| `--store-size` | 门店规模 | `2000` |
| `--region` | 岛屿区域 | `java` |
| `--start-date` | 模拟起始日 | 今天 |
| `--days` | 模拟天数 | `30` |
| `--include-ramadan` | 启用斋月窗口 | `false` |
| `--output` | 输出目录 | `./workspace/simulations` |

**示例**：

```bash
nrt simulate --store-size 2000 --region java --include-ramadan --days 60

# 输出：
# ✓ 生成种子数据
# ✓ 运行预测引擎
# ✓ 运行补货引擎
# ✓ 运行空间优化
# ✓ 结果已保存：./workspace/simulations/sim-20261014-001/
```

**输出目录结构**：

```text
simulations/sim-20261014-001/
├── meta.json
├── seed.json
├── forecast.json
├── replenishment.json
├── planogram.json
└── summary.md
```

---

### 4.9 `nrt serve`

**职责**：启动 API 服务。

**用法**：

```bash
nrt serve [options]
```

**选项**：

| 选项 | 说明 | 默认值 |
|---|---|---|
| `--host` | 监听地址 | `0.0.0.0` |
| `--port` | 端口 | `4000` |
| `--reload` | 开发模式热重载 | `false` |
| `--workers` | 工作进程数 | `1` |

**示例**：

```bash
nrt serve --port 4000 --reload

# 输出：
# ✓ REST  : http://localhost:4000
# ✓ WS    : ws://localhost:4000/ws/replenish
# ✓ 文档  : http://localhost:4000/docs
```

---

### 4.10 `nrt export`

**职责**：导出数据到 JSON / CSV / Parquet。

**用法**：

```bash
nrt export [options]
```

**选项**：

| 选项 | 说明 | 默认值 |
|---|---|---|
| `--store` | 门店 ID | 必填 |
| `--type` | `spatial` / `facings` / `forecast` / `all` | `all` |
| `--format` | `json` / `csv` / `parquet` | `json` |
| `--output` | 输出目录 | `./workspace/exports` |

**示例**：

```bash
nrt export --store st-2000-java-001 --type facings --format csv

# 输出：
# exports/facings_st-2000-java-001_20261014.csv
```

---

### 4.11 `nrt calendar`

**职责**：查询印尼节庆日历。

**用法**：

```bash
nrt calendar [options]
```

**选项**：

| 选项 | 说明 | 默认值 |
|---|---|---|
| `--year` | 年份 | 当前年 |
| `--event` | 事件名（如 `ramadan` / `lebaran`） | 全部 |
| `--window` | 显示影响窗口 | `false` |

**示例**：

```bash
nrt calendar --year 2026 --event ramadan --window

# 输出：
# 事件:       Ramadan Start
# 日期:       2026-02-19
# 类型:       religious
# 影响权重:   1.0
# 影响窗口:   6 周（2026-02-19 至 2026-04-02）
# 关联品类:   food, beverages, fashion, gift
#
# 前置补货窗口：
#   首轮: 2026-01-01 至 2026-01-15
#   次轮: 2026-02-19 至 2026-03-06
#
# Mudik 峰值: 2026-03-18
# 开斋节:     2026-03-21
```

---

### 4.12 `nrt doctor`

**职责**：环境诊断。

**用法**：

```bash
nrt doctor
```

**输出示例**：

```text
Nusantara Retail Twin 环境诊断
─────────────────────────────
✓ Python        3.11.5
✓ Node.js       20.10.0
✓ PostgreSQL    15.4
✓ PostGIS       3.4
✓ 配置文件      ./nrt.config.yaml
✓ 数据库连接    postgresql://localhost:5432/nrt
✓ 工作区        ./workspace (可写)
⚠ 缓存目录      未配置（使用默认 ~/.nrt/cache）
✓ 磁盘空间      12.4 GB 可用

结论：环境可用。
```

---

## 5. 配置文件

`nrt.config.yaml`：

```yaml
# Nusantara Retail Twin 配置
version: 0.1

workspace: ./workspace

database:
  url: postgresql://user:pass@localhost:5432/nrt
  pool_size: 10
  ssl: false

seed:
  default_region: java
  default_store_size: 2000
  random_seed: 42
  output_dir: ./workspace/data/seeds

forecast:
  default_horizon_days: 30
  model: prophet-lgbm-v0.1
  include_ramadan: true
  cache_ttl_minutes: 10

replenishment:
  default_strategy: auto
  lead_time_k_factor:
    java: 0.5
    sumatra: 1.0
    kalimantan: 1.0
    sulawesi: 1.5
    papua: 1.5
  fresh_replenishment_frequency:
    "500": 3
    "2000": 5
    "5000": 7

server:
  host: 0.0.0.0
  port: 4000
  workers: 1

logging:
  level: info
  format: text
  file: ./workspace/logs/nrt.log

calendar:
  country: ID
  year: 2026
  muhammadiyah_offset: 0
```

---

## 6. 输出格式规范

### 6.1 table（默认）

人类可读，列对齐，支持彩色。

```text
Facings  F-001-3-01  SKU-001  Indomie Goreng
  当前: 8  ROP: 42  安全库存: 18
```

### 6.2 json

结构化，可管道给 `jq`。

```json
{
  "store_id": "st-2000-java-001",
  "strategy": "auto",
  "date": "2026-10-14",
  "results": [
    {
      "facing_id": "fc-2000-001-3-01",
      "sku_code": "SKU-001",
      "action": "ORDER",
      "order_quantity": 60,
      "priority": "HIGH"
    }
  ]
}
```

### 6.3 csv

表格数据，适合 Excel / Pandas。

```csv
store_id,facing_id,sku_code,action,order_quantity,priority
st-2000-java-001,fc-2000-001-3-01,SKU-001,ORDER,60,HIGH
```

---

## 7. 退出码规范

| 码 | 含义 |
|---|---|
| 0 | 成功 |
| 1 | 参数错误 |
| 2 | 数据错误 |
| 3 | 校验失败 |
| 4 | 网络错误 |
| 5 | 数据库错误 |
| 6 | 权限错误 |
| 7 | 内部错误 |

---

## 8. 实现规范

### 8.1 技术栈

| 组件 | 选型 |
|---|---|
| CLI 框架 | Typer（Python） |
| 参数解析 | Click（Typer 底层） |
| 输出渲染 | Rich（表格 + 彩色） |
| 配置加载 | PyYAML + Pydantic |
| 进度条 | Rich Progress |
| 日志 | structlog |

### 8.2 目录结构

```text
src/cli/
├── __init__.py
├── main.py                 # Typer app 入口
├── commands/
│   ├── init.py
│   ├── seed.py
│   ├── validate.py
│   ├── migrate.py
│   ├── forecast.py
│   ├── replenish.py
│   ├── optimize.py
│   ├── simulate.py
│   ├── serve.py
│   ├── export.py
│   ├── calendar.py
│   └── doctor.py
├── options/
│   ├── global_options.py
│   └── output_format.py
├── renderers/
│   ├── table_renderer.py
│   ├── json_renderer.py
│   └── csv_renderer.py
└── config/
    ├── loader.py
    └── schema.py
```

### 8.3 入口

`pyproject.toml`：

```toml
[project.scripts]
nrt = "nrt.cli.main:app"
```

### 8.4 命令实现模板

```python
import typer
from rich.console import Console
from nrt.cli.options import OutputFormat, global_options

console = Console()

def seed(
    store_size: str = typer.Option("all", "--store-size", "-s"),
    region: str = typer.Option("java", "--region", "-r"),
    output: str = typer.Option("./data/seeds", "--output", "-o"),
    seed_value: int = typer.Option(42, "--seed"),
    output_format: OutputFormat = global_options.output_format,
):
    """生成门店种子数据。"""
    with console.status("[bold green]生成种子数据..."):
        result = generate_seeds(store_size, region, seed_value)
        write_seeds(result, output)
    
    if output_format == OutputFormat.JSON:
        console.print_json(result.model_dump_json())
    else:
        console.print(f"✓ 已生成 {len(result)} 个门店种子")
```

---

## 9. 与 Agent 的集成

CLI 命令可被 Agent 直接调用：

```python
from nrt.cli.agent import invoke

result = invoke("replenish", {
    "store": "st-2000-java-001",
    "strategy": "ramadan_pre",
    "date": "2026-01-01",
})
```

Agent 通过 `--format json` 消费输出，无需解析表格。

---

## 10. 测试规范

| 测试类型 | 覆盖范围 |
|---|---|
| 单元测试 | 每个命令的参数解析 |
| 集成测试 | 端到端命令执行 |
| 快照测试 | 输出格式一致性 |
| 性能测试 | 大门店（5000㎡）生成时间 < 10s |

**示例**：

```python
from typer.testing import CliRunner
from nrt.cli.main import app

runner = CliRunner()

def test_seed_2000():
    result = runner.invoke(app, ["seed", "--store-size", "2000", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["store_profile"]["store_size_sqm"] == 2000
```

---

## 11. 更新日志

| 日期 | 版本 | 变更 |
|---|---|---|
| 2026-10 | v0.1 | 初始版本，覆盖 12 个命令的定义与实现规范 |
