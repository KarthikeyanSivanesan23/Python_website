import { createContext, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import type { Chapter } from '../types'
import { api, errorMessage } from '../api'
const Context = createContext<{ chapters: Chapter[]; error: string; loading: boolean; reload: () => void }>(null!)
export function CurriculumProvider({ children }: { children: ReactNode }) {
  const [chapters, setChapters] = useState<Chapter[]>([]), [error, setError] = useState(''), [loading, setLoading] = useState(true)
  function reload() { setLoading(true); setError(''); api<Chapter[]>('curriculum/').then(setChapters).catch(e => setError(errorMessage(e))).finally(() => setLoading(false)) }
  useEffect(reload, [])
  return <Context.Provider value={{ chapters, error, loading, reload }}>{children}</Context.Provider>
}
export function useCurriculum() { return useContext(Context) }
