"""`nrt forecast` — 运行需求预测引擎（CLI-DESIGN.md §4.5）。"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from nrt.forecast import ForecastEngine, MODEL_VERSION
from nrt.forecast.history import SalesHistorySimulator
from nrt.model import StoreSeed

console = Console()


def forecast(
    seed_path: Path = typer.Option(Path("./data/seeds/store_2000sqm_full.json"), "--seed", "-s",
                                   help="种子文件（门店与 SKU 目录来源）"),
    sku: list[str] = typer.Option([], "--sku", help="SKU 编码（可多次；空 = 首个 A 类 SKU）"),
    horizon: int = typer.Option(30, "--horizon", "-h", help="预测天数"),
    include_ramadan: bool = typer.Option(False, "--include-ramadan", help="启用斋月窗口特征"),
    history_days: int = typer.Option(150, "--history-days", help="合成历史天数（≥90）"),
    today: str = typer.Option("", "--today", help="模拟日期 YYYY-MM-DD（空 = 系统今天）"),
    as_json: bool = typer.Option(False, "--json", help="JSON 输出（可管道给 jq）"),
) -> None:
    """对门店 SKU 运行需求预测（基线引擎，契约 docs/architecture.md §4.1）。"""
    doc = StoreSeed.model_validate(json.loads(Path(seed_path).read_text(encoding="utf-8")))
    store = doc.store_profile
    skus = doc.skus or []
    if not skus:
        console.print("[red]种子文件无 SKU 目录[/]")
        raise typer.Exit(2)

    targets = [s for s in skus if s.sku_code in sku] if sku else [next(s for s in skus if s.abc_class and s.abc_class.value == "A")]
    engine = ForecastEngine(store)
    sim = SalesHistorySimulator(store, targets, seed=42)
    sim_date = date.fromisoformat(today) if today else None
    events = sim.generate(days=history_days, end_date=sim_date)

    results = []
    for target in targets:
        history = [e for e in events if e["sku_id"] == target.sku_id]
        results.append(
            engine.predict(target, history, horizon_days=horizon,
                           include_ramadan=include_ramadan, today=sim_date)
        )

    if as_json:
        console.print_json(json.dumps(results, ensure_ascii=False))
        return

    for r in results:
        console.print(
            f"\n[bold]Store:[/] {r['store_id']}   [bold]SKU:[/] {r['sku_code']} ({r['sku_name']})\n"
            f"[bold]模型:[/] {r['model_version']}   [bold]置信度:[/] {r['confidence']}"
        )
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("日期")
        table.add_column("需求均值", justify="right")
        table.add_column("P90", justify="right")
        step = max(1, horizon // 10)
        for f in r["horizon"]["daily_forecast"][::step]:
            table.add_row(f["date"], f"{f['demand_mean']:.1f}", f"{f['demand_p90']:.1f}")
        console.print(table)
        console.print(
            f"[bold]安全库存:[/] {r['safety_stock']}   "
            f"[bold]再订货点:[/] {r['reorder_point']}   "
            f"[bold]建议订货:[/] {r['suggested_order_quantity']}"
        )
    console.print(f"\n[dim]模型 {MODEL_VERSION}：Prophet+LightGBM 实现（prophet-lgbm-v0.2）将替换本基线，契约不变[/]")
