# 02 · 门店运营手册（试点版）

> 读者：试点门店店长 + 实施顾问。节奏：每周一次例行操作，约 1 小时。

## 每周例行（建议周一闭店后）

```bash
# 1. 数据刷新：POS 导出销售 CSV → 更新种子（实施顾问协助）
nrt validate data/seeds/store_<门店>.json        # 必须全绿才继续

# 2. 未来 14 天需求预测（含斋月日历与舆情开关）
nrt forecast --seed data/seeds/store_<门店>.json --days 14 --sentiment

# 3. 补货建议（含 MOQ/整箱/库容约束）
nrt replenish --forecast <forecast.json>

# 4. 空间-存量联合优化（面位重排建议）
nrt optimize --replenishment <replenishment.json>

# 5. 临期与 FEFO 检查（生鲜必跑）
nrt lifecycle --seed data/seeds/store_<门店>.json --fefo
```

## 店长执行清单

- [ ] 按 `replenish` 输出下单，**偏离建议 >20% 的 SKU 必须记录原因**
- [ ] 按 `optimize` 面位调整建议执行重排，拍照存档（前后对比）
- [ ] 按 `lifecycle` 临期清单做折价/捆绑，FEFO 先进先出
- [ ] 记录本周实际缺货 SKU 与损耗（生鲜报损称重）
- [ ] 每周五把执行记录发实施顾问（WhatsApp 即可）

## 斋月特别操作

- 斋月前 4 周：预测引擎自动加载斋月日历外生变量，店长只需确认备货资金
- 开斋节前 3 天：关注 mudik_sensitive SKU 的预测上调
- 开斋节后 1 周：临期促销阶梯折扣由 `nrt lifecycle --ramadan-steps` 自动生成

## 红灯规则（出现即停，联系实施顾问）

1. `nrt validate` 报错 → 不要继续跑预测，先修数据
2. 预测值连续 2 周偏差 >50% 的品类 → 检查 POS 数据是否漏导
3. 补货建议超出供应商最大配送量 → 人工拆单，记录反馈

## 复盘模板（第 8 周）

| 指标 | 试点前 4 周均值 | 试点后 4 周均值 | 变化 |
|---|---|---|---|
| A 类 SKU 缺货率 | | | |
| 生鲜损耗率 | | | |
| 建议采纳率 | — | | |
| 库存周转天数 | | | |
