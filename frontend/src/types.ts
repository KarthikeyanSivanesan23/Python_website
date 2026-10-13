export type Track = 'python' | 'dsa'
export interface User { id: number; username: string }
export interface Chapter { id: string; track: Track; order: number; title: string; summary: string; content__minutes: number }
export interface DemoStep { line: number; caption: string; values: string[]; active: number[]; labels: string[]; edges: number[][] }
export interface Demo { kind: string; code: string; steps: DemoStep[] }
export interface TestCase { name: string; expression: string; expected: unknown; stdin: string[] }
export interface Exercise { id: string; title: string; statement: string; starter: string; difficulty: string; tests: TestCase[]; examples: { input: string; output: unknown }[]; constraints: string[]; prerequisites: string[]; source: string; hint_count: number }
export interface Lesson extends Chapter { version: number; content: { objective: string; explanation: string; example: string; expected_output: string; mistake: string; demo: Demo; prerequisites: string[]; minutes: number; extra_examples?: { title: string; explanation: string; code: string; expected_output: string }[] }; exercise: Exercise }
export interface TestResult { name: string; status: 'passed' | 'wrong' | 'syntax_error' | 'runtime_error' | 'timeout' | 'stopped'; actual: string; expected: string; error?: string }
export interface RunResult { stdout: string; stderr: string; results: TestResult[]; error?: string }
export interface Draft { code: string; revision: number; updated_at: string | null }
export interface Progress { lesson: string; completed: boolean; active_seconds: number; updated_at: string }
export interface Attempt { id: number; exercise: string; lesson: string; title: string; results: TestResult[]; passed: boolean; hints_used: number; solution_viewed: boolean; created_at: string }
export interface DashboardData { progress: Progress[]; attempts: Attempt[]; resume: string; revisit: { lesson: string; title: string; reason: string }[]; rules: string }
export interface Readiness { backend: boolean; database: boolean; database_engine: string; database_message: string; ollama: { reachable: boolean; model_available: boolean; model: string; message: string } }
export interface MentorMessage { role: 'user' | 'assistant'; text: string }
