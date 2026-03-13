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
  high:   { badge: 'bg-ve-error-bg text-ve-error border-ve-error-border', dot: 'bg-ve-error' },
  medium: { badge: 'bg-ve-surface text-ve-text border-ve-border', dot: 'bg-ve-btn-primary' },
  low:    { badge: 'bg-ve-bg text-ve-muted border-ve-border-subtle', dot: 'bg-ve-muted' },
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
          <div className="rounded-[6px] p-5 flex flex-col h-full gap-4 bg-ve-surface border border-ve-border hover:border-ve-muted transition-colors relative overflow-hidden">
            
            {/* Header */}
            <div className="flex items-start justify-between gap-2 z-10">
              <p className="text-[11px] font-mono uppercase tracking-widest text-ve-muted leading-tight truncate">{kpi.label}</p>
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
              <span className={cn("font-medium tracking-tight font-mono", `${valueSize} text-ve-text`)}>
                {formattedValue}
              </span>
            </div>

            {/* Progress / Coverage */}
            {kpi.coverage !== undefined && (
              <div className="space-y-1.5 z-10">
                <div className="flex items-center justify-between">
                  <span className="text-[9px] font-mono text-ve-muted uppercase">Coverage</span>
                  <span className="text-[9px] font-mono text-ve-text">{coveragePct}%</span>
                </div>
                <div className="h-[2px] w-full bg-ve-border">
                  <div
                    className="h-full transition-all duration-700 bg-ve-btn-primary"
                    style={{ width: `${coveragePct}%` }}
                  />
                </div>
              </div>
            )}

            {/* Change footer */}
            <div className="flex items-center justify-between mt-auto pt-4 border-t border-ve-border z-10">
              {kpi.change !== undefined && kpi.change !== null ? (
                <div
                  className={cn(
                    "inline-flex items-center gap-1.5 px-2 py-0.5 rounded-[4px] text-[10px] font-mono font-medium",
                    kpi.change > 0 ? "bg-ve-surface text-ve-text border border-ve-border" : 
                    kpi.change < 0 ? "bg-ve-error-bg text-ve-error border border-ve-error-border" : 
                    "bg-ve-bg text-ve-muted border border-ve-border-subtle"
                  )}
                >
                  {kpi.change > 0 ? <TrendingUp className="h-3 w-3" /> : kpi.change < 0 ? <TrendingDown className="h-3 w-3" /> : <Minus className="h-3 w-3" />}
                  {kpi.change > 0 ? '+' : ''}{kpi.change}%
                </div>
              ) : (
                <div className="inline-flex items-center gap-1.5 text-[10px] font-mono text-ve-muted">
                  <Activity className="h-3 w-3" />
                  STABLE
                </div>
              )}
              
              <div className="flex items-center gap-2">
                 <Info className="h-3.5 w-3.5 text-ve-muted opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
            </div>

            {/* Vercel Edge corner accents */}
            <div className="absolute top-0 right-0 w-4 h-4 border-t border-r border-ve-muted opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="absolute bottom-0 left-0 w-4 h-4 border-b border-l border-ve-muted opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        </div>

        {/* Back Side */}
        <div className="absolute inset-0 backface-hidden [transform:rotateY(180deg)]">
          <div className="rounded-[6px] p-5 flex flex-col h-full gap-4 bg-ve-surface border border-ve-border shadow-md relative overflow-hidden">
            
            <div className="relative z-10 flex flex-col h-full">
                <div className="flex items-center justify-between mb-2">
                    <h4 className="text-[10px] font-mono uppercase tracking-widest text-ve-muted">Calculation Context</h4>
                    <div className="flex items-center gap-1.5">
                        {!isEditing && onDelete && (
                            <button
                                onClick={handleDelete}
                                disabled={isDeleting}
                                className="p-1 rounded-[4px] bg-ve-error-bg border border-ve-error-border hover:border-ve-error text-ve-error transition-all disabled:opacity-50"
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
                                className="p-1 rounded-[4px] bg-ve-bg border border-ve-border hover:border-ve-muted hover:text-ve-text text-ve-muted transition-colors"
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
                            <label className="text-[9px] font-mono text-ve-muted uppercase mb-1 block">Formula Editor</label>
                            <textarea
                                value={editFormula}
                                onChange={(e) => setEditFormula(e.target.value)}
                                onClick={(e) => e.stopPropagation()}
                                onKeyDown={(e) => e.stopPropagation()}
                                className="w-full h-20 bg-ve-bg border border-ve-border rounded-[4px] p-2 text-[11px] font-mono text-ve-text focus:outline-none focus:border-ve-text resize-none"
                            />
                        </div>
                        <div className="flex items-center gap-2">
                            <button
                                onClick={handleSave}
                                disabled={isSaving}
                                className="flex-1 bg-ve-btn-primary text-ve-btn-text disabled:opacity-50 h-7 rounded-[4px] text-[10px] font-medium flex items-center justify-center gap-2 hover:bg-ve-btn-hover transition-colors"
                                aria-label="Save changes"
                            >
                                {isSaving ? <Activity className="h-3 w-3 animate-spin" /> : <Save className="h-3 w-3" />}
                                Commit Changes
                            </button>
                            <button
                                onClick={(e) => { e.stopPropagation(); setIsEditing(false); setEditFormula(kpi.formula || ''); }}
                                className="w-7 h-7 bg-ve-bg border border-ve-border text-ve-muted hover:text-ve-text hover:border-ve-muted rounded-[4px] flex items-center justify-center transition-colors"
                                aria-label="Cancel editing"
                            >
                                <X className="h-3.5 w-3.5" />
                            </button>
                        </div>
                    </div>
                ) : (
                    <div className="flex flex-col gap-4 overflow-y-auto pr-1">
                        <div>
                            <span className="text-[9px] font-mono text-ve-muted uppercase block mb-1">Business Meaning</span>
                            <p className="text-[12px] text-ve-text leading-relaxed">
                                {kpi.description || 'System-derived metric mapping.'}
                            </p>
                        </div>
                        <div>
                            <span className="text-[9px] font-mono text-ve-muted uppercase block mb-1">Compute Logic</span>
                            <div className="relative group/formula">
                              <code className="block bg-ve-bg border border-ve-border p-2 rounded-[4px] text-[10px] font-mono text-ve-text break-words">
                                  {kpi.formula || 'NULL_REFERENCE'}
                              </code>
                            </div>
                        </div>
                    </div>
                )}
                
                <div className="mt-auto pt-3 flex items-center justify-between text-[9px] font-mono text-ve-muted uppercase border-t border-ve-border">
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
