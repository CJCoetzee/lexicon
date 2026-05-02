import { useState, useRef } from 'react'
import { api, ApiError } from '../api.js'

export default function UploadZone({ onUploaded }) {
  const inputRef = useRef(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState(null)

  async function handleFile(file) {
    if (!file) return
    setError(null)
    setIsUploading(true)
    try {
      const doc = await api.uploadDocument(file)
      onUploaded?.(doc)
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message || 'Upload failed.')
      } else {
        setError('Network error. Is the backend running?')
      }
    } finally {
      setIsUploading(false)
    }
  }

  function onDrop(e) {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files?.[0]
    handleFile(file)
  }

  return (
    <div className="bg-white rounded-lg border border-ink-200 p-5">
      <h2 className="font-semibold text-ink-900 mb-3">Upload a document</h2>

      <label
        onDragOver={(e) => {
          e.preventDefault()
          setIsDragging(true)
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={onDrop}
        className={`block border-2 border-dashed rounded-md p-6 text-center cursor-pointer transition-colors ${
          isDragging
            ? 'border-accent-500 bg-accent-500/5'
            : 'border-ink-200 hover:border-accent-500'
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.txt,.md"
          className="hidden"
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
        {isUploading ? (
          <p className="text-sm text-ink-700">Uploading…</p>
        ) : (
          <>
            <p className="text-sm text-ink-700">
              Drop a file here, or <span className="text-accent-600 underline">browse</span>
            </p>
            <p className="text-xs text-ink-400 mt-1">PDF, TXT, or Markdown</p>
          </>
        )}
      </label>

      {error && (
        <p role="alert" className="mt-3 text-sm text-red-600">
          {error}
        </p>
      )}
    </div>
  )
}
