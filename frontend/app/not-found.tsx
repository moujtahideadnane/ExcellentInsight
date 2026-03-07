import Link from 'next/link'
import { BarChart3, Home, SearchX } from 'lucide-react'

export const metadata = { title: 'Page not found' }

export default function NotFound() {
  return (
    <div className="min-h-screen bg-[#F8F9FA] flex items-center justify-center p-6">
      <div className="w-full max-w-md text-center">
        {/* Logo */}
        <div className="flex items-center justify-center gap-3 mb-10">
          <div className="h-9 w-9 rounded-xl bg-emerald-500 flex items-center justify-center shadow-lg shadow-emerald-100">
            <BarChart3 className="h-5 w-5 text-white" />
          </div>
          <span className="font-extrabold text-xl text-slate-800">
            Excellent<span className="text-emerald-500">Insight</span>
          </span>
        </div>

        {/* 404 visual */}
        <div className="relative mb-8">
          <div className="text-[140px] font-black text-slate-100 leading-none select-none tracking-tighter">
            404
          </div>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="h-16 w-16 rounded-2xl bg-emerald-50 border border-emerald-100 flex items-center justify-center">
              <SearchX className="h-8 w-8 text-emerald-400" />
            </div>
          </div>
        </div>

        <h1 className="text-2xl font-extrabold text-slate-800 mb-3 tracking-tight">
          Page not found
        </h1>
        <p className="text-slate-400 font-medium mb-8 leading-relaxed">
          The page you are looking for does not exist or has been moved.
        </p>

        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2.5 btn-primary"
        >
          <Home className="h-4 w-4" />
          Back to dashboard
        </Link>
      </div>
    </div>
  )
}
