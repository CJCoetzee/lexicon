// Sprint 1: placeholder. Sprint 2 will wire this up to a real chat API.
export default function ChatPanel({ hasDocuments }) {
  return (
    <div className="bg-white rounded-lg border border-ink-200 p-6 h-full min-h-[480px] flex flex-col items-center justify-center text-center">
      <div className="w-12 h-12 rounded-full bg-ink-100 flex items-center justify-center mb-4">
        <span className="text-2xl">💬</span>
      </div>
      <h2 className="font-semibold text-ink-900">
        {hasDocuments ? 'Chat coming in Sprint 2' : 'Upload a document to begin'}
      </h2>
      <p className="text-sm text-ink-400 mt-2 max-w-sm">
        Once retrieval and generation are wired up, this panel will let you ask
        questions about your uploaded documents and see cited answers.
      </p>
    </div>
  )
}
