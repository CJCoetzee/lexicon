import { useState } from 'react'
import { api, ApiError } from '../api.js'

export default function DocumentList({ documents, onDelete, onClearAll }) {
  const [busyId, setBusyId] = useState(null)
  const [error, setError] = useState(null)

  async function handleDelete(id) {
    setError(null)
    setBusyId(id)
    try {
      await api.deleteDocument(id)
      onDelete?.(id)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Delete failed.')
    } finally {
      setBusyId(null)
    }
  }

  async function handleClearAll() {
    setError(null)
    setBusyId('__all__')
    try {
      await api.clearAllDocuments()
      onClearAll?.()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Clear failed.')
    } finally {
      setBusyId(null)
    }
  }

  if (!documents || documents.length === 0) {
    return (
      <div className="bg-white dark:bg-ink-900 rounded-lg border border-ink-200 dark:border-ink-700 p-5 transition-colors">
        <h2 className="font-semibold text-ink-900 dark:text-ink-50 mb-2">Your documents</h2>
        <p className="text-sm text-ink-400">
          No documents yet. Upload one to get started.
        </p>
      </div>
    )
  }

  return (
    <div className="bg-white dark:bg-ink-900 rounded-lg border border-ink-200 dark:border-ink-700 p-5 transition-colors">
      <div className="flex items-center justify-between mb-3">
        <h2 className="font-semibold text-ink-900 dark:text-ink-50">Your documents</h2>
        <button
          type="button"
          onClick={handleClearAll}
          disabled={busyId !== null}
          className="text-xs text-ink-400 hover:text-red-600 disabled:opacity-40"
        >
          {busyId === '__all__' ? 'Clearing…' : 'Clear all'}
        </button>
      </div>
      <ul className="space-y-2">
        {documents.map((doc) => (
          <li
            key={doc.id}
            className="flex items-center justify-between rounded-md px-3 py-2 hover:bg-ink-50 dark:hover:bg-ink-700/40 group"
          >
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-ink-900 dark:text-ink-50 truncate">{doc.filename}</p>
              <p className="text-xs text-ink-400">
                {doc.char_count != null && `${doc.char_count.toLocaleString('en-US')} chars`}
                {doc.char_count != null && doc.chunks_indexed != null && ' · '}
                {doc.chunks_indexed != null && `${doc.chunks_indexed} chunks`}
              </p>
            </div>
            <button
              type="button"
              onClick={() => handleDelete(doc.id)}
              disabled={busyId !== null}
              aria-label={`Delete ${doc.filename}`}
              className="ml-2 p-1 rounded text-ink-400 opacity-0 group-hover:opacity-100 hover:text-red-600 focus:opacity-100 disabled:opacity-40 transition-opacity"
            >
              {busyId === doc.id ? '…' : '×'}
            </button>
          </li>
        ))}
      </ul>
      {error && (
        <p role="alert" className="mt-3 text-sm text-red-600">
          {error}
        </p>
      )}
    </div>
  )
}
