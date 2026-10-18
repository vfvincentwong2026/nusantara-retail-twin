"""nrt 命令行工具。

对应 src/cli/CLI-DESIGN.md：命令即契约，输出支持 --format json 供 Agent 消费。
当前实现：seed / validate / calendar / forecast；其余命令随对应引擎落地补齐。
"""

from __future__ import annotations

import typer

from nrt.cli.commands import calendar as calendar_cmd
from nrt.cli.commands import doctor as doctor_cmd
from nrt.cli.commands import export as export_cmd
from nrt.cli.commands import forecast as forecast_cmd
from nrt.cli.commands import lifecycle as lifecycle_cmd
from nrt.cli.commands import optimize as optimize_cmd
from nrt.cli.commands import replenish as replenish_cmd
from nrt.cli.commands import seed as seed_cmd
from nrt.cli.commands import simulate as simulate_cmd
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
app.command(name="simulate", help="运行完整模拟链路（seed→forecast→replenish→optimize）")(simulate_cmd.simulate)
app.command(name="lifecycle", help="生命周期管理：FEFO/临期促销/斋月阶梯折扣")(lifecycle_cmd.lifecycle)
app.command(name="doctor", help="诊断运行环境：依赖、数据、契约文档")(doctor_cmd.doctor)
app.command(name="export", help="导出种子数据子集（JSON / CSV）")(export_cmd.export)

# TODO(Phase 6-7)：migrate / serve / sentiment 接入


def main() -> None:
    app()


if __name__ == "__main__":
    main()
