import { useState, useRef, useEffect } from 'react'
import { api, ApiError } from '../api.js'
import CitationList from './CitationList.jsx'
import AnswerText from './AnswerText.jsx'

export default function ChatPanel({ hasDocuments }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isAsking, setIsAsking] = useState(false)
  const [error, setError] = useState(null)
  const scrollRef = useRef(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, isAsking])

  async function submit(e) {
    e.preventDefault()
    const question = input.trim()
    if (!question || isAsking) return

    setError(null)
    setInput('')
    const userMsg = { role: 'user', text: question }
    setMessages((prev) => [...prev, userMsg])
    setIsAsking(true)

    try {
      const result = await api.ask(question)
      const assistantMsg = {
        id: Date.now(),
        role: 'assistant',
        text: result.answer,
        citations: result.citations || [],
        latencyMs: result.latency_ms,
        retrieved: result.retrieved,
      }
      setMessages((prev) => [...prev, assistantMsg])
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : 'Network error. Is the backend running?'
      setError(message)
    } finally {
      setIsAsking(false)
    }
  }

  if (!hasDocuments && messages.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-ink-200 p-6 h-full min-h-[480px] flex flex-col items-center justify-center text-center">
        <div className="w-12 h-12 rounded-full bg-ink-100 flex items-center justify-center mb-4">
          <span className="text-2xl">💬</span>
        </div>
        <h2 className="font-semibold text-ink-900">Upload a document to begin</h2>
        <p className="text-sm text-ink-400 mt-2 max-w-sm">
          Lexicon answers questions using only the documents you upload, and cites the
          passages it used.
        </p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg border border-ink-200 h-full min-h-[480px] flex flex-col">
      <div className="px-5 py-3 border-b border-ink-200 flex items-center justify-between">
        <h2 className="font-semibold text-ink-900">Ask your documents</h2>
        {messages.length > 0 && (
          <button
            type="button"
            onClick={() => setMessages([])}
            className="text-xs text-ink-400 hover:text-ink-700"
          >
            Clear
          </button>
        )}
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
        {messages.length === 0 && (
          <p className="text-sm text-ink-400 text-center mt-12">
            Ask a question about the {hasDocuments ? 'uploaded' : 'sample'} documents.
          </p>
        )}
        {messages.map((msg) => (
          <Message key={msg.id ?? msg.text} message={msg} />
        ))}
        {isAsking && <ThinkingIndicator />}
      </div>

      <form onSubmit={submit} className="border-t border-ink-200 p-3 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question…"
          disabled={isAsking}
          className="flex-1 px-3 py-2 rounded-md border border-ink-200 focus:outline-none focus:border-accent-500 disabled:bg-ink-50"
        />
        <button
          type="submit"
          disabled={!input.trim() || isAsking}
          className="px-4 py-2 rounded-md bg-accent-600 text-white text-sm font-medium hover:bg-accent-700 disabled:bg-ink-200"
        >
          Ask
        </button>
      </form>

      {error && (
        <p role="alert" className="px-5 pb-3 text-sm text-red-600">
          {error}
        </p>
      )}
    </div>
  )
}

function Message({ message }) {
  // Per-message refs so a citation click in this message highlights only
  // this message's citation list.
  const citationRefs = useRef({})
  const [highlightedN, setHighlightedN] = useState(null)

  function handleCitationClick(n) {
    setHighlightedN(n)
    const el = citationRefs.current[n]
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
    // Clear highlight after a beat so it fades back.
    setTimeout(() => setHighlightedN(null), 1500)
  }

  if (message.role === 'user') {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%] bg-accent-600 text-white rounded-lg px-3 py-2 text-sm">
          {message.text}
        </div>
      </div>
    )
  }
  return (
    <div className="flex flex-col gap-2">
      <div className="max-w-[90%] bg-ink-50 rounded-lg px-4 py-3 text-sm text-ink-900 leading-relaxed">
        <AnswerText text={message.text} onCitationClick={handleCitationClick} />
      </div>
      {message.citations && message.citations.length > 0 && (
        <CitationList
          citations={message.citations}
          citationRefs={citationRefs}
          highlightedN={highlightedN}
        />
      )}
      {message.latencyMs != null && (
        <p className="text-xs text-ink-400">
          {message.retrieved} chunk{message.retrieved === 1 ? '' : 's'} retrieved · {message.latencyMs} ms
        </p>
      )}
    </div>
  )
}

function ThinkingIndicator() {
  return (
    <div className="flex items-center gap-2 text-sm text-ink-400">
      <span className="inline-flex gap-1">
        <span className="w-1.5 h-1.5 rounded-full bg-ink-400 animate-bounce" />
        <span className="w-1.5 h-1.5 rounded-full bg-ink-400 animate-bounce [animation-delay:120ms]" />
        <span className="w-1.5 h-1.5 rounded-full bg-ink-400 animate-bounce [animation-delay:240ms]" />
      </span>
      Thinking…
    </div>
  )
}

// useRef imported at top via the React import.
