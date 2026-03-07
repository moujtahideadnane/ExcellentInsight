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
    <div className="w-full max-w-2xl mx-auto py-8">
      {/* Header */}
      <div className="mb-10 text-center">
        <div className={cn(
          "text-[10px] font-mono px-2 py-1 rounded-[2px] mb-4 mx-auto w-fit uppercase tracking-widest border",
          isFailed ? "bg-[#2A0808] text-[#FF4444] border-[#5C1A1A]" : 
          isDone ? "bg-[#111111] text-[#0070F3] border-[#0070F3]/30" : 
          isCancelled ? "bg-[#291704] text-[#F5A623] border-[#F5A623]/30" : 
          "bg-[#111111] text-[#EDEDED] border-[#333333]"
        )}>
          {isFailed ? 'Exception' : isDone ? 'Compiled' : isCancelled ? 'Halted' : 'Executing'}
        </div>
        <h2 className="text-[24px] font-semibold tracking-tight text-[#EDEDED] mb-3">
          {isFailed ? 'Process Terminated.' : isDone ? 'System Online.' : isCancelled ? 'Execution Stopped.' : 'Processing Buffer...'}
        </h2>
        
        {isFailed || isCancelled ? (
          <div className="space-y-6">
            <div className={cn(
               "max-w-md mx-auto p-4 rounded-[4px] border text-[12px] font-mono",
               isCancelled ? "bg-[#291704] border-[#F5A623]/30 text-[#F5A623]" : "bg-[#2A0808] border-[#5C1A1A] text-[#FF4444]"
            )}>
              {data?.message || (isCancelled ? "Process interrupted by user instruction." : "Unhandled exception caught during runtime.")}
            </div>
            <button
              onClick={() => {
                clearActiveJob()
                router.push('/dashboard')
              }}
              className="px-6 py-2 rounded-[4px] bg-[#EDEDED] text-[#000000] font-medium text-[13px] hover:bg-[#CCCCCC] transition-colors"
            >
              Initialize New Context
            </button>
          </div>
        ) : (
          <div className="space-y-6">
            <p className="max-w-md mx-auto text-[13px] text-[#888888] font-mono">
              {data?.message || "Awaiting initialization..."}
            </p>
            {onStop && (
              <button
                onClick={onStop}
                className="px-4 py-2 text-[10px] font-mono uppercase tracking-widest text-[#888888] border border-[#333333] hover:border-[#FF4444] hover:text-[#FF4444] rounded-[4px] transition-colors flex items-center gap-2 mx-auto"
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
          <span className="text-[10px] font-mono uppercase tracking-widest text-[#888888]">Allocated Cache</span>
          <span className="text-[12px] font-mono text-[#0070F3]">
            {progress}%
          </span>
        </div>
        <div className="h-1 w-full bg-[#333333] overflow-hidden">
          <motion.div
            className="h-full bg-[#0070F3]"
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
                isActive ? "border-[#333333] border-l-[#0070F3] bg-[#111111]" : "border-transparent border-l-transparent bg-[#000000]",
                isCompleted && "border-l-[#333333]"
              )}
              style={{
                opacity: isPending ? 0.4 : 1
              }}
            >
              {/* Step indicator */}
              <div className="h-6 w-6 flex items-center justify-center shrink-0">
                {isCompleted ? (
                  <Check className="h-4 w-4 text-[#888888]" />
                ) : isActive ? (
                  <Loader2 className="h-4 w-4 animate-spin text-[#0070F3]" />
                ) : (
                  <div className="h-[4px] w-[4px] bg-[#333333]" />
                )}
              </div>

              <div className="flex-1 min-w-0">
                <div className={cn("text-[13px] font-medium tracking-tight", (isCompleted || isActive) ? "text-[#EDEDED]" : "text-[#888888]")}>
                  {step.label}
                </div>
                <div className="text-[11px] font-mono text-[#888888] mt-0.5">
                  {step.desc}
                </div>
              </div>

              {isActive && (
                <div className="px-2 py-0.5 rounded-[2px] bg-[#111111] border border-[#333333] text-[9px] font-mono text-[#0070F3] uppercase tracking-widest animate-pulse">
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
