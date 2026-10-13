import { lazy, Suspense, useEffect, useState } from 'react'
import { Link, NavLink, Route, Routes, useLocation } from 'react-router-dom'
import { ArrowUpRight, Braces, Menu, X } from 'lucide-react'
import project from '../../../shared/project.json'
import { useAuth } from '../auth'
import Home from './Home'
const LessonPage = lazy(() => import('./LessonPage'))
const Dashboard = lazy(() => import('./Dashboard'))
const AuthPage = lazy(() => import('./AuthPage'))
const StatusPage = lazy(() => import('./StatusPage'))
export default function App() {
  const { user, signout } = useAuth(), location = useLocation()
  const [open, setOpen] = useState(false), [error, setError] = useState('')
  useEffect(() => { setOpen(false); document.title = `${project.name} · ${project.tagline}`; if (!location.pathname.startsWith('/learn/')) window.scrollTo(0, 0) }, [location.pathname])
  return <><a className="skip-link" href="#main">Skip to content</a><header className="site-header"><div className="header-inner page-width"><Link to="/" className="brand" aria-label={`${project.name} home`}><span className="brand-symbol"><Braces size={22}/></span><span>{project.name}<small>LEARNING, IN A NEW DIMENSION</small></span></Link><button className="icon-button mobile-menu" aria-label={open ? 'Close navigation' : 'Open navigation'} aria-expanded={open} onClick={() => setOpen(!open)}>{open ? <X/> : <Menu/>}</button><nav className={open ? 'main-nav open' : 'main-nav'} aria-label="Main navigation"><NavLink to="/" end>Explore</NavLink><NavLink to="/learn/values" className={location.pathname.startsWith('/learn') ? 'active' : ''}>Learn</NavLink><NavLink to="/dashboard">My progress</NavLink><NavLink to="/status" className="service-link">Service status</NavLink></nav><div className="header-account">{user ? <><Link className="avatar" to="/dashboard" title={user.username}>{user.username.slice(0, 1).toUpperCase()}</Link><button className="text-button" onClick={() => void signout().catch(e => setError(e.message))}>Sign out</button></> : <Link className="button secondary" to="/auth">Your workspace <ArrowUpRight size={15}/></Link>}</div></div></header>{error && <p className="page-width error" role="alert">{error}</p>}<main id="main"><Suspense fallback={<p className="page-width section muted">Loading your workspace…</p>}><Routes><Route path="/" element={<Home/>}/><Route path="/learn/:slug" element={<LessonPage/>}/><Route path="/dashboard" element={<Dashboard/>}/><Route path="/auth" element={<AuthPage/>}/><Route path="/status" element={<StatusPage/>}/><Route path="*" element={<div className="page-width section"><h1>This path hasn’t been written.</h1><Link to="/" className="button primary">Back to learning</Link></div>}/></Routes></Suspense></main><footer className="site-footer page-width"><Link className="brand" to="/"><span className="brand-symbol"><Braces size={19}/></span>{project.name}</Link><p>Built for the moment something clicks.</p><Link to="/status">Service status <ArrowUpRight size={13}/></Link><span>Python & DSA · Original curriculum</span></footer></>
}
