import { useEffect, useState } from "react";
import { X, Loader2 } from "lucide-react";
import { fetchRunScores, fetchRunSuspicious, fetchRunReport } from "@/api/runs";
import { useThresholds } from "@/contexts/ThresholdProvider";
import {
  resolveRiskTier,
  riskTierLabel,
  riskTierBadgeClass,
  riskBarClassFromScore,
} from "@/utils/riskTiers";

interface NodeInspectPanelProps {
  runId: string;
  nodeLabel: string;
  nodeType: string;
  nodeRisk: number;
  onClose: () => void;
}

interface ScoreDetail {
  transaction_id: string;
  meta_score: number | null;
  behavioral_score: number | null;
  graph_score: number | null;
  entity_score: number | null;
  temporal_score: number | null;
  offramp_score: number | null;
  explanation_summary: string | null;
}

interface SuspiciousDetail {
  transaction_id: string;
  meta_score: number;
  risk_level: string;
  typology: string | null;
}

export default function NodeInspectPanel({
  runId,
  nodeLabel,
  nodeType,
  nodeRisk,
  onClose,
}: NodeInspectPanelProps) {
  const { config: tierConfig } = useThresholds();
  const [loading, setLoading] = useState(true);
  const [scores, setScores] = useState<ScoreDetail[]>([]);
  const [suspicious, setSuspicious] = useState<SuspiciousDetail[]>([]);
  const [narrative, setNarrative] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);

    (async () => {
      try {
        const [allScores, allSus, report] = await Promise.all([
          fetchRunScores(runId),
          fetchRunSuspicious(runId),
          fetchRunReport(runId).catch(() => null),
        ]);
        if (cancelled) return;

        const addr = nodeLabel.toLowerCase();
        const relatedScores = (allScores as unknown as ScoreDetail[]).filter(
          (s) =>
            (s.transaction_id ?? "").toLowerCase().includes(addr) ||
            addr.includes((s.transaction_id ?? "").slice(0, 8).toLowerCase()),
        );
        setScores(relatedScores.slice(0, 10));

        const relatedSus = (allSus as unknown as SuspiciousDetail[]).filter(
          (s) =>
            (s.transaction_id ?? "").toLowerCase().includes(addr) ||
            addr.includes((s.transaction_id ?? "").slice(0, 8).toLowerCase()),
        );
        setSuspicious(relatedSus.slice(0, 10));

        const topTxns = report?.content?.top_suspicious_transactions ?? [];
        const match = topTxns.find((t: Record<string, unknown>) =>
          String(t.transaction_id ?? "").toLowerCase().includes(addr),
        );
        if (match) {
          setNarrative(
            `Risk: ${match.risk_level} | Typology: ${match.typology ?? "—"}`,
          );
        }
      } catch {
        /* silent */
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [runId, nodeLabel]);

  const tier = resolveRiskTier(nodeRisk, tierConfig);
  const tierLabel = tier ? riskTierLabel(tier) : "Unknown";
  const tierBadge = tier ? riskTierBadgeClass(tier) : "";

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className="flex items-center justify-between border-b border-[var(--color-aegis-border)] px-4 py-3">
        <h3 className="font-display text-sm font-semibold text-[#e6edf3]">Node details</h3>
        <button
          type="button"
          onClick={onClose}
          className="rounded p-1 text-[#9aa7b8] hover:bg-[#1e293b] hover:text-[#e6edf3]"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-4">
          <div>
            <p className="font-data text-[10px] uppercase tracking-wide text-[#6b7c90]">Address / ID</p>
            <p className="mt-0.5 break-all font-mono text-xs text-[#e6edf3]">{nodeLabel}</p>
          </div>

          <div className="flex items-center gap-3">
            <div>
              <p className="font-data text-[10px] uppercase tracking-wide text-[#6b7c90]">Type</p>
              <p className="mt-0.5 font-data text-xs text-[#c8d4e0]">{nodeType}</p>
            </div>
            <div>
              <p className="font-data text-[10px] uppercase tracking-wide text-[#6b7c90]">Risk</p>
              <div className="mt-0.5 flex items-center gap-2">
                <span className={`inline-flex rounded-full px-2 py-0.5 text-[9px] font-medium ${tierBadge}`}>
                  {tierLabel}
                </span>
              </div>
            </div>
          </div>

          <div className="h-1.5 overflow-hidden rounded-full bg-[#060810]">
            <div
              className={`h-full rounded-full ${riskBarClassFromScore(nodeRisk, tierConfig)}`}
              style={{ width: `${Math.min(100, nodeRisk * 100)}%` }}
            />
          </div>

          {loading && (
            <div className="flex items-center gap-2 py-4 text-[var(--color-aegis-muted)]">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="font-data text-xs">Loading details…</span>
            </div>
          )}

          {!loading && narrative && (
            <div className="rounded-lg border border-[var(--color-aegis-border)] bg-[#060810] p-3">
              <p className="font-data text-[10px] uppercase tracking-wide text-[#6b7c90]">Reasoning</p>
              <p className="mt-1 font-data text-xs leading-relaxed text-[#c8d4e0]">{narrative}</p>
            </div>
          )}

          {!loading && scores.length > 0 && (
            <div>
              <p className="font-data text-[10px] uppercase tracking-wide text-[#6b7c90]">
                Score breakdown ({scores.length})
              </p>
              <div className="mt-2 space-y-2">
                {scores.slice(0, 5).map((s) => (
                  <div
                    key={s.transaction_id}
                    className="rounded-lg border border-[var(--color-aegis-border)] bg-[#060810] p-2"
                  >
                    <p className="truncate font-mono text-[10px] text-[#e6edf3]">
                      {s.transaction_id}
                    </p>
                    <div className="mt-1 grid grid-cols-3 gap-1 font-data text-[9px]">
                      {[
                        { k: "Behavioral", v: s.behavioral_score },
                        { k: "Graph", v: s.graph_score },
                        { k: "Entity", v: s.entity_score },
                        { k: "Temporal", v: s.temporal_score },
                        { k: "Offramp", v: s.offramp_score },
                        { k: "Meta", v: s.meta_score },
                      ].map((lens) => (
                        <div key={lens.k}>
                          <span className="text-[#6b7c90]">{lens.k}</span>
                          <span className="ml-1 tabular-nums text-[#e6edf3]">
                            {lens.v != null ? lens.v.toFixed(2) : "—"}
                          </span>
                        </div>
                      ))}
                    </div>
                    {s.explanation_summary && (
                      <p className="mt-1 text-[9px] leading-relaxed text-[#9aa7b8]">
                        {s.explanation_summary}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {!loading && suspicious.length > 0 && (
            <div>
              <p className="font-data text-[10px] uppercase tracking-wide text-[#6b7c90]">
                Suspicious transactions ({suspicious.length})
              </p>
              <ul className="mt-2 space-y-1">
                {suspicious.slice(0, 5).map((t) => (
                  <li
                    key={t.transaction_id}
                    className="flex items-center justify-between rounded-lg border border-[var(--color-aegis-border)] bg-[#060810] px-2 py-1.5"
                  >
                    <span className="truncate font-mono text-[10px] text-[#6ee7b7]">
                      {t.transaction_id.slice(0, 16)}…
                    </span>
                    <span className="font-data text-[9px] tabular-nums text-[#f87171]">
                      {t.typology ?? t.risk_level}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {!loading && scores.length === 0 && suspicious.length === 0 && (
            <p className="font-data text-xs text-[var(--color-aegis-muted)]">
              No detailed scoring data available for this node.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

