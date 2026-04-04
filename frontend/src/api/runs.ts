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
