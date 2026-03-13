/**
 * Centralized formatting utilities for the ExcellentInsight dashboard.
 */

/**
 * Formats a numeric value into a human-readable string with unit scaling (K, M, B, T).
 */
export function formatValue(v: number | undefined, format?: string, unit?: string): string {
  if (v === undefined || v === null || isNaN(v)) return 'N/A';
  
  if (format === 'percentage') {
    return `${v.toLocaleString('en-US', { maximumFractionDigits: 1 })}%`;
  }
  
  const unitLower = (unit || '').toLowerCase();
  const unitHasScale = /(^|\s)(m|k|b|t|million|billion|trillion|milliard|milliards)(\s|$)/i.test(unitLower);
  
  if (format === 'currency') {
    const prefix = unitLower.includes('€') ? '€' : unitLower.includes('£') ? '£' : '$';
    const val = unitHasScale ? v : (v >= 1000 ? v / 1000 : v);
    const suffix = unitHasScale ? '' : (v >= 1000 ? 'K' : '');
    return `${prefix}${val.toLocaleString('en-US', { maximumFractionDigits: 1 })}${suffix}`;
  }

  const abs = Math.abs(v);
  const sign = v < 0 ? '-' : '';
  
  if (unitHasScale) {
     return `${sign}${abs.toLocaleString('en-US', { maximumFractionDigits: 1 })}`;
  }

  if (abs >= 1_000_000_000_000) return `${sign}${(abs / 1_000_000_000_000).toLocaleString('en-US', { maximumFractionDigits: 1 })}T`;
  if (abs >= 1_000_000_000) return `${sign}${(abs / 1_000_000_000).toLocaleString('en-US', { maximumFractionDigits: 1 })}B`;
  if (abs >= 1_000_000) return `${sign}${(abs / 1_000_000).toLocaleString('en-US', { maximumFractionDigits: 1 })}M`;
  if (abs >= 1_000) return `${sign}${(abs / 1_000).toLocaleString('en-US', { maximumFractionDigits: 1 })}K`;
  
  return v.toLocaleString('en-US', { maximumFractionDigits: 1 });
}

/**
 * Specifically formats KPI values for display on cards.
 */
export function formatKpiValue(v: number | undefined, unit?: string, format?: string): string {
  if (v === undefined || v === null || isNaN(v)) return '—';
  return formatValue(v, format, unit);
}

/**
 * Formats byte sizes into human-readable strings.
 */
export function formatBytes(bytes?: number): string {
  if (!bytes) return '0 B';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
}
