"use client"

import React, { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import dynamic from 'next/dynamic'
import {
  BarChart3,
  Calendar,
  FileText,
  Link2 as LinkIcon,
  Loader2,
  Terminal,
  ExternalLink
} from 'lucide-react'
import { motion } from 'framer-motion'
import { ParentSize } from '@visx/responsive'
import { cn } from '@/lib/utils'
import { DashboardData, Chart } from '@/types/dashboard'
import { ChartErrorBoundary } from '@/components/error-boundary/ChartErrorBoundary'
import DomainHeader from '@/components/dashboard/DomainHeader'
import KPIGrid from '@/components/dashboard/KPIGrid'
import InsightView from '@/components/dashboard/InsightView'

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

export default function SharedDashboardPage() {
  const { token } = useParams()
  const [data, setData] = useState<DashboardData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()

    async function fetchSharedDashboard() {
      try {
        // Public endpoint - no authentication required
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/shares/public/${token}`, {
          signal: controller.signal
        })

        if (!response.ok) {
          if (response.status === 404) {
            throw new Error('Shared dashboard not found or link has expired')
          }
          throw new Error('Failed to load shared dashboard')
        }

        const dashboardData = await response.json()
        setData(dashboardData)
      } catch (err: unknown) {
        const e = err as { name?: string; message?: string }
        if (e?.name === 'AbortError') return
        setError(e?.message || 'Unknown error')
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false)
        }
      }
    }

    if (token) fetchSharedDashboard()
    return () => controller.abort()
  }, [token])

  if (isLoading) {
    return (
      <div className="h-screen flex flex-col items-center justify-center gap-4 p-20 bg-[#000000]">
        <Loader2 className="h-8 w-8 animate-spin text-[#EDEDED]" />
        <span className="font-mono text-[#888888] uppercase tracking-widest text-[10px]">
          Loading shared dashboard...
        </span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="h-screen flex flex-col items-center justify-center text-center gap-6 p-20 bg-[#000000]">
        <div className="h-12 w-12 rounded-[4px] flex items-center justify-center bg-[#2A0808] border border-[#5C1A1A]">
          <FileText className="h-5 w-5 text-[#FF4444]" />
        </div>
        <div>
          <h2 className="text-[20px] font-semibold tracking-tight text-[#EDEDED] mb-2 font-mono">
            Access Denied
          </h2>
          <p className="text-[#888888] font-mono text-[12px] max-w-sm">{error}</p>
        </div>
        <Link
          href="/"
          className="flex items-center gap-2 px-4 py-2 bg-[#EDEDED] text-[#000000] text-[12px] font-medium rounded-[4px] hover:bg-[#CCCCCC] transition-colors"
        >
          <ExternalLink className="h-3.5 w-3.5" />
          Go to ExcellentInsight
        </Link>
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="min-h-screen p-6 lg:p-10 pb-32 bg-[#000000]">
      <div className="max-w-7xl mx-auto space-y-12">

        {/* ── Page Header (Shared View) ──────────────────── */}
        <motion.header
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="no-print"
        >
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-8 pb-8 border-b border-[#333333]">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <span className="flex items-center gap-1.5 px-2 py-1 rounded-[2px] bg-[#0070F3]/10 text-[#0070F3] text-[9px] font-mono uppercase tracking-widest border border-[#0070F3]/30">
                  <LinkIcon className="h-3 w-3" />
                  Shared Dashboard
                </span>
                {data.overview?.domain && (
                  <>
                    <div className="h-[2px] w-[2px] bg-[#333333]" />
                    <span className="text-[10px] font-mono uppercase tracking-wider text-[#888888]">
                      {data.overview.domain}
                    </span>
                  </>
                )}
              </div>

              <h1 className="text-[32px] font-semibold tracking-tight text-[#EDEDED] leading-tight mb-4">
                Dashboard <span className="text-[#888888]">Metrics</span>
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

            <Link
              href="/"
              className="flex items-center gap-2 h-8 px-3 rounded-[4px] bg-[#0070F3] text-white text-[11px] font-medium hover:bg-[#0060D3] transition-colors"
            >
              <ExternalLink className="h-3.5 w-3.5" />
              Create Your Own
            </Link>
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

        {/* ── Metrics (Read-only) ─────────────────────── */}
        <section>
          <div className="flex items-center gap-4 mb-6">
            <h2 className="text-[10px] font-mono uppercase tracking-widest text-[#888888] whitespace-nowrap">Node Outputs</h2>
            <div className="flex-1 h-px bg-[#333333]" />
          </div>
          <KPIGrid kpis={data.kpis || []} />
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
                    </div>

                    <div className={cn("p-5", isWide ? "h-[380px]" : "h-[320px]")}>
                      <ChartErrorBoundary>
                        {chart.data && chart.data.length > 0 ? (
                          <ParentSize>
                            {({ width, height }) => {
                              const seriesKeys = chart.series_keys
                              const commonProps = { data: chart.data, width, height, title: undefined, unit: chart.unit, format: chart.format, seriesKeys }
                              if (chart.type === 'bar') return <VisxBarChart {...commonProps} />
                              if (chart.type === 'line') return <VisxLineChart {...commonProps} />
                              if (chart.type === 'area') return <VisxAreaChart {...commonProps} />
                              if (chart.type === 'pie') return <VisxPieChart data={chart.data.map((d) => ({ label: d.label, value: Number(d.value) ?? 0 }))} width={width} height={height} title={undefined} unit={chart.unit} format={chart.format} />
                              return null
                            }}
                          </ParentSize>
                        ) : (
                          <div className="h-full flex flex-col items-center justify-center bg-[#111111] rounded-[4px] border border-dashed border-[#333333]">
                            <BarChart3 className="h-6 w-6 text-[#333333] mb-2" />
                            <p className="text-[10px] font-mono text-[#888888] uppercase tracking-widest">No data</p>
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
              <h3 className="text-[11px] font-mono text-[#888888] uppercase tracking-widest">No visualizations</h3>
            </div>
          )}
        </section>

        {/* ── Insights ─────────────────────────────────── */}
        <InsightView insights={data.insights || []} />

        {/* ── Footer Banner ────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-16 p-6 rounded-[6px] bg-gradient-to-r from-[#0070F3]/10 to-[#7928CA]/10 border border-[#0070F3]/30"
        >
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div>
              <h3 className="text-[14px] font-semibold text-[#EDEDED] mb-1">
                Want to create your own insights?
              </h3>
              <p className="text-[11px] text-[#888888] font-mono">
                Analyze your Excel files with AI-powered insights in seconds
              </p>
            </div>
            <Link
              href="/"
              className="flex items-center gap-2 px-4 py-2 bg-[#0070F3] text-white text-[12px] font-medium rounded-[4px] hover:bg-[#0060D3] transition-colors whitespace-nowrap"
            >
              <ExternalLink className="h-3.5 w-3.5" />
              Try ExcellentInsight Free
            </Link>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
