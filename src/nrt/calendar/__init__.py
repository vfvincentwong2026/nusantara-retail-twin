"""印尼节庆日历模块。

数据来自 docs/ramadan-calendar-2026.md（政府官方日期为准）：
- 斋月首日 2026-02-19（Kemenag Sidang Isbat）
- 开斋节 2026-03-21
- Mudik 峰值 2026-03-18
- 支持 muhammadiyah_offset 应对一天差异
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional, Union

# ---------------------------------------------------------------------------
# 2026 年印尼零售相关节庆（docs/ramadan-calendar-2026.md §5）
# ---------------------------------------------------------------------------
EVENTS_2026: list[dict] = [
    {"name": "New Year", "zh_name": "元旦", "date": "2026-01-01", "type": "national", "impact_weight": 0.4, "window_weeks": 1},
    {"name": "Isra Mikraj", "zh_name": "登霄节", "date": "2026-01-16", "type": "religious", "impact_weight": 0.1, "window_weeks": 0},
    {"name": "Imlek", "zh_name": "春节", "date": "2026-02-17", "type": "cultural", "impact_weight": 0.4, "window_weeks": 0},
    {"name": "Ramadan Start", "zh_name": "斋月首日", "date": "2026-02-19", "type": "religious", "impact_weight": 1.0, "window_weeks": 6, "related_categories": ["food", "beverages", "fashion", "gift"]},
    {"name": "Nyepi", "zh_name": "静居日", "date": "2026-03-19", "type": "religious", "impact_weight": 0.1, "window_weeks": 0},
    {"name": "Mudik Peak", "zh_name": "Mudik 返乡峰值", "date": "2026-03-18", "type": "cultural", "impact_weight": 0.8, "window_weeks": 3},
    {"name": "Idul Fitri", "zh_name": "开斋节", "date": "2026-03-21", "type": "religious", "impact_weight": 1.0, "window_weeks": 4, "related_categories": ["food", "fashion", "gift", "home_appliance"]},
    {"name": "Good Friday", "zh_name": "耶稣受难日", "date": "2026-04-03", "type": "religious", "impact_weight": 0.1, "window_weeks": 0},
    {"name": "Labor Day", "zh_name": "劳动节", "date": "2026-05-01", "type": "national", "impact_weight": 0.4, "window_weeks": 0},
    {"name": "Idul Adha", "zh_name": "宰牲节", "date": "2026-05-27", "type": "religious", "impact_weight": 0.4, "window_weeks": 0},
    {"name": "Back to School", "zh_name": "返校季", "date": "2026-07-01", "type": "cultural", "impact_weight": 0.7, "window_weeks": 4},
    {"name": "Independence Day", "zh_name": "独立日", "date": "2026-08-17", "type": "national", "impact_weight": 0.4, "window_weeks": 1},
    {"name": "Harbolnas", "zh_name": "电商节", "date": "2026-12-10", "end_date": "2026-12-16", "type": "commercial", "impact_weight": 0.7, "window_weeks": 1},
    {"name": "Christmas", "zh_name": "圣诞节", "date": "2026-12-25", "type": "religious", "impact_weight": 0.4, "window_weeks": 0},
]

# Mudik 效应参数（docs/ramadan-calendar-2026.md §3.2）
MUDIK_OFFSETS = {
    "java": -7,        # Java 大城市：需求提前 7 天下降
    "sumatra": 7,      # 节后延迟 7 天上升
    "kalimantan": 5,
    "sulawesi": 3,
    "papua": 3,
}

# 岛屿物流参数（docs/data-model.md §5.2 + README：k 系数）
ISLAND_LOGISTICS = {
    "java": {"lead_time_mean_days": 3.0, "lead_time_std_days": 1.0, "k_factor": 0.5, "cold_chain_available": True},
    "sumatra": {"lead_time_mean_days": 5.0, "lead_time_std_days": 1.5, "k_factor": 1.0, "cold_chain_available": True},
    "kalimantan": {"lead_time_mean_days": 6.0, "lead_time_std_days": 2.0, "k_factor": 1.0, "cold_chain_available": False},
    "sulawesi": {"lead_time_mean_days": 8.0, "lead_time_std_days": 3.0, "k_factor": 1.5, "cold_chain_available": False},
    "papua": {"lead_time_mean_days": 12.0, "lead_time_std_days": 5.0, "k_factor": 1.5, "cold_chain_available": False},
}

# 斋月内销售强度（docs/ramadan-calendar-2026.md §2.1）
_RAMADAN_STAGE_INTENSITY = [
    # (起始日偏移, 结束日偏移, 强度) —— 相对斋月首日
    (0, 9, 1.2),    # 前冲量期 60% → 乘数 1.2
    (10, 19, 1.6),  # 中段 80%
    (20, 30, 2.2),  # 最后冲刺 100%（峰值 ×2.2）
]

# 品类峰值差异（§2.2）：category_key → 峰值乘数
CATEGORY_RAMADAN_PEAK = {
    "food": 2.5,
    "beverages": 2.5,
    "fashion": 3.5,
    "gift": 2.2,
    "home_appliance": 2.0,
    "beauty": 1.8,
    "household": 1.4,
}


class IndonesiaCalendar:
    """印尼节庆日历。默认年份 2026（数据已由政府公告确认）。"""

    def __init__(self, year: int = 2026, muhammadiyah_offset: int = 0):
        if year != 2026:
            raise ValueError("当前仅内置 2026 年官方日历（docs/ramadan-calendar-2026.md）")
        self.year = year
        self.muhammadiyah_offset = muhammadiyah_offset
        self.ramadan_start = date(2026, 2, 19) + timedelta(days=muhammadiyah_offset)
        self.lebaran = date(2026, 3, 21) + timedelta(days=muhammadiyah_offset)
        self.peak_date = date(2026, 3, 13) + timedelta(days=muhammadiyah_offset)
        self.mudik_peak = date(2026, 3, 18) + timedelta(days=muhammadiyah_offset)

    # ------------------------------------------------------------------
    def events(self) -> list[dict]:
        return [dict(e) for e in EVENTS_2026]

    def get_ramadan_window(self, pre_weeks: int = 8, post_weeks: int = 2) -> dict:
        """斋月影响窗口（默认前置 8 周 + 后置 2 周）。"""
        return {
            "start": (self.ramadan_start - timedelta(weeks=pre_weeks)).isoformat(),
            "end": (self.lebaran + timedelta(weeks=post_weeks)).isoformat(),
            "ramadan_start": self.ramadan_start.isoformat(),
            "lebaran": self.lebaran.isoformat(),
        }

    def get_mudik_offset(self, island_region: str) -> int:
        return MUDIK_OFFSETS.get(island_region, 0)

    def pre_replenishment_windows(self, island_region: str = "java") -> list[dict]:
        """前置补货窗口（§4.1：区域差异化）。"""
        k = ISLAND_LOGISTICS[island_region]["k_factor"]
        first_weeks = {0.5: 6, 1.0: 8, 1.5: 10}[k]
        round1_start = self.ramadan_start - timedelta(weeks=first_weeks)
        round1_end = round1_start + timedelta(days=14)
        round2_start = self.ramadan_start - timedelta(days=14)
        round2_end = round2_start + timedelta(days=4)
        return [
            {"round": 1, "start": round1_start.isoformat(), "end": round1_end.isoformat(), "scope": "节庆品"},
            {"round": 2, "start": round2_start.isoformat(), "end": round2_end.isoformat(), "scope": "生鲜/即时"},
        ]

    def get_demand_multipliers(
        self,
        island_region: str = "java",
        category: Optional[str] = None,
    ) -> list[dict]:
        """生成斋月窗口内逐日需求乘数序列（含 Mudik 区域偏移）。"""
        peak = CATEGORY_RAMADAN_PEAK.get(category, 1.5) if category else 2.0
        base = 2.2  # 最后冲刺基准
        scale = peak / base
        offset = self.get_mudik_offset(island_region)

        result = []
        day = self.ramadan_start
        while day <= self.lebaran:
            rel = (day - self.ramadan_start).days
            for start, end, intensity in _RAMADAN_STAGE_INTENSITY:
                if start <= rel <= end:
                    m = 1 + (intensity - 1) * scale
                    break
            else:
                m = 1.0
            # Mudik：城市需求提前回落 / 外岛节后抬升
            mudik_rel = (day - self.mudik_peak).days
            if island_region == "java" and 0 <= mudik_rel <= 7:
                m *= 0.6
            elif island_region != "java" and -3 <= mudik_rel <= 7:
                m *= 1.3
            result.append({"date": day.isoformat(), "multiplier": round(m, 3)})
            day += timedelta(days=1)
        return result

    def ramadan_summary(self, island_region: str = "java") -> dict:
        """种子文档所需的 ramadan_calendar_2026 字段。"""
        return {
            "ramadan_start": self.ramadan_start.isoformat(),
            "lebaran_date": self.lebaran.isoformat(),
            "peak_date": self.peak_date.isoformat(),
            "mudik_peak_date": self.mudik_peak.isoformat(),
            "pre_replenishment_windows": self.pre_replenishment_windows(island_region),
        }
