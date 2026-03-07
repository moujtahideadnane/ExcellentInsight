export interface KPI {
  label: string;
  value: string | number | null;
  change?: number;
  unit?: string;
  priority?: 'high' | 'medium' | 'low';
  coverage?: number;
  format: string;
  formula?: string;
  description?: string;
}

export interface ChartDataPoint {
  label: string;
  value?: number;
  [seriesKey: string]: string | number | undefined;
}

export interface Chart {
  type: 'bar' | 'line' | 'pie' | 'area';
  title: string;
  description?: string;
  unit?: string;
  sheet: string;
  x_axis: string;
  y_axis: string;
  data: ChartDataPoint[];
  x_key: string;
  y_key: string;
  series_keys?: string[];
  coverage?: number;
  format?: 'number' | 'percentage' | string;
  reference?: number;
  reference_label?: string;
}

export interface Insight {
  type: string;
  severity: 'high' | 'medium' | 'low' | 'info' | 'warning';
  text: string;
  title?: string;
}

export interface Relationship {
  from_sheet: string;
  from_col: string;
  to_sheet: string;
  to_col: string;
}

export interface Join {
  left_sheet: string;
  right_sheet: string;
  on: string;
}

export interface DashboardData {
  job_id: string;
  overview: {
    domain: string;
    summary: string;
    sheet_count: number;
    total_rows: number;
    [key: string]: unknown;
  };
  kpis: KPI[];
  charts: Chart[];
  insights: Insight[];
  relationships: Relationship[];
  joins: Join[];
  data_preview: Record<string, Record<string, unknown>[]>;
  stats?: Record<string, unknown>[];
  created_at: string;
  processing_time_ms?: number;
  schema_summary?: Record<string, unknown>;
  llm_usage?: { prompt_tokens?: number; completion_tokens?: number };
  dataset_profile?: {
    candidate_table_types: Array<{ type: string; score: number }>;
  };
}
