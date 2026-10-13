import type { RunResult, TestCase } from '../../types'
export type RuntimeState = 'idle' | 'loading' | 'running'
export class PythonRuntime {
  private worker?: Worker
  private id = 0
  private pending?: { resolve: (result: RunResult) => void; reject: (error: Error) => void }
  private timer?: ReturnType<typeof setTimeout>
  constructor(private onState: (state: RuntimeState) => void) {}
  run(code: string, stdin: string[], tests?: TestCase[]): Promise<RunResult> {
    if (this.pending) return Promise.reject(new Error('Execution is already in progress.'))
    if (!this.worker) this.worker = new Worker(new URL('../../workers/python.worker.ts', import.meta.url), { type: 'module' })
    const id = ++this.id
    this.onState('loading')
    return new Promise((resolve, reject) => {
      this.pending = { resolve, reject }
      this.timer = setTimeout(() => this.stop('Python initialization timed out. Check your connection to the configured Pyodide asset host.'), 90000)
      this.worker!.onmessage = ({ data }) => {
        if (data.id !== this.id || !this.pending) return
        if (data.type === 'running') {
          clearTimeout(this.timer)
          this.onState('running')
          this.timer = setTimeout(() => this.stop('Execution deadline exceeded (8 seconds). The worker was terminated; Run creates a fresh runtime.'), 8000)
        } else if (data.type === 'done' || data.type === 'error') {
          clearTimeout(this.timer)
          const pending = this.pending
          this.pending = undefined
          this.onState('idle')
          if (data.type === 'done') pending.resolve(data.result)
          else pending.reject(new Error(data.message))
        }
      }
      this.worker!.onerror = event => this.stop(event.message || 'Python worker failed to load.')
      this.worker!.postMessage({ id, code, stdin, tests, indexURL: import.meta.env.VITE_PYODIDE_INDEX_URL || 'https://cdn.jsdelivr.net/pyodide/v314.0.7/full/' })
    })
  }
  stop(message = 'Execution stopped. Run will create a fresh Python runtime.') {
    clearTimeout(this.timer)
    this.worker?.terminate(); this.worker = undefined
    this.id++
    const pending = this.pending; this.pending = undefined
    this.onState('idle'); pending?.reject(new Error(message))
  }
  dispose() { this.stop('Editor closed.') }
}
