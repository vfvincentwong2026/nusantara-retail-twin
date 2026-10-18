"""预测精度回测（walk-forward MAPE）。

用合成 POS 数据（nrt synth-pos）验证基线引擎精度，并与挑战者模型打擂台。
挑战者 = Holt 双指数平滑（趋势）× 周内季节指数，纯 numpy 实现，
用于量化「换 Prophet/LightGBM 之前，简单升级能拿多少收益」。

评估协议：每个 SKU 取末尾 horizon 天为验证集，此前全部为训练集；
MAPE 仅在验证窗口内计算，按 ABC 分层汇总。
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

import numpy as np

from nrt.model import SKU, StoreProfile
from nrt.forecast import ForecastEngine


def _daily_series(events: list[dict], start: date, days: int) -> np.ndarray:
    """把事件流（含缺货删零）展开成连续日销量数组。"""
    qty = {date.fromisoformat(e["event_date"]): e["quantity_sold"] for e in events}
    return np.array([qty.get(start + timedelta(days=i), 0) for i in range(days)], dtype=float)


def holt_dow_forecast(series: np.ndarray, horizon: int, alpha: float = 0.4,
                      beta: float = 0.1) -> np.ndarray:
    """Holt 双指数平滑 + 乘性周内季节指数。返回 horizon 天预测。"""
    n = len(series)
    if n < 14:
        return np.full(horizon, series[-1] if n else 0.0)
    level = series[0]
    trend = (series[1:8].mean() - series[0:7].mean()) / 7 if n >= 8 else 0.0
    for t in range(n):
        prev = level
        level = alpha * series[t] + (1 - alpha) * (level + trend)
        trend = beta * (level - prev) + (1 - beta) * trend
    dow_idx = np.arange(n) % 7
    dow_mean = np.array([series[dow_idx == i].mean() if (dow_idx == i).any() else series.mean()
                         for i in range(7)])
    dow_factor = dow_mean / max(dow_mean.mean(), 1e-6)
    last_dow = (n - 1) % 7
    out = []
    for h in range(horizon):
        raw = level + (h + 1) * trend
        out.append(max(raw * dow_factor[(last_dow + 1 + h) % 7], 0.05))
    return np.array(out)


def mape(actual: np.ndarray, forecast: np.ndarray) -> float:
    """MAPE，仅在 actual > 0 的样本上计算（避免删失日除零）。"""
    mask = actual > 0
    if not mask.any():
        return float("nan")
    return float(np.mean(np.abs((actual[mask] - forecast[mask]) / actual[mask])))


def backtest_sku(
    sku: SKU,
    store: StoreProfile,
    events: list[dict],
    horizon: int = 14,
    today: Optional[date] = None,
) -> Optional[dict]:
    """单 SKU 回测：基线引擎 vs Holt-DOW 挑战者。历史不足 90 天返回 None。"""
    if not events:
        return None
    dates = sorted(date.fromisoformat(e["event_date"]) for e in events)
    covered = (dates[-1] - dates[0]).days + 1
    if covered < 90 + horizon:
        return None
    end = dates[-1]
    today = today or (end - timedelta(days=horizon))

    train = [e for e in events if date.fromisoformat(e["event_date"]) <= today]
    actual_events = [e for e in events if date.fromisoformat(e["event_date"]) > today]
    actual = _daily_series(actual_events, today + timedelta(days=1), horizon)

    # 基线引擎（删失日按 0 参与 weekday 均值——真实 POS 场景的朴素做法）
    engine = ForecastEngine(store)
    try:
        pred = engine.predict(sku, train, horizon_days=horizon, today=today)
        baseline_fc = np.array([f["demand_mean"] for f in pred["horizon"]["daily_forecast"]])
    except ValueError:
        return None

    train_series = _daily_series(train, dates[0], (today - dates[0]).days + 1)
    challenger_fc = holt_dow_forecast(train_series, horizon)

    return {
        "sku_id": sku.sku_id,
        "abc_class": sku.abc_class.value if sku.abc_class else "C",
        "fresh": bool(sku.fresh_flag),
        "baseline_mape": round(mape(actual, baseline_fc), 4),
        "challenger_mape": round(mape(actual, challenger_fc), 4),
    }


def summarize(rows: list[dict]) -> dict:
    """按 ABC 分层与整体汇总 MAPE。"""

    def agg(sub: list[dict], key: str) -> dict:
        vals = [r[key] for r in sub if r[key] == r[key]]  # 过滤 NaN
        return {"n": len(vals), "mape_mean": round(float(np.mean(vals)), 4) if vals else None}

    out: dict = {"overall": {"n": len(rows)}}
    for key in ("baseline_mape", "challenger_mape"):
        out["overall"][key] = agg(rows, key)["mape_mean"]
    for cls in ("A", "B", "C"):
        sub = [r for r in rows if r["abc_class"] == cls]
        out[f"abc_{cls}"] = {
            "n": len(sub),
            "baseline_mape": agg(sub, "baseline_mape")["mape_mean"],
            "challenger_mape": agg(sub, "challenger_mape")["mape_mean"],
        }
    fresh = [r for r in rows if r["fresh"]]
    out["fresh"] = {
        "n": len(fresh),
        "baseline_mape": agg(fresh, "baseline_mape")["mape_mean"],
        "challenger_mape": agg(fresh, "challenger_mape")["mape_mean"],
    }
    return out
