"""`nrt weekly-brief` — 店主周报生成器（P0）。

输出 WhatsApp 纯文本 + 可打印 HTML，印尼语，四个引擎合一：
补货建议 / 面位挪移 what-if / 生鲜临期折价 / 省钱估算。
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import typer
from rich.console import Console

from nrt.brief import build_brief, render_html, render_text
from nrt.model import StoreSeed

console = Console()


def weekly_brief(
    seed_path: Path = typer.Option(Path("./data/seeds/store_2000sqm_full.json"), "--seed", "-s",
                                   help="种子文件"),
    today: str = typer.Option("", "--today", help="日期 YYYY-MM-DD（空 = 系统今天）"),
    top: int = typer.Option(20, "--top", "-n", help="补货清单条数"),
    output: Path = typer.Option(None, "--output", "-o", help="输出目录（空 = workspace/briefs/<日期>/）"),
) -> None:
    """生成店主周报（WhatsApp 文本 + 打印 HTML + 数据 JSON）。"""
    doc = StoreSeed.model_validate(json.loads(Path(seed_path).read_text(encoding="utf-8")))
    day = date.fromisoformat(today) if today else date.today()

    console.print("运行引擎：forecast → replenish → space → lifecycle …")
    brief = build_brief(doc, today=day, top_orders=top)

    out_dir = Path(output) if output else Path("workspace/briefs") / day.isoformat()
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "brief.txt").write_text(render_text(brief), encoding="utf-8")
    (out_dir / "brief.html").write_text(render_html(brief), encoding="utf-8")
    (out_dir / "brief.json").write_text(
        json.dumps(brief, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    console.print(f"[green]✓ 周报已生成 → {out_dir}[/green]")
    console.print(f"  补货 {brief['order_summary']['need_replenishment']} SKU"
                  f"（紧急 {brief['order_summary']['urgent']}）· "
                  f"挪位 {len(brief['space_what_if'])} 条 · 临期 {len(brief['expiring'])} 条 · "
                  f"省钱估算 Rp {brief['saving_estimate_idr']:,.0f}")
    console.print("\n[bold]WhatsApp 预览[/bold]（前 12 行）:")
    for line in render_text(brief).splitlines()[:12]:
        console.print(f"  {line}")
