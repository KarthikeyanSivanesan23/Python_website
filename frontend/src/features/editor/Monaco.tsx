import Editor, { loader } from '@monaco-editor/react'
import * as monaco from 'monaco-editor/editor/editor.api'
import 'monaco-editor/languages/definitions/python/register'
import EditorWorker from 'monaco-editor/editor/editor.worker.js?worker'
;(self as unknown as { MonacoEnvironment: unknown }).MonacoEnvironment = { getWorker: () => new EditorWorker() }
loader.config({ monaco })
monaco.editor.defineTheme('studio', {
  base: 'vs-dark', inherit: true,
  rules: [{ token: 'keyword', foreground: 'BDA5F5' }, { token: 'string', foreground: 'A6DBB2' }, { token: 'number', foreground: 'F0C584' }, { token: 'comment', foreground: '788B9F' }],
  colors: { 'editor.background': '#0C1321', 'editor.foreground': '#E2E8EF', 'editor.lineHighlightBackground': '#152236', 'editorLineNumber.foreground': '#60758D', 'editorCursor.foreground': '#79E4D1' },
})
export default function Monaco({ code, onChange, onRun }: { code: string; onChange: (code: string) => void; onRun: () => void }) {
  return <Editor height="330px" language="python" theme="studio" value={code} onChange={value => onChange(value || '')}
    options={{ fontFamily: 'Cascadia Code, Consolas, monospace', fontSize: 14, lineHeight: 24, minimap: { enabled: false }, padding: { top: 18 }, scrollBeyondLastLine: false, wordWrap: 'on', automaticLayout: true, tabSize: 4, ariaLabel: 'Python code editor', fixedOverflowWidgets: true }}
    onMount={editor => { editor.addAction({ id: 'run-python', label: 'Run Python', keybindings: [monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter], run: onRun }) }} loading={<p className="inset muted">Loading code editor…</p>} />
}
