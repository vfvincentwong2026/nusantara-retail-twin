"""`nrt migrate` — 种子文件版本迁移。

把旧版种子 JSON 升级到当前模型版本：补缺失字段、更新 meta.seed_version。
迁移规则可叠加：MIGRATIONS[v] = 从 v 升到下一版的变换函数。
"""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

console = Console()

CURRENT_VERSION = "0.3"

# v0.2 → v0.3：新增舆情适配器所需的 meta.sentiment_defaults 占位
def _v02_to_v03(doc: dict) -> dict:
    doc.setdefault("meta", {})["sentiment_defaults"] = {
        "halal_trust_weight": 1.5,
        "multiplier_cap": 0.25,
        "source": "synthetic",
    }
    return doc


MIGRATIONS = {"0.2": _v02_to_v03}


def migrate(
    files: list[Path] = typer.Argument(..., exists=True, help="种子 JSON 文件（可多个）"),
    in_place: bool = typer.Option(False, "--in-place", help="原地覆盖（默认输出 *_migrated.json）"),
) -> None:
    """将种子文件迁移到当前版本。"""

    for f in files:
        doc = json.loads(Path(f).read_text(encoding="utf-8"))
        ver = str(doc.get("meta", {}).get("seed_version", "0.1"))
        steps = []
        while ver in MIGRATIONS:
            doc = MIGRATIONS[ver](doc)
            steps.append(f"{ver}→{MIGRATIONS and _next(ver)}")
            ver = _next(ver)
        doc.setdefault("meta", {})["seed_version"] = CURRENT_VERSION
        doc["meta"]["migrated_from"] = str(f)
        out = f if in_place else f.with_name(f.stem + "_migrated.json")
        Path(out).write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
        console.print(f"[green]{f.name}[/green] {' → '.join(steps) or '无变换'} → v{CURRENT_VERSION} → {out}")


def _next(ver: str) -> str:
    major, minor = ver.split(".")
    return f"{major}.{int(minor) + 1}"
