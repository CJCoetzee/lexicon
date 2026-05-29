import { useState } from 'react'
import Header from './components/Header.jsx'
import UploadZone from './components/UploadZone.jsx'
import DocumentList from './components/DocumentList.jsx'
import ChatPanel from './components/ChatPanel.jsx'

export default function App() {
  const [documents, setDocuments] = useState([])
  const [suggestedQuestions, setSuggestedQuestions] = useState([])

  function handleUploaded(doc) {
    setDocuments((prev) => [doc, ...prev])
    if (Array.isArray(doc.suggested_questions) && doc.suggested_questions.length) {
      setSuggestedQuestions(doc.suggested_questions)
    }
  }

  function handleDelete(id) {
    setDocuments((prev) => prev.filter((d) => d.id !== id))
  }

  function handleClearAll() {
    setDocuments([])
    setSuggestedQuestions([])
  }

  return (
    <div className="min-h-full flex flex-col">
      <Header />

      <main className="flex-1 max-w-6xl w-full mx-auto px-6 py-10 grid grid-cols-1 lg:grid-cols-[360px_1fr] gap-8">
        <section className="space-y-6">
          <UploadZone onUploaded={handleUploaded} />
          <DocumentList
            documents={documents}
            onDelete={handleDelete}
            onClearAll={handleClearAll}
          />
        </section>

        <section>
          <ChatPanel
            hasDocuments={documents.length > 0}
            suggestedQuestions={suggestedQuestions}
          />
        </section>
      </main>

      <footer className="py-6 text-center text-sm text-ink-400 dark:text-ink-400">
        Lexicon — MSSE Capstone, 2026
      </footer>
    </div>
  )
}
