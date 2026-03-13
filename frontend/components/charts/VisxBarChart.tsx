"use client"

import React, { useMemo } from 'react'
import { getSeriesColor } from '@/lib/chart-colors'
import { formatValue } from '@/lib/format'
import { Group } from '@visx/group'
import { Bar } from '@visx/shape'
import { scaleLinear, scaleBand } from '@visx/scale'
import { AxisLeft, AxisBottom } from '@visx/axis'
import { Grid } from '@visx/grid'
import { useTooltip, TooltipWithBounds, defaultStyles } from '@visx/tooltip'
import { localPoint } from '@visx/event'

interface DataPoint {
  label: string
  value?: number
  [key: string]: string | number | undefined
}

interface VisxBarChartProps {
  data: DataPoint[]
  width: number
  height: number
  title?: string
  unit?: string
  format?: 'number' | 'percentage' | string
  margin?: { top: number; right: number; bottom: number; left: number }
  reference?: number
  referenceLabel?: string
  seriesKeys?: string[]
  onFilter?: (value: string) => void
}

const defaultMargin = { top: 20, right: 20, bottom: 60, left: 60 }



export default function VisxBarChart({ 
  data, 
  width, 
  height, 
  unit,
  format,
  margin = defaultMargin,
  reference,
  referenceLabel = 'Avg',
  seriesKeys,
  onFilter 
}: VisxBarChartProps) {
  const isMultiSeries = Boolean(seriesKeys?.length)
  // Helper for truncation
  const truncate = (str: string, max: number) => {
    return str.length > max ? str.substring(0, max) + "..." : str;
  }

  // Pre-calculate if we need rotation
  const needsRotation = useMemo(() => {
    const avgLabelLength = data.reduce((acc, current) => acc + (current.label?.length || 0), 0) / (data.length || 1);
    const bandwidth = (width - margin.left - margin.right) / (data.length || 1);
    return bandwidth < 60 || avgLabelLength > 10;
  }, [data, width, margin]);

  const finalMargin = useMemo(() => ({
    ...margin,
    bottom: needsRotation ? 85 : 60
  }), [margin, needsRotation]);

  type TooltipData = DataPoint & { seriesKey?: string; seriesValue?: number }
  const {
    showTooltip,
    hideTooltip,
    tooltipData,
    tooltipLeft,
    tooltipTop,
  } = useTooltip<TooltipData>()

  const xMax = width - finalMargin.left - finalMargin.right
  const yMax = height - finalMargin.top - finalMargin.bottom

  const xScale = useMemo(
    () =>
      scaleBand<string>({
        range: [0, xMax],
        round: true,
        domain: data.map((d) => d.label),
        padding: 0.4,
      }),
    [xMax, data]
  )

  const yScale = useMemo(() => {
    const values: number[] = []
    if (isMultiSeries && seriesKeys) {
      data.forEach((d) => {
        seriesKeys.forEach((k) => {
          const v = d[k]
          if (typeof v === 'number' && !isNaN(v)) values.push(v)
        })
      })
      // For stacked bars we need max of row totals
      const totals = data.map((d) => seriesKeys.reduce((sum, k) => sum + (Number(d[k]) || 0), 0))
      if (totals.length) values.push(...totals)
    } else {
      data.forEach((d) => { const v = d.value; if (typeof v === 'number' && !isNaN(v)) values.push(v) })
    }
    const minValue = values.length ? Math.min(...values) : 0
    const maxValue = values.length ? Math.max(...values) : 100
    const lower = minValue < 0 ? minValue * 1.15 : 0
    const upper = maxValue * 1.15
    return scaleLinear<number>({
      range: [yMax, 0],
      round: true,
      domain: [lower, upper],
    })
  }, [yMax, data, isMultiSeries, seriesKeys])


  if (width < 30) return null

  return (
    <div className="relative">
      <svg width={width} height={height}>
        <Group left={finalMargin.left} top={finalMargin.top}>
          <Grid
            xScale={xScale}
            yScale={yScale}
            width={xMax}
            height={yMax}
            stroke="var(--line)"
            strokeOpacity={0.4}
            numTicksRows={5}
            numTicksColumns={0}
          />
          <AxisBottom
            top={yMax}
            scale={xScale}
            stroke="var(--line)"
            tickStroke="var(--line)"
            hideTicks={true}
            tickFormat={(v) => truncate(String(v), needsRotation ? 15 : 20)}
            tickLabelProps={() => ({
              fill: 'var(--muted-foreground)',
              fontSize: 9,
              fontFamily: "'Geist Mono', monospace",
              textAnchor: needsRotation ? 'end' : 'middle',
              verticalAnchor: 'middle',
              angle: needsRotation ? -45 : 0,
              fontWeight: 600,
              dx: needsRotation ? -4 : 0,
              dy: needsRotation ? 4 : 0,
            })}
          />
          <AxisLeft
            scale={yScale}
            stroke="var(--line)"
            tickStroke="var(--line)"
            hideTicks={true}
            numTicks={5}
            tickFormat={(v: unknown) => formatValue(Number(v), format, unit)}
            tickLabelProps={() => ({
              fill: 'var(--muted-foreground)',
              fontSize: 9,
              fontFamily: "'Geist Mono', monospace",
              textAnchor: 'end',
              dx: -4,
              dy: 4,
              fontWeight: 600,
            })}
          />
          {isMultiSeries && seriesKeys ? (
            data.map((d, index) => {
              const barWidth = xScale.bandwidth()
              const barX = Number(xScale(d.label) ?? 0)
              let cumulative = 0
              return (
                <Group key={`stack-${d.label ?? index}`}>
                  {seriesKeys.map((sk, si) => {
                    const val = Number(d[sk]) || 0
                    const prevY = Number(yScale(cumulative) ?? 0)
                    cumulative += val
                    const currY = Number(yScale(cumulative) ?? 0)
                    const segmentHeight = Math.max(0, prevY - currY)
                    const color = getSeriesColor(si)
                    return (
                      <Bar
                        key={`${d.label}-${sk}`}
                        x={barX}
                        y={currY}
                        width={barWidth}
                        height={segmentHeight}
                        fill={color}
                        fillOpacity={0.9}
                        rx={si === 0 ? 6 : 0}
                        onMouseMove={(event) => {
                          const point = localPoint(event) || { x: 0, y: 0 }
                          showTooltip({
                            tooltipData: { ...d, seriesKey: sk, seriesValue: val },
                            tooltipTop: point.y,
                            tooltipLeft: point.x,
                          })
                        }}
                        onMouseLeave={() => hideTooltip()}
                        onClick={() => onFilter?.(d.label)}
                        className="transition-all cursor-pointer hover:opacity-80"
                      />
                    )
                  })}
                </Group>
              )
            })
          ) : (
            data.map((d, index) => {
              const barWidth = xScale.bandwidth()
              const val = d.value ?? 0
              const barHeight = yMax - Number(yScale(val) ?? 0)
              const barX = Number(xScale(d.label) ?? 0)
              const barY = yMax - barHeight
              return (
                <Bar
                  key={`bar-${d.label || 'unknown'}-${index}`}
                  x={barX}
                  y={barY}
                  width={barWidth}
                  height={barHeight}
                  fill={getSeriesColor(0)}
                  fillOpacity={0.9}
                  rx={6}
                  onMouseMove={(event) => {
                    const point = localPoint(event) || { x: 0, y: 0 }
                    showTooltip({
                      tooltipData: d,
                      tooltipTop: point.y,
                      tooltipLeft: point.x,
                    })
                  }}
                  onMouseLeave={() => hideTooltip()}
                  onClick={() => onFilter?.(d.label)}
                   className="transition-all cursor-pointer hover:opacity-75"
                />
              )
            })
          )}

          {/* Reference line */}
          {reference !== undefined && reference !== null && (
            <>
              <line
                x1={0}
                x2={xMax}
                y1={Number(yScale(reference) ?? 0)}
                y2={Number(yScale(reference) ?? 0)}
                stroke={getSeriesColor(0)}
                strokeWidth={1.5}
                strokeDasharray="4 4"
                opacity={0.8}
              />
              <text
                x={xMax - 4}
                y={Number(yScale(reference) ?? 0) - 8}
                textAnchor="end"
                fontSize={10}
                fontFamily="'Geist Mono', monospace"
                fontWeight={700}
                fill={getSeriesColor(0)}
              >
                {referenceLabel}: {reference.toLocaleString(undefined, { maximumFractionDigits: 1 })}{unit ? ` ${unit}` : ''}
              </text>
            </>
          )}
        </Group>
      </svg>
      {isMultiSeries && seriesKeys && seriesKeys.length > 0 && (
        <div className="flex flex-wrap justify-center gap-4 mt-3 pt-2 border-t border-[#333333]">
          {seriesKeys.map((sk, i) => (
            <div key={sk} className="flex items-center gap-2">
              <span
                className="w-3 h-3 rounded-full shrink-0"
                style={{ backgroundColor: getSeriesColor(i) }}
              />
              <span className="text-[11px] font-mono text-[#888888] truncate max-w-[120px]">{sk}</span>
            </div>
          ))}
        </div>
      )}
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
          {tooltipData.seriesKey != null ? (
            <div className="text-sm font-black" style={{ color: getSeriesColor(seriesKeys?.indexOf(tooltipData.seriesKey) ?? 0) }}>
              {tooltipData.seriesKey}: {formatValue(tooltipData.seriesValue, format, unit)}
              {!format && unit && <span className="text-[10px] ml-1 opacity-70">{unit}</span>}
            </div>
          ) : (
            <div className="text-sm font-black" style={{ color: getSeriesColor(0) }}>
              {formatValue(tooltipData.value as number, format, unit)}
              {!format && unit && <span className="text-[10px] ml-1 opacity-70">{unit}</span>}
            </div>
          )}
        </TooltipWithBounds>
      )}
    </div>
  )
}
