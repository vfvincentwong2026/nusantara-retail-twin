import { useMemo, useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import { Instance, Instances, Text } from '@react-three/drei'
import * as THREE from 'three'
import type { Facing, SeedDoc, ShelfLevel } from '@/types/seed'
import { FIXTURE_TYPE_COLOR, heatColor } from '@/lib/seed'

interface StoreMeshProps {
  doc: SeedDoc
  selectedFixtureId: string | null
  onSelectFixture: (id: string | null) => void
  autoRotate: boolean
}

const LEVEL_GAP = 0.42
const PRODUCT_H = 0.26
const PRODUCT_D = 0.44
const SHELF_T = 0.04

// 货架类型 → 3D 高度（米）
const FIXTURE_HEIGHT: Record<string, number> = {
  gondola: 1.8,
  shelf: 2.0,
  cooler: 2.0,
  freezer: 2.0,
  meat_counter: 1.1,
  seafood_counter: 1.1,
  produce_rack: 1.3,
  bakery_counter: 1.4,
  hot_food_counter: 1.4,
}

const CATEGORY_HEX: Record<string, string> = {
  方便面: '#f97316', 饼干: '#fbbf24', 食用油: '#fde047', 大米: '#e7e5e4',
  调味品: '#fb923c', 咖啡: '#92400e', 茶: '#65a30d', 饮料: '#0ea5e9',
  零食: '#f472b6', 乳制品: '#f8fafc', 冷冻食品: '#93c5fd', 清洁用品: '#22d3ee',
  洗护用品: '#c084fc', 母婴用品: '#fda4af', 厨具家居: '#a8a29e', 穆斯林服饰: '#34d399',
  美妆个护: '#f9a8d4', 文具: '#818cf8', 蔬菜: '#4ade80', 水果: '#84cc16',
  鲜肉: '#ef4444', 海鲜: '#14b8a6', 鸡蛋: '#eab308',
}

interface FacingBox {
  key: string
  position: [number, number, number]
  width: number
  color: string
}

function zoneRect(z: SeedDoc['zones'][number]) {
  const xs = z.polygon.map((p) => p.x)
  const ys = z.polygon.map((p) => p.y)
  const x0 = Math.min(...xs), x1 = Math.max(...xs)
  const y0 = Math.min(...ys), y1 = Math.max(...ys)
  return {
    cx: (x0 + x1) / 2,
    cz: (y0 + y1) / 2,
    w: x1 - x0,
    d: y1 - y0,
  }
}

export function StoreMesh({ doc, selectedFixtureId, onSelectFixture, autoRotate }: StoreMeshProps) {
  const group = useRef<THREE.Group>(null)

  const skuColor = useMemo(() => {
    const m = new Map<string, string>()
    for (const s of doc.skus) m.set(s.sku_code, CATEGORY_HEX[s.category_name] ?? '#64748b')
    return m
  }, [doc])

  const levelsByFixture = useMemo(() => {
    const m = new Map<string, ShelfLevel[]>()
    for (const lv of doc.shelf_levels) {
      const arr = m.get(lv.fixture_id) ?? []
      arr.push(lv)
      m.set(lv.fixture_id, arr)
    }
    for (const arr of m.values()) arr.sort((a, b) => a.level_number - b.level_number)
    return m
  }, [doc])

  const facingsByLevel = useMemo(() => {
    const m = new Map<string, Facing[]>()
    for (const fc of doc.facings) {
      const arr = m.get(fc.shelf_level_id) ?? []
      arr.push(fc)
      m.set(fc.shelf_level_id, arr)
    }
    for (const arr of m.values()) arr.sort((a, b) => a.facing_index - b.facing_index)
    return m
  }, [doc])

  // 所有面位 → InstancedMesh 实例（含层板）
  const facingBoxes = useMemo(() => {
    const boxes: FacingBox[] = []
    const boards: FacingBox[] = []
    for (const f of doc.fixtures) {
      const levels = levelsByFixture.get(f.fixture_id) ?? []
      levels.forEach((lv, li) => {
        const y = 0.15 + li * LEVEL_GAP
        const facings = facingsByLevel.get(lv.shelf_level_id) ?? []
        const slot = f.length_m / Math.max(facings.length, 1)
        facings.forEach((fc, i) => {
          const w = Math.min(fc.facing_width_m, slot * 0.92)
          boxes.push({
            key: fc.facing_id,
            position: [
              f.position_x - f.length_m / 2 + slot * (i + 0.5),
              y + PRODUCT_H / 2 + SHELF_T,
              f.position_y,
            ],
            width: w,
            color: fc.sku_code ? (skuColor.get(fc.sku_code) ?? '#64748b') : '#334155',
          })
        })
        // 层板
        boards.push({
          key: `board-${lv.shelf_level_id}`,
          position: [f.position_x, y, f.position_y],
          width: f.length_m,
          color: '#3f3f46',
        })
      })
    }
    return { boxes, boards }
  }, [doc, levelsByFixture, facingsByLevel, skuColor])

  useFrame((_, delta) => {
    if (autoRotate && group.current) group.current.rotation.y += delta * 0.05
  })

  const fp = useMemo(() => {
    const all = doc.zones.map(zoneRect)
    const maxX = Math.max(...all.map((z) => z.cx + z.w / 2))
    const maxZ = Math.max(...all.map((z) => z.cz + z.d / 2))
    return { w: maxX, d: maxZ }
  }, [doc])

  return (
    <group ref={group}>
      {/* 地板 */}
      <mesh position={[fp.w / 2, -0.05, fp.d / 2]} receiveShadow>
        <boxGeometry args={[fp.w + 4, 0.1, fp.d + 4]} />
        <meshStandardMaterial color="#1e293b" />
      </mesh>
      {/* 网格线 */}
      <gridHelper args={[Math.max(fp.w, fp.d) + 4, Math.round(Math.max(fp.w, fp.d) / 5), '#334155', '#273449']} position={[fp.w / 2, 0.001, fp.d / 2]} />

      {/* Zone 热力块 */}
      {doc.zones.map((z) => {
        const r = zoneRect(z)
        return (
          <mesh key={z.zone_id} position={[r.cx, 0.015, r.cz]}>
            <boxGeometry args={[r.w - 0.15, 0.03, r.d - 0.15]} />
            <meshStandardMaterial color={heatColor(z.heat_value, 0.85)} transparent opacity={0.55} />
          </mesh>
        )
      })}

      {/* Zone 标签 */}
      {doc.zones.map((z) => {
        const r = zoneRect(z)
        return (
          <Text
            key={`t-${z.zone_id}`}
            position={[r.cx, 0.06, r.cz]}
            rotation={[-Math.PI / 2, 0, 0]}
            fontSize={Math.max(0.8, fp.w / 45)}
            color="#e2e8f0"
            anchorX="center"
            anchorY="middle"
            fillOpacity={0.85}
          >
            {z.zone_name}
          </Text>
        )
      })}

      {/* 货架柜体 + 选中高亮 */}
      {doc.fixtures.map((f) => {
        const h = FIXTURE_HEIGHT[f.fixture_type] ?? 1.8
        const isSel = f.fixture_id === selectedFixtureId
        return (
          <group key={f.fixture_id} position={[f.position_x, 0, f.position_y]}>
            <mesh
              position={[0, h / 2, 0]}
              castShadow
              onClick={(e) => {
                e.stopPropagation()
                onSelectFixture(isSel ? null : f.fixture_id)
              }}
            >
              <boxGeometry args={[f.length_m, h, 0.62]} />
              <meshStandardMaterial
                color={isSel ? '#f8fafc' : (FIXTURE_TYPE_COLOR[f.fixture_type] ?? '#94a3b8')}
                transparent
                opacity={isSel ? 0.95 : 0.32}
              />
            </mesh>
            {isSel && (
              <mesh position={[0, h / 2, 0]}>
                <boxGeometry args={[f.length_m + 0.15, h + 0.15, 0.8]} />
                <meshBasicMaterial color="#38bdf8" wireframe />
              </mesh>
            )}
          </group>
        )
      })}

      {/* 层板（instanced） */}
      <Instances limit={facingBoxes.boards.length} frustumCulled={false}>
        <boxGeometry args={[1, SHELF_T, 0.6]} />
        <meshStandardMaterial color="#3f3f46" />
        {facingBoxes.boards.map((b) => (
          <Instance key={b.key} position={b.position} scale={[b.width, 1, 1]} />
        ))}
      </Instances>

      {/* 商品面位（instanced，按品类着色） */}
      <Instances limit={facingBoxes.boxes.length} frustumCulled={false}>
        <boxGeometry args={[1, PRODUCT_H, PRODUCT_D]} />
        <meshStandardMaterial />
        {facingBoxes.boxes.map((b) => (
          <Instance key={b.key} position={b.position} scale={[b.width, 1, 1]} color={b.color} />
        ))}
      </Instances>
    </group>
  )
}
