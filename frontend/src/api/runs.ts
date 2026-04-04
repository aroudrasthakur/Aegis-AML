import client from "./client";
import type {
  PipelineRun,
  RunCluster,
  RunSuspiciousTx,
  RunReport,
  RunGraphSnapshot,
} from "@/types/run";

export async function createRun(
  files: File[],
  label?: string,
): Promise<{ run_id: string; status: string; total_files: number }> {
  const form = new FormData();
  files.forEach((f) => form.append("files", f));
  if (label) form.append("label", label);
  const { data } = await client.post("/runs", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function startRun(
  runId: string,
): Promise<{ run_id: string; status: string }> {
  const { data } = await client.post(`/runs/${runId}/start`);
  return data;
}

export async function fetchRuns(
  page = 1,
  limit = 50,
): Promise<{ runs: PipelineRun[]; total: number }> {
  const { data } = await client.get("/runs", { params: { page, limit } });
  return data;
}

export async function fetchRun(runId: string): Promise<PipelineRun> {
  const { data } = await client.get(`/runs/${runId}`);
  return data;
}

export async function fetchRunReport(runId: string): Promise<RunReport> {
  const { data } = await client.get(`/runs/${runId}/report`);
  return data;
}

export async function fetchRunSuspicious(
  runId: string,
): Promise<RunSuspiciousTx[]> {
  const { data } = await client.get(`/runs/${runId}/suspicious`);
  return data;
}

export async function fetchRunClusters(
  runId: string,
): Promise<RunCluster[]> {
  const { data } = await client.get(`/runs/${runId}/clusters`);
  return data;
}

export async function fetchClusterGraph(
  runId: string,
  clusterId: string,
): Promise<RunGraphSnapshot> {
  const { data } = await client.get(
    `/runs/${runId}/clusters/${clusterId}/graph`,
  );
  return data;
}

export async function fetchClusterMembers(
  runId: string,
  clusterId: string,
): Promise<{ id: string; cluster_id: string; wallet_address: string }[]> {
  const { data } = await client.get(
    `/runs/${runId}/clusters/${clusterId}/members`,
  );
  return data;
}

export interface DashboardStats {
  total_runs: number;
  completed_runs: number;
  total_txns_scored: number;
  total_suspicious: number;
  total_clusters: number;
  latest_run: PipelineRun | null;
  latest_suspicious: number;
  latest_clusters: number;
  latest_txns: number;
}

export async function fetchDashboardStats(): Promise<DashboardStats> {
  const { data } = await client.get("/runs/dashboard/stats");
  return data;
}

export interface ModelMetricsResponse {
  metrics: {
    pr_auc: number;
    roc_auc: number;
    threshold: number;
    n_train: number;
    n_cal: number;
    n_test: number;
    n_features: number;
    feature_importance: Record<string, number>;
  } | null;
}

export async function fetchModelMetrics(): Promise<ModelMetricsResponse> {
  const { data } = await client.get("/runs/model/metrics");
  return data;
}

export interface ThresholdResponse {
  threshold: {
    decision_threshold: number;
    high_risk_threshold: number;
    low_risk_ceiling: number;
    optimal_threshold: number;
    optimal_f1: number;
    precision_at_threshold: number;
    recall_at_threshold: number;
    min_recall_target: number;
  } | null;
}

export async function fetchModelThreshold(): Promise<ThresholdResponse> {
  const { data } = await client.get("/runs/model/threshold");
  return data;
}
