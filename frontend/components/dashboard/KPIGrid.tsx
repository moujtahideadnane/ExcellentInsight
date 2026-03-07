"use client"

import React from 'react'
import { KPI } from '@/types/dashboard'
import InteractiveKPICard from './InteractiveKPICard'

interface KPIGridProps {
  kpis: KPI[]
  onUpdateKPI?: (index: number, newFormula: string) => Promise<void>
}

const priorityOrder: Record<string, number> = { high: 0, medium: 1, low: 2 }

export default function KPIGrid({ kpis, onUpdateKPI }: KPIGridProps) {
  // We MUST keep the original index because the backend update API uses it.
  // The UI sorts by priority, so the array index here doesn't match the backend array.
  const displayKpis = (kpis || []).map((kpi, originalIndex) => ({
    ...kpi,
    originalIndex
  })).sort(
    (a, b) => (priorityOrder[a.priority || 'low'] ?? 2) - (priorityOrder[b.priority || 'low'] ?? 2)
  )

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mb-8">
      {displayKpis.map((kpi) => (
        <InteractiveKPICard 
          key={`${kpi.label}-${kpi.originalIndex}`}
          kpi={kpi}
          index={kpi.originalIndex}
          onUpdateFormula={onUpdateKPI ? (formula) => onUpdateKPI(kpi.originalIndex, formula) : undefined}
        />
      ))}
    </div>
  )
}

