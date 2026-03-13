"use client"

import React, { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useJobStore } from '@/stores/job-store'
import api, { getErrorMessage } from '@/lib/api'
import KPIGrid from '@/components/dashboard/KPIGrid'
import InsightView from '@/components/dashboard/InsightView'
import DataPreview from '@/components/dashboard/DataPreview'
import DomainHeader from '@/components/dashboard/DomainHeader'
import { FileText, ArrowLeft } from 'lucide-react'
import { toast } from 'sonner'
import { DashboardData } from '@/types/dashboard'
import SkeletonKPICard from '@/components/dashboard/SkeletonKPICard'
import DashboardHeader from '@/components/dashboard/DashboardHeader'
import VisualLayer from '@/components/dashboard/VisualLayer'
import ConnectivitySection from '@/components/dashboard/ConnectivitySection'

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
      <div className="min-h-screen py-8 px-4 sm:px-6 lg:px-8 pb-32 w-full bg-ve-bg"> {/* REFACTOR: [consolidate-hex] */}
        <div className="max-w-7xl mx-auto space-y-12">
          {/* Header Skeleton */}
          <div className="pb-8 border-b border-ve-border space-y-6">
            <div className="flex items-center gap-2">
              <div className="h-3 w-20 bg-ve-surface rounded-[2px]" />
              <div className="h-3 w-24 bg-ve-surface rounded-[2px]" />
            </div>
            <div className="h-10 w-64 bg-ve-surface rounded-[4px]" />
            <div className="flex gap-4">
              <div className="h-4 w-32 bg-ve-surface rounded-[2px]" />
              <div className="h-4 w-32 bg-ve-surface rounded-[2px]" />
            </div>
          </div>

          {/* Domain Header Skeleton */}
          <div className="p-6 rounded-[6px] bg-ve-skeleton border border-ve-border space-y-4">
            <div className="h-6 w-48 bg-ve-surface rounded-[2px]" />
            <div className="h-4 w-full bg-ve-surface rounded-[2px]" />
            <div className="h-4 w-2/3 bg-ve-surface rounded-[2px]" />
          </div>

          {/* KPIs Skeleton */}
          <section>
            <div className="flex items-center gap-4 mb-6">
              <div className="h-3 w-24 bg-ve-surface rounded-[2px]" />
              <div className="flex-1 h-px bg-ve-border" />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {[1, 2, 3, 4].map(i => <SkeletonKPICard key={i} />)}
            </div>
          </section>

          {/* Charts Skeleton */}
          <section className="space-y-6">
            <div className="flex items-center gap-4">
              <div className="h-3 w-32 bg-ve-surface rounded-[2px]" />
              <div className="flex-1 h-px bg-ve-border" />
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div className="lg:col-span-2 h-[480px] bg-ve-skeleton border border-ve-border rounded-[6px]" />
              <div className="h-[420px] bg-ve-skeleton border border-ve-border rounded-[6px]" />
              <div className="h-[420px] bg-ve-skeleton border border-ve-border rounded-[6px]" />
            </div>
          </section>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-center gap-6 p-20 min-h-[70vh] bg-ve-bg">
        <div className="h-12 w-12 rounded-[4px] flex items-center justify-center bg-ve-error-bg border border-ve-error-border">
          <FileText className="h-5 w-5 text-ve-error" />
        </div>
        <div>
          <h2 className="text-[20px] font-semibold tracking-tight text-ve-text mb-2 font-mono">ERR_NOT_FOUND: {error}</h2>
          <p className="text-ve-muted font-mono text-[12px] max-w-sm">Deployment configuration missing or unavailable.</p>
        </div>
        <button
          onClick={() => {
            clearActiveJob()
            router.push('/dashboard')
          }}
          className="flex items-center gap-2 px-4 py-2 bg-ve-btn-primary text-ve-btn-text text-[12px] font-medium rounded-[4px] hover:bg-ve-btn-hover transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Return
        </button>
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="min-h-screen py-8 px-4 sm:px-6 lg:px-8 pb-32 w-full bg-ve-bg">
      <div className="max-w-7xl mx-auto space-y-12">

        {/* ── Page Header ─────────────────────────────── */}
        <DashboardHeader data={data} jobId={jobId as string} />

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
            <h2 className="text-[10px] font-mono uppercase tracking-widest text-ve-muted whitespace-nowrap">Node Outputs</h2>
            <div className="flex-1 h-px bg-ve-border" />
          </div>
          <KPIGrid kpis={data.kpis || []} onUpdateKPI={handleUpdateKPI} onDeleteKPI={handleDeleteKPI} />
        </section>

        {/* ── Visualizations ───────────────────────────── */}
        <VisualLayer charts={data.charts || []} onFilter={handleFilter} />

        {/* ── Logic & Observations ─────────────────────── */}
        <InsightView insights={data.insights || []} />

        {/* ── Connectivity ────────────────────────────── */}
        <ConnectivitySection relationships={data.relationships} joins={data.joins} />

        {/* ── Preview ─────────────────────────────────── */}
        {data.data_preview && (
          <section className="no-print mt-12" id="data-preview-section">
            <div className="flex items-center gap-4 mb-6">
              <h2 className="text-[10px] font-mono uppercase tracking-[0.2em] text-ve-muted whitespace-nowrap">Source Buffer Output</h2>
              <div className="flex-1 h-px bg-ve-border" />
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
