"use client"

import { useEffect } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { BarChart3, RefreshCw, Home } from 'lucide-react'

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
    <div className="min-h-screen bg-[#F8F9FA] flex items-center justify-center p-6">
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md text-center"
      >
        {/* Logo */}
        <div className="flex items-center justify-center gap-3 mb-10">
          <div className="h-9 w-9 rounded-xl bg-emerald-500 flex items-center justify-center shadow-lg shadow-emerald-100">
            <BarChart3 className="h-5 w-5 text-white" />
          </div>
          <span className="font-extrabold text-xl text-slate-800">
            Excellent<span className="text-emerald-500">Insight</span>
          </span>
        </div>

        {/* Error visual */}
        <div className="relative mb-8">
          <div className="text-[120px] font-black text-slate-100 leading-none select-none">!</div>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-5xl">⚠️</div>
          </div>
        </div>

        <h1 className="text-2xl font-extrabold text-slate-800 mb-3 tracking-tight">
          Something went wrong
        </h1>
        <p className="text-slate-400 font-medium mb-8 leading-relaxed max-w-sm mx-auto">
          An unexpected error occurred. Our team has been notified.
          {error.digest && (
            <span className="block text-xs mt-2 font-mono text-slate-300">
              Ref: {error.digest}
            </span>
          )}
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <button
            onClick={reset}
            className="btn-primary flex items-center gap-2.5 w-full sm:w-auto justify-center"
          >
            <RefreshCw className="h-4 w-4" />
            Try again
          </button>
          <Link
            href="/dashboard"
            className="flex items-center gap-2.5 px-5 py-2.5 rounded-2xl border border-slate-200 font-bold text-sm text-slate-600 hover:bg-slate-50 transition-colors w-full sm:w-auto justify-center"
          >
            <Home className="h-4 w-4" />
            Back to dashboard
          </Link>
        </div>
      </motion.div>
    </div>
  )
}
