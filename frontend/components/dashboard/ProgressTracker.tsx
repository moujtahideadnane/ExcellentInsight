"use client"

import React from 'react'
import { motion } from 'framer-motion'
import { Check, Loader2 } from 'lucide-react'
import { ProgressUpdate } from '@/hooks/useJobProgress'
import { cn } from '@/lib/utils'
import { useJobStore } from '@/stores/job-store'
import { useRouter } from 'next/navigation'

interface ProgressTrackerProps {
  data: ProgressUpdate | null
  onStop?: () => void
}

const steps = [
  { id: 'parsing',   label: 'Memory Allocation & Parse',   desc: 'Buffer extraction sequence' },
  { id: 'schema',    label: 'Schema Recognition', desc: 'Type inference & constraints' },
  { id: 'stats',     label: 'Statistical Engine',    desc: 'Compute correlations & aggregates' },
  { id: 'llm',       label: 'Heuristic Enrichment',     desc: 'AI context projection' },
  { id: 'dashboard', label: 'Virtualization Assembly',  desc: 'Compiling visual matrices' },
  { id: 'done',      label: 'Operation Terminated',     desc: 'Output buffer ready' },
]

export default function ProgressTracker({ data, onStop }: ProgressTrackerProps) {
  const router = useRouter()
  const { clearActiveJob } = useJobStore()
  const currentStepIndex = steps.findIndex(s => s.id === data?.status)
  const isDone = data?.status === 'done'
  const isFailed = data?.status === 'failed'
  const isCancelled = data?.status === 'cancelled'
  const progress = data?.progress || 0

  return (
    <div className="w-full max-w-2xl py-8 text-left">
      {/* Header */}
      <div className="mb-10 text-left">
        <div className={cn(
          "text-[10px] font-mono px-2 py-1 rounded-[2px] mb-4 mx-auto w-fit uppercase tracking-widest border",
          isFailed ? "bg-ve-error-bg text-ve-error border-ve-error-border" : 
          isDone ? "bg-ve-surface text-ve-blue border-ve-blue-border" : 
          isCancelled ? "bg-amber-950 text-ve-warning border-amber-600/30" : 
          "bg-ve-surface text-ve-text border-ve-border"
        )}>
          {isFailed ? 'Exception' : isDone ? 'Compiled' : isCancelled ? 'Halted' : 'Executing'}
        </div>
        <h2 className="text-[24px] font-semibold tracking-tight text-ve-text mb-3">
          {isFailed ? 'Process Terminated.' : isDone ? 'System Online.' : isCancelled ? 'Execution Stopped.' : 'Processing Buffer...'}
        </h2>
        
        {isFailed || isCancelled ? (
          <div className="space-y-6">
            <div className={cn(
               "max-w-md mx-auto p-4 rounded-[4px] border text-[12px] font-mono",
               isCancelled ? "bg-amber-950 border-amber-600/30 text-ve-warning" : "bg-ve-error-bg border-ve-error-border text-ve-error"
            )}>
              {data?.message || (isCancelled ? "Process interrupted by user instruction." : "Unhandled exception caught during runtime.")}
            </div>
            <button
              onClick={() => {
                clearActiveJob()
                router.push('/dashboard')
              }}
              className="px-6 py-2 rounded-[4px] bg-ve-btn-primary text-ve-btn-text font-medium text-[13px] hover:bg-ve-btn-hover transition-colors"
            >
              Initialize New Context
            </button>
          </div>
        ) : (
          <div className="space-y-6">
            <p className="max-w-md mx-auto text-[13px] text-ve-muted font-mono">
              {data?.message || "Awaiting initialization..."}
            </p>
            {onStop && (
              <button
                onClick={onStop}
                className="px-4 py-2 text-[10px] font-mono uppercase tracking-widest text-ve-muted border border-ve-border hover:border-ve-error hover:text-ve-error rounded-[4px] transition-colors flex items-center gap-2 mx-auto"
              >
                ^C Interrupt
              </button>
            )}
          </div>
        )}
      </div>

      {/* Progress bar */}
      <div className="mb-10">
        <div className="flex items-center justify-between mb-2 px-1">
          <span className="text-[10px] font-mono uppercase tracking-widest text-ve-muted">Allocated Cache</span>
          <span className="text-[12px] font-mono text-ve-blue">
            {progress}%
          </span>
        </div>
        <div className="h-1 w-full bg-ve-border overflow-hidden">
          <motion.div
            className="h-full bg-ve-blue"
            initial={{ width: '0%' }}
            animate={{ width: `${progress}%` }}
            transition={{ type: 'spring', stiffness: 50, damping: 20 }}
          />
        </div>
      </div>

      {/* Steps */}
      <div className="space-y-2">
        {steps.map((step, index) => {
          const isCompleted = isDone || index < currentStepIndex
          const isActive = data?.status === step.id && !isDone
          const isPending = !isCompleted && !isActive

          return (
            <motion.div
              key={step.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              className={cn(
                "flex items-center gap-4 px-4 py-3 border border-l-2 transition-all",
                isActive ? "border-ve-border border-l-ve-blue bg-ve-surface" : "border-transparent border-l-transparent bg-ve-bg",
                isCompleted && "border-l-ve-border"
              )}
              style={{
                opacity: isPending ? 0.4 : 1
              }}
            >
              {/* Step indicator */}
              <div className="h-6 w-6 flex items-center justify-center shrink-0">
                {isCompleted ? (
                  <Check className="h-4 w-4 text-ve-muted" />
                ) : isActive ? (
                  <Loader2 className="h-4 w-4 animate-spin text-ve-blue" />
                ) : (
                  <div className="h-[4px] w-[4px] bg-ve-border" />
                )}
              </div>

              <div className="flex-1 min-w-0">
                <div className={cn("text-[13px] font-medium tracking-tight", (isCompleted || isActive) ? "text-ve-text" : "text-ve-muted")}>
                  {step.label}
                </div>
                <div className="text-[11px] font-mono text-ve-muted mt-0.5">
                  {step.desc}
                </div>
              </div>

              {isActive && (
                <div className="px-2 py-0.5 rounded-[2px] bg-ve-surface border border-ve-border text-[9px] font-mono text-ve-blue uppercase tracking-widest animate-pulse">
                  ACTIVE
                </div>
              )}
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}
