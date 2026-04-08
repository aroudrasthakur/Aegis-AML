/**
 * Centralized risk-tier mapping driven exclusively by the threshold config
 * returned from GET /runs/model/threshold.
 *
 * Tier boundaries match backend infer_pipeline.py logic:
 *   high:       meta_score >= highRiskThreshold
 *   medium:     meta_score >= decisionThreshold
 *   medium-low: meta_score >  lowRiskCeiling
 *   low:        meta_score <= lowRiskCeiling
 */

export type RiskTier = "low" | "medium-low" | "medium" | "high";
const RISK_TIER_ORDER: RiskTier[] = ["low", "medium-low", "medium", "high"];

export interface RiskTierConfig {
  lowRiskCeiling: number;
  decisionThreshold: number;
  highRiskThreshold: number;
}

export function riskTierFromScore(
  score: number,
  config: RiskTierConfig,
): RiskTier {
  if (score >= config.highRiskThreshold) return "high";
  if (score >= config.decisionThreshold) return "medium";
  if (score <= config.lowRiskCeiling) return "low";
  return "medium-low";
}

const TIER_META: Record<
  RiskTier,
  { label: string; textClass: string; barClass: string; badgeClass: string }
> = {
  high: {
    label: "High",
    textClass: "text-red-400",
    barClass: "bg-[var(--color-aegis-red)]",
    badgeClass:
      "border border-red-500/40 bg-red-950/40 text-[#ff8a9d]",
  },
  medium: {
    label: "Medium",
    textClass: "text-orange-400",
    barClass: "bg-[var(--color-aegis-amber)]",
    badgeClass:
      "border border-amber-500/30 bg-amber-950/30 text-[#fcd34d]",
  },
  "medium-low": {
    label: "Medium-Low",
    textClass: "text-yellow-400",
    barClass: "bg-[#fbbf24]",
    badgeClass:
      "border border-yellow-500/20 bg-yellow-950/20 text-[#fde68a]",
  },
  low: {
    label: "Low",
    textClass: "text-green-400",
    barClass: "bg-[var(--color-aegis-green)]",
    badgeClass:
      "border border-emerald-500/25 bg-emerald-950/25 text-[#6ee7b7]",
  },
};

export function riskTierLabel(tier: RiskTier): string {
  return TIER_META[tier].label;
}

export function riskTierTextClass(tier: RiskTier): string {
  return TIER_META[tier].textClass;
}

export function riskTierBarClass(tier: RiskTier): string {
  return TIER_META[tier].barClass;
}

export function riskTierBadgeClass(tier: RiskTier): string {
  return TIER_META[tier].badgeClass;
}

/**
 * Derive tier from a score when config is available; fall back to the
 * backend-provided risk_level string when present.
 */
export function resolveRiskTier(
  score: number | null | undefined,
  config: RiskTierConfig | null,
  backendLevel?: string | null,
): RiskTier | null {
  if (backendLevel) {
    const normalized = backendLevel.toLowerCase().trim() as RiskTier;
    if (normalized in TIER_META) return normalized;
  }
  if (score == null) return null;
  if (!config) return null;
  return riskTierFromScore(score, config);
}

export function normalizeRiskTier(level?: string | null): RiskTier | null {
  if (!level) return null;
  const normalized = level.toLowerCase().trim() as RiskTier;
  return normalized in TIER_META ? normalized : null;
}

export function riskTierRank(level?: string | null): number {
  const tier = normalizeRiskTier(level);
  if (!tier) return -1;
  return RISK_TIER_ORDER.indexOf(tier);
}

export function riskBarClassFromScore(
  score: number | null | undefined,
  config: RiskTierConfig | null,
  backendLevel?: string | null,
): string {
  const tier = resolveRiskTier(score, config, backendLevel);
  return tier ? TIER_META[tier].barClass : "bg-[#2d3748]";
}

export function riskBadgeClassFromScore(
  score: number | null | undefined,
  config: RiskTierConfig | null,
  backendLevel?: string | null,
): string {
  const tier = resolveRiskTier(score, config, backendLevel);
  return tier
    ? TIER_META[tier].badgeClass
    : "border border-[var(--color-aegis-border)] bg-[#0d1117] text-[var(--color-aegis-muted)]";
}

export function riskColorFromScore(
  score: number | undefined,
  config: RiskTierConfig | null,
): string {
  if (score === undefined || !config) return "#6b7280";
  const tier = riskTierFromScore(score, config);
  switch (tier) {
    case "high":
      return "#ef4444";
    case "medium":
      return "#f97316";
    case "medium-low":
      return "#eab308";
    case "low":
      return "#22c55e";
  }
}
