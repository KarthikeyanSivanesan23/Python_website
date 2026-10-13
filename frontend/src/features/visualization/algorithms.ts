import type { Demo, DemoStep, Lesson } from '../../types'
const frame = (line: number, caption: string, values: (string | number)[], active: number[] = [], edges: number[][] = [], labels: string[] = []): DemoStep => ({ line, caption, values: values.map(String), active, edges, labels })
const pythonLiteral = (value: unknown): string => {
  if (value === null) return 'None'
  if (Array.isArray(value)) return `[${value.map(pythonLiteral).join(', ')}]`
  if (typeof value === 'object') return `{${Object.entries(value as Record<string, unknown>).map(([k, v]) => `${JSON.stringify(k)}: ${pythonLiteral(v)}`).join(', ')}}`
  return JSON.stringify(value)
}

export function buildDemo(lesson: Lesson, input: string, targetText: string): Demo {
  const id = lesson.id
  const original = lesson.content.demo
  if (lesson.track !== 'dsa') return original
  let code = original.code
  const steps: DemoStep[] = []
  if (id.startsWith('graph-')) {
    const graph: Record<string, string[]> = JSON.parse(input)
    if (!graph || Array.isArray(graph) || typeof graph !== 'object') throw new Error('Enter a JSON adjacency object, such as {"A":["B"],"B":[]}.')
    const keys = Object.keys(graph)
    if (!keys.length || keys.length > 8 || keys.some(k => !/^[A-Za-z0-9]{1,4}$/.test(k)) || keys.some(k => !Array.isArray(graph[k]) || graph[k].length > 8 || graph[k].some(v => typeof v !== 'string' || !keys.includes(v)))) throw new Error('Use 1–8 nodes with short letter/number names. Each neighbor must be an existing node.')
    if (!keys.includes(targetText)) throw new Error('The starting node must exist in the graph.')
    const edges = keys.flatMap((key, i) => graph[key].map(v => [i, keys.indexOf(v)]))
    const seen = new Set<string>(), order: string[] = []
    if (id === 'graph-bfs') {
      const queue = [targetText]; seen.add(targetText)
      while (queue.length) {
        const node = queue.shift()!; order.push(node)
        for (const n of graph[node]) if (!seen.has(n)) { seen.add(n); queue.push(n) }
        steps.push(frame(7, `Visit ${node}. Queue: [${queue.join(', ')}]. Order: ${order.join(' → ')}.`, keys, [keys.indexOf(node)], edges))
      }
    } else {
      const visit = (node: string) => {
        if (seen.has(node)) return
        seen.add(node); order.push(node)
        steps.push(frame(8, `Visit ${node}. Depth-first order so far: ${order.join(' → ')}.`, keys, [keys.indexOf(node)], edges))
        graph[node].forEach(visit)
      }
      visit(targetText)
    }
    code = code.slice(0, code.lastIndexOf('\nprint(')) + `\nprint(${id === 'graph-bfs' ? 'bfs' : 'dfs'}(${pythonLiteral(graph)}, ${pythonLiteral(targetText)}))\n`
    return { ...original, code, steps }
  }
  const parts = input.trim() ? input.split(',').map(s => s.trim()) : []
  if (parts.length > 8 || parts.some(s => !/^-?\d{1,2}$/.test(s))) throw new Error('Use at most 8 comma-separated integers between -99 and 99.')
  const values = parts.map(Number)
  const target = Number(targetText)
  if (!Number.isFinite(target) || !Number.isInteger(target)) throw new Error('Target must be an integer.')
  const call = (fn: string, extra = '') => { code = code.slice(0, code.lastIndexOf('\nprint(')) + `\nprint(${fn}(${JSON.stringify(values)}${extra}))\n` }
  if (id === 'linear-search') {
    call('linear_search', `, ${target}`)
    let found = false
    for (let i = 0; i < values.length; i++) {
      found = values[i] === target
      steps.push(frame(found ? 4 : 3, found ? `Found ${target} at index ${i}.` : `${values[i]} does not equal ${target}. Continue.`, values, [i]))
      if (found) break
    }
    if (!found) steps.push(frame(5, 'No matching value. Return -1.', values))
  } else if (id === 'binary-search') {
    if (values.some((v, i) => i > 0 && v <= values[i - 1])) throw new Error('Binary search inputs must be sorted ascending with distinct values.')
    call('binary_search', `, ${target}`)
    let low = 0, high = values.length - 1, found = false
    while (low <= high) {
      const mid = Math.floor((low + high) / 2)
      steps.push(frame(4, `Search indices ${low}–${high}; midpoint ${mid} holds ${values[mid]}.`, values, [mid]))
      if (values[mid] === target) { steps.push(frame(6, `Found ${target} at index ${mid}.`, values, [mid])); found = true; break }
      if (values[mid] < target) { low = mid + 1; steps.push(frame(8, `Move low to ${low}; discard the left half.`, values, [mid])) }
      else { high = mid - 1; steps.push(frame(10, `Move high to ${high}; discard the right half.`, values, [mid])) }
    }
    if (!found) steps.push(frame(11, 'The interval is empty. Return -1.', values))
  } else if (id === 'bubble-sort') {
    call('bubble_sort'); const a = [...values]
    for (let end = a.length - 1; end > 0; end--) for (let i = 0; i < end; i++) {
      steps.push(frame(5, `Compare indices ${i} and ${i + 1}.`, a, [i, i + 1]))
      if (a[i] > a[i + 1]) { [a[i], a[i + 1]] = [a[i + 1], a[i]]; steps.push(frame(6, 'Swap the out-of-order neighbors.', a, [i, i + 1])) }
    }
    steps.push(frame(7, 'Return the sorted copy.', a, a.map((_, i) => i)))
  } else if (id === 'insertion-sort') {
    call('insertion_sort'); const a = [...values]
    for (let i = 1; i < a.length; i++) {
      const key = a[i]; let j = i - 1
      steps.push(frame(4, `Hold key = ${key} outside the array.`, a, [i]))
      while (j >= 0 && a[j] > key) { a[j + 1] = a[j]; steps.push(frame(7, `Shift ${a[j]} right; key ${key} remains held.`, a, [j + 1])); j-- }
      a[j + 1] = key; steps.push(frame(9, `Insert held key ${key} at index ${j + 1}.`, a, [j + 1]))
    }
    steps.push(frame(10, 'Return the sorted copy.', a))
  } else if (id === 'merge-sort') {
    call('merge_sort')
    const sort = (a: number[]): number[] => {
      if (a.length <= 1) { steps.push(frame(3, `Base case: [${a}] is sorted.`, a)); return [...a] }
      const mid = Math.floor(a.length / 2)
      steps.push(frame(4, `Split this call at ${mid}: [${a.slice(0, mid)}] and [${a.slice(mid)}].`, a, a.slice(0, mid).map((_, i) => i)))
      const l = sort(a.slice(0, mid)), r = sort(a.slice(mid)), out: number[] = []
      let i = 0, j = 0
      while (i < l.length && j < r.length) {
        if (l[i] <= r[j]) out.push(l[i++]); else out.push(r[j++])
        steps.push(frame(10, `Merge sorted halves [${l}] + [${r}]. Output so far: [${out}].`, out, [out.length - 1]))
      }
      out.push(...l.slice(i), ...r.slice(j)); steps.push(frame(16, 'Append the remaining tail and return this merged list.', out)); return out
    }
    sort(values)
  } else if (id === 'recursion') {
    if (values.length !== 1 || values[0] < 0 || values[0] > 7) throw new Error('Enter one factorial input from 0 through 7.')
    call('factorial'); const n = values[0]
    code = original.code.slice(0, original.code.lastIndexOf('\nprint(')) + `\nprint(factorial(${n}))\n`
    const stack: string[] = []
    for (let x = n; x >= 0; x--) { stack.push(`f(${x})`); steps.push(frame(x ? 4 : 3, x ? `f(${x}) waits for f(${x - 1}).` : 'Base case returns 1.', stack, [stack.length - 1])) }
    let result = 1
    for (let x = 1; x <= n; x++) { stack.pop(); result *= x; steps.push(frame(4, `Unwind f(${x}): return ${result}.`, stack, [stack.length - 1])) }
  } else if (id === 'complexity') {
    code = original.code.replace('numbers = [2, 4, 6, 8]', `numbers = ${JSON.stringify(values)}`)
    let total = 0
    values.forEach((n, i) => { total += n; steps.push(frame(4, `${i + 1} of ${values.length} visits. Total = ${total}; only one accumulator.`, values, [i])) })
  } else if (id === 'linked-lists') {
    let head: unknown = null
    for (let i = values.length - 1; i >= 0; i--) head = { value: values[i], next: head }
    code = original.code.replace(/^head = .*\n/, `head = ${pythonLiteral(head)}\n`)
    const v = [...values.map(String), 'None'], edges = values.map((_, i) => [i, i + 1])
    v.forEach((_, i) => steps.push(frame(i === values.length ? 3 : 4, i === values.length ? 'None ends traversal.' : `Visit node ${i}, then follow its next link.`, v, [i], edges)))
  } else if (id === 'trees') {
    const tree = (i: number): unknown => i >= values.length ? null : { value: values[i], left: tree(i * 2 + 1), right: tree(i * 2 + 2) }
    code = original.code.replace(/tree = .*\n/, `tree = ${pythonLiteral(tree(0))}\n`)
    const edges = values.flatMap((_, i) => [i * 2 + 1, i * 2 + 2].filter(j => j < values.length).map(j => [i, j]))
    const order: number[] = []
    const visit = (i: number) => { if (i >= values.length) return; visit(i * 2 + 1); order.push(values[i]); steps.push(frame(4, `Inorder: ${order.join(' → ')}. Input uses level-order node positions.`, values, [i], edges)); visit(i * 2 + 2) }
    visit(0)
  } else if (id === 'stacks-queues') {
    if (!values.length) throw new Error('Use at least one item for pop/popleft.')
    code = original.code.replaceAll('[1, 2, 3]', JSON.stringify(values))
    steps.push(frame(2, 'Stack: the last item is on top.', values, [values.length - 1]), frame(3, `pop returns ${values.at(-1)}.`, values.slice(0, -1)), frame(4, 'Queue: the first arrival is at the front.', values, [0]), frame(5, `popleft returns ${values[0]}.`, values.slice(1)))
  }
  if (!steps.length) steps.push(frame(1, 'Empty input: no elements to visit.', []))
  return { ...original, code, steps }
}

export function defaultInput(id: string) {
  if (id.startsWith('graph-')) return '{"A":["B","C"],"B":["D"],"C":[],"D":[]}'
  if (id === 'binary-search') return '1, 3, 5, 7, 9'
  if (id === 'recursion') return '3'
  if (id === 'trees' || id === 'stacks-queues') return '2, 1, 3'
  return '4, 2, 7, 1'
}
