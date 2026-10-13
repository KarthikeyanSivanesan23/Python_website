import { describe, expect, it } from 'vitest'
import { buildDemo } from './algorithms'
import type { Lesson } from '../../types'
const lesson = (id: string): Lesson => ({ id, track: 'dsa', content: { demo: { kind: id, code: 'def example():\n    pass\n\nprint(example())\n', steps: [] } } } as unknown as Lesson)
describe('editable algorithm demonstrations', () => {
  it('binary search rejects unsorted input and handles absent targets', () => {
    expect(() => buildDemo(lesson('binary-search'), '3,1', '1')).toThrow('sorted')
    const demo = buildDemo(lesson('binary-search'), '1,3,5,7', '6')
    expect(demo.steps.at(-1)?.caption).toContain('Return -1')
  })
  it.each(['bubble-sort', 'insertion-sort', 'merge-sort'])('%s preserves duplicates and negative values', id => {
    const demo = buildDemo(lesson(id), '3,-2,3,0', '0')
    expect(demo.steps.at(-1)?.values).toEqual(['-2', '0', '3', '3'])
  })
  it('graph traversal terminates on cycles and distinguishes BFS from DFS', () => {
    const graph = '{"A":["B","C"],"B":["D"],"C":[],"D":["A"]}'
    const visits = (id: string) => buildDemo(lesson(id), graph, 'A').steps.map(s => s.values[s.active[0]])
    expect(visits('graph-bfs')).toEqual(['A', 'B', 'C', 'D'])
    expect(visits('graph-dfs')).toEqual(['A', 'B', 'D', 'C'])
  })
  it('limits graph and recursion inputs', () => {
    expect(() => buildDemo(lesson('recursion'), '10', '0')).toThrow('0 through 7')
    expect(() => buildDemo(lesson('graph-bfs'), '{"A":["missing"]}', 'A')).toThrow('existing node')
  })
})
