"use client"

import React, { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import FileUpload from '@/components/dashboard/FileUpload'
import ProgressTracker from '@/components/dashboard/ProgressTracker'
import { useJobProgress } from '@/hooks/useJobProgress'
import { useJobStore } from '@/stores/job-store'
import { Server, Database, BrainCircuit, Activity, Command } from 'lucide-react'
import { motion } from 'framer-motion'
import api from '@/lib/api'
import { toast } from 'sonner'

const PIPELINE_STEPS = [
  { id: 1, label: 'Parse',   icon: Database },
  { id: 2, label: 'Schema',  icon: Command },
  { id: 3, label: 'Stats',   icon: Activity },
  { id: 4, label: 'Infer',      icon: BrainCircuit },
  { id: 5, label: 'Deploy',   icon: Server },
]

const FEATURES = [
  { icon: Database,     label: 'Schema detection',  desc: 'Types, PKs, relations' },
  { icon: Activity,     label: 'Statistics engine',  desc: 'Distributions, metrics' },
  { icon: BrainCircuit, label: 'LLM enrichment',     desc: 'Insights & generation' },
  { icon: Server,       label: 'Sub-1min deploy',   desc: 'Zero-latency inference' },
]

export default function DashboardPage() {
  const router = useRouter()
  const { activeJobId, setActiveJobId, clearActiveJob } = useJobStore()
  const jobId = activeJobId ?? ''
  const { data: progress, isComplete } = useJobProgress(jobId)

  const prevStatusRef = React.useRef<string | null>(null)

  useEffect(() => {
    if (activeJobId && progress && ['done', 'failed', 'cancelled'].includes(progress.status)) {
      clearActiveJob()
    }
  }, [activeJobId, progress, clearActiveJob])

  useEffect(() => {
    if (
      activeJobId &&
      isComplete &&
      prevStatusRef.current &&
      !['done', 'failed', 'cancelled'].includes(prevStatusRef.current)
    ) {
      router.push(`/dashboard/${activeJobId}`)
      clearActiveJob()
    }
    if (progress) {
      prevStatusRef.current = progress.status
    }
  }, [isComplete, activeJobId, progress, router, clearActiveJob])

  const handleStopAnalysis = async () => {
    if (!activeJobId) return
    try {
      await api.post(`/dashboard/${activeJobId}/stop`)
      toast.success("Deployment stopping...")
    } catch (err: unknown) {
      console.error(err)
      toast.error("Failed to halt deployment")
    }
  }

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl w-full min-h-full">
      <div className="flex flex-col items-start gap-6 w-full">

        {/* Header */}
        <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
        className="mb-8"
      >
        <div className="text-[10px] font-mono text-[#888888] uppercase tracking-widest mb-2">Workspace Region: Global Edge</div>
        <h1 className="text-[32px] font-semibold text-[#EDEDED] tracking-tight leading-tight">
          Initialize <br/><span className="text-[#888888]">deployment</span>
        </h1>
        <p className="mt-3 text-[14px] text-[#888888] font-mono max-w-lg">
          Mount a dataset. The engine will infer schema, generate metrics, and compile a queryable dashboard.
        </p>
      </motion.div>

      {!activeJobId ? (
        <div className="space-y-6">

          {/* Upload card */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.05 }}
            className="bg-[#111111] border border-[#333333] rounded-[6px] overflow-hidden"
          >
            <div className="p-6">
              <div className="flex items-center gap-3 mb-6">
                <div className="h-6 w-6 rounded-[2px] bg-[#EDEDED] flex items-center justify-center">
                  <Server className="h-3.5 w-3.5 text-[#000000]" />
                </div>
                <span className="text-[11px] font-mono text-[#EDEDED] uppercase tracking-widest">Target Environment</span>
              </div>

              <FileUpload onUploadSuccess={(id) => setActiveJobId(id)} />

              {/* Pipeline steps */}
              <div className="mt-8 pt-6 border-t border-[#333333]">
                <div className="text-[9px] font-mono text-[#888888] uppercase tracking-widest mb-4">Compilation Pipeline</div>
                <div className="flex items-center gap-2 flex-wrap">
                  {PIPELINE_STEPS.map((step, i) => (
                    <React.Fragment key={step.id}>
                      <div className="flex items-center gap-2 px-2 py-1 rounded-[4px] bg-[#000000] border border-[#333333]">
                        <step.icon className="h-3 w-3 text-[#EDEDED]" />
                        <span className="text-[10px] font-mono text-[#EDEDED]">{step.label}</span>
                      </div>
                      {i < PIPELINE_STEPS.length - 1 && (
                        <div className="h-px w-4 bg-[#333333]" />
                      )}
                    </React.Fragment>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>

          {/* Feature grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {FEATURES.map(({ icon: Icon, label, desc }, i) => (
              <motion.div
                key={label}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 + i * 0.06 }}
                className="bg-[#000000] border border-[#333333] rounded-[6px] p-4 group hover:border-[#888888] transition-colors"
              >
                <div className="h-7 w-7 rounded-[4px] bg-[#111111] border border-[#333333] flex items-center justify-center mb-4 group-hover:bg-[#EDEDED] transition-colors">
                  <Icon className="h-3.5 w-3.5 text-[#EDEDED] group-hover:text-[#000000] transition-colors" />
                </div>
                <div className="text-[12px] font-medium text-[#EDEDED] tracking-tight">{label}</div>
                <div className="text-[11px] font-mono text-[#888888] mt-1">{desc}</div>
              </motion.div>
            ))}
          </div>

          {/* Format hint */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.35 }}
            className="flex items-center gap-3 px-4 py-3 rounded-[4px] bg-[#111111] border border-[#333333]"
          >
            <div className="h-1.5 w-1.5 rounded-full bg-[#0070F3] shrink-0" />
            <span className="text-[11px] font-mono text-[#888888]">
              Specs:{' '}
              <span className="text-[#EDEDED]">.xlsx</span>,{' '}
              <span className="text-[#EDEDED]">.xls</span>,{' '}
              <span className="text-[#EDEDED]">.csv</span> | Max{' '}
              <span className="text-[#EDEDED]">100 MB</span>,{' '}
              <span className="text-[#EDEDED]">500K rows/sheet</span>
            </span>
          </motion.div>

        </div>
      ) : (
        // Progress Tracker
        <motion.div
          initial={{ opacity: 0, scale: 0.99 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-[#111111] border border-[#333333] rounded-[6px] p-6 lg:p-8 relative overflow-hidden"
        >
          <ProgressTracker data={progress} onStop={handleStopAnalysis} />
        </motion.div>
      )}
      </div>
    </div>
  )
}
