export default function DocumentList({ documents }) {
  if (!documents || documents.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-ink-200 p-5">
        <h2 className="font-semibold text-ink-900 mb-2">Your documents</h2>
        <p className="text-sm text-ink-400">
          No documents yet. Upload one to get started.
        </p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg border border-ink-200 p-5">
      <h2 className="font-semibold text-ink-900 mb-3">Your documents</h2>
      <ul className="space-y-2">
        {documents.map((doc) => (
          <li
            key={doc.id}
            className="flex items-center justify-between rounded-md px-3 py-2 hover:bg-ink-50"
          >
            <div className="min-w-0">
              <p className="text-sm font-medium text-ink-900 truncate">{doc.filename}</p>
              <p className="text-xs text-ink-400">
                {doc.char_count.toLocaleString('en-US')} chars
              </p>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
