"use client"

import { useEffect } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { AlertTriangle, RefreshCw, Home } from 'lucide-react'

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    // Log error to monitoring (e.g. Sentry) in production
    console.error('[GlobalError]', error)
  }, [error])

  return (
    <div className="min-h-screen bg-[#000000] flex items-center justify-center p-6">
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md text-center"
      >
        {/* Icon */}
        <div className="flex items-center justify-center mb-8">
          <div className="h-14 w-14 rounded-[6px] bg-[#2A0808] border border-[#5C1A1A] flex items-center justify-center">
            <AlertTriangle className="h-7 w-7 text-[#FF4444]" />
          </div>
        </div>

        {/* Error label */}
        <div className="inline-flex items-center px-2 py-1 rounded-[4px] bg-[#2A0808] border border-[#5C1A1A] text-[10px] font-mono text-[#FF4444] uppercase tracking-widest mb-6">
          Runtime Exception
        </div>

        <h1 className="text-[28px] font-semibold tracking-tight text-[#EDEDED] mb-3 leading-tight">
          Something went wrong
        </h1>
        <p className="text-[13px] text-[#888888] font-mono mb-2 leading-relaxed max-w-sm mx-auto">
          An unexpected error occurred. Our team has been notified.
        </p>
        {error.digest && (
          <p className="text-[10px] font-mono text-[#555555] mb-8 uppercase tracking-widest">
            Ref: {error.digest}
          </p>
        )}

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 mt-8">
          <button
            onClick={reset}
            className="flex items-center gap-2 h-9 px-5 rounded-[4px] bg-[#EDEDED] text-[#000000] text-[13px] font-medium hover:bg-[#CCCCCC] transition-colors w-full sm:w-auto justify-center"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Try again
          </button>
          <Link
            href="/dashboard"
            className="flex items-center gap-2 h-9 px-5 rounded-[4px] border border-[#333333] text-[#888888] text-[13px] font-medium hover:border-[#888888] hover:text-[#EDEDED] hover:bg-[#111111] transition-colors w-full sm:w-auto justify-center"
          >
            <Home className="h-3.5 w-3.5" />
            Back to dashboard
          </Link>
        </div>
      </motion.div>
    </div>
  )
}
