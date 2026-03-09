import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { createElement } from 'react'
import { ErrorDisplay } from '@/components/console/error-display'
import type { AgentError } from '@/lib/api/contracts/agent'

describe('ErrorDisplay (CONS-15)', () => {
  const mockError: AgentError = {
    message: 'Test error message',
    code: 'TEST_ERROR',
    details: { foo: 'bar' },
  }

  it('returns null when no error', () => {
    const { container } = render(createElement(ErrorDisplay, { error: null }))
    expect(container.firstChild).toBeNull()
  })

  it('renders error message when present', () => {
    render(createElement(ErrorDisplay, { error: mockError }))
    expect(screen.getByText('Test error message')).toBeInTheDocument()
  })

  it('shows alert icon', () => {
    const { container } = render(createElement(ErrorDisplay, { error: mockError }))
    const svgElement = container.querySelector('svg')
    expect(svgElement).toBeInTheDocument()
  })

  it('uses destructive styling', () => {
    const { container } = render(createElement(ErrorDisplay, { error: mockError }))
    const card = container.firstChild
    expect(card).toHaveClass('bg-destructive/10')
  })

  it('shows error code when present', () => {
    render(createElement(ErrorDisplay, { error: mockError }))
    expect(screen.getByText(/Code: TEST_ERROR/)).toBeInTheDocument()
  })

  it('shows error details when present', () => {
    render(createElement(ErrorDisplay, { error: mockError }))
    expect(screen.getByText(/"foo": "bar"/)).toBeInTheDocument()
  })

  it('hides error code section when not present', () => {
    const errorWithoutCode: AgentError = { message: 'No code error' }
    const { container } = render(createElement(ErrorDisplay, { error: errorWithoutCode }))
    expect(container.querySelector('.text-xs')).not.toBeInTheDocument()
  })

  it('applies custom className', () => {
    const { container } = render(
      createElement(ErrorDisplay, { error: mockError, className: 'custom-class' })
    )
    expect(container.firstChild).toHaveClass('custom-class')
  })
})
