import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import DocumentList from '../DocumentList.jsx'

describe('DocumentList', () => {
  it('shows empty state when no documents', () => {
    render(<DocumentList documents={[]} />)
    expect(screen.getByText(/no documents yet/i)).toBeInTheDocument()
  })

  it('renders document filenames', () => {
    const docs = [
      { id: '1', filename: 'paper.pdf', char_count: 1234 },
      { id: '2', filename: 'notes.md', char_count: 567 },
    ]
    render(<DocumentList documents={docs} />)
    expect(screen.getByText('paper.pdf')).toBeInTheDocument()
    expect(screen.getByText('notes.md')).toBeInTheDocument()
  })

  it('formats character counts with commas', () => {
    const docs = [{ id: '1', filename: 'big.txt', char_count: 1234567 }]
    render(<DocumentList documents={docs} />)
    expect(screen.getByText('1,234,567 chars')).toBeInTheDocument()
  })
})
