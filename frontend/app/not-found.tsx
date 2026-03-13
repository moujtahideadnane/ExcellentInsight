import Link from 'next/link'
import { SearchX, Home } from 'lucide-react'

export const metadata = { title: 'Page not found' }

export default function NotFound() {
  return (
    <div className="min-h-screen bg-[#000000] flex items-center justify-center p-6">
      <div className="w-full max-w-md text-center">

        {/* Icon */}
        <div className="flex items-center justify-center mb-8">
          <div className="h-14 w-14 rounded-[6px] bg-[#111111] border border-[#333333] flex items-center justify-center">
            <SearchX className="h-7 w-7 text-[#888888]" />
          </div>
        </div>

        {/* Status label */}
        <div className="inline-flex items-center px-2 py-1 rounded-[4px] bg-[#111111] border border-[#333333] text-[10px] font-mono text-[#888888] uppercase tracking-widest mb-6">
          ERR_NOT_FOUND
        </div>

        {/* 404 number */}
        <div className="text-[120px] font-black text-[#111111] leading-none select-none tracking-tighter mb-2">
          404
        </div>

        <h1 className="text-[24px] font-semibold tracking-tight text-[#EDEDED] mb-3">
          Page not found
        </h1>
        <p className="text-[13px] text-[#888888] font-mono mb-8 leading-relaxed max-w-sm mx-auto">
          The resource you are looking for does not exist or has been moved.
        </p>

        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 h-9 px-5 rounded-[4px] bg-[#EDEDED] text-[#000000] text-[13px] font-medium hover:bg-[#CCCCCC] transition-colors"
        >
          <Home className="h-3.5 w-3.5" />
          Back to dashboard
        </Link>
      </div>
    </div>
  )
}
