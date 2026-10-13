import { lazy, Suspense, useCallback, useEffect, useRef, useState } from 'react'
import { Check, ChevronRight, Lightbulb, Play, RotateCcw, Send, Square, Terminal, Save, Eye } from 'lucide-react'
import { Link } from 'react-router-dom'
import { api, post, errorMessage } from '../../api'
import { useAuth } from '../../auth'
import type { Draft, Exercise, RunResult, TestResult } from '../../types'
import { PythonRuntime } from './runtime'
import type { RuntimeState } from './runtime'
import Mentor from '../mentor/Mentor'
import { CodeBlock } from '../../components/CodeBlock'
const Monaco = lazy(() => import('./Monaco'))

export default function Practice({ exercise }: { exercise: Exercise }) {
  const { user } = useAuth()
  const [code, setCode] = useState(exercise.starter), [revision, setRevision] = useState(0)
  const [input, setInput] = useState(exercise.tests[0]?.stdin.join('\n') || '')
  const [result, setResult] = useState<RunResult | null>(null), [runtimeState, setRuntimeState] = useState<RuntimeState>('idle')
  const [simple, setSimple] = useState(() => window.matchMedia('(max-width: 700px)').matches)
  const [saveState, setSaveState] = useState(''), [error, setError] = useState(''), [submitState, setSubmitState] = useState('')
  const [hints, setHints] = useState<string[]>([]), [solution, setSolution] = useState<{ solution: string; explanation: string } | null>(null)
  const [revealBusy, setRevealBusy] = useState(false), [ready, setReady] = useState(!user)
  const runtime = useRef<PythonRuntime | null>(null), serverRevision = useRef(0), savedCode = useRef(exercise.starter), saving = useRef(false)
  const currentCode = useRef(code); currentCode.current = code
  const alive = useRef(true), runRef = useRef<() => void>(() => {})
  const bufferKey = `studio:draft:${user?.id ?? 'guest'}:${exercise.id}`
  useEffect(() => { alive.current = true; runtime.current = new PythonRuntime(state => { if (alive.current) setRuntimeState(state) }); return () => { alive.current = false; runtime.current?.dispose() } }, [])
  useEffect(() => {
    let cancelled = false
    setReady(false); setHints([]); setSolution(null)
    const buffer = (() => { try { return JSON.parse(localStorage.getItem(bufferKey) || 'null') as { code: string; updated: number } | null } catch { return null } })()
    if (!user) { setCode(buffer?.code ?? exercise.starter); setSaveState('Guest draft · this browser only'); setReady(true); return }
    api<Draft>(`exercises/${exercise.id}/draft/`).then(draft => {
      if (cancelled) return
      serverRevision.current = draft.revision; savedCode.current = draft.code
      const recovered = buffer && buffer.updated > Date.parse(draft.updated_at || '1970-01-01')
      setCode(recovered ? buffer.code : draft.code); setSaveState(recovered ? 'Recovered unsaved changes' : 'Saved to your account'); setReady(true)
    }).catch(e => { if (!cancelled) { setSaveState(errorMessage(e)); if (buffer) setCode(buffer.code) } })
    return () => { cancelled = true }
  }, [user, exercise.id, exercise.starter, bufferKey])
  const save = useCallback(async () => {
    if (!user || !ready || saving.current || currentCode.current === savedCode.current) return
    saving.current = true
    const snapshot = currentCode.current
    setSaveState('Saving…')
    try {
      const data = await api<Draft>(`exercises/${exercise.id}/draft/`, { method: 'PUT', body: JSON.stringify({ code: snapshot, revision: serverRevision.current }) })
      if (!alive.current) return
      serverRevision.current = data.revision; savedCode.current = snapshot
      if (currentCode.current === snapshot) { localStorage.removeItem(bufferKey); setSaveState('Saved to your account') }
      else setSaveState('Changes waiting to save')
    } catch (e) { if (alive.current) setSaveState(`Not saved: ${errorMessage(e)}`) }
    finally { saving.current = false }
  }, [user, ready, exercise.id, bufferKey])
  useEffect(() => { if (!ready) return; const timer = setTimeout(() => void save(), 1000); return () => clearTimeout(timer) }, [code, save, ready])
  useEffect(() => { if (!user || !ready) return; const timer = setInterval(() => { if (currentCode.current !== savedCode.current) void save() }, 7000); return () => clearInterval(timer) }, [save, user, ready])
  function edit(value: string) {
    if (value.length > 20000) { setError('Code is limited to 20,000 characters.'); return }
    setCode(value); setRevision(r => r + 1)
    try { localStorage.setItem(bufferKey, JSON.stringify({ code: value, updated: Date.now() })) } catch { setSaveState('Local buffer unavailable; use Save draft to persist online.') }
    if (user) setSaveState('Unsaved changes')
  }
  async function execute(submit: boolean) {
    if (!runtime.current || runtimeState !== 'idle') return
    setResult(null); setError(''); setSubmitState('')
    const snapshot = currentCode.current
    let output: RunResult
    try {
      output = await runtime.current.run(snapshot, input === '' ? [] : input.split('\n'), submit ? exercise.tests : undefined)
    } catch (e) {
      const message = errorMessage(e)
      const status = message.includes('deadline') ? 'timeout' : 'stopped'
      output = { stdout: '', stderr: message, results: submit ? exercise.tests.map(t => ({ name: t.name, status, actual: '', expected: JSON.stringify(t.expected) })) as TestResult[] : [] }
    }
    if (!alive.current) return
    setResult(output)
    if (submit && user) {
      try { await post(`exercises/${exercise.id}/submit/`, { code: snapshot, results: output.results }); if (alive.current) setSubmitState('Attempt saved to your practice history.') }
      catch (e) { if (alive.current) setSubmitState(`Results shown locally; attempt not saved. ${errorMessage(e)}`) }
    } else if (submit) setSubmitState('Sign in to record this attempt in your practice history.')
  }
  runRef.current = () => void execute(false)
  async function reveal(kind: 'hint' | 'solution') {
    if (!user) { setError('Sign in to record hint usage and view guidance.'); return }
    setRevealBusy(true); setError('')
    try {
      if (kind === 'hint') { const data = await post<{ hint: string }>(`exercises/${exercise.id}/reveal/hint/`, { level: hints.length }); setHints(old => [...old, data.hint]) }
      else setSolution(await post(`exercises/${exercise.id}/reveal/solution/`))
    } catch (e) { setError(errorMessage(e)) }
    finally { setRevealBusy(false) }
  }
  const feedback = result ? JSON.stringify(result).slice(0, 4000) : 'No execution or test results yet.'
  return <div className="practice-layout"><div className="practice-main">
    <div className="exercise-brief"><span className="eyebrow">YOUR TURN</span><h3>{exercise.title}</h3><p>{exercise.statement}</p><div className="exercise-examples">{exercise.examples.map((example, i) => <div key={i}><small>EXAMPLE {i + 1}</small><code>{example.input || 'Program output'} <ChevronRight size={13}/> {JSON.stringify(example.output)}</code></div>)}</div><p className="fine-print">{exercise.constraints.join(' ')} · {exercise.source}</p></div>
    <div className="editor-panel panel"><div className="editor-toolbar"><div className="file-tab"><span className="python-dot"/>practice.py</div><button className="text-button" onClick={() => setSimple(!simple)}>{simple ? 'Use Monaco editor' : 'Use simple editor'}</button></div>
      {!ready && user && <p className="inset muted">Loading your saved draft… If unavailable, refresh after restoring the backend.</p>}
      {simple ? <textarea className="simple-editor" aria-label="Python code editor" value={code} onChange={e => edit(e.target.value)} spellCheck={false} onKeyDown={e => { if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') { e.preventDefault(); void execute(false) } }}/>: <Suspense fallback={<p className="inset muted">Loading editor…</p>}><Monaco code={code} onChange={edit} onRun={() => runRef.current()}/></Suspense>}
      <div className="editor-actions"><div><button className="button primary" onClick={() => void execute(false)} disabled={runtimeState !== 'idle'}><Play size={15}/> Run</button><button className="button secondary" onClick={() => runtime.current?.stop()} disabled={runtimeState === 'idle'}><Square size={13}/> Stop</button><button className="icon-button" aria-label="Reset code" title="Reset to starter code" onClick={() => edit(exercise.starter)} disabled={runtimeState !== 'idle'}><RotateCcw size={16}/></button></div><button className="button secondary submit" onClick={() => void execute(true)} disabled={runtimeState !== 'idle'}><Send size={14}/> Submit</button></div>
      <div className="save-row"><span aria-live="polite"><span className={`status-dot ${runtimeState === 'idle' ? 'online' : 'working'}`}/> {runtimeState === 'loading' ? 'Loading browser Python…' : runtimeState === 'running' ? 'Executing · 8-second deadline' : 'Python · runs in your browser'}</span><button className="text-button" onClick={() => void save()} disabled={!user || !ready}><Save size={12}/> Save draft</button></div>
      <p className="fine-print inset" role="status">{saveState || 'Loading draft…'} · Ctrl/⌘ + Enter to run. Monaco: Ctrl+M toggles Tab focus navigation.</p>
      <div className="io-panels"><div><label htmlFor={`input-${exercise.id}`}>INPUT <span>one response per line</span></label><textarea id={`input-${exercise.id}`} rows={3} value={input} onChange={e => setInput(e.target.value)} placeholder="Values for input()" maxLength={4000}/></div><div><label><Terminal size={13}/> OUTPUT</label><pre className="output" aria-label="Python output" aria-live="polite">{result?.stdout || (runtimeState !== 'idle' ? 'Waiting for execution…' : 'Run your code to see real output here.')}</pre></div></div>
      {result?.stderr && <div className="error-output"><strong>Execution error</strong><pre aria-label="Python errors">{result.stderr}</pre></div>}
      {!!result?.results.length && <div className="test-results" aria-live="polite"><h4><Check size={16}/> {result.results.filter(r => r.status === 'passed').length} / {result.results.length} checks passed</h4>{result.results.map((r, i) => <details key={i} className={`test-result ${r.status}`} open={r.status !== 'passed'}><summary><span>{r.status === 'passed' ? '✓' : '×'} {r.name}</span><span>{r.status.replaceAll('_', ' ')}</span></summary><pre>Expected: {r.expected}{'\n'}Actual: {r.actual || '(no result)'}{r.error ? `\n${r.error}` : ''}</pre></details>)}<p className="fine-print">These inspectable browser tests provide learning feedback, not a secure assessment. Passing covers these cases, not every possible input.</p></div>}
      {submitState && <p className="inset small" role="status">{submitState}</p>}
    </div>
    {error && <p className="error" role="alert">{error}</p>}
    <div className="guidance-actions"><button className="button secondary" disabled={revealBusy || hints.length >= exercise.hint_count} onClick={() => void reveal('hint')}><Lightbulb size={16}/> Hint {Math.min(hints.length + 1, exercise.hint_count)} / {exercise.hint_count}</button><button className="text-button" disabled={revealBusy} onClick={() => void reveal('solution')}><Eye size={15}/> View reference solution</button></div>
    {hints.map((hint, i) => <div className="hint" key={i}><Lightbulb size={17}/><p><strong>Hint {i + 1}.</strong> {hint}</p></div>)}
    {solution && <details className="solution panel" open><summary>Reviewed reference solution · view recorded</summary><CodeBlock code={solution.solution}/><p className="inset">{solution.explanation}</p></details>}
    <p className="fine-print">Browser Python supports standard-library beginner exercises. It cannot automatically read your local files; file fixtures live in a resettable virtual workspace. External packages and OS integrations may be unavailable. {!user && <Link className="inline-link" to="/auth">Sign in to save across sessions.</Link>}</p>
  </div><Mentor exercise={exercise} code={code} revision={revision} feedback={feedback}/></div>
}
