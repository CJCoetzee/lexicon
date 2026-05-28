import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import AnswerText from '../AnswerText.jsx'

describe('AnswerText', () => {
  it('renders plain text unchanged', () => {
    render(<AnswerText text="Hello world." />)
    expect(screen.getByText('Hello world.')).toBeInTheDocument()
  })

  it('extracts inline citation markers as clickable buttons', () => {
    render(<AnswerText text="The capital is Paris [1] and Berlin [2]." />)
    expect(screen.getByRole('button', { name: /Show citation 1/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Show citation 2/i })).toBeInTheDocument()
  })

  it('handles multiple citations on one claim', () => {
    render(<AnswerText text="Both sources agree [1][2]." />)
    expect(screen.getByRole('button', { name: /Show citation 1/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Show citation 2/i })).toBeInTheDocument()
  })

  it('calls onCitationClick with the citation number when clicked', () => {
    const onClick = vi.fn()
    render(<AnswerText text="See [3] for details." onCitationClick={onClick} />)
    fireEvent.click(screen.getByRole('button', { name: /Show citation 3/i }))
    expect(onClick).toHaveBeenCalledWith(3)
  })

  it('renders nothing when text is empty', () => {
    const { container } = render(<AnswerText text="" />)
    expect(container.firstChild).toBeNull()
  })
})
