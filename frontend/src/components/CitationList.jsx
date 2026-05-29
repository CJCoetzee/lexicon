import { forwardRef } from 'react'

// A single citation. We forward refs through so parents can scroll a
// specific one into view in response to a click in the answer text.
const CitationItem = forwardRef(function CitationItem({ citation, highlighted }, ref) {
  return (
    <li
      ref={ref}
      className={`border-l-2 pl-3 py-1 transition-colors duration-500 ${
        highlighted
          ? 'border-accent-600 bg-accent-500/10'
          : 'border-accent-500'
      }`}
    >
      <p className="text-ink-700 dark:text-ink-200 font-medium text-xs">
        [{citation.n}] {citation.document_name}{' '}
        <span className="text-ink-400 font-normal">
          · chunk {citation.chunk_index} · {(citation.score * 100).toFixed(0)}%
        </span>
      </p>
      <p className="text-ink-700 dark:text-ink-200 mt-1 line-clamp-3 text-xs">{citation.text}</p>
    </li>
  )
})

export default function CitationList({ citations, citationRefs, highlightedN }) {
  return (
    <details className="text-xs" open={highlightedN != null}>
      <summary className="cursor-pointer text-ink-400 hover:text-ink-700 dark:hover:text-ink-200">
        {citations.length} source{citations.length === 1 ? '' : 's'}
      </summary>
      <ul className="mt-2 space-y-2 pl-4">
        {citations.map((c) => (
          <CitationItem
            key={`${c.document_id}-${c.chunk_index}`}
            citation={c}
            ref={(el) => {
              if (citationRefs) citationRefs.current[c.n] = el
            }}
            highlighted={highlightedN === c.n}
          />
        ))}
      </ul>
    </details>
  )
}
