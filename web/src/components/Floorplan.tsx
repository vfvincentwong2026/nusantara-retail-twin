import { useCallback, useMemo, useRef, useState } from 'react'
import type { Fixture, SeedDoc, Zone } from '@/types/seed'
import { FIXTURE_TYPE_COLOR, footprintOf } from '@/lib/seed'
import { zoneBizColor, fmtIDR, type BizLayer } from '@/lib/biz'
import { ResetIcon } from '@/components/ui/icons'

interface ViewBox {
  x: number
  y: number
  w: number
  h: number
}

interface FloorplanProps {
  doc: SeedDoc
  biz: BizLayer
  selectedFixtureId: string | null
  onSelectFixture: (id: string | null) => void
}

const MARGIN = 4

export function Floorplan({ doc, biz, selectedFixtureId, onSelectFixture }: FloorplanProps) {
  const maxRank = Math.max(biz.zones.length - 1, 1)
  const svgRef = useRef<SVGSVGElement>(null)
  const [view, setView] = useState<ViewBox | null>(null)
  const drag = useRef<{ px: number; py: number; start: ViewBox; moved: boolean } | null>(null)

  const fp = useMemo(() => footprintOf(doc), [doc])
  const baseView: ViewBox = useMemo(
    () => ({ x: fp.minX - MARGIN, y: fp.minY - MARGIN, w: fp.width + MARGIN * 2, h: fp.height + MARGIN * 2 }),
    [fp],
  )
  const vb = view ?? baseView

  const zoneById = useMemo(() => new Map(doc.zones.map((z) => [z.zone_id, z])), [doc])
  const selected = doc.fixtures.find((f) => f.fixture_id === selectedFixtureId) ?? null

  // ---- 平移 / 缩放 ----
  const clientToSvg = useCallback(
    (cx: number, cy: number) => {
      const rect = svgRef.current!.getBoundingClientRect()
      return {
        x: vb.x + ((cx - rect.left) / rect.width) * vb.w,
        y: vb.y + ((cy - rect.top) / rect.height) * vb.h,
      }
    },
    [vb],
  )

  const onPointerDown = (e: React.PointerEvent<SVGSVGElement>) => {
    ;(e.target as Element).setPointerCapture?.(e.pointerId)
    drag.current = { px: e.clientX, py: e.clientY, start: vb, moved: false }
  }
  const onPointerMove = (e: React.PointerEvent<SVGSVGElement>) => {
    if (!drag.current) return
    const rect = svgRef.current!.getBoundingClientRect()
    const dx = ((e.clientX - drag.current.px) / rect.width) * drag.current.start.w
    const dy = ((e.clientY - drag.current.py) / rect.height) * drag.current.start.h
    if (Math.abs(e.clientX - drag.current.px) + Math.abs(e.clientY - drag.current.py) > 3) {
      drag.current.moved = true
    }
    setView({ ...drag.current.start, x: drag.current.start.x - dx, y: drag.current.start.y - dy })
  }
  const onPointerUp = () => {
    drag.current = null
  }
  const onWheel = (e: React.WheelEvent<SVGSVGElement>) => {
    const factor = e.deltaY > 0 ? 1.15 : 1 / 1.15
    const c = clientToSvg(e.clientX, e.clientY)
    const w = Math.min(Math.max(vb.w * factor, 4), fp.width * 4)
    const h = (w * vb.h) / vb.w
    setView({
      w,
      h,
      x: c.x - ((c.x - vb.x) / vb.w) * w,
      y: c.y - ((c.y - vb.y) / vb.h) * h,
    })
  }

  const resetView = () => setView(null)

  return (
    <div className="relative h-full w-full overflow-hidden rounded-lg border bg-slate-950">
      <svg
        ref={svgRef}
        className="h-full w-full cursor-grab active:cursor-grabbing"
        viewBox={`${vb.x} ${vb.y} ${vb.w} ${vb.h}`}
        preserveAspectRatio="xMidYMid meet"
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onWheel={onWheel}
      >
        {/* Zone 热力层 */}
        {doc.zones.map((z: Zone) => (
          <polygon
            key={z.zone_id}
            points={z.polygon.map((p) => `${p.x},${p.y}`).join(' ')}
            fill={zoneBizColor((biz.zones.find((b) => b.zone.zone_id === z.zone_id)?.rank ?? 0) / maxRank)}
            stroke="rgba(255,255,255,0.25)"
            strokeWidth={0.06}
            className="pointer-events-none"
          />
        ))}

        {/* Zone 名称 */}
        {doc.zones.map((z) => {
          const cx = z.polygon.reduce((s, p) => s + p.x, 0) / z.polygon.length
          const cy = z.polygon.reduce((s, p) => s + p.y, 0) / z.polygon.length
          return (
            <text
              key={`t-${z.zone_id}`}
              x={cx}
              y={cy}
              textAnchor="middle"
              className="pointer-events-none select-none fill-white"
              style={{ fontSize: Math.max(0.6, vb.w / 60), fontWeight: 500, fontVariantNumeric: 'tabular-nums' }}
              opacity={vb.w < fp.width * 1.6 ? 0.75 : 0}
            >
              {z.zone_name} · {fmtIDR(biz.zones.find((b) => b.zone.zone_id === z.zone_id)?.marginPerM2 ?? 0)}/㎡
            </text>
          )
        })}

        {/* Fixture 层 */}
        {doc.fixtures.map((f: Fixture) => {
          const isSel = f.fixture_id === selectedFixtureId
          const zone = zoneById.get(f.zone_id)
          return (
            <g
              key={f.fixture_id}
              transform={`translate(${f.position_x}, ${f.position_y})`}
              onPointerDown={(e) => e.stopPropagation()}
              onClick={() => {
                if (!drag.current?.moved) onSelectFixture(isSel ? null : f.fixture_id)
              }}
              className="cursor-pointer"
            >
              <title>{`${f.fixture_label} · ${zone?.zone_name ?? ''}`}</title>
              <rect
                x={-f.length_m / 2}
                y={-0.35}
                width={f.length_m}
                height={0.7}
                rx={0.12}
                fill={FIXTURE_TYPE_COLOR[f.fixture_type] ?? '#94a3b8'}
                fillOpacity={isSel ? 1 : 0.75}
                stroke={isSel ? '#f8fafc' : '#0f172a'}
                strokeWidth={isSel ? 0.12 : 0.05}
              />
              {biz.fixtures.get(f.fixture_id)?.isBottom && (
                <rect
                  x={-f.length_m / 2 - 0.1}
                  y={-0.45}
                  width={f.length_m + 0.2}
                  height={0.9}
                  rx={0.15}
                  fill="none"
                  stroke="#f87171"
                  strokeWidth={0.06}
                  opacity={0.9}
                  pointerEvents="none"
                />
              )}
              {isSel && (
                <rect
                  className="fixture-pulse"
                  x={-f.length_m / 2 - 0.18}
                  y={-0.53}
                  width={f.length_m + 0.36}
                  height={1.06}
                  rx={0.2}
                  fill="none"
                  stroke="#f8fafc"
                  strokeWidth={0.07}
                  strokeDasharray="0.3 0.18"
                />
              )}
              <text
                y={0.18}
                textAnchor="middle"
                className="pointer-events-none select-none fill-slate-950"
                style={{ fontSize: 0.42, fontWeight: 500 }}
              >
                {f.fixture_label}
              </text>
            </g>
          )
        })}
      </svg>

      {/* 悬浮信息 */}
      {selected && (
        <div className="pointer-events-none absolute bottom-3 left-3 rounded-lg border ds-hairline bg-slate-900/80 px-3 py-2 text-xs text-slate-200 backdrop-blur">
          <span className="font-medium text-white">{selected.fixture_label}</span>
          {' · '}
          {zoneById.get(selected.zone_id)?.zone_name}
          {' · '}
          {fmtIDR(biz.fixtures.get(selected.fixture_id)?.dailyMargin ?? 0)}/hari
          {' · '}#{((biz.fixtures.get(selected.fixture_id)?.rank ?? 0) + 1)} 毛利
          {biz.fixtures.get(selected.fixture_id)?.isBottom ? ' · ⚠️ 末位面位' : ''}
        </div>
      )}

      <button
        onClick={resetView}
        className="absolute right-3 top-3 flex items-center gap-1.5 rounded-lg border ds-hairline bg-slate-900/80 px-3 py-1.5 text-xs text-slate-200 backdrop-blur transition-colors hover:bg-slate-800 hover:text-white"
      >
        <ResetIcon className="h-3.5 w-3.5" />
        复位视图
      </button>
      <div className="pointer-events-none absolute left-3 top-3 text-[11px] text-slate-500">
        拖动平移 · 滚轮缩放 · 点击货架查看面位
      </div>
    </div>
  )
}
