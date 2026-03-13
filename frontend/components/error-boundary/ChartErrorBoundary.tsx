"use client"

import React, { Component, ReactNode } from 'react'
import { AlertTriangle } from 'lucide-react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void
}

interface State {
  hasError: boolean
  error: Error | null
}

/**
 * Error boundary specifically for chart components.
 * Prevents a single broken chart from crashing the entire dashboard.
 */
export class ChartErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Log to your error reporting service
    console.error('Chart Error:', error, errorInfo)

    if (this.props.onError) {
      this.props.onError(error, errorInfo)
    }
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="h-full flex flex-col items-center justify-center gap-3 bg-ve-surface rounded-[4px] border border-dashed border-ve-border p-8">
          <AlertTriangle className="h-6 w-6 text-ve-warning" />
          <div className="text-center">
            <h3 className="text-[11px] font-mono text-ve-muted uppercase tracking-widest mb-1">
              Render Failed
            </h3>
            <p className="text-[12px] font-mono text-ve-dimmed">
              {this.state.error?.message || 'Unable to display chart'}
            </p>
          </div>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="text-[10px] font-mono text-ve-blue hover:text-ve-text transition-colors uppercase tracking-wider"
          >
            Retry
          </button>
        </div>
      )
    }

    return this.props.children
  }
}

/**
 * Higher-order component to wrap charts with error boundary
 */
export function withChartErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  displayName?: string
) {
  const WrappedComponent = (props: P) => (
    <ChartErrorBoundary>
      <Component {...props} />
    </ChartErrorBoundary>
  )

  WrappedComponent.displayName = displayName || `withChartErrorBoundary(${Component.displayName || Component.name})`

  return WrappedComponent
}
