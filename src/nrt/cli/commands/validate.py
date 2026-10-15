"""`nrt validate` — 校验种子数据与数据模型的一致性。

校验项对应 src/cli/CLI-DESIGN.md §4.3。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import typer
from rich.console import Console

from nrt.model import StoreSeed
from nrt.seed.catalog import SCALE_PARAMS

console = Console()


def _check(condition: bool, label: str, errors: list[str]) -> None:
    console.print(f"  {'[green]✓[/]' if condition else '[red]✗[/]'} {label}")
    if not condition:
        errors.append(label)


def validate(
    files: list[Path] = typer.Argument(..., help="种子 JSON 文件"),
    strict: bool = typer.Option(False, "--strict", help="严格模式（警告即失败）"),
) -> None:
    """校验种子数据文件。"""
    exit_code = 0
    for path in files:
        errors: list[str] = []
        console.print(f"[bold]{path}[/]")
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            doc = StoreSeed.model_validate(data)
        except Exception as e:  # noqa: BLE001
            console.print(f"  [red]✗ 解析失败：{e}[/]")
            sys.exit(3)

        p = doc.store_profile
        sp = SCALE_PARAMS.get(p.store_size_sqm)
        _check(sp is not None, f"store_size_sqm {p.store_size_sqm} 在支持范围内", errors)
        if sp:
            _check(p.store_format.value == sp["format"],
                   f"store_format = {p.store_format.value}（期望 {sp['format']}）", errors)
            _check(abs(p.sku_density - p.target_sku_count / p.store_size_sqm) < 0.5,
                   f"sku_density {p.sku_density} 与 target_sku_count 一致", errors)
        _check(p.island_region is not None, f"island_region = {p.island_region.value}", errors)
        _check(0 < (p.fresh_ratio or 0) < 1, f"fresh_ratio {p.fresh_ratio} 在 0–1 之间", errors)

        gs = doc.generation_summary
        _check(gs.zones_count == len(doc.zones), f"zones: {len(doc.zones)}", errors)
        _check(gs.fixtures_count == len(doc.fixtures), f"fixtures: {len(doc.fixtures)}", errors)
        if not doc.is_sample:
            _check(gs.shelf_levels_count == len(doc.shelf_levels),
                   f"shelf_levels: {len(doc.shelf_levels)}", errors)

        if doc.is_sample:
            facings, skus = doc.sample_facings or [], doc.sample_skus or []
            console.print("  [dim]样例文档：跳过条目数 vs 汇总核对（样例为截断展示）[/]")
            # 样例的覆盖率按 generation_summary 的全量口径计算
            fresh_rate = gs.fresh_skus_count / max(gs.skus_count, 1)
            _check(not sp or abs(fresh_rate - sp["fresh_ratio"]) < 0.03,
                   f"生鲜占比（汇总口径） {fresh_rate:.1%}", errors)
            halal_rate = gs.halal_certified_skus_count / max(gs.skus_count, 1)
            _check(not sp or abs(halal_rate - sp["halal_ratio"]) < 0.03,
                   f"清真覆盖率（汇总口径） {halal_rate:.1%} ≈ 目标 {sp['halal_ratio']:.0%}", errors)
        else:
            facings, skus = doc.facings or [], doc.skus or []
            _check(gs.facings_count == len(facings), f"facings: {len(facings)}", errors)
            _check(gs.skus_count == len(skus), f"skus: {len(skus)}", errors)
            if sp:
                _check(len(facings) == sp["facings"],
                       f"facings 总数 {len(facings)} 达规模承诺 {sp['facings']}", errors)
                _check(len(skus) >= sp["target_sku_count"] * 0.999,
                       f"skus 总数 {len(skus)} 达规模承诺 {sp['target_sku_count']}", errors)

        if not doc.is_sample:
            _check(gs.fresh_skus_count == sum(1 for s in skus if s.fresh_flag),
                   f"生鲜 SKU: {gs.fresh_skus_count}", errors)
            _check(gs.halal_certified_skus_count == sum(1 for s in skus if s.halal_certified),
                   f"清真 SKU: {gs.halal_certified_skus_count}", errors)
            halal_rate = gs.halal_certified_skus_count / len(skus)
            _check(abs(halal_rate - sp["halal_ratio"]) < 0.03,
                   f"清真覆盖率 {halal_rate:.1%} ≈ 目标 {sp['halal_ratio']:.0%}", errors)

        # 引用完整性：facing.sku_code → sku.sku_code；shelf_level.fixture_id → fixture
        sku_codes = {s.sku_code for s in skus}
        dangling = [f.sku_code for f in facings if f.sku_code and f.sku_code not in sku_codes]
        _check(not dangling, "facing → sku 引用完整", errors)
        fixture_ids = {f.fixture_id for f in doc.fixtures}
        dangling_lv = [lv.fixture_id for lv in doc.shelf_levels if lv.fixture_id not in fixture_ids]
        _check(not dangling_lv, "shelf_level → fixture 引用完整", errors)

        if errors:
            console.print(f"  [red]校验失败：{len(errors)} 项[/]")
            exit_code = 3
        else:
            console.print("  [bold green]校验通过[/]")

    if exit_code:
        sys.exit(exit_code)
