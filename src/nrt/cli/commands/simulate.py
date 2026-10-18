"""`nrt simulate` — 运行完整模拟链路（CLI-DESIGN.md §4.8）。

seed → forecast → replenish → optimize，输出模拟档案目录：

    workspace/simulations/sim-YYYYMMDD-HHMMSS/
    ├── meta.json
    ├── seed.json
    ├── forecast.json
    ├── replenishment.json
    ├── planogram.json
    └── summary.md
"""

from __future__ import annotations

import json
import random
from datetime import date
from pathlib import Path

import typer
from rich.console import Console

from nrt.forecast import ForecastEngine
from nrt.forecast.history import SalesHistorySimulator
from nrt.replenishment import ReplenishmentEngine
from nrt.seed import SeedGenerator
from nrt.space import SpaceOptimizer

console = Console()

ABC_TURNOVER = {"A": 12.0, "B": 6.0, "C": 2.5}


def simulate(
    store_size: int = typer.Option(2000, "--store-size", "-s", help="门店规模 500/2000/5000"),
    region: str = typer.Option("java", "--region", "-r", help="岛屿区域"),
    start_date: str = typer.Option("", "--start-date", help="模拟起始日 YYYY-MM-DD（空 = 今天）"),
    days: int = typer.Option(30, "--days", "-d", help="模拟天数（预测 horizon）"),
    include_ramadan: bool = typer.Option(False, "--include-ramadan", help="启用斋月窗口"),
    sku_limit: int = typer.Option(500, "--sku-limit", help="参与模拟的 SKU 上限（0 = 全部）"),
    output: Path = typer.Option(Path("./workspace/simulations"), "--output", "-o", help="输出根目录"),
    seed_value: int = typer.Option(42, "--seed", help="随机种子"),
) -> None:
    """端到端模拟：生成种子 → 预测 → 补货 → 空间优化。"""
    today = date.fromisoformat(start_date) if start_date else date.today()

    with console.status("[bold green]生成种子数据…"):
        seed_doc = SeedGenerator(store_size=store_size, region=region, seed=seed_value).generate()
    store = None
    from nrt.model import StoreSeed

    seed = StoreSeed.model_validate(seed_doc)
    store = seed.store_profile
    targets = [s for s in (seed.skus or []) if s.abc_class and s.abc_class.value == "A"]
    if sku_limit > 0:
        targets = targets[:sku_limit]
    console.print(f"✓ 种子：{store.store_name}，A 类 SKU {len(targets)} 个")

    with console.status("[bold green]运行预测引擎…"):
        engine = ForecastEngine(store)
        events = SalesHistorySimulator(store, targets, seed=seed_value).generate(days=150, end_date=today)
        forecasts = {
            s.sku_id: engine.predict(
                s, [e for e in events if e["sku_id"] == s.sku_id],
                horizon_days=days, include_ramadan=include_ramadan, today=today,
            )
            for s in targets
        }
    console.print(f"✓ 预测：{len(forecasts)} 条 DemandForecast（horizon {days} 天）")

    with console.status("[bold green]运行补货引擎…"):
        rng = random.Random(seed_value)
        inventory = {
            s.sku_id: round(forecasts[s.sku_id]["reorder_point"] * rng.uniform(0.0, 1.3))
            for s in targets
        }
        replenishment = ReplenishmentEngine(store).run(
            targets, forecasts, inventory, strategy="auto", today=today
        )
    sm = replenishment["summary"]
    console.print(
        f"✓ 补货：需补货 {sm['need_replenishment']}（紧急 {sm['urgent']}），"
        f"预估成本 IDR {sm['estimated_cost_idr']:,.0f}"
    )

    with console.status("[bold green]运行空间-存量优化…"):
        cats: dict[str, dict] = {}
        for s in seed.skus or []:
            c = cats.setdefault(s.category_name, {"margins": [], "turnovers": [], "n": 0, "fresh": s.fresh_flag})
            c["n"] += 1
            c["margins"].append(s.gross_margin or 0.2)
            c["turnovers"].append(ABC_TURNOVER[s.abc_class.value if s.abc_class else "C"])
        categories = [
            {
                "category_id": name,
                "sku_count": c["n"],
                "avg_gross_margin": sum(c["margins"]) / len(c["margins"]),
                "avg_daily_turnover": sum(c["turnovers"]) / len(c["turnovers"]),
                "avg_facing_width_m": 0.2,
                "min_facings_required": max(6, round(c["n"] * 0.01)),
            }
            for name, c in cats.items()
        ]
        planogram = SpaceOptimizer(store).solve(
            categories,
            total_facings=seed.generation_summary.facings_count,
            fresh_ratio_min=store.fresh_ratio or 0.0,
            fresh_categories={n for n, c in cats.items() if c["fresh"]},
            objective="balanced",
        )
    console.print(f"✓ 空间优化：{planogram['solver_status']}，目标值 {planogram['objective_value']:,.0f}")

    # ---- 输出档案 ----
    stamp = today.strftime("%Y%m%d") + f"-{store_size}{region[:3]}"
    out_dir = Path(output) / f"sim-{stamp}"
    out_dir.mkdir(parents=True, exist_ok=True)

    meta = {
        "simulation_id": f"sim-{stamp}",
        "store_size_sqm": store_size,
        "island_region": region,
        "start_date": today.isoformat(),
        "days": days,
        "include_ramadan": include_ramadan,
        "sku_count": len(targets),
        "engines": {
            "forecast": "baseline-v0.2",
            "replenishment": "auto (reorder_point + fefo + ramadan_pre)",
            "optimizer": "ortools-cp-sat (balanced)",
        },
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    (out_dir / "seed.json").write_text(json.dumps(seed_doc, ensure_ascii=False), encoding="utf-8")
    (out_dir / "forecast.json").write_text(
        json.dumps(list(forecasts.values()), ensure_ascii=False), encoding="utf-8"
    )
    (out_dir / "replenishment.json").write_text(
        json.dumps(replenishment, ensure_ascii=False), encoding="utf-8"
    )
    (out_dir / "planogram.json").write_text(json.dumps(planogram, ensure_ascii=False), encoding="utf-8")

    top_forecast = sorted(
        forecasts.values(), key=lambda f: max(d["demand_mean"] for d in f["horizon"]["daily_forecast"]),
        reverse=True,
    )[:5]
    lines = [
        f"# 模拟档案 {meta['simulation_id']}",
        "",
        f"- 门店：{store.store_name}（{store.store_size_sqm}㎡，{store.island_region.value}）",
        f"- 起始日：{today.isoformat()}，horizon {days} 天，斋月特征：{'开' if include_ramadan else '关'}",
        f"- SKU 样本：{len(targets)}（A 类）",
        "",
        "## 需求 Top 5（期内最大日需求）",
        "",
        "| SKU | 品类 | 峰值日需求 | ROP | 置信度 |",
        "|---|---|---|---|---|",
    ]
    for f in top_forecast:
        sku = next(s for s in targets if s.sku_id == f["sku_id"])
        peak = max(d["demand_mean"] for d in f["horizon"]["daily_forecast"])
        lines.append(f"| {f['sku_name']} | {sku.category_name} | {peak:.1f} | {f['reorder_point']} | {f['confidence']} |")
    lines += [
        "",
        "## 补货汇总",
        "",
        f"- 检查 {sm['checked']} SKU，需补货 {sm['need_replenishment']}（紧急 {sm['urgent']}）",
        f"- 总订货量 {sm['total_order_quantity']}，预估成本 IDR {sm['estimated_cost_idr']:,.0f}",
        "",
        "## 空间优化（balanced）",
        "",
        f"- 求解状态 {planogram['solver_status']}，目标值 {planogram['objective_value']:,.0f}",
        f"- 面位分配总和 {sum(a['allocated_facings'] for a in planogram['allocations'])}",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    console.print(f"\n[bold green]✓ 结果已保存：{out_dir}[/]")
