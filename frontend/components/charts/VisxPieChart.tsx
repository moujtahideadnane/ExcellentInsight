"use client"

import React, { useMemo } from 'react'
import { SERIES_COLORS } from '@/lib/chart-colors'
import { Group } from '@visx/group'
import { Pie } from '@visx/shape'
import { scaleOrdinal } from '@visx/scale'
import { useTooltip, TooltipWithBounds, defaultStyles } from '@visx/tooltip'
import { localPoint } from '@visx/event'

interface DataPoint {
  label: string
  value: number
}

interface VisxPieChartProps {
  data: DataPoint[]
  width: number
  height: number
  title?: string
  unit?: string
  format?: 'number' | 'percentage' | string
  margin?: { top: number; right: number; bottom: number; left: number }
  onFilter?: (value: string) => void
}

const defaultMargin = { top: 20, right: 20, bottom: 20, left: 20 }

export default function VisxPieChart({ 
  data, 
  width, 
  height, 
  unit,
  format,
  margin = defaultMargin,
  onFilter 
}: VisxPieChartProps) {
  const {
    showTooltip,
    hideTooltip,
    tooltipData,
    tooltipLeft,
    tooltipTop,
  } = useTooltip<DataPoint>()

  const innerWidth = width - margin.left - margin.right
  const innerHeight = height - margin.top - margin.bottom
  const radius = Math.min(innerWidth, innerHeight) / 2
  const centerY = innerHeight / 2
  const centerX = innerWidth / 2

  const colorScale = useMemo(
    () =>
      scaleOrdinal({
        domain: data.map((d) => d.label),
        range: [...SERIES_COLORS],
      }),
    [data]
  )

  const formatValue = (v: number | undefined): string => {
    if (v === undefined || v === null || isNaN(v)) return 'N/A'
    if (format === 'percentage') return `${v.toLocaleString('en-US', { maximumFractionDigits: 1 })}%`
    
    const unitLower = (unit || '').toLowerCase()
    const unitHasScale = /(^|\s)(m|k|b|t|million|billion|trillion|milliard|milliards)(\s|$)/i.test(unitLower)
    
    if (format === 'currency') {
      const prefix = unitLower.includes('€') ? '€' : unitLower.includes('£') ? '£' : '$'
      const val = unitHasScale ? v : (v >= 1000 ? v / 1000 : v)
      const suffix = unitHasScale ? '' : (v >= 1000 ? 'K' : '')
      return `${prefix}${val.toLocaleString('en-US', { maximumFractionDigits: 1 })}${suffix}`
    }

    const abs = Math.abs(v)
    const sign = v < 0 ? '-' : ''
    
    if (unitHasScale) {
       return `${sign}${abs.toLocaleString('en-US', { maximumFractionDigits: 1 })}`
    }

    if (abs >= 1_000_000_000_000) return `${sign}${(abs / 1_000_000_000_000).toLocaleString('en-US', { maximumFractionDigits: 1 })}T`
    if (abs >= 1_000_000_000) return `${sign}${(abs / 1_000_000_000).toLocaleString('en-US', { maximumFractionDigits: 1 })}B`
    if (abs >= 1_000_000) return `${sign}${(abs / 1_000_000).toLocaleString('en-US', { maximumFractionDigits: 1 })}M`
    if (abs >= 1_000) return `${sign}${(abs / 1_000).toLocaleString('en-US', { maximumFractionDigits: 1 })}K`
    return v.toLocaleString('en-US', { maximumFractionDigits: 1 })
  }

  if (width < 30) return null

  return (
    <div className="relative h-full flex items-center justify-center">
      <svg width={width} height={height}>
        <Group top={centerY + margin.top} left={centerX + margin.left}>
          <Pie
            data={data}
            pieValue={(d) => d.value}
            outerRadius={radius}
            innerRadius={radius * 0.6}
            padAngle={0.03}
          >
            {(pie) => {
              return pie.arcs.map((arc, index) => {
                const { label } = arc.data
                // centroid not currently used
                // const [centroidX, centroidY] = pie.path.centroid(arc)
                return (
                  <g key={`arc-${label}-${index}`}>
                    <path
                      d={pie.path(arc) || ''}
                      fill={colorScale(label)}
                      fillOpacity={0.9}
                      onMouseMove={(event) => {
                        const point = localPoint(event) || { x: 0, y: 0 }
                        showTooltip({
                          tooltipData: arc.data,
                          tooltipTop: point.y,
                          tooltipLeft: point.x,
                        })
                      }}
                      onMouseLeave={() => hideTooltip()}
                      onClick={() => onFilter?.(label)}
                      className="transition-all cursor-pointer hover:fill-opacity-100"
                    />
                  </g>
                )
              })
            }}
          </Pie>
        </Group>
      </svg>
      {tooltipData && (
        <TooltipWithBounds
          key={`tooltip-${tooltipData.label}`}
          top={tooltipTop}
          left={tooltipLeft}
          style={{
            ...defaultStyles,
            backgroundColor: 'var(--bg-elevated, #1C1C1C)',
            color: 'var(--text, #EDEDED)',
            border: '1px solid var(--border-subtle, #222222)',
            borderRadius: 'var(--radius, 6px)',
            padding: '12px 14px',
            boxShadow: '0 4px 24px rgba(0, 0, 0, 0.5)',
            fontFamily: "'Geist Mono', monospace",
          }}
        >
          <div className="text-[10px] uppercase tracking-widest font-extrabold mb-1 opacity-50">{tooltipData.label}</div>
            <div className="text-sm font-black" style={{ color: colorScale(tooltipData.label) }}>
            {formatValue(tooltipData.value)}
            {unit && !format && <span className="opacity-70 ml-1">{unit}</span>}
          </div>
        </TooltipWithBounds>
      )}
    </div>
  )
}
