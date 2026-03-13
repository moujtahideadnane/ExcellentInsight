// REFACTOR: [global-error-boundary]
"use client"

import React, { Component, ReactNode } from 'react'
import { AlertOctagon, RefreshCw, ArrowLeft } from 'lucide-react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

/**
 * Global error boundary wrapping the entire application.
 * Catches unhandled exceptions at the top level and renders
 * a styled fallback using CSS variables from the Vercel Edge palette.
 */
export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('[GlobalErrorBoundary]', error, errorInfo)
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null })
  }

  handleReload = () => {
    if (typeof window !== 'undefined') {
      window.location.reload()
    }
  }

  handleGoHome = () => {
    if (typeof window !== 'undefined') {
      window.location.href = '/'
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            minHeight: '100vh',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '2rem',
            gap: '2rem',
            backgroundColor: 'var(--bg)',
            color: 'var(--text)',
            fontFamily: 'var(--font-sans)',
          }}
        >
          {/* Icon */}
          <div
            style={{
              height: 56,
              width: 56,
              borderRadius: 6,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: '#2A0808',
              border: '1px solid #5C1A1A',
            }}
          >
            <AlertOctagon style={{ height: 28, width: 28, color: '#FF4444' }} />
          </div>

          {/* Copy */}
          <div style={{ textAlign: 'center', maxWidth: 480 }}>
            <h1
              style={{
                fontSize: 20,
                fontWeight: 600,
                letterSpacing: '-0.02em',
                color: 'var(--text)',
                fontFamily: 'var(--font-mono)',
                marginBottom: 8,
              }}
            >
              ERR_UNHANDLED_EXCEPTION
            </h1>
            <p
              style={{
                fontSize: 13,
                color: 'var(--text-muted)',
                fontFamily: 'var(--font-mono)',
                lineHeight: 1.6,
              }}
            >
              {this.state.error?.message || 'Something went wrong. The application encountered an unexpected error.'}
            </p>

            {/* Stack trace in dev */}
            {process.env.NODE_ENV === 'development' && this.state.error?.stack && (
              <details
                style={{
                  marginTop: 16,
                  padding: 12,
                  backgroundColor: 'var(--bg-surface)',
                  border: '1px solid var(--border)',
                  borderRadius: 4,
                  textAlign: 'left',
                  fontSize: 10,
                  fontFamily: 'var(--font-mono)',
                  color: 'var(--text-muted)',
                  maxHeight: 200,
                  overflow: 'auto',
                }}
              >
                <summary style={{ cursor: 'pointer', marginBottom: 8, color: 'var(--text-muted)' }}>
                  Stack Trace
                </summary>
                <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                  {this.state.error.stack}
                </pre>
              </details>
            )}
          </div>

          {/* Actions */}
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', justifyContent: 'center' }}>
            <button
              onClick={this.handleRetry}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                height: 36,
                padding: '0 20px',
                borderRadius: 4,
                backgroundColor: 'var(--text)',
                color: 'var(--bg)',
                fontSize: 13,
                fontWeight: 500,
                border: 'none',
                cursor: 'pointer',
                fontFamily: 'var(--font-sans)',
              }}
            >
              <RefreshCw style={{ height: 14, width: 14 }} />
              Retry
            </button>
            <button
              onClick={this.handleGoHome}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                height: 36,
                padding: '0 20px',
                borderRadius: 4,
                backgroundColor: 'transparent',
                color: 'var(--text-muted)',
                fontSize: 13,
                fontWeight: 500,
                border: '1px solid var(--border)',
                cursor: 'pointer',
                fontFamily: 'var(--font-sans)',
              }}
            >
              <ArrowLeft style={{ height: 14, width: 14 }} />
              Go Home
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
