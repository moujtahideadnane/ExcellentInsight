"use client"

import React from 'react'
import { Table, Database, Filter, X, BarChart3, Terminal } from 'lucide-react'
import { cn } from '@/lib/utils'
import api from '@/lib/api'
import { toast } from 'sonner'
import { motion, AnimatePresence } from 'framer-motion'

interface SheetStatColumn {
  name?: string
  type?: string
  null_count?: number
  unique_count?: number
  mean?: number | null
}

interface SheetStat {
  name?: string
  row_count?: number
  columns?: SheetStatColumn[]
  [key: string]: unknown
}

interface DataPreviewProps {
  data: Record<string, Record<string, unknown>[]>
  stats?: SheetStat[]
  jobId?: string
  activeFilter?: { sheet: string, column: string, value: string } | null
  onClearFilter?: () => void
}

export default function DataPreview({ data, stats, jobId, activeFilter, onClearFilter }: DataPreviewProps) {
  const [activeSheet, setActiveSheet] = React.useState<string | null>(null)
  const [viewMode, setViewMode] = React.useState<'raw' | 'stats'>('raw')
  const [filteredRows, setFilteredRows] = React.useState<Record<string, unknown>[] | null>(null)
  const [isFiltering, setIsFiltering] = React.useState(false)

  React.useEffect(() => {
    if (data && Object.keys(data).length > 0 && !activeSheet) {
      const firstKey = Object.keys(data)[0]
      if (firstKey) setActiveSheet(firstKey)
    }
  }, [data, activeSheet])

  React.useEffect(() => {
    async function fetchDrillDown() {
      if (!jobId || !activeFilter) {
        setFilteredRows(null)
        return
      }

      setIsFiltering(true)
      try {
        const res = await api.get(`/dashboard/${jobId}/drill-down`, {
          params: {
            sheet: activeFilter.sheet,
            column: activeFilter.column,
            value: activeFilter.value
          }
        })
        setFilteredRows(res.data)
        setActiveSheet(activeFilter.sheet)
      } catch {
        toast.error("Drill-down pipeline failed")
        setFilteredRows(null)
      } finally {
        setIsFiltering(false)
      }
    }

    fetchDrillDown()
  }, [activeFilter, jobId])

  if (!data || Object.keys(data).length === 0) return null

  const sheets = Object.keys(data)
  const currentRows = activeSheet ? (data[activeSheet] || []) : []
  const rowSource = Array.isArray(filteredRows) ? filteredRows : currentRows
  const firstRow = rowSource[0]
  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  const columns = firstRow ? Object.keys(firstRow) : (activeSheet && data[activeSheet]?.[0] ? Object.keys(data[activeSheet][0]!) : [])
  const currentSheetStats = Array.isArray(stats) ? stats.find((s: SheetStat) => s.name === activeSheet) : null

  return (
    <div className="bg-[#111111] rounded-[6px] overflow-hidden border border-[#333333]">
      {/* ── Control Center ────────────────────────────── */}
      <div className="p-6 border-b border-[#333333] bg-[#000000]">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 mb-6">
          <div className="flex items-center gap-4">
            <div className="h-10 w-10 rounded-[4px] flex items-center justify-center bg-[#111111] border border-[#333333]">
              <Database className="h-5 w-5 text-[#EDEDED]" />
            </div>
            <div>
              <h3 className="text-[18px] font-semibold tracking-tight text-[#EDEDED]">Buffer Explorer</h3>
              <p className="text-[12px] font-mono text-[#888888] mt-1">
                {activeFilter ? "Inspecting transient drill-down" : "Raw memory block inspection"}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-1.5 p-1 rounded-[4px] bg-[#111111] border border-[#333333]">
            {[
              { id: 'raw',   label: 'Raw Output', icon: Table },
              { id: 'stats', label: 'Schema',     icon: BarChart3 }
            ].map((btn) => (
              <button
                key={btn.id}
                onClick={() => setViewMode(btn.id as 'raw' | 'stats')}
                disabled={btn.id === 'stats' && !currentSheetStats}
                className={cn(
                  "px-3 py-1.5 rounded-[4px] text-[11px] font-mono uppercase tracking-wider transition-colors flex items-center gap-2",
                  viewMode === btn.id 
                    ? "bg-[#EDEDED] text-[#000000]" 
                    : "text-[#888888] hover:text-[#EDEDED] hover:bg-[#222222] disabled:opacity-30 disabled:cursor-not-allowed"
                )}
              >
                <btn.icon className="h-3.5 w-3.5" />
                {btn.label}
              </button>
            ))}
          </div>
        </div>

        {/* Dynamic Filter Badge */}
        <AnimatePresence>
          {activeFilter && (
            <motion.div 
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              className="flex items-center gap-3 px-3 py-2 rounded-[4px] mb-6 w-fit bg-[#2A0808] border border-[#5C1A1A]"
            >
              <Filter className="h-3 w-3 text-[#FF4444]" />
              <div className="h-4 w-px bg-[#5C1A1A] mx-1" />
              <span className="text-[10px] font-mono uppercase tracking-widest text-[#FF4444]">Filter</span>
              <span className="text-[12px] font-mono text-[#EDEDED]">{activeFilter.column}: {activeFilter.value}</span>
              <button 
                onClick={onClearFilter}
                className="ml-2 h-5 w-5 rounded-[2px] flex items-center justify-center transition-colors hover:bg-[#5C1A1A] text-[#FF4444]"
              >
                <X className="h-3 w-3" />
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Tab Selection */}
        <div className="flex flex-wrap gap-2">
          {sheets.map((sheet) => (
            <button
              key={sheet}
              onClick={() => setActiveSheet(sheet)}
              className={cn(
                "px-3 py-1.5 rounded-[4px] text-[11px] font-mono uppercase tracking-widest transition-colors outline-none",
                activeSheet === sheet 
                  ? "bg-[#EDEDED] text-[#000000] border border-[#EDEDED]" 
                  : "bg-[#111111] text-[#888888] border border-[#333333] hover:border-[#888888] hover:text-[#EDEDED]"
              )}
            >
              {sheet}
            </button>
          ))}
        </div>
      </div>

      {/* ── Signal Table ───────────────────────────── */}
      <div className={cn(
        "overflow-x-auto max-h-[600px] overflow-y-auto relative bg-[#000000]",
        isFiltering && "opacity-40 grayscale pointer-events-none transition-all duration-500"
      )}>
        {isFiltering && (
          <div className="absolute inset-0 z-50 flex items-center justify-center">
             <div className="h-8 w-8 border-2 border-[#333333] border-t-[#EDEDED] rounded-full animate-spin" />
          </div>
        )}

        {viewMode === 'raw' ? (
          <div className="inline-block min-w-full align-middle">
            <table className="min-w-full divide-y divide-[#333333]">
              <thead className="sticky top-0 z-20 bg-[#000000]">
                <tr>
                  {columns.map((column) => (
                    <th key={column} className="px-5 py-3 text-left text-[10px] font-mono text-[#888888] uppercase tracking-widest border-b border-[#333333]">
                      {column}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-[#111111] divide-y divide-[#222222]">
                {rowSource.map((row, i) => (
                  <tr key={i} className="hover:bg-[#222222] transition-colors group">
                    {columns.map((column) => (
                      <td key={column} className="px-5 py-3 text-[12px] font-mono text-[#888888] whitespace-nowrap group-hover:text-[#EDEDED] transition-colors">
                        {row[column]?.toString() || '-'}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
            {rowSource.length === 0 && (
              <div className="p-24 text-center">
                <Table className="h-8 w-8 mx-auto mb-4 text-[#333333]" />
                <p className="text-[10px] font-mono text-[#888888] uppercase tracking-widest">Null Output</p>
              </div>
            )}
          </div>
        ) : (
          <table className="min-w-full divide-y divide-[#333333]">
            <thead className="sticky top-0 z-20 bg-[#000000]">
              <tr>
                <th className="px-5 py-3 text-left text-[10px] font-mono text-[#888888] uppercase tracking-widest border-b border-[#333333]">Key</th>
                <th className="px-5 py-3 text-left text-[10px] font-mono text-[#888888] uppercase tracking-widest border-b border-[#333333]">Type</th>
                <th className="px-5 py-3 text-center text-[10px] font-mono text-[#888888] uppercase tracking-widest border-b border-[#333333]">Null Coef</th>
                <th className="px-5 py-3 text-center text-[10px] font-mono text-[#888888] uppercase tracking-widest border-b border-[#333333]">Cardinality</th>
                <th className="px-5 py-3 text-right text-[10px] font-mono text-[#888888] uppercase tracking-widest border-b border-[#333333]">Mean Val</th>
              </tr>
            </thead>
            <tbody className="bg-[#111111] divide-y divide-[#222222] font-mono">
              {(currentSheetStats?.columns || []).map((col: SheetStatColumn, i: number) => {
                const nullPct = Math.round(((col.null_count ?? 0) / (currentSheetStats?.row_count || 1)) * 100)
                return (
                  <tr key={i} className="hover:bg-[#222222] transition-colors group">
                    <td className="px-5 py-3 text-[12px] font-mono text-[#EDEDED] whitespace-nowrap">{col.name}</td>
                    <td className="px-5 py-3">
                      <span className="px-1.5 py-0.5 rounded-[2px] bg-[#333333] text-[#EDEDED] text-[9px] font-mono uppercase tracking-widest">
                        {col.type}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-center">
                      <div className="flex flex-col items-center gap-1.5">
                        <span className={cn(
                          "text-[10px] font-mono tracking-wider",
                          nullPct > 20 ? "text-[#FF4444]" : nullPct > 0 ? "text-[#F5A623]" : "text-[#888888]"
                        )}>
                          {nullPct}%
                        </span>
                        <div className="w-10 h-0.5 bg-[#333333] overflow-hidden">
                          <div className={cn("h-full", nullPct > 20 ? "bg-[#FF4444]" : "bg-[#888888]")} style={{ width: `${100 - nullPct}%` }} />
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-3 text-[12px] text-[#888888] text-center font-mono">{col.unique_count}</td>
                    <td className="px-5 py-3 text-[12px] font-mono text-[#EDEDED] text-right">{col.mean != null ? Number(col.mean).toLocaleString(undefined, { maximumFractionDigits: 1 }) : 'NULL'}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>
      
      {/* ── System Tag ─────────────────────────────── */}
      <div className="p-3 bg-[#000000] border-t border-[#333333] text-center flex items-center justify-center gap-3">
        <Terminal className="h-3 w-3 text-[#333333]" />
        <span className="text-[9px] text-[#888888] font-mono uppercase tracking-widest pt-0.5">Integrity verified computationally</span>
        <Terminal className="h-3 w-3 text-[#333333]" />
      </div>
    </div>
  )
}
