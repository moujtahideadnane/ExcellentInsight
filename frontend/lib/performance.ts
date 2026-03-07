/**
 * Performance monitoring utilities for tracking Web Vitals and custom metrics.
 * Integrates with Next.js and provides hooks for real-time performance tracking.
 */

export interface PerformanceMetric {
  name: string
  value: number
  rating: 'good' | 'needs-improvement' | 'poor'
  id: string
  navigationType?: string
}

/**
 * Web Vitals thresholds (Core Web Vitals)
 * Source: https://web.dev/vitals/
 */
const THRESHOLDS = {
  // Largest Contentful Paint (LCP) - measures loading performance
  LCP: { good: 2500, poor: 4000 },
  // First Input Delay (FID) - measures interactivity
  FID: { good: 100, poor: 300 },
  // Cumulative Layout Shift (CLS) - measures visual stability
  CLS: { good: 0.1, poor: 0.25 },
  // First Contentful Paint (FCP)
  FCP: { good: 1800, poor: 3000 },
  // Time to First Byte (TTFB)
  TTFB: { good: 800, poor: 1800 },
  // Interaction to Next Paint (INP)
  INP: { good: 200, poor: 500 },
}

/**
 * Get rating for a metric based on thresholds
 */
export function getRating(
  name: keyof typeof THRESHOLDS,
  value: number
): 'good' | 'needs-improvement' | 'poor' {
  const threshold = THRESHOLDS[name]
  if (!threshold) return 'good'

  if (value <= threshold.good) return 'good'
  if (value <= threshold.poor) return 'needs-improvement'
  return 'poor'
}

/**
 * Send metric to analytics service
 * Customize this based on your analytics provider (Google Analytics, Vercel, etc.)
 */
export function sendToAnalytics(metric: PerformanceMetric) {
  // Development logging
  if (process.env.NODE_ENV === 'development') {
    console.log('📊 Performance Metric:', {
      name: metric.name,
      value: Math.round(metric.value),
      rating: metric.rating,
      id: metric.id,
    })
  }

  // Send to your analytics service here
  // Example with Google Analytics:
  // if (window.gtag) {
  //   window.gtag('event', metric.name, {
  //     value: Math.round(metric.value),
  //     metric_id: metric.id,
  //     metric_rating: metric.rating,
  //   })
  // }

  // Example with Vercel Analytics:
  // if (window.va) {
  //   window.va('event', 'Web Vitals', {
  //     name: metric.name,
  //     value: metric.value,
  //     rating: metric.rating,
  //   })
  // }
}

/**
 * Track custom performance marks
 * Useful for measuring specific operations (API calls, renders, etc.)
 */
export class PerformanceTracker {
  private marks: Map<string, number> = new Map()

  /**
   * Start tracking an operation
   */
  start(label: string) {
    if (typeof performance === 'undefined') return

    const markName = `${label}-start`
    performance.mark(markName)
    this.marks.set(label, performance.now())
  }

  /**
   * End tracking and measure duration
   */
  end(label: string): number | null {
    if (typeof performance === 'undefined') return null

    const startTime = this.marks.get(label)
    if (!startTime) {
      console.warn(`No start mark found for "${label}"`)
      return null
    }

    const endTime = performance.now()
    const duration = endTime - startTime

    // Create performance measure
    const startMarkName = `${label}-start`
    const endMarkName = `${label}-end`
    const measureName = label

    try {
      performance.mark(endMarkName)
      performance.measure(measureName, startMarkName, endMarkName)

      // Log in development
      if (process.env.NODE_ENV === 'development') {
        console.log(`⏱️ ${label}: ${duration.toFixed(2)}ms`)
      }

      // Clean up
      this.marks.delete(label)
      performance.clearMarks(startMarkName)
      performance.clearMarks(endMarkName)
      performance.clearMeasures(measureName)

      return duration
    } catch (error) {
      console.error('Error measuring performance:', error)
      return duration
    }
  }

  /**
   * Measure an async operation
   */
  async measure<T>(label: string, fn: () => Promise<T>): Promise<T> {
    this.start(label)
    try {
      const result = await fn()
      this.end(label)
      return result
    } catch (error) {
      this.end(label)
      throw error
    }
  }
}

// Global singleton instance
export const perf = new PerformanceTracker()

/**
 * React hook for measuring component render time
 * Usage:
 * ```tsx
 * function MyComponent() {
 *   useRenderTime('MyComponent')
 *   return <div>...</div>
 * }
 * ```
 */
export function useRenderTime(componentName: string) {
  const isBrowser = typeof window !== 'undefined'
  const renderStart = isBrowser ? performance.now() : 0

  // Use effect to measure after render
  React.useEffect(() => {
    if (!isBrowser) return
    const renderEnd = performance.now()
    const duration = renderEnd - renderStart

    if (process.env.NODE_ENV === 'development' && duration > 16) {
      // Warn if render takes longer than 1 frame (16ms at 60fps)
      console.warn(
        `⚠️ Slow render: ${componentName} took ${duration.toFixed(2)}ms`
      )
    }
  })
}

/**
 * Detect slow network conditions
 */
export function getNetworkType(): string {
  if (typeof navigator === 'undefined') return 'unknown'

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const nav = navigator as any
  const connection = nav.connection || nav.mozConnection || nav.webkitConnection

  if (!connection) return 'unknown'

  return connection.effectiveType || 'unknown'
}

/**
 * Check if user has data saver enabled
 */
export function isDataSaverEnabled(): boolean {
  if (typeof navigator === 'undefined') return false

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const nav = navigator as any
  const connection = nav.connection || nav.mozConnection || nav.webkitConnection

  return connection?.saveData === true
}

/**
 * Monitor long tasks (> 50ms) that block main thread
 */
export function observeLongTasks(
  callback: (duration: number) => void
): () => void {
  if (typeof window === 'undefined' || !('PerformanceObserver' in window)) {
    return () => {}
  }

  try {
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        // Long task is > 50ms
        if (entry.duration > 50) {
          callback(entry.duration)

          if (process.env.NODE_ENV === 'development') {
            console.warn(
              `🐌 Long task detected: ${entry.duration.toFixed(2)}ms`
            )
          }
        }
      }
    })

    observer.observe({ entryTypes: ['longtask'] })

    return () => observer.disconnect()
  } catch (error) {
    console.error('Error observing long tasks:', error)
    return () => {}
  }
}

// Import React for useRenderTime hook
import React from 'react'
