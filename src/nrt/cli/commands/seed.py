"""`nrt seed` — 生成三档门店全量种子数据。

输出文件名 store_{size}sqm_full.json，与手工样例（store_{size}sqm.json）并存。
"""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

from nrt.seed import SeedGenerator
from nrt.seed.catalog import SCALE_PARAMS

console = Console()


def seed(
    store_size: str = typer.Option("all", "--store-size", "-s",
                                    help="门店面积：500 / 2000 / 5000 / all"),
    region: str = typer.Option("java", "--region", "-r",
                               help="岛屿区域：java / sumatra / kalimantan / sulawesi / papua"),
    output: Path = typer.Option(Path("./data/seeds"), "--output", "-o", help="输出目录"),
    seed_value: int = typer.Option(42, "--seed", help="随机种子（保证可复现）"),
    sku_count: int = typer.Option(0, "--sku-count", help="覆盖 SKU 数量（0 = 按规模默认）"),
    fresh_ratio: float = typer.Option(-1.0, "--fresh-ratio", help="覆盖生鲜占比（<0 = 按规模默认）"),
) -> None:
    """生成门店全量种子数据（SKU / Facings 为完整列表）。"""
    sizes = sorted(SCALE_PARAMS) if store_size == "all" else [int(store_size)]
    output.mkdir(parents=True, exist_ok=True)

    written = []
    for size in sizes:
        gen = SeedGenerator(
            store_size=size,
            region=region,
            seed=seed_value,
            sku_count=sku_count or None,
            fresh_ratio=fresh_ratio if fresh_ratio >= 0 else None,
        )
        doc = gen.generate()
        path = output / f"store_{size}sqm_full.json"
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        written.append((path, doc["generation_summary"]))

    for path, s in written:
        console.print(
            f"[bold green]✓[/] {path}  "
            f"SKU {s['skus_count']}（生鲜 {s['fresh_skus_count']}，清真 {s['halal_certified_skus_count']}）  "
            f"Facings {s['facings_count']}  货架 {s['fixtures_count']}"
        )
