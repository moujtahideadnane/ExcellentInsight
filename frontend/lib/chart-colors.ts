/**
 * Chart color palette — single source of truth for all multi-series charts.
 *
 * Colors are perceptually distinct and chosen to work well on both light and
 * dark backgrounds. They deliberately avoid the greens that dominate the
 * brand palette so that chart series stand out from the UI chrome.
 *
 * Usage:
 *   import { SERIES_COLORS, getSeriesColor } from '@/lib/chart-colors'
 *   const fill = getSeriesColor(seriesIndex)
 */

export const SERIES_COLORS: readonly string[] = [
  '#6366f1', // indigo
  '#f59e0b', // amber
  '#06b6d4', // cyan
  '#f43f5e', // rose
  '#8b5cf6', // violet
  '#10b981', // emerald (brand, used sparingly as 6th)
  '#fb923c', // orange
  '#3b82f6', // blue
  '#a3e635', // lime
  '#ec4899', // pink
  '#14b8a6', // teal
  '#fbbf24', // yellow
] as const

/**
 * Returns the color for a given series index, wrapping if needed.
 */
export function getSeriesColor(index: number): string {
  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  return SERIES_COLORS[index % SERIES_COLORS.length]!
}
