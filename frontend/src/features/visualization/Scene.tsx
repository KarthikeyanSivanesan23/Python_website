import { Canvas } from '@react-three/fiber'
import { Line } from '@react-three/drei'
import { CanvasTexture, MeshStandardMaterial, SRGBColorSpace } from 'three'
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js'
import { useEffect, useMemo } from 'react'
import type { DemoStep } from '../../types'

function positions(step: DemoStep, kind: string): [number, number, number][] {
  const n = step.values.length
  return step.values.map((_, i) => {
    if (kind === 'tree') {
      const level = Math.floor(Math.log2(i + 1)), first = 2 ** level - 1, count = 2 ** level
      return [(i - first - (count - 1) / 2) * (5 / count), 1.4 - level * 1.25, 0]
    }
    if (kind === 'graph') return [Math.cos(i / n * Math.PI * 2 - Math.PI / 2) * 2.4, Math.sin(i / n * Math.PI * 2 - Math.PI / 2) * 1.6, 0]
    if (kind === 'stack' || kind === 'recursion') return [0, (i - (n - 1) / 2) * 0.75, 0]
    return [(i - (n - 1) / 2) * Math.min(1.65, 8 / Math.max(n, 1)), 0, 0]
  })
}
function Label({ text, color = '#edf0f4', small = false }: { text: string; color?: string; small?: boolean }) {
  const texture = useMemo(() => {
    const canvas = document.createElement('canvas')
    canvas.width = 512; canvas.height = 128
    const context = canvas.getContext('2d')!
    context.font = `${small ? '400' : '600'} ${text.length > 12 ? 30 : 42}px Consolas, monospace`
    context.fillStyle = color; context.textAlign = 'center'; context.textBaseline = 'middle'
    context.fillText(text.replaceAll('\n', ' '), 256, 64, 490)
    const map = new CanvasTexture(canvas); map.colorSpace = SRGBColorSpace
    return map
  }, [text, color, small])
  useEffect(() => () => texture.dispose(), [texture])
  return <sprite scale={[small ? 1.8 : 2.1, small ? .45 : .525, 1]} renderOrder={2}><spriteMaterial map={texture} transparent depthTest={false}/></sprite>
}
function Objects({ step, kind, tilt }: { step: DemoStep; kind: string; tilt: number }) {
  const points = useMemo(() => positions(step, kind), [step, kind])
  const geometry = useMemo(() => new RoundedBoxGeometry(kind === 'stack' || kind === 'recursion' ? 2.3 : 1.35, 0.7, 0.65, 3, 0.09), [kind])
  const materials = useMemo(() => [new MeshStandardMaterial({ color: '#293c58', roughness: .35, metalness: .35 }), new MeshStandardMaterial({ color: '#5ae0cf', roughness: .35, metalness: .35 })], [])
  useEffect(() => () => geometry.dispose(), [geometry])
  useEffect(() => () => materials.forEach(m => m.dispose()), [materials])
  const scale = ['tree', 'graph', 'stack', 'recursion'].includes(kind) ? 1 : step.values.length <= 3 ? 1.45 : 1
  return <group scale={scale} rotation={[0.04 + tilt * 0.08, -0.18 + tilt * 0.2, 0]}>
    {step.edges.map(([a, b], i) => points[a] && points[b] ? <Line key={i} points={[points[a], points[b]]} color="#718fa4" lineWidth={2} /> : null)}
    {step.values.map((value, i) => <group key={i} position={points[i]}>
      <mesh geometry={geometry} material={materials[step.active.includes(i) ? 1 : 0]} dispose={null}/>
      <group position={[0, 0, 0.35]}><Label text={value} color={step.active.includes(i) ? '#082b28' : '#edf0f4'}/></group>
      <group position={[0, -0.59, 0]}><Label small text={step.labels[i] || (['array', 'linear', 'binary', 'bubble', 'insertion', 'merge'].includes(kind) ? `[${i}]` : '')} color="#adc1d5"/></group>
    </group>)}
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -2.4, -0.5]}><planeGeometry args={[15, 10]} /><meshStandardMaterial color="#0c1726" transparent opacity={0.7} /></mesh>
    <gridHelper args={[16, 24, '#1e364b', '#142539']} position={[0, -2.39, 0]} />
  </group>
}
export default function Scene({ step, kind, tilt = 0 }: { step: DemoStep; kind: string; tilt?: number }) {
  return <Canvas frameloop="demand" dpr={[1, 1.5]} camera={{ position: [0, .8, ['stack', 'recursion'].includes(kind) ? Math.max(7, step.values.length * .95 + 2) : 7], fov: 42 }} gl={{ antialias: true, alpha: true }} aria-hidden="true">
    <ambientLight intensity={1.6} /><directionalLight position={[3, 5, 6]} intensity={3} color="#d1eeff" /><pointLight position={[-4, 2, 3]} intensity={30} color="#9575ed" />
    <Objects step={step} kind={kind} tilt={tilt} />
  </Canvas>
}
