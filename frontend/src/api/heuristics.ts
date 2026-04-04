import client from "./client";
import type { HeuristicResult } from "@/types/heuristic";

export interface HeuristicStatsResponse {
  total_scored: number;
  most_common_top_typology: string | null;
  most_common_top_typology_count: number;
  typology_frequency: Record<string, number>;
  triggered_ids_frequency: Record<string, number>;
}

export async function fetchHeuristicStats(): Promise<HeuristicStatsResponse> {
  const { data } = await client.get<HeuristicStatsResponse>("/heuristics/stats");
  return data;
}

export async function fetchHeuristicResults(
  transactionId: string,
): Promise<HeuristicResult> {
  const { data } = await client.get<HeuristicResult>(`/heuristics/${transactionId}`);
  return data;
}
