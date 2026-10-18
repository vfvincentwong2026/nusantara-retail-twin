"""nrt 命令行工具。

对应 src/cli/CLI-DESIGN.md：命令即契约，输出支持 --format json 供 Agent 消费。
当前实现：seed / validate / calendar / forecast；其余命令随对应引擎落地补齐。
"""

from __future__ import annotations

import typer

from nrt.cli.commands import calendar as calendar_cmd
from nrt.cli.commands import forecast as forecast_cmd
from nrt.cli.commands import optimize as optimize_cmd
from nrt.cli.commands import replenish as replenish_cmd
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
app.command(name="forecast", help="运行需求预测引擎")(forecast_cmd.forecast)
app.command(name="replenish", help="运行补货引擎")(replenish_cmd.replenish)
app.command(name="optimize", help="运行空间-存量 MILP 优化")(optimize_cmd.optimize)

# TODO(Phase 6)：migrate / simulate / serve / export / doctor


def main() -> None:
    app()


if __name__ == "__main__":
    main()
