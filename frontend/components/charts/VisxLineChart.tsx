"use client"

import React, { useMemo } from 'react'
import { getSeriesColor } from '@/lib/chart-colors'
import { formatValue } from '@/lib/format'
import { Group } from '@visx/group'
import { LinePath } from '@visx/shape'
import { curveMonotoneX } from '@visx/curve'
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

interface VisxLineChartProps {
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

const defaultMargin = { top: 20, right: 30, bottom: 60, left: 60 }



export default function VisxLineChart({ 
  data, 
  width, 
  height, 
  unit,
  format,
  margin = defaultMargin,
  reference,
  referenceLabel = 'Goal',
  seriesKeys,
  onFilter 
}: VisxLineChartProps) {
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

  const {
    showTooltip,
    hideTooltip,
    tooltipData,
    tooltipLeft,
    tooltipTop,
  } = useTooltip<DataPoint & { seriesKey?: string; seriesValue?: number }>()

  const xMax = width - finalMargin.left - finalMargin.right
  const yMax = height - finalMargin.top - finalMargin.bottom

  const xScale = useMemo(
    () =>
      scaleBand<string>({
        range: [0, xMax],
        domain: data.map((d) => d.label),
        padding: 0.1,
      }),
    [xMax, data]
  )

  const yScale = useMemo(() => {
    const values: number[] = []
    if (isMultiSeries && seriesKeys) {
      data.forEach((d) => seriesKeys.forEach((k) => { const v = d[k]; if (typeof v === 'number' && !isNaN(v)) values.push(v) }))
    } else {
      data.forEach((d) => { const v = d.value; if (typeof v === 'number' && !isNaN(v)) values.push(v) })
    }
    const minValue = values.length ? Math.min(...values) : 0
    const maxValue = values.length ? Math.max(...values) : 100
    const lower = minValue < 0 ? minValue * 1.15 : 0
    const upper = maxValue * 1.15
    return scaleLinear<number>({ range: [yMax, 0], domain: [lower, upper] })
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
            numTicksColumns={data.length}
          />
          <AxisBottom
            top={yMax}
            scale={xScale}
            stroke="var(--line)"
            tickStroke="var(--line)"
            hideTicks={true}
            tickFormat={(v) => truncate(String(v), needsRotation ? 12 : 20)}
            tickLabelProps={() => ({
              fill: 'var(--muted-foreground)',
              fontSize: 9,
              fontFamily: "'Geist Mono', monospace",
              textAnchor: needsRotation ? 'end' : 'middle',
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
            <>
              {seriesKeys.map((sk, si) => (
                <LinePath
                  key={sk}
                  data={data}
                  x={(d) => (xScale(d.label) ?? 0) + xScale.bandwidth() / 2}
                  y={(d) => Number(yScale(Number(d[sk]) ?? 0) ?? 0)}
                  stroke={getSeriesColor(si)}
                  strokeWidth={2.5}
                  curve={curveMonotoneX}
                />
              ))}
              {data.map((d, i) =>
                seriesKeys.map((sk, si) => {
                  const val = Number(d[sk]) ?? 0
                  return (
                    <circle
                      key={`${i}-${sk}`}
                      cx={(xScale(d.label) ?? 0) + xScale.bandwidth() / 2}
                      cy={Number(yScale(val) ?? 0)}
                      r={4}
                      fill="white"
                      stroke={getSeriesColor(si)}
                      strokeWidth={2}
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
                      className="cursor-pointer hover:r-6 transition-all"
                    />
                  )
                })
              )}
            </>
          ) : (
            <>
              <LinePath
                data={data}
                x={(d) => (xScale(d.label) ?? 0) + xScale.bandwidth() / 2}
                y={(d) => Number(yScale(d.value ?? 0) ?? 0)}
                stroke={getSeriesColor(0)}
                strokeWidth={3}
                curve={curveMonotoneX}
              />
              {data.map((d, i) => (
                <circle
                  key={i}
                  cx={(xScale(d.label) ?? 0) + xScale.bandwidth() / 2}
                  cy={Number(yScale(d.value ?? 0) ?? 0)}
                  r={4}
                  fill="white"
                  stroke={getSeriesColor(0)}
                  strokeWidth={2}
                  onMouseMove={(event) => {
                    const point = localPoint(event) || { x: 0, y: 0 }
                    showTooltip({ tooltipData: d, tooltipTop: point.y, tooltipLeft: point.x })
                  }}
                  onMouseLeave={() => hideTooltip()}
                  onClick={() => onFilter?.(d.label)}
                  className="cursor-pointer hover:r-6 transition-all"
                />
              ))}
            </>
          )}

          {reference !== undefined && reference !== null && (
            <>
              <line
                x1={0}
                x2={xMax}
                y1={Number(yScale(reference) ?? 0)}
                y2={Number(yScale(reference) ?? 0)}
                stroke="#a3a3a3"
                strokeWidth={1.5}
                strokeDasharray="4 4"
              />
              <text
                x={xMax}
                y={Number(yScale(reference) ?? 0) - 8}
                textAnchor="end"
                fontSize={10}
                fontFamily="'Geist Mono', monospace"
                fontWeight={700}
                fill="#737373"
              >
                {referenceLabel}: {reference.toLocaleString(undefined, { maximumFractionDigits: 1 })}
              </text>
            </>
          )}
        </Group>
      </svg>
      {isMultiSeries && seriesKeys && seriesKeys.length > 0 && (
        <div className="flex flex-wrap justify-center gap-4 mt-3 pt-2 border-t border-[#333333]">
          {seriesKeys.map((sk, i) => (
            <div key={sk} className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full shrink-0" style={{ backgroundColor: getSeriesColor(i) }} />
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
          {'seriesKey' in tooltipData && tooltipData.seriesKey != null ? (
            <div className="text-sm font-black" style={{ color: getSeriesColor(seriesKeys?.indexOf(tooltipData.seriesKey) ?? 0) }}>
              {tooltipData.seriesKey}: {formatValue(tooltipData.seriesValue, format, unit)}
              {unit && !format && <span className="opacity-70 ml-1">{unit}</span>}
            </div>
          ) : (
            <div className="text-sm font-black" style={{ color: getSeriesColor(0) }}>
              {formatValue(tooltipData.value as number, format, unit)}
              {unit && !format && <span className="opacity-70 ml-1">{unit}</span>}
            </div>
          )}
        </TooltipWithBounds>
      )}
    </div>
  )
}
