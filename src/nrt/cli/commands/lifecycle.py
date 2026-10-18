"""`nrt lifecycle` — 生命周期管理报告（§4.4）。"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import typer
from rich.console import Console

from nrt.lifecycle import LifecycleManager
from nrt.model import StoreSeed

console = Console()


def lifecycle(
    seed_path: Path = typer.Option(Path("./data/seeds/store_2000sqm_full.json"), "--seed", "-s"),
    today: str = typer.Option("", "--date", help="模拟日期 YYYY-MM-DD（空 = 今天）"),
    limit: int = typer.Option(200, "--limit", help="最多处理 SKU 数"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """FEFO 批次评估：临期捆绑 / 折价 / 斋月阶梯折扣。"""
    doc = StoreSeed.model_validate(json.loads(Path(seed_path).read_text(encoding="utf-8")))
    store = doc.store_profile
    skus = [s for s in (doc.skus or []) if s.shelf_life_days][:limit]

    from nrt.calendar import IndonesiaCalendar

    mgr = LifecycleManager(store, calendar=IndonesiaCalendar(year=2026))
    sim_date = date.fromisoformat(today) if today else None
    result = mgr.run(skus, today=sim_date)

    if as_json:
        console.print_json(json.dumps(result, ensure_ascii=False))
        return

    sm = result["summary"]
    console.print(f"\nStore: {result['store_id']}   日期: {result['date']}   FEFO: 先到期先出")
    active = [a for a in result["actions"] if a["action"] != "HOLD"]
    for a in active[:20]:
        tag = "[red]BUNDLE[/]" if a["action"] == "BUNDLE_PROMOTION" else "[yellow]MARKDOWN[/]"
        extra = ""
        if a["suggested_discount_pct"]:
            extra += f" -{a['suggested_discount_pct']}%"
        if a["bundle_with_category"]:
            extra += f" ×捆:{a['bundle_with_category']}"
        console.print(
            f"{tag} {a['sku_code']} {a['sku_name'][:26]:<26} "
            f"剩 {a['remaining_shelf_life_days']:>2} 天  [{a['reason']}]{extra}"
        )
    if len(active) > 20:
        console.print(f"[dim]… 其余 {len(active) - 20} 条见 --json[/]")
    console.print(
        f"\n[bold]汇总：[/] 批次 {sm['checked']}  ·  临期捆绑 {sm['bundle_promotions']}  "
        f"·  折价 {sm['markdowns']}  ·  清真捆绑 {sm['halal_bundles']}  ·  斋月阶梯 {sm['ramadan_stair']}"
    )
