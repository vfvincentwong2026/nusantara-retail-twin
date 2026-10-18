"""历史销售模拟器。

在接入真实 POS 数据前（Phase 8），为种子门店生成确定性的合成销售历史，
用于驱动需求预测引擎的开发与验证。生成规则贴近印尼零售现实：

- 速度按 ABC 分层：A 类 8–20 件/日，B 类 3–8，C 类 0.5–3
- 周末上浮（印尼家庭集中采购）：周六/周日 ×1.15–1.35
- 斋月窗口按品类乘数曲线（docs/ramadan-calendar-2026.md §2）
- Mudik 期间 Java 大城市回落 / 外岛抬升
- 生鲜（fresh_flag）波动系数高于常温品
"""

from __future__ import annotations

import math
import random
from datetime import date, timedelta
from typing import Optional

from nrt.calendar import IndonesiaCalendar
from nrt.model import SKU, StoreProfile

# ABC 基准日销（件/日）
ABC_VELOCITY = {"A": (8.0, 20.0), "B": (3.0, 8.0), "C": (0.5, 3.0)}
WEEKEND_BUMP = {5: (1.15, 1.35), 6: (1.15, 1.30)}  # 周五（礼拜后采购）/周六
FRESH_CV = 0.45  # 生鲜波动系数
AMBIENT_CV = 0.28

# 品类 → 日历模块的 category key（src/nrt/seed/catalog.py 的 related 字段口径）
CATEGORY_KEY = {
    "方便面": "food", "饼干": "food", "食用油": "food", "大米": "food", "调味品": "food",
    "咖啡": "food", "茶": "beverages", "饮料": "beverages", "零食": "food", "乳制品": "food",
    "冷冻食品": "food", "清洁用品": "household", "洗护用品": "household", "母婴用品": "household",
    "厨具家居": "household", "穆斯林服饰": "fashion", "美妆个护": "beauty", "文具": "none",
    "蔬菜": "food", "水果": "food", "鲜肉": "food", "海鲜": "food", "鸡蛋": "food",
}


class SalesHistorySimulator:
    """为一家门店生成 Store × SKU × Day 的合成销售事件。"""

    def __init__(
        self,
        store: StoreProfile,
        skus: list[SKU],
        calendar: Optional[IndonesiaCalendar] = None,
        seed: int = 42,
    ):
        self.store = store
        self.skus = skus
        self.cal = calendar or IndonesiaCalendar(year=2026)
        self.rng = random.Random(seed)

    def _velocity_of(self, sku: SKU) -> float:
        lo, hi = ABC_VELOCITY[sku.abc_class.value if sku.abc_class else "C"]
        v = self.rng.uniform(lo, hi)
        if sku.fresh_flag:
            v *= 1.15  # 生鲜周转更快
        return v

    def generate(self, days: int = 150, end_date: Optional[date] = None) -> list[dict]:
        """生成销售事件列表，契约字段对应 docs/data-model.md §4.2。"""
        end = end_date or date.today()
        start = end - timedelta(days=days - 1)
        ramadan = self.cal.get_demand_multipliers(
            self.store.island_region.value, category=None
        )
        mult_by_date = {m["date"]: m["multiplier"] for m in ramadan}

        events: list[dict] = []
        for sku in self.skus:
            base = self._velocity_of(sku)
            cv = FRESH_CV if sku.fresh_flag else AMBIENT_CV
            cat_key = CATEGORY_KEY.get(sku.category_name)
            # 斋月品类峰值差异在窗口内叠加（§2.2）
            cat_peak = self.cal.get_demand_multipliers(self.store.island_region.value, category=cat_key)
            cat_mult = {m["date"]: m["multiplier"] for m in cat_peak}
            theta = self.rng.uniform(0, 2 * math.pi)  # 相位错开，避免全店同涨同跌
            day = start
            while day <= end:
                dow = day.weekday()
                weekend = self.rng.uniform(*WEEKEND_BUMP.get(dow, (1.0, 1.0)))
                seasonal = 1 + 0.08 * math.sin(2 * math.pi * (day - start).days / 30 + theta)
                dstr = day.isoformat()
                m_ramadan = mult_by_date.get(dstr, 1.0)
                m_cat = cat_mult.get(dstr, 1.0)
                # 品类峰值与全店曲线取几何平均，避免叠加过度
                m_event = math.sqrt(m_ramadan * m_cat) if m_ramadan != 1.0 or m_cat != 1.0 else 1.0
                lam = base * weekend * seasonal * m_event
                qty = _poisson(self.rng, lam)
                if qty > 0:
                    events.append(
                        {
                            "store_id": self.store.store_id,
                            "sku_id": sku.sku_id,
                            "facing_id": None,
                            "event_date": dstr,
                            "quantity_sold": qty,
                            "unit_price": sku.unit_price,
                            "promotion_flag": False,
                            "promotion_type": None,
                        }
                    )
                day += timedelta(days=1)
        return events

    def generate_pos(
        self,
        days: int = 365,
        end_date: Optional[date] = None,
        stockout_rate: float = 0.03,
        promo_rate: float = 0.02,
        wastage_rate: float = 0.05,
    ) -> dict:
        """生成带「真实 POS 脏特征」的合成数据（Phase 8 试点演练用）。

        在 generate() 的事件流基础上叠加：
        - 缺货删失：按 stockout_rate 丢失整天销售（POS 里是 0，不是低需求）
        - 促销尖峰：按 promo_rate 注入 ×1.8 促销日（promotion_flag=True）
        - 生鲜报损：按 wastage_rate 生成 wastage 记录（复盘损耗率用）
        """
        sales = self.generate(days=days, end_date=end_date)
        rng = random.Random(self.rng.random())
        fresh_ids = {s.sku_id for s in self.skus if s.fresh_flag}

        censored = [e for e in sales if rng.random() < stockout_rate]
        for e in censored:
            e["quantity_sold"] = 0  # 删失：当天 POS 显示 0，真需求未知
            e["censored"] = True

        promoted = [e for e in sales if not e.get("censored") and rng.random() < promo_rate]
        for e in promoted:
            e["quantity_sold"] = int(round(e["quantity_sold"] * 1.8))
            e["promotion_flag"] = True
            e["promotion_type"] = "instore_bundle"

        wastage = []
        for e in sales:
            if e["sku_id"] in fresh_ids and e["quantity_sold"] > 0 and rng.random() < wastage_rate:
                wastage.append(
                    {
                        "store_id": e["store_id"],
                        "sku_id": e["sku_id"],
                        "event_date": e["event_date"],
                        "quantity_wasted": max(1, int(round(e["quantity_sold"] * rng.uniform(0.05, 0.3)))),
                        "reason": "expiry",
                    }
                )
        return {
            "store_id": self.store.store_id,
            "days": days,
            "sales": sorted(sales, key=lambda e: (e["sku_id"], e["event_date"])),
            "wastage": wastage,
            "summary": {
                "sale_events": len(sales),
                "censored_days": len(censored),
                "promo_events": len(promoted),
                "wastage_events": len(wastage),
            },
        }


def _poisson(rng: random.Random, lam: float) -> int:
    """Knuth 泊松采样；lam 较大时用高斯近似（带 cv 放大尾部）。"""
    if lam <= 0:
        return 0
    if lam < 30:
        l = math.exp(-lam)
        k = 0
        p = 1.0
        while p > l:
            k += 1
            p *= rng.random()
        return k - 1
    # 大均值：正态近似，右尾略厚（零售现实的爆发性团购）
    z = rng.gauss(0, 1)
    if z > 1.5:
        z += rng.random() * 0.8
    return max(0, int(round(lam + math.sqrt(lam) * z)))
