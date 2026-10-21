const BASE_URL = (import.meta.env.VITE_API_URL || '/api').replace(/\/$/, '')

export function getApiBaseUrl() {
  return BASE_URL
}

export async function api(path, options = {}) {
  const headers = new Headers(options.headers || {})
  let body = options.body

  if (body !== undefined && body !== null && !(body instanceof FormData) && typeof body !== 'string') {
    headers.set('Content-Type', 'application/json')
    body = JSON.stringify(body)
  }

  let response
  try {
    response = await fetch(`${BASE_URL}${path}`, { ...options, headers, body })
  } catch {
    throw new Error(`Не удалось подключиться к API ${BASE_URL}. Проверь, запущен ли Flask и доступен ли адрес.`)
  }

  const raw = await response.text()
  let data = null
  if (raw) {
    try { data = JSON.parse(raw) } catch { data = raw }
  }

  if (!response.ok) {
    let detail = ''
    if (typeof data === 'string') detail = data.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 180)
    else detail = data?.error || data?.message || data?.description || ''
    throw new Error(`Ошибка API ${response.status}${detail ? `: ${detail}` : ''}`)
  }
  return data
}

export const get = (path) => api(path)
export const post = (path, data = {}) => api(path, { method: 'POST', body: data })
export const put = (path, data = {}) => api(path, { method: 'PUT', body: data })
export const del = (path) => api(path, { method: 'DELETE' })

export function asArray(value, candidateKeys = []) {
  if (Array.isArray(value)) return value
  if (value && typeof value === 'object') {
    for (const key of candidateKeys) if (Array.isArray(value[key])) return value[key]
  }
  return []
}
