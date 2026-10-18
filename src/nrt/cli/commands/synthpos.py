"""`nrt synth-pos` — 生成带真实 POS 脏特征的合成销售数据（Phase 8 演练）。

输出 workspace/simulations/synth-pos/<时间戳>/ 下的 pos.json：
- sales：含缺货删零（censored）、促销尖峰（promotion_flag）的日销事件
- wastage：生鲜报损记录
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import typer
from rich.console import Console

from nrt.forecast.history import SalesHistorySimulator
from nrt.model import StoreSeed

console = Console()


def synthpos(
    seed_path: Path = typer.Option(Path("./data/seeds/store_500sqm_full.json"), "--seed", "-s",
                                   help="种子文件（门店与 SKU 目录来源）"),
    days: int = typer.Option(365, "--days", "-d", help="生成天数（≥104）"),
    today: str = typer.Option("", "--today", help="结束日期 YYYY-MM-DD（空 = 系统今天）"),
    stockout_rate: float = typer.Option(0.03, "--stockout-rate", help="缺货删失概率"),
    promo_rate: float = typer.Option(0.02, "--promo-rate", help="促销日概率"),
    wastage_rate: float = typer.Option(0.05, "--wastage-rate", help="生鲜报损记录概率"),
    output: Path = typer.Option(Path(""), "--output", "-o", help="输出目录（空 = workspace/simulations/synth-pos/<时间戳>/）"),
) -> None:
    """合成 POS 数据：模拟真实门店日销、缺货、促销与报损。"""
    if days < 104:
        console.print("[red]--days 至少 104（90 天训练 + 14 天回测验证）[/red]")
        raise typer.Exit(2)
    doc = StoreSeed.model_validate(json.loads(Path(seed_path).read_text(encoding="utf-8")))
    skus = doc.skus or []
    if not skus:
        console.print("[red]种子文件无 SKU 目录[/]")
        raise typer.Exit(2)

    sim = SalesHistorySimulator(doc.store_profile, skus, seed=42)
    end = date.fromisoformat(today) if today else None
    pos = sim.generate_pos(days=days, end_date=end, stockout_rate=stockout_rate,
                           promo_rate=promo_rate, wastage_rate=wastage_rate)

    if str(output) == "." or str(output) == "":
        stamp = date.today().isoformat()
        out_dir = Path("workspace/simulations/synth-pos") / stamp
    else:
        out_dir = Path(output)
    out_dir.mkdir(parents=True, exist_ok=True)
    pos_file = out_dir / "pos.json"
    pos_file.write_text(json.dumps(pos, ensure_ascii=False), encoding="utf-8")

    s = pos["summary"]
    console.print(f"[green]已生成 {s['sale_events']:,} 条销售事件[/green] "
                  f"（缺货删零 {s['censored_days']:,} 天 / 促销 {s['promo_events']:,} 天 / 报损 {s['wastage_events']:,} 条）")
    console.print(f"→ {pos_file}")
