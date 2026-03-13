"use client"

import React, { Component, ReactNode } from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'

interface Props {
  children: ReactNode
  section?: string
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: React.ErrorInfo | null
}

/**
 * Error boundary for entire dashboard sections.
 * Provides detailed error info and recovery options.
 */
export class DashboardErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null, errorInfo: null }
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error(`Dashboard Section Error (${this.props.section || 'Unknown'}):`, error, errorInfo)

    this.setState({
      error,
      errorInfo
    })

    // Send to error tracking service (Sentry, LogRocket, etc.)
    if (typeof window !== 'undefined') {
      const w = window as unknown as { reportError?: (e: Error) => void }
      if (w.reportError) {
        w.reportError(error)
      }
    }
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null })
    // Force reload if needed
    if (typeof window !== 'undefined') {
      window.location.reload()
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-[400px] flex flex-col items-center justify-center gap-6 p-12 bg-ve-bg border border-ve-border rounded-[6px]">
          <div className="h-12 w-12 rounded-[4px] flex items-center justify-center bg-ve-error-bg border border-ve-error-border">
            <AlertTriangle className="h-6 w-6 text-ve-error" />
          </div>

          <div className="text-center max-w-md">
            <h2 className="text-[16px] font-semibold tracking-tight text-ve-text mb-2 font-mono">
              {this.props.section ? `${this.props.section} Error` : 'Component Error'}
            </h2>
            <p className="text-[12px] font-mono text-ve-muted mb-4">
              {this.state.error?.message || 'An unexpected error occurred in this section.'}
            </p>

            {process.env.NODE_ENV === 'development' && this.state.errorInfo && (
              <details className="text-left mt-4 p-3 bg-ve-surface rounded-[4px] border border-ve-border text-[10px] font-mono text-ve-dimmed overflow-auto max-h-[200px]">
                <summary className="cursor-pointer text-ve-muted hover:text-ve-text mb-2">
                  Stack Trace
                </summary>
                <pre className="whitespace-pre-wrap">
                  {this.state.errorInfo.componentStack}
                </pre>
              </details>
            )}
          </div>

          <button
            onClick={this.handleReset}
            className="flex items-center gap-2 px-4 py-2 bg-ve-btn-primary text-ve-btn-text text-[12px] font-medium rounded-[4px] hover:bg-ve-btn-hover transition-colors"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Reload Section
          </button>
        </div>
      )
    }

    return this.props.children
  }
}
