/// <reference lib="webworker" />
import type { PyodideInterface } from 'pyodide'
import type { RunResult, TestCase } from '../types'

declare const self: DedicatedWorkerGlobalScope
let runtime: Promise<PyodideInterface> | undefined
let busy = false
const harness = `
import sys, io, json, traceback, os, shutil
from contextlib import redirect_stdout, redirect_stderr

class _BoundedOutput(io.StringIO):
    def write(self, value):
        room = 16000 - self.tell()
        if room > 0:
            super().write(value[:room])
        return len(value)

def _run_attempt(payload):
    root = '/home/pyodide/practice'
    os.chdir('/home/pyodide')
    if os.path.exists(root):
        shutil.rmtree(root)
    os.mkdir(root)
    os.chdir(root)
    for name, text in {'data.txt': '3\\n4\\n5\\n', 'empty.txt': '', 'signed.txt': '-5\\n3\\n'}.items():
        with open(name, 'w', encoding='utf-8') as file:
            file.write(text)
    results = []
    all_out, all_err = '', ''
    tests = payload.get('tests') or [None]
    for test in tests:
        # Each case gets fresh names, input, output, and file fixtures.
        os.chdir('/home/pyodide')
        if os.path.exists(root):
            shutil.rmtree(root)
        os.mkdir(root)
        os.chdir(root)
        for name, text in {'data.txt': '3\\n4\\n5\\n', 'empty.txt': '', 'signed.txt': '-5\\n3\\n'}.items():
            with open(name, 'w', encoding='utf-8') as file:
                file.write(text)
        stdout, stderr = _BoundedOutput(), _BoundedOutput()
        lines = test['stdin'] if test else payload['stdin']
        old_stdin = sys.stdin
        sys.stdin = io.StringIO(''.join(line + '\\n' for line in lines))
        namespace = {'__name__': '__main__'}
        result = {'name': test['name'] if test else 'Run', 'status': 'passed', 'actual': '', 'expected': '', 'error': ''}
        try:
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exec(compile(payload['code'], '<practice>', 'exec'), namespace)
                if test:
                    actual = eval(test['expression'], namespace) if test['expression'] else stdout.getvalue()
                    result['status'] = 'passed' if actual == test['expected'] else 'wrong'
                    result['actual'] = repr(actual)[:3000]
                    result['expected'] = repr(test['expected'])[:3000]
        except BaseException as exc:
            result['status'] = 'syntax_error' if isinstance(exc, SyntaxError) else 'runtime_error'
            result['error'] = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))[-3000:]
            if test:
                result['expected'] = repr(test['expected'])[:3000]
            stderr.write(result['error'])
        finally:
            sys.stdin = old_stdin
        all_out += stdout.getvalue()
        all_err += stderr.getvalue()
        if stdout.tell() >= 16000:
            all_out += '\\n[Output capped at 16,000 characters]'
        if test:
            results.append(result)
    return json.dumps({'stdout': all_out[:16500], 'stderr': all_err[:16000], 'results': results})
`

self.onmessage = async (event: MessageEvent<{ id: number; code: string; stdin: string[]; tests?: TestCase[]; indexURL: string }>) => {
  if (busy) return
  busy = true
  const { id, indexURL, ...payload } = event.data
  try {
    if (!runtime) {
      self.postMessage({ id, type: 'loading' })
      runtime = (async () => {
        const url = `${indexURL}pyodide.mjs`
        const { loadPyodide } = await import(/* @vite-ignore */ url) as typeof import('pyodide')
        return loadPyodide({ indexURL })
      })()
    }
    const py = await runtime
    self.postMessage({ id, type: 'running' })
    const globals = py.toPy({ payload_json: JSON.stringify(payload) })
    try {
      const encoded = await py.runPythonAsync(`${harness}\n_run_attempt(json.loads(payload_json))`, { globals })
      self.postMessage({ id, type: 'done', result: JSON.parse(encoded) as RunResult })
    } finally { globals.destroy() }
  } catch (error) {
    self.postMessage({ id, type: 'error', message: error instanceof Error ? error.message : String(error) })
    runtime = undefined
  } finally { busy = false }
}
