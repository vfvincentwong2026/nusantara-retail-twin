"""生成 web 前端演示用种子数据（web/public/seeds/）。

演示数据保留完整空间结构（zones / fixtures / shelf_levels / facings），
SKU 目录按规模压缩（约 1/10），保证 facing → sku 引用完整且文件可入 git。
全量数据请使用 `nrt seed` 生成。
"""

from __future__ import annotations

import json
from pathlib import Path

from nrt.seed import SeedGenerator

WEB_SKU_COUNT = {500: 600, 2000: 1200, 5000: 2500}
OUT = Path(__file__).resolve().parent.parent / "web" / "public" / "seeds"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for size, sku_count in WEB_SKU_COUNT.items():
        doc = SeedGenerator(store_size=size, region="java", seed=42, sku_count=sku_count).generate()
        doc["meta"]["source"] += " （web demo：SKU 目录压缩，空间结构完整）"
        path = OUT / f"store_{size}sqm_demo.json"
        path.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        s = doc["generation_summary"]
        print(f"✓ {path.name}  SKU {s['skus_count']}  Facings {s['facings_count']}  "
              f"{path.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
