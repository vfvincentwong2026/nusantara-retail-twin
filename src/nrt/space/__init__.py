"""空间-存量优化器（Phase 5）。

对应 docs/architecture.md §4.3 契约：MILP 求解货架空间分配，
在单位面积利润最大化与缺货风险最小化之间动态权衡。
实现：OR-Tools（CP-SAT，整数规划）。

输入：品类列表（sku_count / 毛利 / 日周转 / 面位宽度 / 最小面位数）+
约束（品类面位上限 / 生鲜占比下限）。
输出：allocations（allocated_facings / expected_daily_profit / stockout_risk）、
objective_value、solver_status。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from ortools.linear_solver import pywraplp

from nrt.model import StoreProfile

OBJECTIVES = ("profit", "stockout_min", "balanced")


class SpaceOptimizer:
    def __init__(self, store: StoreProfile):
        self.store = store

    # ------------------------------------------------------------------
    def solve(
        self,
        categories: list[dict],
        total_facings: int,
        max_facings_per_category: Optional[dict[str, int]] = None,
        fresh_ratio_min: float = 0.0,
        fresh_categories: Optional[set[str]] = None,
        objective: str = "balanced",
        time_limit_ms: int = 5000,
    ) -> dict:
        """求解品类 → 面位分配。

        决策变量：x_c = 品类 c 分配到的面位数（整数）。
        目标：
        - profit：Σ margin_c × turnover_c × x_c（单位面积利润最大）
        - stockout_min：缺货风险近似为 1/(x_c × turnover_c)，最小化 Σ 1/(x_c·t_c)
        - balanced：利润 − λ × 缺货惩罚（λ 由毛利归一化）
        约束：Σ x_c = total_facings；x_c ≥ min_facings_required；
        x_c ≤ max_facings_per_category[c]；生鲜面位占比 ≥ fresh_ratio_min。
        """
        if objective not in OBJECTIVES:
            raise ValueError(f"未知目标：{objective}（可选 {OBJECTIVES}）")
        max_per = max_facings_per_category or {}
        fresh = fresh_categories or set()

        solver = pywraplp.Solver.CreateSolver("CP_SAT")
        if solver is None:
            raise RuntimeError("OR-Tools CP-SAT 求解器不可用")

        x: dict[str, pywraplp.Variable] = {}
        for c in categories:
            ub = max_per.get(c["category_id"], total_facings)
            x[c["category_id"]] = solver.IntVar(
                c["min_facings_required"], ub, f"x_{c['category_id']}"
            )

        # Σ x_c = total_facings
        solver.Add(solver.Sum(x[c["category_id"]] for c in categories) == total_facings)

        # 生鲜占比：Σ_fresh x_c ≥ fresh_ratio_min × total_facings
        if fresh and fresh_ratio_min > 0:
            solver.Add(
                solver.Sum(x[c["category_id"]] for c in categories if c["category_id"] in fresh)
                >= fresh_ratio_min * total_facings
            )

        # 目标函数
        profits = {
            c["category_id"]: c["avg_gross_margin"] * c["avg_daily_turnover"] for c in categories
        }
        if objective == "profit":
            solver.Maximize(solver.Sum(profits[cid] * x[cid] for cid in x))
        else:
            # balanced / stockout_min：利润 − 缺货惩罚。
            # 缺货风险的线性代理：品类实际分配低于「按需求占比的理想面位数」
            # 的缺口越大，缺货风险越高。p_c ≥ ideal_c − x_c（分段线性）。
            total_turnover = sum(c["avg_daily_turnover"] for c in categories)
            avg_profit = sum(profits.values()) / max(len(profits), 1)
            lam = (3.0 * avg_profit) if objective == "balanced" else (15.0 * avg_profit)
            penalty = {}
            for c in categories:
                cid = c["category_id"]
                ideal = total_facings * c["avg_daily_turnover"] / max(total_turnover, 1e-6)
                penalty[cid] = solver.NumVar(0, total_facings, f"p_{cid}")
                solver.Add(penalty[cid] >= ideal - x[cid])
            solver.Maximize(
                solver.Sum(profits[cid] * x[cid] for cid in x)
                - solver.Sum(lam * penalty[cid] * max(profits[cid], 1e-3) / avg_profit for cid in x)
            )

        solver.set_time_limit(time_limit_ms)
        status = solver.Solve()
        status_map = {
            pywraplp.Solver.OPTIMAL: "OPTIMAL",
            pywraplp.Solver.FEASIBLE: "FEASIBLE",
            pywraplp.Solver.INFEASIBLE: "INFEASIBLE",
            pywraplp.Solver.MODEL_INVALID: "MODEL_INVALID",
        }
        allocations = []
        for c in categories:
            cid = c["category_id"]
            facings = int(round(x[cid].solution_value())) if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE) else c["min_facings_required"]
            turnover_per_facing = max(c["avg_daily_turnover"], 1e-3)
            stockout_risk = round(min(0.9, 1.0 / (facings * turnover_per_facing)), 3)
            allocations.append(
                {
                    "category_id": cid,
                    "allocated_facings": facings,
                    "expected_daily_profit": round(facings * profits[cid], 2),
                    "stockout_risk": stockout_risk,
                }
            )
        tz7 = timezone(timedelta(hours=7))
        return {
            "planogram_id": str(uuid.uuid4()),
            "store_id": self.store.store_id,
            "generated_at": datetime.now(tz7).isoformat(timespec="seconds"),
            "allocations": allocations,
            "objective_value": round(solver.Objective().Value(), 2) if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE) else 0,
            "solver_status": status_map.get(status, str(status)),
            "objective": objective,
            "total_facings": total_facings,
        }
