import { useCallback, useMemo, useRef, useState } from 'react'
import type { Fixture, SeedDoc, Zone } from '@/types/seed'
import { FIXTURE_TYPE_COLOR, footprintOf, heatColor } from '@/lib/seed'

interface ViewBox {
  x: number
  y: number
  w: number
  h: number
}

interface FloorplanProps {
  doc: SeedDoc
  selectedFixtureId: string | null
  onSelectFixture: (id: string | null) => void
}

const MARGIN = 4

export function Floorplan({ doc, selectedFixtureId, onSelectFixture }: FloorplanProps) {
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
            fill={heatColor(z.heat_value, 0.28)}
            stroke={heatColor(z.heat_value, 0.9)}
            strokeWidth={0.12}
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
              className="pointer-events-none select-none fill-slate-300"
              style={{ fontSize: Math.max(0.6, vb.w / 60) }}
              opacity={vb.w < fp.width * 1.6 ? 1 : 0}
            >
              {z.zone_name} · {z.heat_value.toFixed(2)}
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
              <text
                y={0.18}
                textAnchor="middle"
                className="pointer-events-none select-none fill-slate-950"
                style={{ fontSize: 0.42, fontWeight: 700 }}
              >
                {f.fixture_label}
              </text>
            </g>
          )
        })}
      </svg>

      {/* 悬浮信息 */}
      {selected && (
        <div className="pointer-events-none absolute bottom-3 left-3 rounded-md bg-slate-900/85 px-3 py-2 text-xs text-slate-200 backdrop-blur">
          <span className="font-semibold text-white">{selected.fixture_label}</span>
          {' · '}
          {zoneById.get(selected.zone_id)?.zone_name}
          {' · '}
          {selected.fixture_type}
          {' · '}
          ({selected.position_x.toFixed(1)}, {selected.position_y.toFixed(1)})m
        </div>
      )}

      <button
        onClick={resetView}
        className="absolute right-3 top-3 rounded-md bg-slate-800/85 px-3 py-1.5 text-xs text-slate-200 backdrop-blur hover:bg-slate-700"
      >
        复位视图
      </button>
      <div className="pointer-events-none absolute left-3 top-3 text-[11px] text-slate-500">
        拖动平移 · 滚轮缩放 · 点击货架查看面位
      </div>
    </div>
  )
}
