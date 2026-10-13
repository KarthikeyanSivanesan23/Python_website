import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, ArrowDown, BookOpen, Braces, Check, ChevronRight, Code2, Layers3, Pause, Play, Sparkles, Terminal, Zap } from 'lucide-react'
import gsap from 'gsap'
import { useCurriculum } from './Curriculum'
import { useAuth } from '../auth'
import { api } from '../api'
import type { DashboardData, DemoStep } from '../types'
import { Visual } from '../features/visualization/Demonstration'
import { CodeBlock } from '../components/CodeBlock'

const heroSteps: DemoStep[] = [
  { line: 1, caption: 'A little curiosity goes a long way.', values: ['curiosity', 'practice', 'progress'], active: [], labels: ['0', '1', '2'], edges: [] },
  { line: 3, caption: 'curiosity', values: ['curiosity', 'practice', 'progress'], active: [0], labels: ['0', '1', '2'], edges: [] },
  { line: 3, caption: 'practice', values: ['curiosity', 'practice', 'progress'], active: [1], labels: ['0', '1', '2'], edges: [] },
  { line: 3, caption: 'progress', values: ['curiosity', 'practice', 'progress'], active: [2], labels: ['0', '1', '2'], edges: [] },
]
const heroCode = 'skills = ["curiosity", "practice", "progress"]\nfor skill in skills:\n    print(f"Build with {skill}.")'
export default function Home() {
  const { chapters, error, loading, reload } = useCurriculum(), { user } = useAuth()
  const [track, setTrack] = useState<'python' | 'dsa'>('python'), [index, setIndex] = useState(0), [resume, setResume] = useState('values')
  const [playing, setPlaying] = useState(!window.matchMedia('(prefers-reduced-motion: reduce)').matches)
  const root = useRef<HTMLDivElement>(null), heroVisible = useRef(true)
  useEffect(() => { if (user) api<DashboardData>('dashboard/').then(data => setResume(data.resume)).catch(() => {}) }, [user])
  useEffect(() => {
    const observer = new IntersectionObserver(([e]) => { heroVisible.current = e.isIntersecting })
    if (root.current) observer.observe(root.current)
    const mm = gsap.matchMedia()
    mm.add('(prefers-reduced-motion: no-preference)', () => { gsap.from('.hero-copy > *', { y: 22, opacity: 0, duration: 0.75, stagger: 0.1, ease: 'power2.out' }) })
    return () => { observer.disconnect(); mm.revert() }
  }, [])
  useEffect(() => { if (!playing) return; const timer = setInterval(() => { if (!document.hidden && heroVisible.current) setIndex(i => (i + 1) % heroSteps.length) }, 2200); return () => clearInterval(timer) }, [playing])
  return <>
    <section className="hero page-width" ref={root}>
      <div className="hero-copy"><div className="hero-kicker"><span className="status-dot online"/> A NEW DIMENSION OF LEARNING</div><h1>Don’t just read<br/>Python.<br/><span>See it come alive.</span></h1><p>Turn “I think I get it” into “I built it.” Explore concepts in 3D, write real Python, and find your next step with a personal AI mentor.</p><div className="hero-actions"><Link className="button primary large" to={`/learn/${user ? resume : 'values'}`}>{user ? 'Continue learning' : 'Start learning'}<ArrowRight size={18}/></Link><a className="button ghost large" href="#learning-path">Explore the path <ArrowDown size={16}/></a></div><div className="hero-benefits"><span><Check size={14}/> Beginner friendly</span><span><Check size={14}/> Learn by doing</span><span><Check size={14}/> No Python install</span></div></div>
      <div className="hero-lab"><div className="orbit orbit-one"/><div className="orbit orbit-two"/><div className="floating-tag tag-top"><Braces size={15}/> Ideas become understanding</div><div className="hero-scene"><Visual step={heroSteps[index]} kind="array" tilt={0.4}/></div><div className="hero-terminal"><div className="terminal-top"><span className="window-dots"><i/><i/><i/></span><span>your_first_steps.py</span><span className="badge">PYTHON</span></div><CodeBlock code={heroCode} activeLine={heroSteps[index].line}/><div className="hero-output"><Terminal size={15}/><span>{index === 0 ? 'Ready to explore.' : `Build with ${heroSteps[index].caption}.`}</span><button className="icon-button" onClick={() => setPlaying(!playing)} aria-label={playing ? 'Pause hero demonstration' : 'Play hero demonstration'}>{playing ? <Pause size={14}/> : <Play size={14}/>}</button></div><div className="hero-demo-note">Authored preview · run your own code in the lessons</div></div><div className="floating-tag tag-bottom"><span className="mentor-mini"><Sparkles size={14}/></span> A mentor for your next “why?”</div></div>
    </section>
    <div className="feature-strip page-width"><span><BoxIcon/> Visual understanding</span><span><Code2 size={18}/> Real Python execution</span><span><Sparkles size={18}/> Local AI guidance</span><span><Layers3 size={18}/> Python → DSA</span></div>
    <section className="section page-width" id="learning-path"><div className="section-top"><div><span className="eyebrow">SMALL STEPS. REAL MOMENTUM.</span><h2>Your path from curious<br/>to capable.</h2><p className="muted">A thoughtful sequence. Room to experiment. Progress that stays with you.</p></div><div className="track-switch segmented"><button className={track === 'python' ? 'selected' : ''} onClick={() => setTrack('python')}><Code2 size={16}/> Python foundations</button><button className={track === 'dsa' ? 'selected' : ''} onClick={() => setTrack('dsa')}><Layers3 size={16}/> DSA essentials</button></div></div>
      {loading ? <p className="panel inset muted">Loading your learning path…</p> : error ? <div className="panel inset"><p className="error">{error}</p><button className="button secondary" onClick={reload}>Retry curriculum</button></div> : !chapters.length ? <p className="panel inset">No lessons are seeded yet. Run <code>python manage.py seed_content</code> in the backend.</p> : <div className="course-grid">{chapters.filter(c => c.track === track).map((chapter, i) => <Link className={`course-card ${i === 0 ? 'featured' : ''}`} key={chapter.id} to={`/learn/${chapter.id}`}><div className="course-card-top"><span className="chapter-number">{String(chapter.order).padStart(2, '0')}</span><span className="small muted">{chapter.content__minutes} MIN</span></div><div className="course-glyph">{i % 4 === 0 ? <Braces/> : i % 4 === 1 ? <Zap/> : i % 4 === 2 ? <Terminal/> : <Layers3/>}</div><h3>{chapter.title}</h3><p>{chapter.summary}</p><div className="course-card-bottom"><span>{track === 'python' ? 'FOUNDATIONS' : 'ALGORITHMIC THINKING'}</span><ArrowRight size={18}/></div></Link>)}</div>}
    </section>
    <section className="learning-loop page-width"><div><span className="eyebrow">LESS PASSIVE WATCHING. MORE “AHA.”</span><h2>Understand it.<br/>Try it. Make it yours.</h2><p>One connected workspace takes you from a visual explanation to a working solution. Your progress is based on practice, not predictions.</p><Link className="inline-link" to="/learn/values">Step inside your first lesson <ArrowRight size={16}/></Link></div><div className="loop-steps">{[{ icon: BookOpen, title: 'See the idea', text: 'Scroll through a clear explanation. Step through the moving parts.' }, { icon: Code2, title: 'Test your understanding', text: 'Write and run actual Python. Learn from output and exercise checks.' }, { icon: Sparkles, title: 'Find your next step', text: 'Ask your local Ollama mentor for a focused hint, then try again.' }].map((s, i) => <div key={s.title}><span className="loop-icon"><s.icon size={21}/></span><div><small>0{i + 1}</small><h3>{s.title}</h3><p>{s.text}</p></div><ChevronRight size={17}/></div>)}</div></section>
    <section className="closing page-width"><span className="eyebrow">YOUR FIRST LINE IS JUST THE BEGINNING</span><h2>A little practice.<br/><span>A whole new way to think.</span></h2><Link to="/learn/values" className="button primary large">Let’s write some Python <ArrowRight size={18}/></Link><p className="fine-print">24 original lessons · 2 connected tracks · your pace</p></section>
  </>
}
function BoxIcon() { return <span className="tiny-cube">◇</span> }
