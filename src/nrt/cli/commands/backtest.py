"""`nrt backtest` — 预测精度回测：基线引擎 vs Holt-DOW 挑战者（walk-forward MAPE）。

输入为 `nrt synth-pos` 产出的 pos.json；输出报告 JSON，按 ABC 分层汇总。
"""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from nrt.forecast.backtest import backtest_sku, summarize
from nrt.model import StoreSeed

console = Console()


def backtest(
    pos_file: Path = typer.Argument(..., exists=True, help="synth-pos 产出的 pos.json"),
    seed_path: Path = typer.Option(Path("./data/seeds/store_500sqm_full.json"), "--seed", "-s",
                                   help="种子文件（门店与 SKU 目录来源）"),
    horizon: int = typer.Option(14, "--horizon", help="验证窗口天数"),
    sku_limit: int = typer.Option(0, "--sku-limit", help="最多回测 SKU 数（0 = 全部）"),
    output: Path = typer.Option(None, "--output", "-o", help="报告输出路径（空 = 打印）"),
) -> None:
    """walk-forward 回测，量化基线引擎与升级模型的 MAPE 差距。"""
    doc = StoreSeed.model_validate(json.loads(Path(seed_path).read_text(encoding="utf-8")))
    sku_by_id = {s.sku_id: s for s in (doc.skus or [])}

    pos = json.loads(Path(pos_file).read_text(encoding="utf-8"))
    events_by_sku: dict[str, list[dict]] = {}
    for e in pos["sales"]:
        events_by_sku.setdefault(e["sku_id"], []).append(e)

    targets = list(events_by_sku)
    if sku_limit > 0:
        targets = targets[:sku_limit]

    rows = []
    for sku_id in targets:
        sku = sku_by_id.get(sku_id)
        if sku is None:
            continue
        r = backtest_sku(sku, doc.store_profile, events_by_sku[sku_id], horizon=horizon)
        if r:
            rows.append(r)

    if not rows:
        console.print("[red]无满足 90 天历史的 SKU，无法回测[/red]")
        raise typer.Exit(2)

    report = {"pos_file": str(pos_file), "horizon": horizon, "sku_tested": len(rows),
              "summary": summarize(rows), "details": rows}

    table = Table(title=f"回测结果（horizon={horizon}d, n={len(rows)} SKU）")
    table.add_column("分层", style="cyan")
    table.add_column("基线 MAPE", justify="right")
    table.add_column("Holt-DOW MAPE", justify="right")
    table.add_column("Croston-SBA MAPE", justify="right")
    sm = report["summary"]
    tiers = [("整体", "overall"), ("A 类", "abc_A"), ("B 类", "abc_B"), ("C 类", "abc_C"), ("生鲜", "fresh")]
    for label, key in tiers:
        v = sm.get(key, {})
        b, c, k = v.get("baseline_mape"), v.get("challenger_mape"), v.get("croston_mape")
        delta = f"{(k - b) * 100:+.1f}pp" if (b is not None and k is not None) else "—"
        table.add_row(f"{label} (n={v.get('n', 0)})",
                      f"{b * 100:.1f}%" if b is not None else "—",
                      f"{c * 100:.1f}%" if c is not None else "—",
                      f"{k * 100:.1f}% ({delta})" if k is not None else "—")
    console.print(table)

    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        console.print(f"[green]报告 → {output}[/green]")
    else:
        console.print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
