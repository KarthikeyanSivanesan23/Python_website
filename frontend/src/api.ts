let csrf = ''
export class ApiError extends Error {
  constructor(message: string, public status: number) { super(message) }
}
export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), path.includes('/mentor/') ? 70000 : 12000)
  try {
    const response = await fetch(`/api/${path}`, { ...options, signal: options.signal || controller.signal, credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf, ...options.headers } })
    const text = await response.text()
    let data: Record<string, unknown>
    try { data = JSON.parse(text) } catch { throw new ApiError('The backend is unavailable or returned an invalid response. Check the Django server and database configuration.', response.status) }
    if (!response.ok) throw new ApiError(typeof data.detail === 'string' ? data.detail : JSON.stringify(data), response.status)
    if (typeof data.csrfToken === 'string') csrf = data.csrfToken
    return data as T
  } catch (error) {
    if (error instanceof ApiError) throw error
    throw new Error(error instanceof Error && error.name === 'AbortError' ? 'Request timed out. Try again when the service is available.' : 'Cannot reach the backend. Check that Django is running on port 8001.')
  } finally { clearTimeout(timeout) }
}
export function post<T>(path: string, data: unknown = {}): Promise<T> { return api<T>(path, { method: 'POST', body: JSON.stringify(data) }) }
export function errorMessage(error: unknown) { return error instanceof Error ? error.message : 'Something went wrong. Please try again.' }
