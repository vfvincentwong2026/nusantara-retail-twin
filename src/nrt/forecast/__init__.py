"""需求预测引擎（Phase 4）。

对应 docs/architecture.md §4.1 契约：
- 粒度 Store × SKU × Day，最小历史 90 天
- 输出 demand_mean / demand_p90 / safety_stock / reorder_point /
  suggested_order_quantity / confidence / model_version

架构原则「可替换的预测层」：ForecastEngine 是基线实现（可解释的时间序列
分解：周季节律 × 节庆乘数 × Mudik 偏移），满足同一输入输出契约的
Prophet + LightGBM 实现（model_version = prophet-lgbm-v0.2）可在不改动
调用方的情况下替换。
"""

from __future__ import annotations

import math
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from nrt.calendar import IndonesiaCalendar, ISLAND_LOGISTICS
from nrt.model import SKU, StoreProfile
from nrt.forecast.history import CATEGORY_KEY

MODEL_VERSION = "baseline-v0.2"
Z_SERVICE = 1.65  # ~95% 服务水平


class ForecastEngine:
    """基线预测器：历史 weekday 均值 × 事件乘数 + 提前期安全库存。"""

    def __init__(
        self,
        store: StoreProfile,
        calendar: Optional[IndonesiaCalendar] = None,
    ):
        self.store = store
        self.cal = calendar or IndonesiaCalendar(year=2026)

    # ------------------------------------------------------------------
    def predict(
        self,
        sku: SKU,
        historical_sales: list[dict],
        horizon_days: int = 30,
        include_ramadan: bool = False,
        today: Optional[date] = None,
    ) -> dict:
        """单 SKU 预测，输出严格遵循 §4.1 输出契约。"""
        if len(historical_sales) < 90:
            raise ValueError(f"历史数据不足 90 天：{len(historical_sales)} 天")
        today = today or date.today()

        by_dow: list[list[int]] = [[] for _ in range(7)]
        daily: list[tuple[date, int]] = []
        for e in historical_sales:
            d = date.fromisoformat(e["event_date"])
            by_dow[d.weekday()].append(e["quantity_sold"])
            daily.append((d, e["quantity_sold"]))

        dow_mean = [(_mean(v) if v else 1.0) for v in by_dow]
        overall = _mean([q for _, q in daily])

        # 历史残差 → 预测区间宽度
        residuals = []
        for d, q in daily:
            expected = dow_mean[d.weekday()]
            if expected > 0:
                residuals.append((q - expected) / expected)
        cv = _std(residuals) if len(residuals) > 5 else 0.3

        # 事件乘数（可选斋月窗口）
        cat_key = CATEGORY_KEY.get(sku.category_name)
        mults: dict[str, float] = {}
        if include_ramadan:
            for m in self.cal.get_demand_multipliers(self.store.island_region.value, category=cat_key):
                mults[m["date"]] = m["multiplier"]

        start = today + timedelta(days=1)
        daily_forecast = []
        for i in range(horizon_days):
            d = start + timedelta(days=i)
            base = dow_mean[d.weekday()] * (overall / max(_mean(dow_mean), 1e-6))
            m = mults.get(d.isoformat(), 1.0)
            mean = max(base * m, 0.05)
            p90 = mean * (1 + Z_SERVICE * cv)
            daily_forecast.append(
                {
                    "date": d.isoformat(),
                    "demand_mean": round(mean, 2),
                    "demand_p90": round(p90, 2),
                }
            )

        # 安全库存 / 再订货点 / 建议订货量（§4.2 输入契约）
        logistics = ISLAND_LOGISTICS[self.store.island_region.value]
        lt_mean = logistics["lead_time_mean_days"]
        lt_std = logistics["lead_time_std_days"]
        k = logistics["k_factor"]
        lt_eff = lt_mean + k * lt_std  # LT_eff = LT_mean + k × σ_LT
        daily_mean = _mean([f["demand_mean"] for f in daily_forecast[: int(math.ceil(lt_eff))]]) or overall
        lt_demand_std = daily_mean * cv * math.sqrt(lt_eff)
        safety_stock = math.ceil(Z_SERVICE * lt_demand_std)
        reorder_point = math.ceil(daily_mean * lt_eff) + safety_stock
        # 建议订货量：补到 ROP + 一个有效提前期的需求，生鲜受保质期约束
        target = reorder_point + daily_mean * lt_eff
        if sku.fresh_flag and sku.shelf_life_days:
            max_shelf_units = daily_mean * min(sku.shelf_life_days * 0.6, 10)
            target = min(target, max(max_shelf_units, daily_mean * 2))
        suggested = max(0, math.ceil(target))

        confidence = max(0.4, min(0.95, 1 - cv * 0.8))
        tz7 = timezone(timedelta(hours=7))
        return {
            "forecast_id": str(uuid.uuid4()),
            "store_id": self.store.store_id,
            "sku_id": sku.sku_id,
            "sku_code": sku.sku_code,
            "sku_name": sku.sku_name,
            "generated_at": datetime.now(tz7).isoformat(timespec="seconds"),
            "horizon": {
                "start_date": start.isoformat(),
                "end_date": (start + timedelta(days=horizon_days - 1)).isoformat(),
                "daily_forecast": daily_forecast,
            },
            "safety_stock": safety_stock,
            "reorder_point": reorder_point,
            "suggested_order_quantity": suggested,
            "confidence": round(confidence, 3),
            "model_version": MODEL_VERSION,
        }


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _std(xs: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    m = _mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))
