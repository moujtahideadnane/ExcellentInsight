"use client"

import React, { useState } from 'react'
import { formatKpiValue } from '@/lib/format'
import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown, Minus, Activity, Edit3, Save, X, Info, Trash2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { KPI } from '@/types/dashboard'

interface InteractiveKPICardProps {
  kpi: KPI
  index: number
  onUpdateFormula?: (newFormula: string) => Promise<void>
  onDelete?: () => Promise<void>
}

const priorityStyles: Record<string, { badge: string; dot: string }> = {
  high:   { badge: 'bg-[#2A0808] text-[#FF4444] border-[#5C1A1A]', dot: 'bg-[#FF4444]' },
  medium: { badge: 'bg-[#111111] text-[#EDEDED] border-[#333333]', dot: 'bg-[#EDEDED]' },
  low:    { badge: 'bg-[#000000] text-[#888888] border-[#222222]', dot: 'bg-[#888888]' },
}

export default function InteractiveKPICard({ kpi, index, onUpdateFormula, onDelete }: InteractiveKPICardProps) {
  const [isFlipped, setIsFlipped] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [editFormula, setEditFormula] = useState(kpi.formula || '')
  const [isSaving, setIsSaving] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  const valueAsNumber = typeof kpi.value === 'number' ? kpi.value : (typeof kpi.value === 'string' ? Number(kpi.value) : undefined);
  const formattedValue = formatKpiValue(valueAsNumber, kpi.unit, kpi.format)
  
  const valueSize = formattedValue.length > 10 ? 'text-2xl' : 'text-3xl'
  const pConf = priorityStyles[kpi.priority ?? 'low']
  const coveragePct = Math.round((kpi.coverage ?? 0) * 100)

  const handleSave = async (e: React.MouseEvent | React.KeyboardEvent) => {
    e.stopPropagation()
    if (!onUpdateFormula) return
    setIsSaving(true)
    try {
      await onUpdateFormula(editFormula)
      setIsEditing(false)
    } finally {
      setIsSaving(false)
    }
  }

  const handleDelete = async (e: React.MouseEvent | React.KeyboardEvent) => {
    e.stopPropagation()
    if (!onDelete) return

    setIsDeleting(true)
    try {
      await onDelete()
    } catch (error) {
      console.error('Failed to delete KPI:', error)
      setIsDeleting(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (isEditing) return
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      setIsFlipped(!isFlipped)
    }
  }

  return (
    <div 
      className="relative h-[220px] w-full perspective-1000 group cursor-pointer outline-none"
      onMouseEnter={() => !isEditing && setIsFlipped(true)}
      onMouseLeave={() => !isEditing && setIsFlipped(false)}
      onClick={() => !isEditing && setIsFlipped(!isFlipped)}
      onKeyDown={handleKeyDown}
      tabIndex={0}
      role="button"
      aria-expanded={isFlipped}
      aria-label={`KPI Card: ${kpi.label}. Value: ${formattedValue}. Press space or enter to view details.`}
    >
      <motion.div
        className="relative w-full h-full preserve-3d"
        animate={{ rotateY: isFlipped ? 180 : 0 }}
        transition={{ duration: 0.4, type: 'spring', stiffness: 300, damping: 25 }}
      >
        {/* Front Side */}
        <div className="absolute inset-0 backface-hidden">
          <div className="rounded-[6px] p-5 flex flex-col h-full gap-4 bg-[#111111] border border-[#333333] hover:border-[#888888] transition-colors relative overflow-hidden">
            
            {/* Header */}
            <div className="flex items-start justify-between gap-2 z-10">
              <p className="text-[11px] font-mono uppercase tracking-widest text-[#888888] leading-tight truncate">{kpi.label}</p>
              <div className="flex items-center gap-2 shrink-0">
                {kpi.priority && (
                  <div className={cn("px-2 py-0.5 rounded-[4px] text-[9px] font-mono border uppercase tracking-wider", pConf?.badge)}>
                    {kpi.priority}
                  </div>
                )}
              </div>
            </div>

            {/* Value */}
            <div className="flex items-baseline gap-1.5 min-h-[2.5rem] flex-wrap z-10">
              <span className={cn("font-medium tracking-tight font-mono", `${valueSize} text-[#EDEDED]`)}>
                {formattedValue}
              </span>
            </div>

            {/* Progress / Coverage */}
            {kpi.coverage !== undefined && (
              <div className="space-y-1.5 z-10">
                <div className="flex items-center justify-between">
                  <span className="text-[9px] font-mono text-[#888888] uppercase">Coverage</span>
                  <span className="text-[9px] font-mono text-[#EDEDED]">{coveragePct}%</span>
                </div>
                <div className="h-[2px] w-full bg-[#333333]">
                  <div
                    className="h-full transition-all duration-700 bg-[#EDEDED]"
                    style={{ width: `${coveragePct}%` }}
                  />
                </div>
              </div>
            )}

            {/* Change footer */}
            <div className="flex items-center justify-between mt-auto pt-4 border-t border-[#333333] z-10">
              {kpi.change !== undefined && kpi.change !== null ? (
                <div
                  className={cn(
                    "inline-flex items-center gap-1.5 px-2 py-0.5 rounded-[4px] text-[10px] font-mono font-medium",
                    kpi.change > 0 ? "bg-[#111111] text-[#EDEDED] border border-[#333333]" : 
                    kpi.change < 0 ? "bg-[#2A0808] text-[#FF4444] border border-[#5C1A1A]" : 
                    "bg-[#000000] text-[#888888] border border-[#222222]"
                  )}
                >
                  {kpi.change > 0 ? <TrendingUp className="h-3 w-3" /> : kpi.change < 0 ? <TrendingDown className="h-3 w-3" /> : <Minus className="h-3 w-3" />}
                  {kpi.change > 0 ? '+' : ''}{kpi.change}%
                </div>
              ) : (
                <div className="inline-flex items-center gap-1.5 text-[10px] font-mono text-[#888888]">
                  <Activity className="h-3 w-3" />
                  STABLE
                </div>
              )}
              
              <div className="flex items-center gap-2">
                 <Info className="h-3.5 w-3.5 text-[#888888] opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
            </div>

            {/* Vercel Edge corner accents */}
            <div className="absolute top-0 right-0 w-4 h-4 border-t border-r border-[#888888] opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="absolute bottom-0 left-0 w-4 h-4 border-b border-l border-[#888888] opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        </div>

        {/* Back Side */}
        <div className="absolute inset-0 backface-hidden [transform:rotateY(180deg)]">
          <div className="rounded-[6px] p-5 flex flex-col h-full gap-4 bg-[#111111] border border-[#333333] shadow-md relative overflow-hidden">
            
            <div className="relative z-10 flex flex-col h-full">
                <div className="flex items-center justify-between mb-2">
                    <h4 className="text-[10px] font-mono uppercase tracking-widest text-[#888888]">Calculation Context</h4>
                    <div className="flex items-center gap-1.5">
                        {!isEditing && onDelete && (
                            <button
                                onClick={handleDelete}
                                disabled={isDeleting}
                                className="p-1 rounded-[4px] bg-[#2A0808] border border-[#5C1A1A] hover:border-[#FF4444] text-[#FF4444] transition-all disabled:opacity-50"
                                title="Delete KPI"
                                aria-label="Delete metric"
                            >
                                {isDeleting ? (
                                    <Activity className="h-3.5 w-3.5 animate-spin" />
                                ) : (
                                    <Trash2 className="h-3.5 w-3.5" />
                                )}
                            </button>
                        )}
                        {!isEditing && onUpdateFormula && (
                            <button 
                                onClick={(e) => { e.stopPropagation(); setIsEditing(true); }}
                                className="p-1 rounded-[4px] bg-[#000000] border border-[#333333] hover:border-[#888888] hover:text-[#EDEDED] text-[#888888] transition-colors"
                                title="Edit Formula"
                                aria-label="Edit formula"
                            >
                                <Edit3 className="h-3.5 w-3.5" />
                            </button>
                        )}
                    </div>
                </div>

                {isEditing ? (
                    <div className="flex flex-col gap-3 h-full">
                        <div className="flex-1">
                            <label className="text-[9px] font-mono text-[#888888] uppercase mb-1 block">Formula Editor</label>
                            <textarea
                                value={editFormula}
                                onChange={(e) => setEditFormula(e.target.value)}
                                onClick={(e) => e.stopPropagation()}
                                onKeyDown={(e) => e.stopPropagation()}
                                className="w-full h-20 bg-[#000000] border border-[#333333] rounded-[4px] p-2 text-[11px] font-mono text-[#EDEDED] focus:outline-none focus:border-[#EDEDED] resize-none"
                            />
                        </div>
                        <div className="flex items-center gap-2">
                            <button
                                onClick={handleSave}
                                disabled={isSaving}
                                className="flex-1 bg-[#EDEDED] text-[#000000] disabled:opacity-50 h-7 rounded-[4px] text-[10px] font-medium flex items-center justify-center gap-2 hover:bg-[#CCCCCC] transition-colors"
                                aria-label="Save changes"
                            >
                                {isSaving ? <Activity className="h-3 w-3 animate-spin" /> : <Save className="h-3 w-3" />}
                                Commit Changes
                            </button>
                            <button
                                onClick={(e) => { e.stopPropagation(); setIsEditing(false); setEditFormula(kpi.formula || ''); }}
                                className="w-7 h-7 bg-[#000000] border border-[#333333] text-[#888888] hover:text-[#EDEDED] hover:border-[#888888] rounded-[4px] flex items-center justify-center transition-colors"
                                aria-label="Cancel editing"
                            >
                                <X className="h-3.5 w-3.5" />
                            </button>
                        </div>
                    </div>
                ) : (
                    <div className="flex flex-col gap-4 overflow-y-auto pr-1">
                        <div>
                            <span className="text-[9px] font-mono text-[#888888] uppercase block mb-1">Business Meaning</span>
                            <p className="text-[12px] text-[#EDEDED] leading-relaxed">
                                {kpi.description || 'System-derived metric mapping.'}
                            </p>
                        </div>
                        <div>
                            <span className="text-[9px] font-mono text-[#888888] uppercase block mb-1">Compute Logic</span>
                            <div className="relative group/formula">
                              <code className="block bg-[#000000] border border-[#333333] p-2 rounded-[4px] text-[10px] font-mono text-[#EDEDED] break-words">
                                  {kpi.formula || 'NULL_REFERENCE'}
                              </code>
                            </div>
                        </div>
                    </div>
                )}
                
                <div className="mt-auto pt-3 flex items-center justify-between text-[9px] font-mono text-[#888888] uppercase border-t border-[#333333]">
                    <span>Format: {kpi.format || 'RAW'}</span>
                    <span>Node: {index}</span>
                </div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
