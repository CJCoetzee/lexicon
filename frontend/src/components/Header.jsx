import { useEffect, useState } from 'react'

function readInitialTheme() {
  if (typeof document === 'undefined') return 'light'
  return document.documentElement.classList.contains('dark') ? 'dark' : 'light'
}

export default function Header() {
  const [theme, setTheme] = useState(readInitialTheme)

  useEffect(() => {
    const root = document.documentElement
    if (theme === 'dark') root.classList.add('dark')
    else root.classList.remove('dark')
    try {
      localStorage.setItem('lexicon-theme', theme)
    } catch {
      /* ignore */
    }
  }, [theme])

  return (
    <header className="border-b border-ink-200 dark:border-ink-700 bg-white dark:bg-ink-900 transition-colors">
      <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-md bg-accent-600 text-white font-semibold flex items-center justify-center">
            L
          </div>
          <div>
            <h1 className="font-semibold text-ink-900 dark:text-ink-50">Lexicon</h1>
            <p className="text-xs text-ink-400 -mt-0.5">Chat with your documents</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <button
            type="button"
            onClick={() => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))}
            aria-label="Toggle dark mode"
            className="p-1.5 rounded-md text-ink-700 dark:text-ink-50 hover:bg-ink-100 dark:hover:bg-ink-700 transition-colors"
            title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {theme === 'dark' ? <SunIcon /> : <MoonIcon />}
          </button>
          <a
            href="https://github.com/CJCoetzee/lexicon"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-ink-700 dark:text-ink-50 hover:text-accent-600 transition-colors"
          >
            GitHub
          </a>
        </div>
      </div>
    </header>
  )
}

function SunIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
    </svg>
  )
}

function MoonIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
    </svg>
  )
}
