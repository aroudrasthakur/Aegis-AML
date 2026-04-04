import type { RunSuspiciousTx } from "@/types/run";
import type { TransactionQueueRow } from "@/types/transaction";
import type { RiskTierConfig } from "@/utils/riskTiers";
import { resolveRiskTier, riskTierLabel } from "@/utils/riskTiers";

/** Report snippet for lens scores when DB scores row is missing (legacy fallback). */
export type ReportLensSnippet = {
  behavioral_score?: number;
  graph_score?: number;
  entity_score?: number;
  temporal_score?: number;
  offramp_score?: number;
};

/**
 * Map API ``RunSuspiciousTx`` (enriched with run_transactions + run_scores) to table rows.
 */
export function mapEnrichedSuspiciousToQueueRow(
  t: RunSuspiciousTx,
  tierConfig: RiskTierConfig | null,
  reportLensFallback?: ReportLensSnippet | null,
): TransactionQueueRow {
  const tier = resolveRiskTier(t.meta_score, tierConfig, t.risk_level);
  const hasLens =
    t.behavioral_score != null ||
    t.graph_score != null ||
    t.entity_score != null ||
    t.temporal_score != null ||
    t.offramp_score != null;

  const lensFromScores = hasLens
    ? {
        behavioral: Number(t.behavioral_score ?? 0),
        graph: Number(t.graph_score ?? 0),
        entity: Number(t.entity_score ?? 0),
        temporal: Number(t.temporal_score ?? 0),
        offramp: Number(t.offramp_score ?? 0),
      }
    : undefined;

  const lensFromReport =
    reportLensFallback &&
    (reportLensFallback.behavioral_score != null ||
      reportLensFallback.graph_score != null ||
      reportLensFallback.entity_score != null ||
      reportLensFallback.temporal_score != null ||
      reportLensFallback.offramp_score != null)
      ? {
          behavioral: Number(reportLensFallback.behavioral_score ?? 0),
          graph: Number(reportLensFallback.graph_score ?? 0),
          entity: Number(reportLensFallback.entity_score ?? 0),
          temporal: Number(reportLensFallback.temporal_score ?? 0),
          offramp: Number(reportLensFallback.offramp_score ?? 0),
        }
      : undefined;

  return {
    id: t.id,
    display_ref: `TX-${t.transaction_id.slice(0, 6)}`,
    transaction_id: t.transaction_id,
    tx_hash: t.tx_hash ?? null,
    sender_wallet: t.sender_wallet ?? "",
    receiver_wallet: t.receiver_wallet ?? "",
    amount: t.amount ?? 0,
    asset_type: t.asset_type ?? null,
    chain_id: t.chain_id ?? null,
    timestamp: t.timestamp ?? "",
    fee: t.fee ?? null,
    label: t.label ?? null,
    label_source: t.label_source ?? null,
    created_at: "",
    risk_score: t.meta_score,
    heuristics_count: t.heuristic_triggered_count ?? null,
    typology_tag:
      t.typology ?? t.heuristic_top_typology ?? (tier ? riskTierLabel(tier) : undefined),
    lens_scores: lensFromScores ?? lensFromReport,
  };
}
