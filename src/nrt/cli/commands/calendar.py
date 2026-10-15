"""`nrt calendar` — 查询印尼节庆日历。"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from nrt.calendar import IndonesiaCalendar

console = Console()


def calendar_cmd(
    year: int = typer.Option(2026, "--year", "-y", help="年份（当前内置 2026）"),
    event: str = typer.Option("", "--event", "-e", help="事件名（如 ramadan / lebaran），空 = 全部"),
    window: bool = typer.Option(False, "--window", "-w", help="显示斋月影响窗口与补货窗口"),
    region: str = typer.Option("java", "--region", "-r", help="岛屿区域（用于补货窗口）"),
) -> None:
    """查询印尼节庆日历。"""
    cal = IndonesiaCalendar(year=year)
    events = cal.events()
    if event:
        key = event.lower()
        events = [e for e in events if key in e["name"].lower() or key in e.get("zh_name", "")]

    table = Table(title=f"Indonesia Retail Calendar {year}")
    table.add_column("日期", style="cyan")
    table.add_column("节日")
    table.add_column("类型")
    table.add_column("权重", justify="right")
    table.add_column("窗口", justify="right")
    for e in events:
        end = f" ~ {e['end_date']}" if e.get("end_date") else ""
        table.add_row(e["date"] + end, f"{e['zh_name']} ({e['name']})",
                      e["type"], f"{e['impact_weight']:.1f}", f"{e['window_weeks']} 周")
    console.print(table)

    if window:
        w = cal.get_ramadan_window(pre_weeks=8, post_weeks=2)
        console.print(f"\n[bold]斋月窗口[/]：{w['start']} ~ {w['end']}"
                      f"（斋月首日 {w['ramadan_start']}，开斋节 {w['lebaran']}）")
        console.print(f"[bold]Mudik 偏移[/]（{region}）：{cal.get_mudik_offset(region):+d} 天")
        for r in cal.pre_replenishment_windows(region):
            console.print(f"  第 {r['round']} 轮前置补货（{r['scope']}）：{r['start']} ~ {r['end']}")
