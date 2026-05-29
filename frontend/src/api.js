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

  deleteDocument(id) {
    return request(`/api/documents/${encodeURIComponent(id)}`, { method: 'DELETE' })
  },

  clearAllDocuments() {
    return request('/api/documents', { method: 'DELETE' })
  },

  ask(question, topK = 5, history = []) {
    return request('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, top_k: topK, history }),
    })
  },

  // Streaming variant. Returns an async generator that yields SSE events:
  //   {type: 'token',  text: '...'}
  //   {type: 'done',   citations: [...], latency_ms, retrieved}
  //   {type: 'error',  message}
  async *askStream(question, topK = 5, history = []) {
    const response = await fetch(`${BASE_URL}/api/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, top_k: topK, history }),
    })
    if (!response.ok) {
      const text = await response.text().catch(() => response.statusText)
      throw new ApiError(text || 'stream failed', response.status, null)
    }
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buf = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buf += decoder.decode(value, { stream: true })
      const chunks = buf.split('\n\n')
      buf = chunks.pop() // keep the trailing partial event
      for (const chunk of chunks) {
        for (const line of chunk.split('\n')) {
          if (!line.startsWith('data: ')) continue
          try {
            yield JSON.parse(line.slice(6))
          } catch {
            // ignore malformed lines
          }
        }
      }
    }
  },
}

export { ApiError }
