import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook } from '@testing-library/react'
import { useJobProgress } from '@/hooks/useJobProgress'

// Mock EventSourcePolyfill
vi.mock('event-source-polyfill', () => ({
  EventSourcePolyfill: vi.fn()
}))

// Mock auth store
vi.mock('@/stores/auth-store', () => ({
  useAuthStore: {
    getState: () => ({
      accessToken: 'mock-token',
      refreshToken: 'mock-refresh',
      setAuth: vi.fn(),
      logout: vi.fn(),
    }),
  },
}))

// Mock api
vi.mock('@/lib/api', () => ({
  default: {
    post: vi.fn(),
  },
}))

describe('useJobProgress', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should initialize with loading state', () => {
    const { result } = renderHook(() => useJobProgress({ jobId: 'test-123' }))

    expect(result.current.isLoading).toBe(true)
    expect(result.current.data).toBe(null)
    expect(result.current.error).toBe(null)
  })

  it('should handle null jobId', () => {
    const { result } = renderHook(() => useJobProgress({ jobId: null }))

    // Hook should still initialize properly even with null jobId
    expect(result.current).toBeDefined()
    expect(result.current.data).toBe(null)
    expect(result.current.error).toBe(null)
    expect(result.current.reconnect).toBeInstanceOf(Function)
    expect(result.current.close).toBeInstanceOf(Function)
  })

  it('should accept string jobId for backward compatibility', () => {
    const { result } = renderHook(() => useJobProgress('test-456'))

    expect(result.current).toBeDefined()
    expect(result.current.reconnect).toBeInstanceOf(Function)
    expect(result.current.close).toBeInstanceOf(Function)
  })
})
