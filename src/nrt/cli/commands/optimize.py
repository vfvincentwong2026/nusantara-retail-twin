"""`nrt optimize` — 运行空间-存量 MILP 优化（CLI-DESIGN.md §4.7）。"""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from nrt.model import StoreSeed
from nrt.space import SpaceOptimizer

console = Console()

# ABC 类 → 日均周转代理（件/面位/日）
ABC_TURNOVER = {"A": 12.0, "B": 6.0, "C": 2.5}


def optimize(
    seed_path: Path = typer.Option(Path("./data/seeds/store_2000sqm_full.json"), "--seed", "-s",
                                   help="种子文件"),
    objective: str = typer.Option("balanced", "--objective", "-o", help="profit / stockout_min / balanced"),
    as_json: bool = typer.Option(False, "--json", help="JSON 输出"),
) -> None:
    """MILP 求解品类 → 面位分配。"""
    doc = StoreSeed.model_validate(json.loads(Path(seed_path).read_text(encoding="utf-8")))
    store = doc.store_profile
    skus = doc.skus or []
    if not skus:
        console.print("[red]种子文件无 SKU 目录[/]")
        raise typer.Exit(2)

    # 聚合品类参数（契约 §4.3 输入）
    cats: dict[str, dict] = {}
    for s in skus:
        c = cats.setdefault(
            s.category_name,
            {
                "category_id": s.category_name,
                "sku_count": 0,
                "margins": [],
                "turnovers": [],
                "fresh": s.fresh_flag,
            },
        )
        c["sku_count"] += 1
        c["margins"].append(s.gross_margin or 0.2)
        c["turnovers"].append(ABC_TURNOVER[s.abc_class.value if s.abc_class else "C"])
    categories = []
    for c in cats.values():
        categories.append(
            {
                "category_id": c["category_id"],
                "sku_count": c["sku_count"],
                "avg_gross_margin": sum(c["margins"]) / len(c["margins"]),
                "avg_daily_turnover": sum(c["turnovers"]) / len(c["turnovers"]),
                "avg_facing_width_m": 0.2,
                "min_facings_required": max(6, round(c["sku_count"] * 0.01)),
            }
        )

    total_facings = doc.generation_summary.facings_count
    fresh_ids = {c["category_id"] for c in categories if cats[c["category_id"]]["fresh"]}
    optimizer = SpaceOptimizer(store)
    result = optimizer.solve(
        categories,
        total_facings=total_facings,
        fresh_ratio_min=store.fresh_ratio or 0.0,
        fresh_categories=fresh_ids,
        objective=objective,
    )

    if as_json:
        console.print_json(json.dumps(result, ensure_ascii=False))
        return

    console.print(
        f"\n[bold]目标函数值:[/] {result['objective_value']:,.0f}   "
        f"[bold]求解状态:[/] {result['solver_status']}   "
        f"[bold]目标:[/] {objective}   [bold]总面位:[/] {total_facings}"
    )
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("品类")
    table.add_column("分配 Facings", justify="right")
    table.add_column("日利润 (IDR)", justify="right")
    table.add_column("缺货风险", justify="right")
    for a in sorted(result["allocations"], key=lambda x: -x["allocated_facings"]):
        table.add_row(
            a["category_id"],
            str(a["allocated_facings"]),
            f"{a['expected_daily_profit']:,.0f}",
            f"{a['stockout_risk']:.3f}",
        )
    console.print(table)
