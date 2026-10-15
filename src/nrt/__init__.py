"""Nusantara Retail Twin — 零售空间数字孪生与智能补货模拟引擎。

对应 docs/architecture.md 的分层：
- nrt.model          空间与商品实体（Store → Zone → Fixture → ShelfLevel → Facing → SKU）
- nrt.calendar       印尼节庆日历（斋月 / 开斋节 / Mudik / Harbolnas）
- nrt.seed           三档门店全量种子数据生成器
- nrt.forecast       需求预测引擎（Phase 4，接口已预留）
- nrt.replenishment  补货引擎（Phase 5，接口已预留）
- nrt.space          空间-存量 MILP 优化（Phase 5，接口已预留）
- nrt.lifecycle      FEFO 生命周期管理（Phase 6，接口已预留）
- nrt.sentiment      舆情信号适配器（Phase 6，接口已预留）
- nrt.cli            nrt 命令行工具
"""

from nrt.model import (
    ABCClass,
    Facing,
    Fixture,
    FixtureType,
    IslandRegion,
    ShelfLevel,
    SKU,
    StoreFormat,
    StoreProfile,
    StoreSeed,
    Zone,
    ZoneType,
)
from nrt.twin import RetailTwin

__version__ = "0.2.0"

__all__ = [
    "ABCClass",
    "Facing",
    "Fixture",
    "FixtureType",
    "IslandRegion",
    "RetailTwin",
    "ShelfLevel",
    "SKU",
    "StoreFormat",
    "StoreProfile",
    "StoreSeed",
    "Zone",
    "ZoneType",
    "__version__",
]
