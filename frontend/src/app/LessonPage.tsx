import { lazy, Suspense, useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, ArrowRight, BookOpen, CheckCircle2, Clock, Lightbulb } from 'lucide-react'
import { api, post, errorMessage } from '../api'
import { useAuth } from '../auth'
import { useCurriculum } from './Curriculum'
import type { DashboardData, Lesson } from '../types'
import { CodeBlock } from '../components/CodeBlock'
import Demonstration from '../features/visualization/Demonstration'
const Practice = lazy(() => import('../features/editor/Practice'))

export default function LessonPage() {
  const { slug } = useParams(), { user } = useAuth(), { chapters } = useCurriculum()
  const [lesson, setLesson] = useState<Lesson | null>(null), [error, setError] = useState(''), [completed, setCompleted] = useState<string[]>([])
  const [completionMessage, setCompletionMessage] = useState(''), [retry, setRetry] = useState(0)
  const activity = useRef(Date.now())
  useEffect(() => { let cancelled = false; setLesson(null); setError(''); setCompletionMessage(''); window.scrollTo(0, 0); api<Lesson>(`lessons/${slug}/`).then(data => { if (!cancelled) setLesson(data) }).catch(e => { if (!cancelled) setError(errorMessage(e)) }); return () => { cancelled = true } }, [slug, retry])
  useEffect(() => { if (user) api<DashboardData>('dashboard/').then(data => setCompleted(data.progress.filter(p => p.completed).map(p => p.lesson))).catch(() => {}); else setCompleted([]) }, [user, slug])
  useEffect(() => {
    if (!user || !lesson) return
    void post(`progress/${lesson.id}/`).catch(() => {})
    const active = () => { activity.current = Date.now() }
    const events = ['pointerdown', 'keydown', 'scroll']
    events.forEach(name => window.addEventListener(name, active, { passive: true }))
    const interval = setInterval(() => { if (!document.hidden && Date.now() - activity.current < 30000) void post(`progress/${lesson.id}/`, { active_seconds: 15 }).catch(() => {}) }, 15000)
    return () => { events.forEach(name => window.removeEventListener(name, active)); clearInterval(interval) }
  }, [user, lesson])
  async function complete() {
    if (!lesson) return
    try { await post(`progress/${lesson.id}/`, { completed: !completed.includes(lesson.id) }); setCompleted(list => list.includes(lesson.id) ? list.filter(id => id !== lesson.id) : [...list, lesson.id]); setCompletionMessage('Progress saved to your account.') } catch (e) { setCompletionMessage(errorMessage(e)) }
  }
  if (error) return <div className="page-width section"><h1>Lesson unavailable</h1><p className="error">{error}</p><button className="button secondary" onClick={() => setRetry(n => n + 1)}>Retry lesson</button></div>
  if (!lesson) return <div className="page-width section"><p className="muted">Opening your next chapter…</p></div>
  const track = chapters.filter(c => c.track === lesson.track), index = track.findIndex(c => c.id === lesson.id), next = track[index + 1], previous = track[index - 1]
  return <div className="lesson-shell page-width"><aside className="lesson-sidebar"><Link className="back-link" to="/#learning-path"><ArrowLeft size={15}/> Learning path</Link><span className="eyebrow">{lesson.track === 'python' ? 'PYTHON FOUNDATIONS' : 'DSA ESSENTIALS'}</span><h3>Your next chapter.</h3><div className="track-progress"><div style={{ width: `${track.length ? completed.filter(id => track.some(c => c.id === id)).length / track.length * 100 : 0}%` }}/></div><span className="fine-print">{completed.filter(id => track.some(c => c.id === id)).length} of {track.length} chapters completed</span><nav aria-label="Topic navigation">{track.map(c => <Link key={c.id} className={c.id === lesson.id ? 'current' : ''} to={`/learn/${c.id}`}><span>{completed.includes(c.id) ? <CheckCircle2 size={16}/> : String(c.order).padStart(2, '0')}</span>{c.title}</Link>)}</nav><Link className="text-button" to={`/learn/${lesson.track === 'python' ? 'complexity' : 'values'}`}>Switch to {lesson.track === 'python' ? 'DSA' : 'Python'} <ArrowRight size={14}/></Link></aside>
    <article className="lesson-content"><div className="lesson-breadcrumb"><span>{lesson.track === 'python' ? 'Python foundations' : 'DSA essentials'}</span><span>/</span>Chapter {String(lesson.order).padStart(2, '0')}</div><header className="lesson-header"><div className="lesson-meta"><span className="badge">{lesson.exercise.difficulty}</span><span><Clock size={13}/> {lesson.content.minutes} min</span><span><BookOpen size={13}/> Read · explore · practise</span></div><h1>{lesson.title}</h1><p>{lesson.content.objective}</p><nav className="chapter-anchors" aria-label="Lesson sections"><a href="#understand">01 Understand</a><a href="#visualize">02 Visualize</a><a href="#practice">03 Practise</a></nav></header>
      <section className="lesson-section" id="understand"><span className="eyebrow">01 / BUILD YOUR MENTAL MODEL</span><h2>A small idea, a useful foundation.</h2><p className="explanation">{lesson.content.explanation}</p>{!!lesson.content.prerequisites.length && <div className="prerequisites"><span>Builds on</span>{lesson.content.prerequisites.map(id => <Link key={id} to={`/learn/${id}`}>{chapters.find(c => c.id === id)?.title || id}</Link>)}</div>}<div className="example-grid panel"><div><div className="file-tab"><span className="python-dot"/>example.py</div><CodeBlock code={lesson.content.example}/></div><div className="expected-output"><span className="eyebrow">EXPECTED OUTPUT</span>{lesson.id === 'input-output' && <p className="fine-print">Input: Ada</p>}<pre>{lesson.content.expected_output}</pre></div></div><div className="mistake"><Lightbulb size={20}/><div><h4>A common detour</h4><p>{lesson.content.mistake}</p></div></div></section>
      {lesson.content.extra_examples?.map(example => <div className="lesson-section" key={example.title}><h3>{example.title}</h3><p className="explanation">{example.explanation}</p><div className="example-grid panel"><CodeBlock code={example.code}/><div className="expected-output"><span className="eyebrow">EXPECTED OUTPUT</span><pre>{example.expected_output}</pre></div></div></div>)}
      <section className="lesson-section" id="visualize"><span className="eyebrow">02 / CONNECT THE MOVING PARTS</span><h2>Slow it down. See the connection.</h2><Demonstration key={lesson.id} lesson={lesson}/></section>
      <section className="lesson-section" id="practice"><span className="eyebrow">03 / MAKE IT YOURS</span><h2>Understanding starts with trying.</h2><Suspense fallback={<p>Loading your practice workspace…</p>}><Practice key={`${lesson.id}:${user?.id || 'guest'}`} exercise={lesson.exercise}/></Suspense></section>
      <div className="chapter-complete panel"><div><h3>{completed.includes(lesson.id) ? 'Another idea made yours.' : 'Ready to close this chapter?'}</h3><p className="muted">Mark it complete when you have studied and practised. You can always revisit it.</p>{completionMessage && <p role="status" className="small">{completionMessage}</p>}</div>{user ? <button className="button primary" onClick={() => void complete()}><CheckCircle2 size={16}/>{completed.includes(lesson.id) ? 'Mark incomplete' : 'Mark complete'}</button> : <Link className="button primary" to="/auth">Sign in to save progress</Link>}</div>
      <div className="lesson-next">{previous ? <Link to={`/learn/${previous.id}`}><ArrowLeft size={17}/><span><small>PREVIOUS CHAPTER</small>{previous.title}</span></Link> : <span/>}{next ? <Link to={`/learn/${next.id}`}><span><small>KEEP YOUR MOMENTUM</small>{next.title}</span><ArrowRight size={18}/></Link> : <Link to={lesson.track === 'python' ? '/learn/complexity' : '/dashboard'}><span><small>NEXT STEP</small>{lesson.track === 'python' ? 'Explore DSA essentials' : 'Your practice dashboard'}</span><ArrowRight size={18}/></Link>}</div>
    </article></div>
}
