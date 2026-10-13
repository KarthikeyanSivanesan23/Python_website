import { Component, lazy, Suspense, useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { Pause, Play, RotateCcw, SkipForward, Box, Monitor } from 'lucide-react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import type { Demo, DemoStep, Lesson } from '../../types'
import { buildDemo, defaultInput } from './algorithms'
import { CodeBlock } from '../../components/CodeBlock'
gsap.registerPlugin(ScrollTrigger)
const Scene = lazy(() => import('./Scene'))

class SceneBoundary extends Component<{ children: ReactNode; fallback: ReactNode }, { failed: boolean }> {
  state = { failed: false }
  static getDerivedStateFromError() { return { failed: true } }
  render() { return this.state.failed ? this.props.fallback : this.props.children }
}
function FlatVisual({ step }: { step: DemoStep }) {
  return <div className="flat-visual">{step.values.length ? step.values.map((v, i) => <div className={`flat-node ${step.active.includes(i) ? 'active' : ''}`} key={i}><small>{step.labels[i] || `node ${i}`}</small><strong>{v}</strong></div>) : <p>Empty collection</p>}{step.edges.length > 0 && <p className="flat-links">Links: {step.edges.map(([a, b]) => `${step.values[a]} → ${step.values[b]}`).join(' · ')}</p>}</div>
}
export function Visual({ step, kind, tilt = 0 }: { step: DemoStep; kind: string; tilt?: number }) {
  const [light, setLight] = useState(() => window.matchMedia('(max-width: 700px), (prefers-reduced-motion: reduce)').matches)
  const [available] = useState(() => { try { const c = document.createElement('canvas'); const gl = c.getContext('webgl2'); const ok = !!gl; gl?.getExtension('WEBGL_lose_context')?.loseContext(); return ok } catch { return false } })
  return <div className="visual-wrap">
    <div className="visual-mode"><span><Box size={13} /> {light || !available ? 'Lightweight view' : 'Live 3D scene'}</span>{available && <button className="text-button" onClick={() => setLight(!light)}><Monitor size={13} /> {light ? 'Use 3D' : 'Use 2D'}</button>}</div>
    <div className="scene-frame">{!light && available ? <SceneBoundary fallback={<FlatVisual step={step} />}><Suspense fallback={<FlatVisual step={step} />}><Scene step={step} kind={kind} tilt={tilt} /></Suspense></SceneBoundary> : <FlatVisual step={step} />}</div>
    {!light && available && <div className="scene-legend" aria-label="Visualization values">{step.values.map((value, i) => <span key={i} className={step.active.includes(i) ? 'active' : ''}>{step.labels[i] ? `${step.labels[i]}: ` : ''}{value}</span>)}{!!step.edges.length && <small>Links: {step.edges.map(([a, b]) => `${step.values[a]} → ${step.values[b]}`).join(' · ')}</small>}</div>}
  </div>
}
export default function Demonstration({ lesson }: { lesson: Lesson }) {
  const [demo, setDemo] = useState<Demo>(lesson.content.demo)
  const [index, setIndex] = useState(0), [playing, setPlaying] = useState(false)
  const [input, setInput] = useState(defaultInput(lesson.id)), [target, setTarget] = useState(lesson.id.startsWith('graph-') ? 'A' : '7')
  const [error, setError] = useState(''), [tilt, setTilt] = useState(0), [visible, setVisible] = useState(false)
  const root = useRef<HTMLDivElement>(null)
  const step = demo.steps[index]
  useEffect(() => {
    const observer = new IntersectionObserver(([entry]) => setVisible(entry.isIntersecting), { threshold: 0.1 })
    if (root.current) observer.observe(root.current)
    const mm = gsap.matchMedia()
    mm.add('(prefers-reduced-motion: no-preference)', () => {
      const obj = { value: 0 }
      gsap.to(obj, { value: 1, ease: 'none', scrollTrigger: { trigger: root.current, start: 'top bottom', end: 'bottom top', scrub: 0.6 }, onUpdate: () => setTilt(obj.value) })
    })
    return () => { observer.disconnect(); mm.revert() }
  }, [])
  useEffect(() => {
    if (!playing || !visible) return
    const timer = setInterval(() => {
      if (document.hidden) return
      setIndex(i => { if (i >= demo.steps.length - 1) { setPlaying(false); return i } return i + 1 })
    }, 1500)
    return () => clearInterval(timer)
  }, [playing, visible, demo.steps.length])
  function apply() {
    try { setDemo(buildDemo(lesson, input, target)); setIndex(0); setPlaying(false); setError('') } catch (e) { setError(e instanceof Error ? e.message : 'Invalid input.') }
  }
  return <div className="demonstration panel" ref={root}>
    <div className="panel-heading"><span className="eyebrow">THE CONCEPT, MADE VISIBLE</span><span className="badge">Authored demonstration</span></div>
    {lesson.track === 'dsa' && <div className="demo-inputs"><label>{lesson.id.startsWith('graph-') ? 'Adjacency list (JSON)' : lesson.id === 'recursion' ? 'Factorial input (0–7)' : lesson.id === 'trees' ? 'Node values in level order' : 'Input values (up to 8)'}<input value={input} onChange={e => setInput(e.target.value)} /></label>{['linear-search', 'binary-search', 'graph-bfs', 'graph-dfs'].includes(lesson.id) && <label className="target-label">{lesson.id.startsWith('graph-') ? 'Start node' : 'Target'}<input value={target} onChange={e => setTarget(e.target.value)} /></label>}<button className="button secondary" onClick={apply}>Apply input</button></div>}
    {error && <p className="error" role="alert">{error}</p>}
    <div className="demo-grid"><div><Visual step={step} kind={demo.kind} tilt={tilt} /><div className="step-caption" aria-live="polite"><span className="step-count">{String(index + 1).padStart(2, '0')}</span><p>{step.caption}</p></div></div><div className="demo-code"><div className="file-tab"><span className="python-dot"/>demonstration.py <span>LINE {step.line}</span></div><CodeBlock code={demo.code} activeLine={step.line}/></div></div>
    <div className="demo-controls"><button className="button secondary" onClick={() => { if (index === demo.steps.length - 1) setIndex(0); setPlaying(!playing) }}>{playing ? <Pause size={16}/> : <Play size={16}/>} {playing ? 'Pause' : 'Play'}</button><button className="icon-button" title="Next demonstration step" aria-label="Next demonstration step" onClick={() => { setPlaying(false); setIndex(i => Math.min(i + 1, demo.steps.length - 1)) }} disabled={index === demo.steps.length - 1}><SkipForward size={18}/></button><button className="icon-button" title="Reset demonstration" aria-label="Reset demonstration" onClick={() => { setPlaying(false); setIndex(0) }}><RotateCcw size={16}/></button><input aria-label="Demonstration step" type="range" min={0} max={demo.steps.length - 1} value={index} onChange={e => { setPlaying(false); setIndex(Number(e.target.value)) }}/><span>{index + 1} / {demo.steps.length}</span></div>
    <p className="fine-print inset">This step-through follows the displayed teaching example. It does not trace code written in your editor.</p>
  </div>
}
