# 项目日志 / Changelog

记录每次推进的产出与决策，最新在前。

---

## 2026-10-19 · 空间价值 + 洽谈弹药 + UI 设计系统

**产品决策（PM 评审）**
- 定位修正：不是补货工具，是「沃尔玛级零售智能下沉为印尼 400 万独立店基础设施」；数据飞轮（L0 周报 → L1 决策接管 → L2 供应商协同 → L3 网络效应）是护城河
- 核心洞察来自与沃尔玛/山姆 20 年店长交流：**店主对空间是盲的**——空间价值可视化 + 挪位增收 what-if 是差异化主菜，补货只是入场券
- 验证方法：无真实门店期间，用合成数据 dogfood 全部闭环

**产出**
- `nrt space-report`：分区坪效榜（500㎡ 店实测：入口促销区 892k vs 食品杂货 75k IDR/㎡/日，12 倍差）+ 品类内末位面位 + 挪位增收建议（头名 +Rp 7.0 M/日）
- 回测三模型擂台（5004 SKU × 365 天）：C 类 Croston-SBA 48.2% 优于基线 56.3%；分段选型落地 `hybrid-v0.3`，整体 MAPE 48.2% → 44.3%
- `nrt synth-pos`（合成 POS：缺货删零/促销/报损）+ `nrt backtest`（walk-forward MAPE）
- `nrt migrate` / `nrt serve`（agent-bridge 入口）——CLI 16 令齐备，代码 TODO 清零
- 洽谈包 `docs/pilot/pitch/`：印尼语 A4 一页提案（数字全部来自模拟）+ WhatsApp 话术
- Web UI 按 Kimi 设计系统重设计：13 枚极简线框图标、深色交互强调、3D 网格地面、选中呼吸描边
- 试点三件套 `docs/pilot/`：8 周计划、27 问评估问卷、店长运营手册

## 2026-10-18 · 部署上线

- Cloudflare Pages 上线：nusantara-retail-twin.pages.dev，push 自动部署
- 修复 CI：`cloudflare/pages-action`（已下线）→ `wrangler pages deploy` CLI
- GitHub 首次 push（12 提交）；secrets 配置指引完成

## 补充（同日）· 呈现层全面补齐（PM 检讨后）

- 根因：引擎先行、呈现补票——空间价值算出来但画布上看不见
- 新 `web/src/lib/biz.ts` 业务图层：镜像 SpaceAnalyzer（坪效/末位面位/what-if）到前端
- 2D：分区坪效连续热力（标签直显 Rp/㎡/日）、末位 10% 面位货架红描边、选中货架显示日毛利+毛利排名
- 3D：地面分区按坪效着色、末位货架红色警示
- 演示模式 `?demo=1`：全屏坪效热力 + 总日毛利 + 挪位增收浮签（洽谈第一屏，隐藏编辑器）
- 周报 HTML 加三张 SVG 图：分区坪效条形图 / 订单优先级环形图 / 临期倒计时条
