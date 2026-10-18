"""`nrt export` — 导出种子数据子集（JSON / CSV）。

供下游工具或 Agent 按需消费种子：只取需要的 section、限制行数、选格式。
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import typer
from rich.console import Console

console = Console()

LIST_SECTIONS = ["zones", "fixtures", "shelf_levels", "facings", "skus"]
DICT_SECTIONS = ["meta", "store_profile", "ramadan_calendar_2026", "generation_summary"]


def export(
    seed_file: Path = typer.Argument(..., exists=True, help="种子 JSON 文件路径"),
    section: str = typer.Option("skus", "--section", "-s",
                                help=f"导出节：{'/'.join(LIST_SECTIONS + DICT_SECTIONS)}"),
    limit: int = typer.Option(0, "--limit", "-n", help="最多导出行数（0 = 全部）"),
    format_: str = typer.Option("json", "--format", "-f", help="输出格式：json / csv"),
    output: Path = typer.Option(Path("-"), "--output", "-o", help="输出文件（- = 标准输出）"),
) -> None:
    """从种子文件导出指定节的子集。"""
    if section not in LIST_SECTIONS + DICT_SECTIONS:
        console.print(f"[red]未知 section：{section}[/red]")
        raise typer.Exit(code=2)

    data: dict[str, Any] = json.loads(seed_file.read_text(encoding="utf-8"))
    if section not in data:
        console.print(f"[red]种子文件不含 section：{section}[/red]")
        raise typer.Exit(code=2)

    payload: Any = data[section]
    if section in LIST_SECTIONS:
        rows: list[dict] = list(payload)
        if limit > 0:
            rows = rows[:limit]
        if format_ == "csv":
            text = _to_csv(rows)
        elif format_ == "json":
            text = json.dumps(rows, ensure_ascii=False, indent=2)
        else:
            console.print(f"[red]未知格式：{format_}[/red]")
            raise typer.Exit(code=2)
    else:
        text = json.dumps(payload, ensure_ascii=False, indent=2)

    if str(output) == "-":
        typer.echo(text)
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        n = len(rows) if section in LIST_SECTIONS else 1
        console.print(f"[green]已导出 {section} × {n} 行 → {output}[/green]")


def _to_csv(rows: list[dict]) -> str:
    """简单 CSV 序列化：嵌套值转为 JSON 字符串。"""
    keys: list[str] = []
    for row in rows:
        for k in row:
            if k not in keys:
                keys.append(k)
    lines: list[str] = []
    from io import StringIO

    buf = StringIO()
    writer = csv.DictWriter(buf, fieldnames=keys)
    writer.writeheader()
    for row in rows:
        writer.writerow({k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v)
                         for k, v in row.items()})
    lines.append(buf.getvalue())
    return "".join(lines)
