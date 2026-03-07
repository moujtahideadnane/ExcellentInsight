import { describe, it, expect, vi, beforeAll, afterAll } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ChartErrorBoundary } from '@/components/error-boundary/ChartErrorBoundary'

function ThrowError(): React.ReactNode {
  throw new Error('Test error')
}

describe('ChartErrorBoundary', () => {
  // Suppress console.error for this test
  const originalError = console.error
  beforeAll(() => {
    console.error = vi.fn()
  })
  afterAll(() => {
    console.error = originalError
  })

  it('should render children when there is no error', () => {
    render(
      <ChartErrorBoundary>
        <div>Chart content</div>
      </ChartErrorBoundary>
    )

    expect(screen.getByText('Chart content')).toBeTruthy()
  })

  it('should show error UI when child component throws', () => {
    render(
      <ChartErrorBoundary>
        <ThrowError />
      </ChartErrorBoundary>
    )

    expect(screen.getByText('Render Failed')).toBeTruthy()
    expect(screen.getByText(/Test error/)).toBeTruthy()
  })

  it('should show custom fallback when provided', () => {
    const fallback = <div>Custom error message</div>

    render(
      <ChartErrorBoundary fallback={fallback}>
        <ThrowError />
      </ChartErrorBoundary>
    )

    expect(screen.getByText('Custom error message')).toBeTruthy()
  })

  it('should call onError callback when error occurs', () => {
    const onError = vi.fn()

    render(
      <ChartErrorBoundary onError={onError}>
        <ThrowError />
      </ChartErrorBoundary>
    )

    expect(onError).toHaveBeenCalled()
  })
})
