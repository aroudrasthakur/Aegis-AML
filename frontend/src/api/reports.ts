import client from "./client";
import type { Report } from "../types/report";

export async function fetchReports() {
  const { data } = await client.get<Report[]>("/reports");
  return data;
}

export async function generateReport(caseId: string) {
  const { data } = await client.post<Report>(`/reports/generate/${caseId}`);
  return data;
}

export async function downloadReport(reportId: string) {
  const { data } = await client.get(`/reports/${reportId}/download`, {
    responseType: "blob",
  });
  return data;
}

export interface SarGenerationResponse {
  sar_id: string;
  report_id: string;
  case_id: string;
  download_url: string;
  status: string;
  generated_at: string;
}

export async function generateSar(reportId: string) {
  const { data } = await client.post<SarGenerationResponse>(
    `/reports/${reportId}/generate-sar`,
  );
  return data;
}

export async function downloadSar(sarId: string) {
  const { data } = await client.get(`/reports/sar/${sarId}/download`, {
    responseType: "blob",
  });
  return data;
}
