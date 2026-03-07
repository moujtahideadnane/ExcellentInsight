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
        <div className="min-h-[400px] flex flex-col items-center justify-center gap-6 p-12 bg-[#000000] border border-[#333333] rounded-[6px]">
          <div className="h-12 w-12 rounded-[4px] flex items-center justify-center bg-[#2A0808] border border-[#5C1A1A]">
            <AlertTriangle className="h-6 w-6 text-[#FF4444]" />
          </div>

          <div className="text-center max-w-md">
            <h2 className="text-[16px] font-semibold tracking-tight text-[#EDEDED] mb-2 font-mono">
              {this.props.section ? `${this.props.section} Error` : 'Component Error'}
            </h2>
            <p className="text-[12px] font-mono text-[#888888] mb-4">
              {this.state.error?.message || 'An unexpected error occurred in this section.'}
            </p>

            {process.env.NODE_ENV === 'development' && this.state.errorInfo && (
              <details className="text-left mt-4 p-3 bg-[#111111] rounded-[4px] border border-[#333333] text-[10px] font-mono text-[#666666] overflow-auto max-h-[200px]">
                <summary className="cursor-pointer text-[#888888] hover:text-[#EDEDED] mb-2">
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
            className="flex items-center gap-2 px-4 py-2 bg-[#EDEDED] text-[#000000] text-[12px] font-medium rounded-[4px] hover:bg-[#CCCCCC] transition-colors"
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
