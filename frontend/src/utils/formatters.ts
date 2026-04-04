export function formatNumber(value: number, decimals = 2): string {
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

/** Model / risk scores (typically 0–1) shown with 4 decimal places on the dashboard. */
export function formatScore4(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return value.toFixed(4);
}

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(value);
}

export function formatDate(value: string): string {
  if (value == null || String(value).trim() === "") return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

import {
  resolveRiskTier,
  riskTierLabel,
  riskTierTextClass,
  type RiskTierConfig,
} from "./riskTiers";

export function formatRiskLevel(
  score: number | null,
  config?: RiskTierConfig | null,
  backendLevel?: string | null,
): { label: string; color: string } {
  const tier = resolveRiskTier(score, config ?? null, backendLevel);
  if (!tier) return { label: "Unknown", color: "text-gray-400" };
  return { label: riskTierLabel(tier), color: riskTierTextClass(tier) };
}

export function truncateAddress(address: string, chars = 6): string {
  if (address.length <= chars * 2 + 2) return address;
  return `${address.slice(0, chars)}...${address.slice(-chars)}`;
}
