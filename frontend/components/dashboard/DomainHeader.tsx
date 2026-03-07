"use client"

import React from 'react'
import { motion } from 'framer-motion'
import { Layers, Rows3, Cpu, TerminalSquare } from 'lucide-react'
import { cn } from '@/lib/utils'

interface DomainHeaderProps {
  domain: string
  summary: string
  sheetCount?: number
  totalRows?: number
  llmUsage?: { prompt_tokens?: number; completion_tokens?: number; total_tokens?: number }
}

const DOMAIN_EMOJI: Record<string, string> = {
  sales: '📈', hr: '👥', finance: '💰', logistics: '🚚', supply: '🏭',
  marketing: '📣', healthcare: '🏥', retail: '🛍️', travel: '✈️',
  default: '📊',
}

function domainEmoji(domain: string): string {
  const key = domain.toLowerCase()
  for (const [k, v] of Object.entries(DOMAIN_EMOJI)) {
    if (key.includes(k)) return v
  }
  return DOMAIN_EMOJI.default || '📊'
}

function formatRows(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return String(n)
}

export default function DomainHeader({ domain, summary, sheetCount, totalRows, llmUsage }: DomainHeaderProps) {
  const emoji = domainEmoji(domain)
  const totalTokens = ((llmUsage?.prompt_tokens ?? 0) + (llmUsage?.completion_tokens ?? 0)) || (llmUsage?.total_tokens ?? 0)

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-[6px] overflow-hidden mb-8 border border-[#333333] bg-[#000000]"
    >
      <div className="absolute inset-x-0 top-0 h-[1px] bg-gradient-to-r from-[#EDEDED] via-[#888888] to-transparent" />

      <div className="p-6">
        <div className="flex flex-wrap items-start justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 rounded-[4px] flex items-center justify-center text-2xl shrink-0 bg-[#111111] border border-[#333333]">
              {emoji}
            </div>
            <div>
              <div className="text-[10px] font-mono uppercase tracking-widest text-[#888888] mb-1">Context Analysis</div>
              <h2 className="text-[20px] font-semibold tracking-tight text-[#EDEDED]">
                {domain}
              </h2>
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            {sheetCount !== undefined && (
              <StatChip icon={<Layers className="h-3.5 w-3.5" />} label="Datasets" value={String(sheetCount)} />
            )}
            {totalRows !== undefined && (
              <StatChip icon={<Rows3 className="h-3.5 w-3.5" />} label="Rows" value={formatRows(totalRows)} />
            )}
            {totalTokens > 0 && (
              <StatChip icon={<Cpu className="h-3.5 w-3.5" />} label="Compute" value={totalTokens >= 1_000 ? `${(totalTokens / 1_000).toFixed(1)}K ctx` : String(totalTokens)} />
            )}
            <StatChip icon={<TerminalSquare className="h-3.5 w-3.5" />} label="Engine" value="v2.4.0" accent />
          </div>
        </div>

        {summary && (
          <div className="mt-6 pt-5 border-t border-[#222222]">
            <p className="text-[13px] leading-relaxed text-[#888888] font-mono">
              <span className="text-[#EDEDED] font-semibold mr-2">{'>'}</span>{summary}
            </p>
          </div>
        )}
      </div>
    </motion.div>
  )
}

function StatChip({ icon, label, value, accent = false }: { icon: React.ReactNode; label: string; value: string; accent?: boolean }) {
  return (
    <div
      className={cn(
        "inline-flex items-center gap-2 px-3 py-1.5 rounded-[4px] border transition-colors",
        accent 
          ? "bg-[#111111] border-[#EDEDED] text-[#EDEDED]" 
          : "bg-[#000000] border-[#333333] text-[#888888]"
      )}
    >
      <span>{icon}</span>
      <span className="text-[9px] font-mono font-bold uppercase tracking-wider opacity-70">{label}</span>
      <span className="text-[12px] font-mono font-semibold">{value}</span>
    </div>
  )
}
