"use client"

import React, { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import dynamic from 'next/dynamic'
import { useJobStore } from '@/stores/job-store'
import api, { getErrorMessage } from '@/lib/api'
import KPIGrid from '@/components/dashboard/KPIGrid'
import InsightView from '@/components/dashboard/InsightView'
import DataPreview from '@/components/dashboard/DataPreview'
import DomainHeader from '@/components/dashboard/DomainHeader'
import ExportDropdown from '@/components/dashboard/ExportDropdown'
import ShareButton from '@/components/dashboard/ShareButton'
import {
  BarChart3,
  Calendar,
  FileText,
  ArrowLeft,
  Link2,
  Loader2,
  Terminal,
  Activity
} from 'lucide-react'
import { motion } from 'framer-motion'
import { ParentSize } from '@visx/responsive'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'
import { DashboardData, Chart, Relationship, Join } from '@/types/dashboard'
import { ChartErrorBoundary } from '@/components/error-boundary/ChartErrorBoundary'

// Lazy load heavy chart components
const VisxBarChart = dynamic(() => import('@/components/charts/VisxBarChart'), {
  loading: () => <ChartSkeleton />,
  ssr: false
})
const VisxLineChart = dynamic(() => import('@/components/charts/VisxLineChart'), {
  loading: () => <ChartSkeleton />,
  ssr: false
})
const VisxPieChart = dynamic(() => import('@/components/charts/VisxPieChart'), {
  loading: () => <ChartSkeleton />,
  ssr: false
})
const VisxAreaChart = dynamic(() => import('@/components/charts/VisxAreaChart'), {
  loading: () => <ChartSkeleton />,
  ssr: false
})

function ChartSkeleton() {
  return (
    <div className="h-full flex items-center justify-center">
      <Loader2 className="h-6 w-6 animate-spin text-[#888888]" />
    </div>
  )
}

const CHART_TYPE_LABEL: Record<string, string> = {
  line: 'Trend line',
  bar: 'Columns',
  area: 'Density',
  pie: 'Composition',
}

export default function DashboardDetailPage() {
  const { jobId } = useParams()
  const router = useRouter()
  const { clearActiveJob } = useJobStore()
  const [data, setData] = useState<DashboardData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeFilter, setActiveFilter] = useState<{ sheet: string, column: string, value: string } | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    async function fetchDashboard() {
      try {
        const response = await api.get(`/dashboard/${jobId}`, { signal: controller.signal })
        setData(response.data)
      } catch (err: unknown) {
        const e = err as { name?: string; code?: string }
        if (e?.name === 'AbortError' || e?.code === 'ERR_CANCELED') return
        setError(getErrorMessage(err))
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false)
        }
      }
    }
    if (jobId) fetchDashboard()
    return () => controller.abort()
  }, [jobId])

  const handleFilter = (sheet: string, column: string, value: string) => {
    if (activeFilter?.column === column && activeFilter?.value === value) {
      setActiveFilter(null)
      toast.info("Filter cleared")
    } else {
      setActiveFilter({ sheet, column, value })
      toast.success(`Filtered for "${value}"`)
      document.getElementById('data-preview-section')?.scrollIntoView({ behavior: 'smooth' })
    }
  }

  const handleUpdateKPI = async (index: number, newFormula: string) => {
    try {
      const response = await api.patch(`/dashboard/${jobId}/kpis/${index}`, { formula: newFormula })
      setData(response.data)
      toast.success("Metric updated and recalculated")
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      toast.error(axiosErr.response?.data?.detail || "Failed to update metric")
    }
  }

  const handleDeleteKPI = async (index: number) => {
    try {
      const response = await api.delete(`/dashboard/${jobId}/kpis/${index}`)
      setData(response.data)
      toast.success("KPI deleted successfully")
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      toast.error(axiosErr.response?.data?.detail || "Failed to delete KPI")
      throw err // Re-throw so the component can handle the error state
    }
  }

  useEffect(() => {
    clearActiveJob()
  }, [clearActiveJob])

  if (isLoading) {
    return (
      <div className="h-full flex flex-col items-center justify-center gap-4 p-20 min-h-[70vh] bg-[#000000]">
        <Loader2 className="h-8 w-8 animate-spin text-[#EDEDED]" />
        <span className="font-mono text-[#888888] uppercase tracking-widest text-[10px]">
          Awaiting completion...
        </span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-center gap-6 p-20 min-h-[70vh] bg-[#000000]">
        <div className="h-12 w-12 rounded-[4px] flex items-center justify-center bg-[#2A0808] border border-[#5C1A1A]">
          <FileText className="h-5 w-5 text-[#FF4444]" />
        </div>
        <div>
          <h2 className="text-[20px] font-semibold tracking-tight text-[#EDEDED] mb-2 font-mono">ERR_NOT_FOUND: {error}</h2>
          <p className="text-[#888888] font-mono text-[12px] max-w-sm">Deployment configuration missing or unavailable.</p>
        </div>
        <button
          onClick={() => {
            clearActiveJob()
            router.push('/dashboard')
          }}
          className="flex items-center gap-2 px-4 py-2 bg-[#EDEDED] text-[#000000] text-[12px] font-medium rounded-[4px] hover:bg-[#CCCCCC] transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Return
        </button>
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="min-h-screen p-6 lg:p-10 pb-32 bg-[#000000]">
      <div className="max-w-7xl mx-auto space-y-12">

        {/* ── Page Header ─────────────────────────────── */}
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
              <ShareButton jobId={jobId as string} />
              <ExportDropdown jobId={jobId as string} />
            </div>
          </div>
        </motion.header>

        {/* ── Context Analysis ────────────────────────── */}
        <DomainHeader
          domain={data.overview?.domain || 'Analytics'}
          summary={data.overview?.summary || ''}
          sheetCount={data.overview?.sheet_count}
          totalRows={data.overview?.total_rows}
          llmUsage={data.llm_usage}
        />

        {/* ── Metrics ─────────────────────────────────── */}
        <section>
          <div className="flex items-center gap-4 mb-6">
            <h2 className="text-[10px] font-mono uppercase tracking-widest text-[#888888] whitespace-nowrap">Node Outputs</h2>
            <div className="flex-1 h-px bg-[#333333]" />
          </div>
          <KPIGrid kpis={data.kpis || []} onUpdateKPI={handleUpdateKPI} onDeleteKPI={handleDeleteKPI} />
        </section>

        {/* ── Visualizations ───────────────────────────── */}
        <section className="space-y-6">
          <div className="flex items-center gap-4">
            <h2 className="text-[10px] font-mono uppercase tracking-widest text-[#888888] whitespace-nowrap">Virtualization Layer</h2>
            <div className="flex-1 h-px bg-[#333333]" />
            <span className="text-[9px] font-mono text-[#888888] uppercase tracking-widest">{data.charts?.length || 0} Engines</span>
          </div>

          {(data.charts || []).length > 0 ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {(data.charts || []).map((chart: Chart, index: number) => {
                const isWide = index === 0 || chart.type === 'line' || chart.type === 'area'
                return (
                  <motion.div
                    key={`chart-${index}`}
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className={cn(
                      "bg-[#000000] border border-[#333333] rounded-[6px] overflow-hidden group hover:border-[#888888] transition-colors",
                      isWide && "lg:col-span-2"
                    )}
                  >
                    <div className="flex items-start justify-between p-5 border-b border-[#333333]">
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <span className="px-1.5 py-0.5 rounded-[2px] bg-[#111111] border border-[#333333] text-[9px] font-mono text-[#888888] uppercase tracking-wider">
                            {CHART_TYPE_LABEL[chart.type] ?? chart.type}
                          </span>
                          {chart.sheet?.includes('+') && (
                            <span className="flex items-center gap-1 px-1.5 py-0.5 rounded-[2px] bg-[#0070F3]/10 text-[#0070F3] border border-[#0070F3]/30 text-[9px] font-mono uppercase tracking-wider">
                              <Link2 className="h-2.5 w-2.5" />
                              Join
                            </span>
                          )}
                        </div>
                        <h3 className="text-[15px] font-medium tracking-tight text-[#EDEDED]">
                          {chart.title}
                        </h3>
                        {chart.description && (
                          <p className="text-[12px] font-mono text-[#888888] mt-1 max-w-xl">
                            {chart.description}
                          </p>
                        )}
                      </div>
                      
                      {chart.coverage !== undefined && (
                        <div className="flex flex-col items-end gap-1.5 pt-1">
                          <span className="text-[9px] font-mono text-[#888888] uppercase tracking-widest leading-none">Integrity</span>
                          <div className="flex items-center gap-2">
                            <div className="w-12 h-1 bg-[#333333] overflow-hidden">
                              <div
                                className="h-full bg-[#0070F3] transition-all duration-1000"
                                style={{ width: `${chart.coverage * 100}%` }}
                              />
                            </div>
                            <span className="text-[9px] font-mono text-[#EDEDED]">{Math.round(chart.coverage * 100)}%</span>
                          </div>
                        </div>
                      )}
                    </div>

                    <div className={cn("p-5", isWide ? "h-[380px]" : "h-[320px]")}>
                      <ChartErrorBoundary>
                        {chart.data && chart.data.length > 0 ? (
                          <ParentSize>
                            {({ width, height }) => {
                              const seriesKeys = chart.series_keys ?? (() => {
                                const first = chart.data[0] as Record<string, unknown>
                                if (!first) return undefined
                                const keys = Object.keys(first).filter(k => k !== 'label' && k !== 'value')
                                return keys.length > 0 ? keys : undefined
                              })()
                              const commonProps = { data: chart.data, width, height, title: undefined, unit: chart.unit, format: chart.format, reference: chart.reference, referenceLabel: chart.reference_label, seriesKeys, onFilter: (val: string) => handleFilter(chart.sheet, chart.x_axis, val) }
                              if (chart.type === 'bar') return <VisxBarChart {...commonProps} />
                              if (chart.type === 'line') return <VisxLineChart {...commonProps} />
                              if (chart.type === 'area') return <VisxAreaChart {...commonProps} />
                              if (chart.type === 'pie') return <VisxPieChart data={chart.data.map((d) => ({ label: d.label, value: Number(d.value) ?? 0 }))} width={width} height={height} title={undefined} unit={chart.unit} format={chart.format} onFilter={(val: string) => handleFilter(chart.sheet, chart.x_axis, val)} />
                              return null
                            }}
                          </ParentSize>
                        ) : (
                          <div className="h-full flex flex-col items-center justify-center bg-[#111111] rounded-[4px] border border-dashed border-[#333333]">
                            <BarChart3 className="h-6 w-6 text-[#333333] mb-2" />
                            <p className="text-[10px] font-mono text-[#888888] uppercase tracking-widest">Partial data available</p>
                          </div>
                        )}
                      </ChartErrorBoundary>
                    </div>
                  </motion.div>
                )
              })}
            </div>
          ) : (
            <div className="py-20 rounded-[6px] border border-dashed border-[#333333] flex flex-col items-center justify-center text-center bg-[#111111]">
              <BarChart3 className="h-8 w-8 text-[#333333] mb-4" />
              <h3 className="text-[11px] font-mono text-[#888888] uppercase tracking-widest">Visual Layer Null</h3>
              <p className="text-[#888888] text-[12px] font-mono mt-1">Insufficient data to compile visual projections.</p>
            </div>
          )}
        </section>

        {/* ── Logic & Observations ─────────────────────── */}
        <InsightView insights={data.insights || []} />

        {/* ── Connectivity ────────────────────────────── */}
        {((data.relationships || []).length > 0 || (data.joins || []).length > 0) && (
          <section className="no-print mt-12">
            <div className="flex items-center gap-4 mb-6">
              <h2 className="text-[10px] font-mono uppercase tracking-widest text-[#888888] whitespace-nowrap">Schema Dependencies</h2>
              <div className="flex-1 h-px bg-[#333333]" />
            </div>
            <div className="flex flex-wrap gap-3">
              {(data.relationships || []).map((rel: Relationship, idx: number) => (
                <div key={`rel-${idx}`} className="flex items-center gap-4 px-4 py-3 rounded-[4px] bg-[#000000] border border-[#333333] hover:border-[#888888] transition-colors">
                  <div className="text-right">
                    <div className="text-[9px] font-mono text-[#888888] uppercase tracking-widest mb-0.5">{rel.from_sheet}</div>
                    <div className="text-[12px] font-mono text-[#EDEDED]">{rel.from_col}</div>
                  </div>
                  <div className="flex items-center gap-1 text-[#333333]">
                    <div className="h-px w-4 bg-current" />
                    <div className="h-1.5 w-1.5 rounded-[1px] bg-[#EDEDED]" />
                    <div className="h-px w-4 bg-current" />
                  </div>
                  <div>
                    <div className="text-[9px] font-mono text-[#888888] uppercase tracking-widest mb-0.5">{rel.to_sheet}</div>
                    <div className="text-[12px] font-mono text-[#EDEDED]">{rel.to_col}</div>
                  </div>
                </div>
              ))}
              {(data.joins || []).map((join: Join, idx: number) => (
                <div key={`join-${idx}`} className="flex items-center gap-3 px-4 py-3 rounded-[4px] bg-[#111111] border border-[#0070F3]/30 border-dashed">
                  <Link2 className="h-3.5 w-3.5 text-[#0070F3]" />
                  <div>
                    <div className="text-[9px] font-mono text-[#0070F3] uppercase tracking-widest mb-0.5">Runtime Link</div>
                    <div className="text-[12px] font-mono text-[#EDEDED]">{join.left_sheet} × {join.right_sheet}</div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* ── Preview ─────────────────────────────────── */}
        {data.data_preview && (
          <section className="no-print mt-12" id="data-preview-section">
            <div className="flex items-center gap-4 mb-6">
              <h2 className="text-[10px] font-mono uppercase tracking-[0.2em] text-[#888888] whitespace-nowrap">Source Buffer Output</h2>
              <div className="flex-1 h-px bg-[#333333]" />
            </div>
            <DataPreview
              data={data.data_preview}
              stats={data.stats}
              jobId={jobId as string}
              activeFilter={activeFilter}
              onClearFilter={() => setActiveFilter(null)}
            />
          </section>
        )}
      </div>
    </div>
  )
}
