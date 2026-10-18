"""`nrt space-report` — 空间价值周报（店主三问：哪里最赚/哪里浪费/挪多少）。"""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from nrt.model import StoreSeed
from nrt.space_value import SpaceAnalyzer

console = Console()


def space_report(
    seed_path: Path = typer.Option(Path("./data/seeds/store_500sqm_full.json"), "--seed", "-s",
                                   help="种子文件"),
    top_n: int = typer.Option(3, "--top", "-n", help="what-if 建议条数"),
    output: Path = typer.Option(None, "--output", "-o", help="JSON 输出路径（空 = 打印表格）"),
) -> None:
    """空间价值分析：分区坪效榜 + 末位面位 + 挪位增收建议。"""
    doc = StoreSeed.model_validate(json.loads(Path(seed_path).read_text(encoding="utf-8")))
    rep = SpaceAnalyzer(doc).report(top_n=top_n)

    table = Table(title=f"空间价值报告 · {doc.store_profile.store_name}")
    table.add_column("分区", style="cyan")
    table.add_column("面积 ㎡", justify="right")
    table.add_column("面位", justify="right")
    table.add_column("日毛利 IDR", justify="right")
    table.add_column("坪效 IDR/㎡/日", justify="right")
    for z in rep["zone_ranking"]:
        table.add_row(z["zone_name"], f"{z['area_m2']:.0f}", str(z["facings"]),
                      f"{z['daily_margin_idr']:,.0f}", f"{z['margin_per_m2_idr']:,.0f}")
    console.print(table)

    console.print("\n[bold]末位面位（品类内效率最低）[/bold]")
    bt = Table()
    bt.add_column("面位")
    bt.add_column("分区")
    bt.add_column("SKU")
    bt.add_column("效率比", justify="right")
    for r in rep["bottom_facings"][:5]:
        bt.add_row(r["facing_id"], r["zone_name"], r["sku_name"], f"{r['efficiency_ratio']:.2f}")
    console.print(bt)

    console.print("\n[bold]挪位增收建议（what-if）[/bold]")
    wt = Table()
    wt.add_column("操作")
    wt.add_column("分区")
    wt.add_column("从 → 到", style="cyan")
    wt.add_column("日毛利增量", justify="right")
    for w in rep["what_if_top"]:
        wt.add_row(w["action"], w["zone"], f"{w['from_sku']} → {w['to_sku_name'][:20]}",
                   f"+Rp {w['delta_daily_margin_idr']:,.0f}/日")
    console.print(wt)

    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
        console.print(f"\n[green]报告 → {output}[/green]")
