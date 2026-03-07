import { describe, it, expect } from 'vitest'
import { getErrorMessage } from '@/lib/api'

describe('API Utilities', () => {
  describe('getErrorMessage', () => {
    it('should return generic message for 5xx errors', () => {
      const error = {
        isAxiosError: true,
        response: {
          status: 500,
          data: { detail: 'Internal server error' }
        }
      }

      const message = getErrorMessage(error)
      expect(message).toBe('Something went wrong on our end. Please try again in a moment.')
    })

    it('should return API detail for 4xx errors', () => {
      const error = {
        isAxiosError: true,
        response: {
          status: 400,
          data: { detail: 'Invalid request' }
        }
      }

      const message = getErrorMessage(error)
      expect(message).toBe('Invalid request')
    })

    it('should handle timeout errors', () => {
      const error = {
        isAxiosError: true,
        code: 'ECONNABORTED',
        message: 'timeout'
      }

      const message = getErrorMessage(error)
      expect(message).toBe('The request timed out. Please check your connection.')
    })

    it('should return generic message for unknown errors', () => {
      const error = new Error('Unknown')

      const message = getErrorMessage(error)
      expect(message).toBe('An unexpected error occurred.')
    })
  })
})
