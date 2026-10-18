"""`nrt replenish` — 运行补货引擎（CLI-DESIGN.md §4.6）。"""

from __future__ import annotations

import json
import random
from datetime import date
from pathlib import Path

import typer
from rich.console import Console

from nrt.forecast import ForecastEngine
from nrt.forecast.history import SalesHistorySimulator
from nrt.model import StoreSeed
from nrt.replenishment import ReplenishmentEngine

console = Console()


def replenish(
    seed_path: Path = typer.Option(Path("./data/seeds/store_2000sqm_full.json"), "--seed", "-s",
                                   help="种子文件"),
    strategy: str = typer.Option("auto", "--strategy", help="reorder_point / fefo / ramadan_pre / auto"),
    today: str = typer.Option("", "--date", help="模拟日期 YYYY-MM-DD（空 = 系统今天）"),
    sku: list[str] = typer.Option([], "--sku", help="SKU 编码过滤（可多次）"),
    limit: int = typer.Option(0, "--limit", help="最多处理的 SKU 数（0 = 全部）"),
    as_json: bool = typer.Option(False, "--json", help="JSON 输出"),
) -> None:
    """运行补货引擎：预测 → 库存快照 → ORDER/HOLD/URGENT 决策。"""
    doc = StoreSeed.model_validate(json.loads(Path(seed_path).read_text(encoding="utf-8")))
    store = doc.store_profile
    skus = [s for s in (doc.skus or []) if not sku or s.sku_code in sku]
    if limit > 0:
        skus = skus[:limit]
    if not skus:
        console.print("[red]无匹配 SKU[/]")
        raise typer.Exit(2)

    sim_date = date.fromisoformat(today) if today else None
    engine = ForecastEngine(store)
    sim = SalesHistorySimulator(store, skus, seed=42)
    events = sim.generate(days=150, end_date=sim_date)

    forecasts = {}
    for s in skus:
        history = [e for e in events if e["sku_id"] == s.sku_id]
        forecasts[s.sku_id] = engine.predict(
            s, history, horizon_days=30, include_ramadan=True, today=sim_date
        )

    # 库存快照（合成：0%–130% ROP 均匀分布，覆盖 URGENT/ORDER/HOLD 三种状态）
    rng = random.Random(42)
    inventory = {s.sku_id: round(forecasts[s.sku_id]["reorder_point"] * rng.uniform(0.0, 1.3)) for s in skus}

    rep = ReplenishmentEngine(store)
    result = rep.run(skus, forecasts, inventory, strategy=strategy, today=sim_date)

    if as_json:
        console.print_json(json.dumps(result, ensure_ascii=False))
        return

    sm = result["summary"]
    console.print(
        f"\nStore: {result['store_id']}\n策略:  {strategy}\n日期:  {result['date']}\n"
    )
    need = [d for d in result["decisions"] if d["action"] in ("ORDER", "URGENT")]
    for d in need[:20]:
        flag = "[red]URGENT[/]" if d["action"] == "URGENT" else "[yellow]ORDER[/]"
        console.print(
            f"{flag} {d['sku_code']}  {d.get('sku_name', '')[:28]:<28} "
            f"当前 {d['current_inventory']:>4}  ROP {d['reorder_point']:>4}  "
            f"订 {d['order_quantity']:>4}  [{d['priority']}]  {d['reason']}"
        )
    if len(need) > 20:
        console.print(f"[dim]… 其余 {len(need) - 20} 条见 --json 输出[/]")
    console.print(
        f"\n[bold]汇总：[/] 检查 {sm['checked']}  SKU  ·  需补货 {sm['need_replenishment']}  "
        f"·  紧急 {sm['urgent']}  ·  总订货量 {sm['total_order_quantity']}  "
        f"·  预估成本 IDR {sm['estimated_cost_idr']:,.0f}"
    )
