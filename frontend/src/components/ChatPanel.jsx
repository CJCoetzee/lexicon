import { useState, useRef, useEffect } from 'react'
import { api, ApiError } from '../api.js'
import CitationList from './CitationList.jsx'
import AnswerText from './AnswerText.jsx'

export default function ChatPanel({ hasDocuments, suggestedQuestions = [] }) {
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
    const userMsg = { id: `u-${Date.now()}`, role: 'user', text: question }
    const assistantId = `a-${Date.now()}`

    // Conversation history sent to the backend — exclude the just-added
    // user turn (it's the "current question") and any in-flight assistant.
    const history = messages.map((m) => ({ role: m.role, text: m.text }))

    setMessages((prev) => [
      ...prev,
      userMsg,
      {
        id: assistantId, role: 'assistant', text: '',
        citations: [], latencyMs: null, retrieved: null, streaming: true,
      },
    ])
    setIsAsking(true)

    try {
      for await (const event of api.askStream(question, 5, history)) {
        if (event.type === 'token') {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, text: m.text + event.text } : m,
            ),
          )
        } else if (event.type === 'done') {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    citations: event.citations || [],
                    latencyMs: event.latency_ms,
                    retrieved: event.retrieved,
                    streaming: false,
                  }
                : m,
            ),
          )
        } else if (event.type === 'error') {
          throw new Error(event.message || 'Stream error')
        }
      }
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : (err.message || 'Network error. Is the backend running?')
      setError(message)
      // Remove the empty in-flight assistant message on error.
      setMessages((prev) => prev.filter((m) => m.id !== assistantId || m.text))
    } finally {
      setIsAsking(false)
    }
  }

  if (!hasDocuments && messages.length === 0) {
    return (
      <div className="bg-white dark:bg-ink-900 rounded-lg border border-ink-200 dark:border-ink-700 p-6 transition-colors h-full min-h-[480px] flex flex-col items-center justify-center text-center">
        <div className="w-12 h-12 rounded-full bg-ink-100 dark:bg-ink-700 flex items-center justify-center mb-4">
          <span className="text-2xl">💬</span>
        </div>
        <h2 className="font-semibold text-ink-900 dark:text-ink-50">Upload a document to begin</h2>
        <p className="text-sm text-ink-400 mt-2 max-w-sm">
          Lexicon answers questions using only the documents you upload, and cites the
          passages it used.
        </p>
      </div>
    )
  }

  return (
    <div className="bg-white dark:bg-ink-900 rounded-lg border border-ink-200 dark:border-ink-700 h-full min-h-[480px] flex flex-col transition-colors">
      <div className="px-5 py-3 border-b border-ink-200 dark:border-ink-700 flex items-center justify-between">
        <h2 className="font-semibold text-ink-900 dark:text-ink-50">Ask your documents</h2>
        {messages.length > 0 && (
          <button
            type="button"
            onClick={() => setMessages([])}
            className="text-xs text-ink-400 hover:text-ink-700 dark:hover:text-ink-200"
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
        {isAsking && messages[messages.length - 1]?.role !== 'assistant' && <ThinkingIndicator />}
      </div>

      {suggestedQuestions.length > 0 && messages.length === 0 && (
        <div className="px-5 pb-2">
          <p className="text-xs text-ink-400 mb-2">Try asking:</p>
          <div className="flex flex-wrap gap-2">
            {suggestedQuestions.map((q) => (
              <button
                key={q}
                type="button"
                onClick={() => setInput(q)}
                className="text-xs px-3 py-1.5 rounded-full border border-ink-200 dark:border-ink-700 text-ink-700 dark:text-ink-200 hover:border-accent-500 hover:text-accent-600 dark:hover:text-accent-500 transition-colors"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      <form onSubmit={submit} className="border-t border-ink-200 dark:border-ink-700 p-3 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question…"
          disabled={isAsking}
          className="flex-1 px-3 py-2 rounded-md border border-ink-200 dark:border-ink-700 bg-white dark:bg-ink-900 text-ink-900 dark:text-ink-50 focus:outline-none focus:border-accent-500 disabled:bg-ink-50 dark:disabled:bg-ink-700"
        />
        <button
          type="submit"
          disabled={!input.trim() || isAsking}
          className="px-4 py-2 rounded-md bg-accent-600 text-white text-sm font-medium hover:bg-accent-700 disabled:bg-ink-200 dark:disabled:bg-ink-700"
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
  const detailsRef = useRef(null)
  const [highlightedN, setHighlightedN] = useState(null)

  function handleCitationClick(n) {
    // Force the source panel open. It's uncontrolled after this -- the
    // user closes it themselves via the summary toggle.
    if (detailsRef.current && !detailsRef.current.open) {
      detailsRef.current.open = true
    }
    setHighlightedN(n)
    // Scroll the cited entry into view on the next frame so the panel
    // has finished expanding before we measure.
    requestAnimationFrame(() => {
      const el = citationRefs.current[n]
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    })
    // Fade the highlight back after a beat. Panel stays open.
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
      <div className="max-w-[90%] bg-ink-50 dark:bg-ink-700/40 rounded-lg px-4 py-3 text-sm text-ink-900 dark:text-ink-50 leading-relaxed">
        {message.text ? (
          <AnswerText text={message.text} onCitationClick={handleCitationClick} />
        ) : (
          <span className="text-ink-400">…</span>
        )}
        {message.streaming && message.text && (
          <span className="inline-block w-1 h-4 ml-0.5 bg-accent-500 align-middle animate-pulse" />
        )}
      </div>
      {message.citations && message.citations.length > 0 && (
        <CitationList
          citations={message.citations}
          citationRefs={citationRefs}
          highlightedN={highlightedN}
          detailsRef={detailsRef}
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
