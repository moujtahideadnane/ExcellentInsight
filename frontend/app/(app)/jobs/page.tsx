"use client"

import React, { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import { motion } from 'framer-motion'
import { Server, Clock, ArrowRight, FileText, Plus, AlertTriangle } from 'lucide-react'
import { useJobStore } from '@/stores/job-store'
import { cn } from '@/lib/utils'
import { formatBytes } from '@/lib/format'

interface Job {
  id: string
  status: string
  file_name?: string
  created_at: string
  file_size_bytes?: number
  processing_time_ms?: number
  llm_result?: { domain?: string } | null
}

const STATUS_CONFIG: Record<string, { color: string; bg: string; border: string; label: string }> = {
  completed:  { color: '#EDEDED', bg: '#111111', border: '#333333', label: 'COMPILED' },
  done:       { color: '#EDEDED', bg: '#111111', border: '#333333', label: 'ONLINE' },
  failed:     { color: '#FF4444', bg: '#2A0808', border: '#5C1A1A', label: 'EXCEPTION' },
  processing: { color: '#0070F3', bg: 'rgba(0, 112, 243, 0.1)', border: 'rgba(0, 112, 243, 0.3)', label: 'EXECUTING' },
  pending:    { color: '#888888', bg: '#111111', border: '#333333', label: 'AWAIT' },
  analyzing:  { color: '#0070F3', bg: 'rgba(0, 112, 243, 0.1)', border: 'rgba(0, 112, 243, 0.3)', label: 'ANALYZING' },
  enriching:  { color: '#0070F3', bg: 'rgba(0, 112, 243, 0.1)', border: 'rgba(0, 112, 243, 0.3)', label: 'ENRICHING' },
  parsing:    { color: '#0070F3', bg: 'rgba(0, 112, 243, 0.1)', border: 'rgba(0, 112, 243, 0.3)', label: 'PARSING' },
}

const DEFAULT_STATUS = { color: '#888888', bg: '#111111', border: '#333333', label: 'STATUS_UNKNOWN' }



export default function JobsPage() {
  const router    = useRouter()
  const { clearActiveJob } = useJobStore()
  const [jobs,      setJobs]      = useState<Job[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error,     setError]     = useState<string | null>(null)

  const fetchJobs = async () => {
    try {
      const res = await api.get('/jobs')
      setJobs(res.data?.jobs ?? res.data ?? [])
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      setError(axiosErr.response?.data?.detail || 'Failed to load process history')
    } finally {
      setIsLoading(false)
    }
  }

  // [Adding Auto-Polling for Active Operations]
  useEffect(() => {
    fetchJobs()
  }, [])

  useEffect(() => {
    const hasActiveJobs = jobs.some(j => ['processing', 'pending', 'analyzing', 'enriching', 'parsing'].includes(j.status))
    if (!hasActiveJobs) return

    const intervalId = setInterval(() => {
      fetchJobs()
    }, 4000)

    return () => clearInterval(intervalId)
  }, [jobs])

  return (
    <div className="p-6 lg:p-8 max-w-5xl mx-auto min-h-full">

      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8 border-b border-ve-border pb-8"
      >
        <div className="text-[10px] font-mono text-ve-muted uppercase tracking-widest mb-2">Resource Allocation Directory</div>
        <h1 className="text-[32px] font-semibold text-ve-text tracking-tight leading-tight">
          System <span className="text-ve-muted">Deployments</span>
        </h1>
        <p className="mt-3 text-[14px] text-ve-muted font-mono max-w-lg">
          Query the execution history of previously deployed analytical nodes.
        </p>
      </motion.div>

      {/* Loading Skeleton */}
      {isLoading && (
        <div className="grid grid-cols-1 gap-3">
          {[...Array(5)].map((_, i) => (
            <div 
              key={`skeleton-${i}`} 
              className="group flex flex-col sm:flex-row items-start sm:items-center justify-between p-4 rounded-[4px] bg-ve-bg border border-ve-border animate-pulse gap-4 sm:gap-0"
            >
              <div className="flex items-center gap-4 min-w-0 w-full sm:w-auto">
                {/* Icon Skeleton */}
                <div className="h-8 w-8 rounded-[4px] bg-ve-surface shrink-0" />
                
                <div className="min-w-0 flex-1 space-y-2">
                  {/* Title Skeleton */}
                  <div className="h-4 w-32 sm:w-48 bg-ve-surface rounded-[2px]" />
                  
                  {/* Subtitle/Time Skeleton */}
                  <div className="h-3 w-24 sm:w-36 bg-ve-surface rounded-[2px]" />
                </div>
              </div>

              {/* Status Badge Skeleton */}
              <div className="h-5 w-20 bg-ve-surface rounded-[2px] shrink-0" />
            </div>
          ))}
        </div>
      )}

      {/* Error */}
      {/* [Create Actionable Error States] */}
      {error && (
        <div className="flex items-center justify-between gap-3 px-4 py-3 rounded-[4px] mb-6 bg-ve-error-bg border border-ve-error-border">
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-4 w-4 shrink-0 text-ve-error" />
            <p className="text-ve-error text-[12px] font-mono">{error}</p>
          </div>
          <button
            onClick={() => {
              setIsLoading(true)
              setError(null)
              fetchJobs()
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-[4px] bg-ve-error text-ve-bg text-[11px] font-medium font-mono hover:opacity-90 transition-opacity"
          >
            Retry
          </button>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !error && jobs.length === 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex flex-col items-center justify-center py-32 text-center border border-dashed border-ve-border rounded-[6px] bg-ve-surface"
        >
          <div className="h-12 w-12 flex items-center justify-center mb-4">
            <Server className="h-6 w-6 text-ve-border" />
          </div>
          <h3 className="text-[14px] font-semibold tracking-tight text-ve-text mb-2">Log Directory Empty</h3>
          <p className="mb-6 max-w-sm text-ve-muted font-mono text-[11px] leading-relaxed">
            There are no documented deployments in this workspace. Initialize a deployment to start capturing analytical outputs.
          </p>
          <button
            onClick={() => {
              clearActiveJob()
              router.push('/dashboard')
            }}
            className="flex items-center gap-2 rounded-[4px] bg-ve-btn-primary text-ve-btn-text px-4 py-2 font-medium text-[12px] hover:bg-ve-btn-hover transition-colors"
          >
            <Plus className="h-3.5 w-3.5" />
            Initialize Run
          </button>
        </motion.div>
      )}

      {/* Jobs list */}
      {!isLoading && !error && jobs.length > 0 && (
        <div className="grid grid-cols-1 gap-3">
          {jobs.map((job, i) => {
            const sc = STATUS_CONFIG[job.status] || STATUS_CONFIG['pending'] || DEFAULT_STATUS
            const isClickable = job.status === 'completed' || job.status === 'done'
            const displayName = job.file_name || `${job.id.slice(0, 12)}`
            const sizeStr = job.file_size_bytes ? formatBytes(job.file_size_bytes) : null
            const domain = job.llm_result?.domain

            return (
              <motion.div
                key={job.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.04 }}
                onClick={() => isClickable && router.push(`/dashboard/${job.id}`)}
                // [Adding Micro-Interactions & Tactility] added hover:-translate-y-[1px] hover:shadow-md
                className={cn(
                  "group flex items-center justify-between p-4 rounded-[4px] transition-all bg-ve-bg border border-ve-border",
                  isClickable ? "cursor-pointer hover:border-ve-muted hover:-translate-y-[1px] hover:shadow-md" : "opacity-70 grayscale"
                )}
              >
                <div className="flex items-center gap-4 min-w-0">
                  <div className="h-8 w-8 rounded-[4px] bg-ve-surface border border-ve-border flex items-center justify-center group-hover:bg-ve-text group-hover:border-ve-text transition-colors shrink-0">
                    <FileText className="h-4 w-4 text-ve-muted group-hover:text-ve-bg transition-colors" />
                  </div>
                  
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-3 mb-1">
                      <span className="text-[13px] font-medium text-ve-text tracking-tight truncate">
                         {displayName}
                      </span>
                      {sizeStr && (
                        <>
                          <div className="h-px w-3 bg-ve-border" />
                          <span className="text-[10px] font-mono text-ve-muted uppercase tracking-widest">
                            {sizeStr}
                          </span>
                        </>
                      )}
                    </div>
                    
                    <div className="flex items-center gap-3">
                      <span className="text-[10px] font-mono text-ve-muted flex items-center gap-1.5 uppercase tracking-wider">
                         <Clock className="h-3 w-3" />
                         {new Date(job.created_at).toLocaleString('en-US', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
                      </span>
                      {domain && (
                        <>
                           <div className="h-px w-3 bg-ve-border" />
                           <span className="text-[9px] font-mono text-ve-blue uppercase tracking-widest">{domain} schema</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-4 shrink-0">
                   <div 
                      className="px-2 py-1 rounded-[2px] text-[9px] font-mono uppercase tracking-widest border"
                      style={{ backgroundColor: sc.bg, color: sc.color, borderColor: sc.border }}
                   >
                      {sc.label}
                   </div>
                   {isClickable && (
                     <ArrowRight className="h-4 w-4 text-ve-border group-hover:text-ve-text group-hover:translate-x-1 transition-all" />
                   )}
                </div>
              </motion.div>
            )
          })}
        </div>
      )}
    </div>
  )
}
