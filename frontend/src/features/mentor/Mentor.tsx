import { useCallback, useEffect, useRef, useState } from 'react'
import { ArrowUp, Sparkles, WifiOff } from 'lucide-react'
import { Link } from 'react-router-dom'
import { api, post, errorMessage } from '../../api'
import { useAuth } from '../../auth'
import type { Exercise, MentorMessage, Readiness } from '../../types'

export default function Mentor({ exercise, code, revision, feedback }: { exercise: Exercise; code: string; revision: number; feedback: string }) {
  const { user } = useAuth()
  const [mode, setMode] = useState<'explain' | 'coach'>('coach'), [message, setMessage] = useState('')
  const [messages, setMessages] = useState<MentorMessage[]>([]), [busy, setBusy] = useState(false), [error, setError] = useState('')
  const [status, setStatus] = useState<Readiness | null>(null), [automatic, setAutomatic] = useState(false)
  const current = useRef({ code, revision, feedback }); current.current = { code, revision, feedback }
  const inFlight = useRef(false), lastAuto = useRef(''), mounted = useRef(true)
  const refresh = useCallback(() => { api<Readiness>('readiness/').then(setStatus).catch(e => setError(errorMessage(e))) }, [])
  useEffect(() => { mounted.current = true; refresh(); return () => { mounted.current = false } }, [refresh])
  useEffect(() => { let cancelled = false; setMessages([]); if (user) api<MentorMessage[]>(`exercises/${exercise.id}/mentor/`).then(data => { if (!cancelled) setMessages(data) }).catch(e => { if (!cancelled) setError(errorMessage(e)) }); return () => { cancelled = true } }, [user, exercise.id])
  const send = useCallback(async (text: string, auto = false) => {
    if (!user || inFlight.current || !text.trim()) return
    const snapshot = { ...current.current }
    inFlight.current = true; setBusy(true); setError('')
    if (!auto) setMessage('')
    try {
      const result = await post<{ text: string; revision: number }>(`exercises/${exercise.id}/mentor/`, { mode, message: text, ...snapshot })
      if (!mounted.current) return
      if (result.revision !== current.current.revision || snapshot.code !== current.current.code) { setError('Your code changed while the mentor was thinking. The outdated response was discarded; ask again for your current attempt.'); return }
      setMessages(previous => [...previous, { role: 'user' as const, text }, { role: 'assistant' as const, text: result.text }].slice(-20))
    } catch (e) { if (mounted.current) setError(errorMessage(e)) }
    finally { inFlight.current = false; if (mounted.current) setBusy(false) }
  }, [exercise.id, mode, user])
  useEffect(() => {
    if (!automatic || !revision || !user || !status?.ollama.model_available || code.trim().length < 20) return
    const timer = setTimeout(() => {
      if (inFlight.current || lastAuto.current === code || document.hidden) return
      lastAuto.current = code
      void send('Give me one focused hint about my current approach. Do not reveal the full solution.', true)
    }, 3500)
    return () => clearTimeout(timer)
  }, [code, revision, automatic, user, status, send])
  const available = status?.ollama.model_available
  return <aside className="mentor panel" aria-label="Python mentor">
    <div className="mentor-heading"><div className="mentor-orb"><Sparkles size={21}/></div><div><h3>Your thinking partner</h3><span className="muted small">Ollama mentor · {status?.ollama.model || 'checking connection'}</span></div><span className={`status-dot ${available ? 'online' : ''}`}/></div>
    <div className="segmented"><button className={mode === 'explain' ? 'selected' : ''} onClick={() => setMode('explain')}>Explain the question</button><button className={mode === 'coach' ? 'selected' : ''} onClick={() => setMode('coach')}>Coach my attempt</button></div>
    {!available && <div className="mentor-unavailable"><WifiOff size={18}/><div><strong>{status ? 'Mentor unavailable' : 'Checking Ollama…'}</strong><p>{status?.ollama.message || 'Lessons and Python execution remain available.'}</p><button className="text-button" onClick={refresh}>Check connection again</button></div></div>}
    <div className="mentor-messages" aria-live="polite">{messages.length === 0 ? <div className="mentor-empty"><Sparkles size={24}/><h4>A nudge, not a shortcut.</h4><p>Ask what the question means, share your approach, or run your code and ask about the result.</p><span className="fine-print">Answers appear here only after a real Ollama response.</span></div> : messages.map((m, i) => <div key={i} className={`chat-message ${m.role}`}><small>{m.role === 'user' ? 'YOU' : 'OLLAMA · AI GUIDANCE'}</small><p>{m.text}</p></div>)}{busy && <p className="thinking"><span className="status-dot online"/> Thinking about this attempt… You can keep running code.</p>}</div>
    {error && <p className="error inset" role="alert">{error}</p>}
    {user ? <><form className="mentor-compose" onSubmit={e => { e.preventDefault(); void send(message) }}><textarea aria-label="Ask your mentor" value={message} onChange={e => setMessage(e.target.value)} maxLength={1500} placeholder={mode === 'coach' ? 'Here’s what I’m trying…' : 'What does this question ask me to do?'} rows={2}/><button className="icon-button send-button" aria-label="Send mentor message" disabled={busy || !available || !message.trim()}><ArrowUp size={19}/></button></form><label className="auto-hints"><input type="checkbox" checked={automatic} onChange={e => setAutomatic(e.target.checked)}/> Optional hints after a typing pause</label></> : <p className="inset"><Link to="/auth" className="inline-link">Sign in</Link> to talk to the mentor and save your conversations.</p>}
    <p className="fine-print inset">AI explanations can be imperfect. Deterministic test feedback is shown separately in your editor.</p>
  </aside>
}
