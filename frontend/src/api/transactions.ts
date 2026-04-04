import client from "./client";
import type { Transaction, TransactionScore } from "../types/transaction";

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
}

export async function fetchTransactions(params?: {
  page?: number;
  limit?: number;
  label?: string;
  min_risk?: number;
}) {
  const { data } = await client.get<PaginatedResponse<Transaction>>("/transactions", { params });
  return data;
}

export async function fetchTransaction(id: string) {
  const { data } = await client.get<Transaction & { score: TransactionScore | null }>(`/transactions/${id}`);
  return data;
}

export async function scoreTransactions() {
  const { data } = await client.post<{ scored: number }>("/transactions/score");
  return data;
}
