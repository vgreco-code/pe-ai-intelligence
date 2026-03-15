import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { TierBadge } from '../../components/TierBadge'

describe('TierBadge', () => {
  it('renders the tier label', () => {
    render(<TierBadge tier="AI-Ready" />)
    expect(screen.getByText('AI-Ready')).toBeInTheDocument()
  })

  it('applies ready class for AI-Ready', () => {
    const { container } = render(<TierBadge tier="AI-Ready" />)
    expect(container.firstChild).toHaveClass('tier-badge-ready')
  })

  it('applies buildable class for AI-Buildable', () => {
    const { container } = render(<TierBadge tier="AI-Buildable" />)
    expect(container.firstChild).toHaveClass('tier-badge-buildable')
  })

  it('applies emerging class for AI-Emerging', () => {
    const { container } = render(<TierBadge tier="AI-Emerging" />)
    expect(container.firstChild).toHaveClass('tier-badge-emerging')
  })

  it('applies limited class for AI-Limited', () => {
    const { container } = render(<TierBadge tier="AI-Limited" />)
    expect(container.firstChild).toHaveClass('tier-badge-limited')
  })

  it('applies fallback class for unknown tier', () => {
    const { container } = render(<TierBadge tier="Unknown" />)
    expect(container.firstChild).toHaveClass('bg-gray-100')
  })

  it('always has the base tier-badge class', () => {
    const { container } = render(<TierBadge tier="AI-Ready" />)
    expect(container.firstChild).toHaveClass('tier-badge')
  })

  it('forwards extra className prop', () => {
    const { container } = render(<TierBadge tier="AI-Ready" className="extra-class" />)
    expect(container.firstChild).toHaveClass('extra-class')
  })

  it('renders as a span element', () => {
    render(<TierBadge tier="AI-Ready" />)
    expect(screen.getByText('AI-Ready').tagName).toBe('SPAN')
  })
})
