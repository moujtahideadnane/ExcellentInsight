"use client"

import { useState, useEffect, useRef } from 'react'
import { useAuthStore } from '@/stores/auth-store'
import { EventSourcePolyfill } from 'event-source-polyfill'
import api from '@/lib/api'

export interface ProgressUpdate {
  id: string
  status: string
  progress: number
  message?: string
  telemetry?: Array<{
    step: string
    duration: number
    timestamp: string
  }>
}

interface UseJobProgressOptions {
  jobId: string | null
  onProgress?: (progress: ProgressUpdate) => void
  onError?: (error: Error) => void
  onReconnect?: (attempt: number) => void
  maxRetries?: number
  retryDelay?: number
  autoReconnect?: boolean
}

interface UseJobProgressReturn {
  data: ProgressUpdate | null
  isLoading: boolean
  isComplete: boolean
  error: Error | null
  reconnect: () => void
  close: () => void
}

/**
 * Hook to track job progress via Server-Sent Events (SSE).
 * Accepts either a jobId string or a full UseJobProgressOptions object.
 */
export function useJobProgress(options: UseJobProgressOptions | string): UseJobProgressReturn {
  // Support both string (jobId) and options object for backward compatibility
  const opts: UseJobProgressOptions = typeof options === 'string' 
    ? { jobId: options }
    : options || { jobId: null }

  const { jobId, onProgress, onError, onReconnect, maxRetries = 5, retryDelay = 1000, autoReconnect = true } = opts

  const [data, setData] = useState<ProgressUpdate | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const [isComplete, setIsComplete] = useState(false)
  const retryRef = useRef(0)
  const sourceRef = useRef<InstanceType<typeof EventSourcePolyfill> | null>(null)

  async function parseJwtPayload(token: string | null) {
    if (!token) return null
    try {
      const parts = token.split('.')
      if (parts.length < 2 || !parts[1]) return null
      const payload = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')))
      return payload
    } catch {
      return null
    }
  }

  async function ensureValidAccessToken(): Promise<string | null> {
    const access = useAuthStore.getState().accessToken
    const refresh = useAuthStore.getState().refreshToken
    const payload = await parseJwtPayload(access)
    const now = Math.floor(Date.now() / 1000)
    // If token is missing or will expire within 30s, try refresh
    if (!access || (payload && payload.exp && payload.exp - now < 30)) {
      if (!refresh) {
        // nothing we can do
        return access
      }
      try {
        const resp = await api.post('/auth/refresh', { refresh_token: refresh })
        const { access_token, refresh_token, user } = resp.data
        useAuthStore.getState().setAuth(user, access_token, refresh_token)
        return access_token
      } catch {
        // Refresh failed — logout to force re-auth
        useAuthStore.getState().logout()
        return null
      }
    }
    return access
  }

  const connect = async () => {
    if (!jobId) {
      setIsLoading(false)
      return
    }

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

    // Ensure we have a valid token (refresh proactively if needed)
    const token = await ensureValidAccessToken()

    // Build URL; prefer header auth but keep query token fallback if header not available
    const url = `${apiUrl}/jobs/${jobId}/progress${token ? '' : `?token=${useAuthStore.getState().accessToken || ''}`}`

    // Close any existing source before creating a new one
    if (sourceRef.current) {
      try { sourceRef.current.close() } catch { /* ignore */ }
    }

    const sourceOptions: { headers?: { Authorization: string } } = {}
    if (token) {
      sourceOptions.headers = { Authorization: `Bearer ${token}` }
    }

    const source = new EventSourcePolyfill(url, sourceOptions)
    sourceRef.current = source

    source.onmessage = (event: MessageEvent) => {
      try {
        const progressData: ProgressUpdate = JSON.parse(event.data)
        setData(progressData)
        setIsLoading(false)
        
        if (onProgress) {
          onProgress(progressData)
        }

        // Handle terminal states and warnings
        if (progressData.status === 'done' || progressData.status === 'failed' || progressData.status === 'cancelled') {
          setIsComplete(true)
          close()
        } else if (progressData.status === 'warning') {
          // Connection warning but job still processing - don't close connection
          console.warn('SSE Warning:', progressData.message)
        }
      } catch (parseErr) {
        console.error('Error parsing progress data:', parseErr)
        if (onError) {
          onError(parseErr instanceof Error ? parseErr : new Error(String(parseErr)))
        }
      }
    }

    source.onerror = (evt: Event & { message?: string }) => {
      console.error('SSE connection error', evt)
      if (onError) {
        try { onError(new Error((evt as Event & { message?: string })?.message || 'SSE connection error')) } catch { /* ignore */ }
      }

      if (autoReconnect && retryRef.current < maxRetries) {
        const attempt = retryRef.current + 1
        const delay = retryDelay * Math.pow(2, retryRef.current)
        console.log(`Reconnecting in ${delay}ms (attempt ${attempt}/${maxRetries})`)
        if (onReconnect) {
          try { onReconnect(attempt) } catch { /* ignore */ }
        }
        // schedule reconnect
        setTimeout(() => {
          retryRef.current = attempt
          connect()
        }, delay)
      } else {
        setError(new Error('Failed to reconnect to SSE stream'))
        setIsLoading(false)
      }
    }

    source.onopen = () => {
      console.log('SSE connection established')
      // reset retry counter on successful open
      retryRef.current = 0
      setIsLoading(false)
    }
  }

  const reconnect = () => {
    if (sourceRef.current) {
      try { sourceRef.current.close() } catch { /* ignore */ }
      sourceRef.current = null
    }
    retryRef.current = 0
    setIsLoading(true)
    setError(null)
    connect()
  }

  const close = () => {
    if (sourceRef.current) {
      try { sourceRef.current.close() } catch { /* ignore */ }
      sourceRef.current = null
    }
  }

  useEffect(() => {
    if (jobId) {
      connect()
    }
    return () => {
      close()
    }
    // connect/close omitted to avoid reconnecting every render; refs used inside
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId])

  return {
    data,
    isLoading,
    isComplete,
    error,
    reconnect,
    close
  }
}
