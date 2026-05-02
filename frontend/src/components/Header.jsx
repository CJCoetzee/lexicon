export default function Header() {
  return (
    <header className="border-b border-ink-200 bg-white">
      <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-md bg-accent-600 text-white font-semibold flex items-center justify-center">
            L
          </div>
          <div>
            <h1 className="font-semibold text-ink-900">Lexicon</h1>
            <p className="text-xs text-ink-400 -mt-0.5">Chat with your documents</p>
          </div>
        </div>
        <a
          href="https://github.com"
          className="text-sm text-ink-700 hover:text-accent-600 transition-colors"
        >
          GitHub
        </a>
      </div>
    </header>
  )
}
