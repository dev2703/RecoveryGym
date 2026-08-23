/** Shared API response types for the RecoveryGym web app. */

export interface SimState {
  ee_x?: number;
  ee_y?: number;
  object_x?: number;
  object_y?: number;
  target_x?: number;
  target_y?: number;
}

export interface RunEvent {
  event: string;
  step?: number;
  detail?: string;
}

export interface CounterfactualResult {
  model?: string;
  frame_count?: number;
  chunk_complete?: boolean;
}

export interface RunResult {
  run_id: string;
  recovery_score: number;
  recovery_plan: string[];
  events: RunEvent[];
  final_state: SimState;
  counterfactual?: CounterfactualResult;
  counterfactual_error?: string;
}

export interface BenchmarkMetrics {
  nominal_success_rate?: number;
  final_success_rate?: number;
  recovery_success_rate?: number;
  ood_recovery_success?: number;
  robustness_score?: number;
}

export interface BenchmarkResult {
  benchmark_id?: string;
  status: string;
  metrics?: BenchmarkMetrics;
  baseline_metrics?: BenchmarkMetrics;
  episodes_completed?: number;
  episodes_total?: number;
}

export interface DatasetInfo {
  dataset_path: string;
  format: string;
  summary?: {
    count: number;
    with_action_chunks: number;
    ood?: number;
  };
  hf_upload?: {
    repo_id: string;
    rows: number;
    url: string;
  };
}

export interface TrainingInfo {
  training_id: string;
  status: string;
  message?: string;
  comparison?: ComparisonResult;
}

export interface ComparisonRow {
  method: string;
  known_success_pct: number;
  ood_success_pct: number;
}

export interface ComparisonResult {
  summary_table: ComparisonRow[];
}
