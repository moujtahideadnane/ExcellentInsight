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
    border: 'border-ve-error', 
    bg: 'bg-ve-error-bg',
    text: 'text-ve-error',
    label: 'CRITICAL'
  },
  medium: { 
    icon: Target, 
    border: 'border-ve-warning', 
    bg: 'bg-amber-950',
    text: 'text-ve-warning',
    label: 'STRATEGIC' 
  },
  low: { 
    icon: Info, 
    border: 'border-ve-blue', 
    bg: 'bg-blue-950',
    text: 'text-ve-blue',
    label: 'OBSERVATION'
  },
  info: { 
    icon: Info, 
    border: 'border-ve-border', 
    bg: 'bg-ve-surface',
    text: 'text-ve-muted',
    label: 'NOTE'
  },
  warning: { 
    icon: AlertCircle, 
    border: 'border-ve-warning', 
    bg: 'bg-amber-950',
    text: 'text-ve-warning',
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

  let correlationCount = 0
  const displayInsights = insights.filter(insight => {
    if (insight.type === 'correlation') {
      correlationCount++
      return correlationCount <= 3
    }
    return true
  })

  return (
    <div className="space-y-6 mt-8">
      <div className="flex items-center gap-4">
        <h2 className="text-[10px] font-mono uppercase tracking-widest text-ve-muted whitespace-nowrap">Automated Reasoning</h2>
        <div className="flex-1 h-px bg-ve-border" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-px bg-ve-border border border-ve-border rounded-[6px] overflow-hidden">
        {displayInsights.map((insight, index) => {
          const fallback = severityConfig.info || severityConfig.low || { icon: Info, border: '', bg: '', text: '', label: '' }
          const config = severityConfig[insight.severity as keyof typeof severityConfig] || fallback
          const Icon = config.icon
          const TypeIcon = TYPE_ICONS[insight.type] || Info

          return (
            <motion.div
              key={index}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: index * 0.1 }}
              className={cn(
                "p-5 relative overflow-hidden flex flex-col justify-start bg-ve-bg hover:bg-ve-surface transition-colors border-t-2",
                config.border
              )}
              style={{ minHeight: '180px' }}
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <div className="h-6 w-6 rounded-[2px] flex items-center justify-center bg-ve-surface border border-ve-border">
                    <TypeIcon className="h-3.5 w-3.5 text-ve-muted" />
                  </div>
                  <span className="text-[9px] font-mono uppercase tracking-wider text-ve-muted">
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
                <h4 className="text-[14px] font-medium text-ve-text mb-2 leading-tight">
                  {insight.title}
                </h4>
              )}
              <p className="text-[13px] leading-relaxed text-ve-muted font-mono">
                {insight.text}
              </p>
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}
