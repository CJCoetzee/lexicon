// Tiny API client. Centralises base URL + error handling so components stay
// focused on UI. In dev, Vite proxies /api -> http://localhost:5000.
// In production, set VITE_API_BASE_URL to the deployed backend URL.

const BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

class ApiError extends Error {
  constructor(message, status, body) {
    super(message)
    this.status = status
    this.body = body
  }
}

async function request(path, options = {}) {
  const response = await fetch(`${BASE_URL}${path}`, options)
  const contentType = response.headers.get('content-type') || ''
  const body = contentType.includes('application/json')
    ? await response.json()
    : await response.text()

  if (!response.ok) {
    const message = (body && body.message) || response.statusText
    throw new ApiError(message, response.status, body)
  }
  return body
}

export const api = {
  health() {
    return request('/healthz')
  },

  uploadDocument(file) {
    const form = new FormData()
    form.append('file', file)
    return request('/api/documents', {
      method: 'POST',
      body: form,
    })
  },

  supportedTypes() {
    return request('/api/documents/supported-types')
  },

  ask(question, topK = 5) {
    return request('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, top_k: topK }),
    })
  },
}

export { ApiError }
