"use client"

import React from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { ArrowLeft, Calendar, Terminal, BarChart3, Activity } from 'lucide-react'
import ShareButton from '@/components/dashboard/ShareButton'
import ExportDropdown from '@/components/dashboard/ExportDropdown'
import { DashboardData } from '@/types/dashboard'

interface DashboardHeaderProps {
  data: DashboardData
  jobId: string
}

export default function DashboardHeader({ data, jobId }: DashboardHeaderProps) {
  const router = useRouter()

  return (
    <motion.header
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="no-print"
    >
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-8 pb-8 border-b border-[#333333]">
        <div>
          <div className="flex items-center gap-2 mb-4">
            <button onClick={() => router.push('/jobs')} className="text-[10px] font-mono uppercase tracking-wider text-[#888888] hover:text-[#EDEDED] transition-colors flex items-center gap-1.5">
              <ArrowLeft className="h-3 w-3" />
              root/history
            </button>
            <div className="h-[2px] w-[2px] bg-[#333333]" />
            <span className="text-[10px] font-mono uppercase tracking-wider text-[#0070F3]">
              {data.overview?.domain || 'General'}
            </span>
            {data.dataset_profile?.candidate_table_types?.some((t: { type: string; score: number }) => t.score >= 0.6) && (
              <>
                <div className="h-[2px] w-[2px] bg-[#333333]" />
                <span className="flex items-center gap-1.5 px-1.5 py-0.5 rounded-[2px] bg-[#0070F3]/10 text-[#0070F3] text-[9px] font-mono uppercase tracking-widest border border-[#0070F3]/30">
                  <Activity className="h-2.5 w-2.5" />
                  Domain Optimized
                </span>
              </>
            )}
          </div>

          <h1 className="text-[32px] font-semibold tracking-tight text-[#EDEDED] leading-tight mb-4">
            Deployment <span className="text-[#888888]">Metrics</span>
          </h1>

          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-2">
              <Calendar className="h-3.5 w-3.5 text-[#888888]" />
              <span className="text-[11px] text-[#EDEDED] font-mono uppercase">
                {new Date(data.created_at).toLocaleDateString('en-US', { day: '2-digit', month: 'short', year: 'numeric' })}
              </span>
            </div>
            <div className="h-3 w-px bg-[#333333]" />
            <div className="flex items-center gap-2">
              <Terminal className="h-3.5 w-3.5 text-[#888888]" />
              <span className="text-[11px] text-[#EDEDED] font-mono uppercase">
                {data.kpis?.length || 0} compute nodes
              </span>
            </div>
            <div className="h-3 w-px bg-[#333333]" />
            <div className="flex items-center gap-2">
              <BarChart3 className="h-3.5 w-3.5 text-[#888888]" />
              <span className="text-[11px] text-[#EDEDED] font-mono uppercase">
                {data.charts?.length || 0} visual engines
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <ShareButton jobId={jobId} />
          <ExportDropdown jobId={jobId} />
        </div>
      </div>
    </motion.header>
  )
}
