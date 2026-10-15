import { useMemo, useState } from 'react'
import type { FacingEdit, SeedDoc } from '@/types/seed'
import { FIXTURE_TYPE_LABEL, ZONE_TYPE_LABEL, formatIDR } from '@/lib/seed'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface InspectorProps {
  doc: SeedDoc
  fixtureId: string | null
  edits: Record<string, FacingEdit>
  onEdit: (facingId: string, edit: FacingEdit) => void
  onResetEdits: () => void
  onExport: () => void
  dirtyCount: number
}

const CATEGORY_COLOR: Record<string, string> = {
  方便面: '#f97316',
  饼干: '#fbbf24',
  食用油: '#fde047',
  大米: '#e7e5e4',
  调味品: '#fb923c',
  咖啡: '#92400e',
  茶: '#65a30d',
  饮料: '#0ea5e9',
  零食: '#f472b6',
  乳制品: '#f8fafc',
  冷冻食品: '#93c5fd',
  清洁用品: '#22d3ee',
  洗护用品: '#c084fc',
  母婴用品: '#fda4af',
  厨具家居: '#a8a29e',
  穆斯林服饰: '#34d399',
  美妆个护: '#f9a8d4',
  文具: '#818cf8',
  蔬菜: '#4ade80',
  水果: '#84cc16',
  鲜肉: '#ef4444',
  海鲜: '#14b8a6',
  鸡蛋: '#eab308',
}

export function Inspector({ doc, fixtureId, edits, onEdit, onResetEdits, onExport, dirtyCount }: InspectorProps) {
  const [skuFilter, setSkuFilter] = useState('')
  const fixture = doc.fixtures.find((f) => f.fixture_id === fixtureId) ?? null
  const zone = fixture ? doc.zones.find((z) => z.zone_id === fixture.zone_id) : null

  const levels = useMemo(
    () =>
      fixture
        ? doc.shelf_levels
            .filter((lv) => lv.fixture_id === fixture.fixture_id)
            .sort((a, b) => a.level_number - b.level_number)
        : [],
    [doc, fixture],
  )

  const skuByCode = useMemo(() => new Map(doc.skus.map((s) => [s.sku_code, s])), [doc])

  const filteredSkus = useMemo(() => {
    const q = skuFilter.trim().toLowerCase()
    if (!q) return doc.skus.slice(0, 200)
    return doc.skus
      .filter(
        (s) =>
          s.sku_name.toLowerCase().includes(q) ||
          s.sku_code.toLowerCase().includes(q) ||
          s.category_name.includes(q) ||
          s.brand.toLowerCase().includes(q),
      )
      .slice(0, 200)
  }, [doc, skuFilter])

  if (!fixture) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle className="text-sm">货架图编辑器</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-muted-foreground">
          <p>点击平面图上的货架，查看其货架层与陈列面位（Facing）。</p>
          <p>
            平台按「单一数据源」原则工作：在此修改面位的 SKU 或容量后，导出的 JSON
            与 2D / 3D 视图共用同一份文档（docs/architecture.md §1）。
          </p>
          {dirtyCount > 0 && (
            <div className="flex gap-2 pt-2">
              <Button size="sm" onClick={onExport}>
                导出修改后的种子（{dirtyCount} 处）
              </Button>
              <Button size="sm" variant="outline" onClick={onResetEdits}>
                放弃修改
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="flex h-full flex-col">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm">
            {fixture.fixture_label} · {FIXTURE_TYPE_LABEL[fixture.fixture_type] ?? fixture.fixture_type}
          </CardTitle>
          <Badge variant="secondary">{zone ? `${zone.zone_name}（${ZONE_TYPE_LABEL[zone.zone_type] ?? zone.zone_type}）` : ''}</Badge>
        </div>
        <p className="text-xs text-muted-foreground">
          {fixture.length_m}m 长 · {levels.length} 层 ·{' '}
          {levels.reduce((n, lv) => n + doc.facings.filter((fc) => fc.shelf_level_id === lv.shelf_level_id).length, 0)}{' '}
          个面位
        </p>
      </CardHeader>
      <CardContent className="min-h-0 flex-1 space-y-4 overflow-y-auto">
        {/* 货架层可视化：每层一行面位色块 */}
        <div className="space-y-1.5">
          {levels.map((lv) => {
            const facings = doc.facings
              .filter((fc) => fc.shelf_level_id === lv.shelf_level_id)
              .sort((a, b) => a.facing_index - b.facing_index)
            return (
              <div key={lv.shelf_level_id} className="flex items-center gap-2">
                <span className="w-14 shrink-0 text-[11px] text-muted-foreground">
                  L{lv.level_number}
                  {lv.is_eye_level ? ' 👁' : ''}
                </span>
                <div className="flex flex-1 gap-0.5">
                  {facings.map((fc) => {
                    const edited = edits[fc.facing_id]
                    const code = edited ? edited.sku_code : fc.sku_code
                    const sku = code ? skuByCode.get(code) : null
                    const color = sku ? (CATEGORY_COLOR[sku.category_name] ?? '#64748b') : '#334155'
                    const isSel = false
                    return (
                      <button
                        key={fc.facing_id}
                        title={`${fc.facing_id}\n${sku?.sku_name ?? '未分配'}`}
                        className="h-5 flex-1 rounded-sm border border-slate-700 transition-transform hover:scale-125"
                        style={{ background: color, outline: isSel ? '2px solid #f8fafc' : undefined }}
                        onClick={() =>
                          document.getElementById(`row-${fc.facing_id}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' })
                        }
                      />
                    )
                  })}
                </div>
              </div>
            )
          })}
        </div>

        {/* SKU 搜索 */}
        <Input
          placeholder="搜索 SKU 名称 / 编码 / 品类 / 品牌…"
          value={skuFilter}
          onChange={(e) => setSkuFilter(e.target.value)}
          className="text-xs"
        />

        {/* 面位编辑表 */}
        <div className="space-y-1">
          {levels.flatMap((lv) =>
            doc.facings
              .filter((fc) => fc.shelf_level_id === lv.shelf_level_id)
              .sort((a, b) => a.facing_index - b.facing_index)
              .map((fc) => {
                const edit = edits[fc.facing_id]
                const code = edit ? edit.sku_code : fc.sku_code
                const sku = code ? skuByCode.get(code) : null
                const maxUnits = edit ? edit.max_units : fc.max_units
                return (
                  <div
                    key={fc.facing_id}
                    id={`row-${fc.facing_id}`}
                    className="flex items-center gap-2 rounded-md px-2 py-1.5 text-xs hover:bg-slate-800/60"
                  >
                    <span className="w-20 shrink-0 font-mono text-[10px] text-muted-foreground">
                      L{lv.level_number}-{String(fc.facing_index).padStart(2, '0')}
                    </span>
                    <select
                      className="h-7 min-w-0 flex-1 rounded border border-slate-700 bg-slate-900 px-1 text-xs"
                      value={code ?? ''}
                      onChange={(e) => onEdit(fc.facing_id, { sku_code: e.target.value || null, max_units: maxUnits })}
                    >
                      <option value="">（未分配）</option>
                      {sku && !filteredSkus.some((s) => s.sku_code === sku.sku_code) && (
                        <option value={sku.sku_code}>{sku.sku_name}</option>
                      )}
                      {filteredSkus.map((s) => (
                        <option key={s.sku_code} value={s.sku_code}>
                          {s.sku_name} · {formatIDR(s.unit_price)}
                        </option>
                      ))}
                    </select>
                    <input
                      type="number"
                      min={0}
                      max={200}
                      className="h-7 w-16 rounded border border-slate-700 bg-slate-900 px-1 text-xs"
                      value={maxUnits}
                      onChange={(e) =>
                        onEdit(fc.facing_id, { sku_code: code, max_units: Math.max(0, Number(e.target.value) || 0) })
                      }
                    />
                    {edit && <Badge variant="outline" className="shrink-0 text-[10px]">改</Badge>}
                  </div>
                )
              }),
          )}
        </div>
      </CardContent>
      {dirtyCount > 0 && (
        <div className="flex gap-2 border-t p-3">
          <Button size="sm" className="flex-1" onClick={onExport}>
            导出种子 JSON（{dirtyCount} 处修改）
          </Button>
          <Button size="sm" variant="outline" onClick={onResetEdits}>
            放弃
          </Button>
        </div>
      )}
    </Card>
  )
}

// 供 App 判断面位所属货架（保留以备用）
export function fixtureOfFacing(levelsOf: Map<string, string>, shelfLevelId: string): string | undefined {
  return levelsOf.get(shelfLevelId)
}
