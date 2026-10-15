"""nrt 命令行工具。

对应 src/cli/CLI-DESIGN.md：命令即契约，输出支持 --format json 供 Agent 消费。
当前实现（Phase 2）：seed / validate / calendar；其余命令随对应引擎落地补齐。
"""

from __future__ import annotations

import typer

from nrt.cli.commands import calendar as calendar_cmd
from nrt.cli.commands import seed as seed_cmd
from nrt.cli.commands import validate as validate_cmd

app = typer.Typer(
    name="nrt",
    help="Nusantara Retail Twin — 零售空间数字孪生与智能补货模拟 CLI",
    no_args_is_help=True,
    add_completion=False,
)
app.command(name="seed", help="生成门店全量种子数据")(seed_cmd.seed)
app.command(name="validate", help="校验种子数据与数据模型一致性")(validate_cmd.validate)
app.command(name="calendar", help="查询印尼节庆日历")(calendar_cmd.calendar_cmd)

# TODO(Phase 3-6)：migrate / forecast / replenish / optimize / simulate / serve / export / doctor


def main() -> None:
    app()


if __name__ == "__main__":
    main()
