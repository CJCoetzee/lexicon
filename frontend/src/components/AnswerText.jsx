// Renders an answer string and turns inline [n] citation markers into
// clickable superscripts. Clicking calls onCitationClick(n) so the
// parent can scroll/highlight the citation entry.
const CITATION_RE = /\[(\d+)\]/g

export default function AnswerText({ text, onCitationClick }) {
  if (!text) return null
  const parts = []
  let last = 0
  for (const match of text.matchAll(CITATION_RE)) {
    if (match.index > last) {
      parts.push(<span key={last}>{text.slice(last, match.index)}</span>)
    }
    const n = Number(match[1])
    parts.push(
      <button
        type="button"
        key={`c-${match.index}`}
        onClick={() => onCitationClick?.(n)}
        className="text-accent-600 font-medium text-xs align-super ml-0.5 hover:underline focus:outline-none focus:ring-2 focus:ring-accent-500/40 rounded"
        title={`Show citation ${n}`}
      >
        [{n}]
      </button>,
    )
    last = match.index + match[0].length
  }
  if (last < text.length) {
    parts.push(<span key={last}>{text.slice(last)}</span>)
  }
  return <>{parts}</>
}
