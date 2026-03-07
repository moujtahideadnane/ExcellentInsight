"use client"

import React from 'react'
import { motion } from 'framer-motion'
import { Target, AlertCircle, Info, Sparkles, TrendingUp, Zap } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Insight } from '@/types/dashboard'

interface InsightViewProps {
  insights: Insight[]
}

const severityConfig: Record<string, { icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }>; border: string; bg: string; text: string; label: string }> = {
  high: { 
    icon: AlertCircle, 
    border: 'border-[#FF4444]', 
    bg: 'bg-[#2A0808]',
    text: 'text-[#FF4444]',
    label: 'CRITICAL'
  },
  medium: { 
    icon: Target, 
    border: 'border-[#F5A623]', 
    bg: 'bg-[#291704]',
    text: 'text-[#F5A623]',
    label: 'STRATEGIC' 
  },
  low: { 
    icon: Info, 
    border: 'border-[#0070F3]', 
    bg: 'bg-[#001736]',
    text: 'text-[#0070F3]',
    label: 'OBSERVATION'
  },
  info: { 
    icon: Info, 
    border: 'border-[#333333]', 
    bg: 'bg-[#111111]',
    text: 'text-[#888888]',
    label: 'NOTE'
  },
  warning: { 
    icon: AlertCircle, 
    border: 'border-[#F5A623]', 
    bg: 'bg-[#291704]',
    text: 'text-[#F5A623]',
    label: 'ALERT'
  },
}

const TYPE_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  kpi: TrendingUp,
  correlation: Zap,
  business_summary: Sparkles,
}

export default function InsightView({ insights }: InsightViewProps) {
  if (!insights || insights.length === 0) return null

  return (
    <div className="space-y-6 mt-8">
      <div className="flex items-center gap-4">
        <h2 className="text-[10px] font-mono uppercase tracking-widest text-[#888888] whitespace-nowrap">Automated Reasoning</h2>
        <div className="flex-1 h-px bg-[#333333]" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-px bg-[#333333] border border-[#333333] rounded-[6px] overflow-hidden">
        {insights.map((insight, index) => {
          const config = severityConfig[insight.severity as keyof typeof severityConfig] || severityConfig.low!
          const Icon = config.icon
          const TypeIcon = TYPE_ICONS[insight.type] || Info

          return (
            <motion.div
              key={index}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: index * 0.1 }}
              className={cn(
                "p-5 relative overflow-hidden flex flex-col justify-start bg-[#000000] hover:bg-[#111111] transition-colors border-t-2",
                config.border
              )}
              style={{ minHeight: '180px' }}
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <div className="h-6 w-6 rounded-[2px] flex items-center justify-center bg-[#111111] border border-[#333333]">
                    <TypeIcon className="h-3.5 w-3.5 text-[#888888]" />
                  </div>
                  <span className="text-[9px] font-mono uppercase tracking-wider text-[#888888]">
                    {(insight.type || 'Insight').replace('_', ' ')}
                  </span>
                </div>
                <div className={cn("flex items-center gap-1.5 px-2 py-0.5 rounded-[4px] border", config.bg, config.border)}>
                  <Icon className={cn("h-3 w-3", config.text)} />
                  <span className={cn("text-[8px] font-mono uppercase tracking-wider", config.text)}>
                    {config.label}
                  </span>
                </div>
              </div>

              {insight.title && (
                <h4 className="text-[14px] font-medium text-[#EDEDED] mb-2 leading-tight">
                  {insight.title}
                </h4>
              )}
              <p className="text-[13px] leading-relaxed text-[#888888] font-mono">
                {insight.text}
              </p>
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}
