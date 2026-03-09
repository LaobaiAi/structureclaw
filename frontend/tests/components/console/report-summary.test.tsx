import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ReportSummary } from '@/components/console/report-summary'

describe('ReportSummary (CONS-17)', () => {
  it('returns null when no report', () => {
    const { container } = render(<ReportSummary report={undefined} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders summary markdown when present', () => {
    const report = { summary: '# Test Report\n\nThis is a **test**.' }
    render(<ReportSummary report={report} />)

    // ReactMarkdown renders markdown headers as h1 elements
    expect(screen.getByRole('heading', { name: /test report/i })).toBeInTheDocument()
  })

  it('renders markdown content when present', () => {
    const report = { markdown: '## Analysis Results\n\n- Item 1\n- Item 2' }
    render(<ReportSummary report={report} />)

    expect(screen.getByRole('heading', { name: /analysis results/i })).toBeInTheDocument()
  })

  it('prefers summary over markdown', () => {
    const report = {
      summary: '# Summary Content',
      markdown: '# Markdown Content',
    }
    render(<ReportSummary report={report} />)

    expect(screen.getByRole('heading', { name: /summary content/i })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: /markdown content/i })).not.toBeInTheDocument()
  })
})
