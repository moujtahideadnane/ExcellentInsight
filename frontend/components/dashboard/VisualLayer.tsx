"use client"

import React from 'react'
import dynamic from 'next/dynamic'
import { motion } from 'framer-motion'
import { BarChart3, Link2, Loader2 } from 'lucide-react'
import { ParentSize } from '@visx/responsive'
import { cn } from '@/lib/utils'
import { Chart } from '@/types/dashboard'
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
      <Loader2 className="h-6 w-6 animate-spin text-ve-muted" />
    </div>
  )
}

const CHART_TYPE_LABEL: Record<string, string> = {
  line: 'Trend line',
  bar: 'Columns',
  area: 'Density',
  pie: 'Composition',
}

interface VisualLayerProps {
  charts: Chart[]
  onFilter: (sheet: string, column: string, value: string) => void
}

export default function VisualLayer({ charts = [], onFilter }: VisualLayerProps) {
  return (
    <section className="space-y-6">
      <div className="flex items-center gap-4">
        <h2 className="text-[10px] font-mono uppercase tracking-widest text-ve-muted whitespace-nowrap">Virtualization Layer</h2>
        <div className="flex-1 h-px bg-ve-border" />
        <span className="text-[9px] font-mono text-ve-muted uppercase tracking-widest">{charts.length} Engines</span>
      </div>

      {charts.length > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {charts.map((chart, index) => {
            const isWide = index === 0 || chart.type === 'line' || chart.type === 'area'
            return (
              <motion.div
                key={`chart-${index}`}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className={cn(
                  "bg-ve-bg border border-ve-border rounded-[6px] overflow-hidden group hover:border-ve-muted transition-colors",
                  isWide && "lg:col-span-2"
                )}
              >
                <div className="flex items-start justify-between p-5 border-b border-ve-border">
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="px-1.5 py-0.5 rounded-[2px] bg-ve-surface border border-ve-border text-[9px] font-mono text-ve-muted uppercase tracking-wider">
                        {CHART_TYPE_LABEL[chart.type] ?? chart.type}
                      </span>
                      {chart.sheet?.includes('+') && (
                        <span className="flex items-center gap-1 px-1.5 py-0.5 rounded-[2px] bg-ve-blue-muted text-ve-blue border border-ve-blue-border text-[9px] font-mono uppercase tracking-wider">
                          <Link2 className="h-2.5 w-2.5" />
                          Join
                        </span>
                      )}
                    </div>
                    <h3 className="text-[15px] font-medium tracking-tight text-ve-text">
                      {chart.title}
                    </h3>
                    {chart.description && (
                      <p className="text-[12px] font-mono text-ve-muted mt-1 max-w-xl">
                        {chart.description}
                      </p>
                    )}
                  </div>
                  
                  {chart.coverage !== undefined && (
                    <div className="flex flex-col items-end gap-1.5 pt-1">
                      <span className="text-[9px] font-mono text-ve-muted uppercase tracking-widest leading-none">Integrity</span>
                      <div className="flex items-center gap-2">
                        <div className="w-12 h-1 bg-ve-border overflow-hidden">
                          <div
                            className="h-full bg-ve-blue transition-all duration-1000"
                            style={{ width: `${chart.coverage * 100}%` }}
                          />
                        </div>
                        <span className="text-[9px] font-mono text-ve-text">{Math.round(chart.coverage * 100)}%</span>
                      </div>
                    </div>
                  )}
                </div>

                <div className={cn("p-6", isWide ? "h-[380px]" : "h-[320px]")}>
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
                          const commonProps = { 
                            data: chart.data, 
                            width, 
                            height, 
                            title: undefined, 
                            unit: chart.unit, 
                            format: chart.format, 
                            reference: chart.reference, 
                            referenceLabel: chart.reference_label, 
                            seriesKeys, 
                            onFilter: (val: string) => onFilter(chart.sheet, chart.x_axis, val) 
                          }
                          if (chart.type === 'bar') return <VisxBarChart {...commonProps} />
                          if (chart.type === 'line') return <VisxLineChart {...commonProps} />
                          if (chart.type === 'area') return <VisxAreaChart {...commonProps} />
                          if (chart.type === 'pie') return <VisxPieChart data={chart.data.map((d) => ({ label: d.label, value: Number(d.value) ?? 0 }))} width={width} height={height} title={undefined} unit={chart.unit} format={chart.format} onFilter={(val: string) => onFilter(chart.sheet, chart.x_axis, val)} />
                          return null
                        }}
                      </ParentSize>
                    ) : (
                      <div className="h-full flex flex-col items-center justify-center bg-ve-surface rounded-[4px] border border-dashed border-ve-border">
                        <BarChart3 className="h-6 w-6 text-ve-border mb-2" />
                        <p className="text-[10px] font-mono text-ve-muted uppercase tracking-widest">Partial data available</p>
                      </div>
                    )}
                  </ChartErrorBoundary>
                </div>
              </motion.div>
            )
          })}
        </div>
      ) : (
        <div className="py-20 rounded-[6px] border border-dashed border-ve-border flex flex-col items-center justify-center text-center bg-ve-surface">
          <BarChart3 className="h-8 w-8 text-ve-border mb-4" />
          <h3 className="text-[11px] font-mono text-ve-muted uppercase tracking-widest">Visual Layer Null</h3>
          <p className="text-ve-muted text-[12px] font-mono mt-1">Insufficient data to compile visual projections.</p>
        </div>
      )}
    </section>
  )
}
