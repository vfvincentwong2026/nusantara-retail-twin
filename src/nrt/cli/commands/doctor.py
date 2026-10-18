"""`nrt doctor` — 环境诊断。

纯 stdlib 实现，检查 Python 版本、第三方依赖、数据目录与契约文档，
输出结构化诊断结果，供 Agent 或用户快速定位环境问题。
"""

from __future__ import annotations

import json
import platform
import sys
from pathlib import Path

import typer
from rich.console import Console

console = Console()

DEPS = ["typer", "pydantic", "rich", "numpy", "ortools"]
ROOT = Path(__file__).resolve().parents[4]
SEED_SIZES = ["500", "2000", "5000"]


def _check(ok: bool) -> str:
    return "✅" if ok else "❌"


def doctor(
    format_: str = typer.Option("text", "--format", "-f", help="输出格式：text / json"),
) -> None:
    """诊断运行环境：依赖、数据、契约文档。"""
    results: dict = {"checks": [], "ok": True}

    def add(name: str, ok: bool, detail: str) -> None:
        results["checks"].append({"name": name, "ok": ok, "detail": detail})
        if not ok:
            results["ok"] = False

    py = sys.version_info
    add("python", py >= (3, 10),
        f"{platform.python_version()} ({'要求 >=3.10' if py < (3, 10) else '满足 >=3.10'})")

    for dep in DEPS:
        try:
            mod = __import__(dep)
            ver = getattr(mod, "__version__", "?")
            add(f"dep:{dep}", True, f"{ver}")
        except ImportError:
            add(f"dep:{dep}", False, "未安装")

    seeds_dir = ROOT / "data" / "seeds"
    add("dir:data/seeds", seeds_dir.is_dir(),
        str(seeds_dir) if seeds_dir.is_dir() else "缺失（运行 nrt seed 生成）")
    if seeds_dir.is_dir():
        for size in SEED_SIZES:
            f = seeds_dir / f"store_{size}sqm_full.json"
            add(f"seed:{size}sqm", f.exists(),
                f"{f.stat().st_size / 1e6:.1f} MB" if f.exists() else "缺失（运行 nrt seed --store-size " + size + "）")

    for doc in ["docs/architecture.md", "docs/data-model.md", "src/cli/CLI-DESIGN.md"]:
        add(f"doc:{doc}", (ROOT / doc).exists(), "存在" if (ROOT / doc).exists() else "缺失")

    if format_ == "json":
        typer.echo(json.dumps(results, ensure_ascii=False, indent=2))
        if not results["ok"]:
            raise typer.Exit(code=1)
        return

    for c in results["checks"]:
        console.print(f"{_check(c['ok'])}  {c['name']:<28} {c['detail']}")
    console.print()
    if results["ok"]:
        console.print("[green]环境健康，全部检查通过。[/green]")
    else:
        console.print("[red]存在失败项，请按提示修复后重试。[/red]")
        raise typer.Exit(code=1)
