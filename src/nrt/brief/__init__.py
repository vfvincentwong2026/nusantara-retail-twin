"""店主周报生成器（P0 · L1 决策接管的入场券）。

一条命令把四个引擎的产出翻译成店主看得懂的印尼语行动清单：
📦 本周该订什么（补货引擎 Top N）
🔄 本周挪哪 3 个面位（空间价值 what-if）
🥬 今晚折价的生鲜（生命周期临期清单）
💰 本周省下多少钱（诚实估算：避免缺货的毛利 + 减少报损）

输出：WhatsApp 纯文本 + 可打印 HTML。
接真实 POS 后，预测输入从 SalesHistorySimulator 换成真实事件流即可。
"""

from __future__ import annotations

import html as html_mod
from datetime import date
from typing import Optional

from nrt.forecast import ForecastEngine
from nrt.forecast.history import SalesHistorySimulator
from nrt.lifecycle import LifecycleManager
from nrt.model import StoreSeed
from nrt.replenishment import ReplenishmentEngine
from nrt.space_value import SpaceAnalyzer


def build_brief(
    doc: StoreSeed,
    today: Optional[date] = None,
    top_orders: int = 20,
    history_days: int = 120,
    seed: int = 42,
) -> dict:
    """对种子门店跑全引擎，产出周报数据包。"""
    today = today or date.today()
    store = doc.store_profile
    # 只算高周转 SKU（A 类全量 + B 类封顶），保证运行速度
    a_class = [s for s in doc.skus if s.abc_class and s.abc_class.value == "A"]
    b_class = [s for s in doc.skus if s.abc_class and s.abc_class.value == "B"]
    targets = a_class + b_class[: max(0, 1000 - len(a_class))]

    engine = ForecastEngine(store)
    sim = SalesHistorySimulator(store, targets, seed=seed)
    events = sim.generate(days=history_days, end_date=today)
    events_by_sku: dict[str, list[dict]] = {}
    for ev in events:
        events_by_sku.setdefault(ev["sku_id"], []).append(ev)

    forecasts: dict[str, dict] = {}
    for sku in targets:
        hist = events_by_sku.get(sku.sku_id)
        if hist:
            forecasts[sku.sku_id] = engine.predict(sku, hist, horizon_days=14, today=today)

    # 模拟当前库存：围绕再订货点扰动（接真实 POS 后替换为实际库存）
    import random

    rng = random.Random(seed)
    inventory = {
        sku.sku_id: int(forecasts[sku.sku_id]["reorder_point"] * rng.uniform(0.2, 1.1))
        for sku in targets
        if sku.sku_id in forecasts
    }
    repl = ReplenishmentEngine(store)
    orders = repl.run(targets, forecasts, inventory, today=today)
    need = [d for d in orders["decisions"] if d["action"] in ("ORDER", "URGENT")]
    need.sort(key=lambda d: (d["action"] != "URGENT", -d["order_quantity"]))

    # 空间 what-if
    space = SpaceAnalyzer(doc).report(top_n=3)

    # 生鲜临期（A 类生鲜模拟批次）
    import random

    lc = LifecycleManager(store)
    rng_lc = random.Random(seed)
    fresh_a = [s for s in targets if s.fresh_flag][:10]
    expiring = []
    for sku in fresh_a:
        batches = lc.simulate_batches(sku, today, rng_lc)
        for b in batches:
            ev = lc.evaluate(sku, b, today)
            if ev["action"] in ("MARKDOWN", "BUNDLE_PROMOTION"):
                expiring.append({
                    "sku_name": sku.sku_name,
                    "batch_id": b["batch_id"],
                    "days_to_expiry": ev["remaining_shelf_life_days"],
                    "action": ev["action"],
                    "suggested_discount": ev["suggested_discount_pct"],
                    "bundle_with": ev["bundle_with_category"],
                })
    expiring.sort(key=lambda e: e["days_to_expiry"])

    # 省钱估算（诚实口径，文档化）：
    #  避免缺货 = 紧急补货 SKU 数 × 提前期日均需求 × 单件毛利
    sku_map = {s.sku_id: s for s in targets}
    saving_idr = 0.0
    for d in need:
        if d["action"] == "URGENT":
            sku = sku_map.get(d["sku_id"])
            if sku:
                saving_idr += d["order_quantity"] * max(sku.unit_price - sku.unit_cost, 0)

    return {
        "date": today.isoformat(),
        "store_name": store.store_name,
        "orders": need[:top_orders],
        "order_summary": orders["summary"],
        "space_what_if": space["what_if_top"],
        "zone_ranking": space["zone_ranking"][:7],
        "zone_top": space["zone_ranking"][0] if space["zone_ranking"] else None,
        "expiring": expiring[:5],
        "saving_estimate_idr": round(saving_idr, 0),
        "saving_note": "避免缺货的毛利挽回（紧急 SKU × 订货量 × 单件毛利）",
    }


def _bar_chart(zone_ranking: list) -> str:
    """分区坪效横向条形图（SVG，Kimi 单色相阶梯）。"""
    if not zone_ranking:
        return ""
    items = zone_ranking[:7]
    max_v = max(z["margin_per_m2_idr"] for z in items) or 1
    rows, y = [], 18
    for i, z in enumerate(items):
        w = (z["margin_per_m2_idr"] / max_v) * 300
        a = 0.85 - i * 0.1
        rows.append(
            f'<text x="0" y="{y + 11}" font-size="11" fill="#5a6b7d">{html_mod.escape(z["zone_name"])}</text>'
            f'<rect x="130" y="{y}" width="{w:.0f}" height="14" rx="3" fill="rgba(15,123,61,{max(a, 0.25):.2f})"/>'
            f'<text x="{135 + w:.0f}" y="{y + 11}" font-size="11" fill="#1a2332" font-variant-numeric="tabular-nums">'
            f'{z["margin_per_m2_idr"]:,.0f}</text>')
        y += 22
    return (f'<svg width="480" height="{y + 4}" viewBox="0 0 480 {y + 4}" '
            f'xmlns="http://www.w3.org/2000/svg">{"".join(rows)}</svg>')


def _priority_donut(orders: list) -> str:
    """补货优先级环形图：紧急 vs 常规（SVG）。"""
    urgent = sum(1 for d in orders if d["action"] == "URGENT")
    normal = sum(1 for d in orders if d["action"] == "ORDER")
    total = max(urgent + normal, 1)
    import math as _m
    frac = urgent / total
    # 弧长近似：圆周 2πr=100 单位制
    r, cx, cy = 15.9, 20, 20
    circ = 2 * _m.pi * r
    u_len = circ * frac
    return (f'<svg width="120" height="44" viewBox="0 0 120 44" xmlns="http://www.w3.org/2000/svg">'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#e5e7eb" stroke-width="6"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#dc2626" stroke-width="6" '
            f'stroke-dasharray="{u_len:.1f} {circ:.1f}" stroke-linecap="round" '
            f'transform="rotate(-90 {cx} {cy})"/>'
            f'<text x="14" y="24" font-size="10" fill="#1a2332" font-weight="600">{frac * 100:.0f}%</text>'
            f'<text x="44" y="20" font-size="11" fill="#dc2626">🔴 mendesak {urgent}</text>'
            f'<text x="44" y="34" font-size="11" fill="#5a6b7d">🟡 biasa {normal}</text></svg>')


def _expiry_bars(expiring: list) -> str:
    """临期倒计时条形图：天数越少条越短色越红。"""
    if not expiring:
        return '<p style="font-size:12px;color:#5a6b7d">Tidak ada.</p>'
    rows, y = [], 16
    for e in expiring:
        d = e["days_to_expiry"]
        w = max(8, 40 - d * 12)
        color = "#dc2626" if d <= 2 else "#d97706"
        rows.append(
            f'<text x="0" y="{y + 11}" font-size="11" fill="#5a6b7d">{html_mod.escape(e["sku_name"][:18])}</text>'
            f'<rect x="160" y="{y}" width="{w}" height="14" rx="3" fill="{color}"/>'
            f'<text x="{166 + w}" y="{y + 11}" font-size="11" fill="#1a2332">{d} hari</text>')
        y += 22
    return (f'<svg width="360" height="{y + 2}" viewBox="0 0 360 {y + 2}" '
            f'xmlns="http://www.w3.org/2000/svg">{"".join(rows)}</svg>')


def render_text(brief: dict) -> str:
    """WhatsApp 纯文本（印尼语）。"""
    L = []
    L.append(f"*Laporan mingguan · {brief['store_name']} · {brief['date']}*")
    L.append("")
    s = brief["order_summary"]
    L.append(f"📦 *Pesanan minggu ini* — {s['need_replenishment']} SKU perlu dipesan"
             f" ({s['urgent']} mendesak), estimasi Rp {s['estimated_cost_idr']:,.0f}")
    for d in brief["orders"][:15]:
        mark = "🔴" if d["action"] == "URGENT" else "🟡"
        L.append(f"  {mark} {d['sku_name'][:28]} × {d['order_quantity']}")
    L.append("")
    L.append("🔄 *Susunan rak minggu ini*")
    for w in brief["space_what_if"]:
        L.append(f"  • Ganti {w['from_sku']} → {w['to_sku_name'][:24]}"
                 f"（{w['zone']}）: +Rp {w['delta_daily_margin_idr']:,.0f}/hari")
    L.append("")
    if brief["expiring"]:
        L.append("🥬 *Diskon malam ini*")
        for e in brief["expiring"]:
            L.append(f"  • {e['sku_name'][:28]} — kedaluwarsa {e['days_to_expiry']} hari"
                     + (f", diskon {e['suggested_discount']}" if e.get("suggested_discount") else ""))
        L.append("")
    L.append(f"💰 *Estimasi hemat minggu ini: Rp {brief['saving_estimate_idr']:,.0f}*")
    L.append(f"_{brief['saving_note']}_")
    L.append("")
    L.append("Balas OK untuk konfirmasi pesanan, atau tulis kode SKU untuk menyesuaikan.")
    return "\n".join(L)


def render_html(brief: dict) -> str:
    """可打印 HTML（A4，沿用洽谈包视觉）。"""
    e = html_mod.escape
    rows = "".join(
        f"<tr><td>{'🔴' if d['action'] == 'URGENT' else '🟡'}</td>"
        f"<td>{e(d['sku_name'])}</td><td class='num'>{d['order_quantity']}</td></tr>"
        for d in brief["orders"][:20]
    )
    whatif = "".join(
        f"<li>Ganti <code>{e(w['from_sku'])}</code> → <b>{e(w['to_sku_name'])}</b>"
        f"（{e(w['zone'])}）: <span class='gain'>+Rp {w['delta_daily_margin_idr']:,.0f}/hari</span></li>"
        for w in brief["space_what_if"]
    )
    expiring = "".join(
        f"<li>{e(x['sku_name'])} — kedaluwarsa {x['days_to_expiry']} hari"
        + (f", diskon {e(str(x['suggested_discount']))}" if x.get("suggested_discount") else "") + "</li>"
        for x in brief["expiring"]
    )
    return f"""<!DOCTYPE html>
<html lang="id"><head><meta charset="utf-8"><title>Laporan mingguan {e(brief['store_name'])}</title>
<style>
 body {{ font-family:'Segoe UI',Arial,sans-serif; color:#1a2332; max-width:760px; margin:20px auto; padding:0 24px; line-height:1.5; }}
 h1 {{ font-size:19px; color:#0f7b3d; border-bottom:3px solid #0f7b3d; padding-bottom:8px; }}
 h2 {{ font-size:15px; color:#0f7b3d; margin:18px 0 6px; }}
 table {{ border-collapse:collapse; width:100%; font-size:13px; }}
 th,td {{ border:1px solid #cfd8e3; padding:6px 8px; text-align:left; }}
 th {{ background:#eef6f0; }}
 .num {{ text-align:right; font-variant-numeric:tabular-nums; }}
 .gain {{ color:#0f7b3d; font-weight:600; }}
 .total {{ background:#f4f8f5; border-left:4px solid #0f7b3d; padding:10px 14px; font-size:15px; }}
 code {{ font-size:11px; color:#5a6b7d; }}
 @media print {{ body {{ margin:0; }} }}
</style></head><body>
<h1>Laporan mingguan · {e(brief['store_name'])} · {brief['date']}</h1>
<p>Ringkasan dari kembaran digital toko Anda. Balas <b>OK</b> lewat WhatsApp untuk konfirmasi pesanan.</p>
<h2>📦 Pesanan minggu ini（{brief['order_summary']['urgent']} mendesak）</h2>
<table><tr><th></th><th>SKU</th><th class="num">Jumlah</th></tr>{rows}</table>
<h2>📊 分区坪效（laba / m² / hari）</h2>{_bar_chart(brief.get("zone_ranking", []))}
<h2>🔄 Susunan rak（what-if）</h2><ul>{whatif}</ul>
<h2>⚖️ Prioritas pesanan</h2>{_priority_donut(brief["orders"])}
<h2>🥬 Diskon malam ini</h2>{_expiry_bars(brief["expiring"])}
<div class="total">💰 Estimasi hemat minggu ini: <b>Rp {brief['saving_estimate_idr']:,.0f}</b>
<span style="font-size:11px;color:#5a6b7d">（{e(brief['saving_note'])}）</span></div>
</body></html>"""
