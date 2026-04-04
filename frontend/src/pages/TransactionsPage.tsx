import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Eye, Loader2 } from "lucide-react";
import TransactionTable from "@/components/TransactionTable";
import RunSelectorDropdown from "@/components/RunSelectorDropdown";
import { useRunContext } from "@/contexts/useRunContext";
import { useThresholds } from "@/contexts/ThresholdProvider";
import { fetchRunSuspicious, fetchRunReport } from "@/api/runs";
import {
  resolveRiskTier,
  riskTierLabel,
} from "@/utils/riskTiers";
import type { TransactionQueueRow } from "@/types/transaction";

export default function TransactionsPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const focus = searchParams.get("focus");
  const { runs } = useRunContext();
  const { config: tierConfig } = useThresholds();

  const completedRuns = useMemo(
    () => runs.filter((r) => r.status === "completed"),
    [runs],
  );
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [rows, setRows] = useState<TransactionQueueRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [page, setPage] = useState(1);
  const pageSize = 25;

  useEffect(() => {
    if (!selectedRunId && completedRuns.length > 0) {
      setSelectedRunId(completedRuns[0].id);
    }
  }, [completedRuns, selectedRunId]);

  useEffect(() => {
    if (!selectedRunId) {
      setRows([]);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    setPage(1);

    (async () => {
      try {
        const [sus, report] = await Promise.all([
          fetchRunSuspicious(selectedRunId),
          fetchRunReport(selectedRunId).catch(() => null),
        ]);
        if (cancelled) return;
        const topTxns = report?.content?.top_suspicious_transactions ?? [];

        const mapped: TransactionQueueRow[] = sus.map((t) => {
          const detail = topTxns.find(
            (d: { transaction_id: string }) => d.transaction_id === t.transaction_id,
          );
          const tier = resolveRiskTier(t.meta_score, tierConfig, t.risk_level);
          return {
            id: t.id,
            display_ref: `TX-${t.transaction_id.slice(0, 6)}`,
            transaction_id: t.transaction_id,
            tx_hash: null,
            sender_wallet: detail?.transaction_id ? "" : "",
            receiver_wallet: "",
            amount: 0,
            asset_type: null,
            chain_id: null,
            timestamp: "",
            fee: null,
            label: null,
            label_source: null,
            created_at: "",
            risk_score: t.meta_score,
            heuristics_count: 0,
            typology_tag: t.typology ?? (tier ? riskTierLabel(tier) : undefined),
            lens_scores: detail
              ? {
                  behavioral: detail.behavioral_score,
                  graph: detail.graph_score,
                  entity: detail.entity_score,
                  temporal: detail.temporal_score,
                  offramp: detail.offramp_score,
                }
              : undefined,
          };
        });
        mapped.sort((a, b) => (b.risk_score ?? 0) - (a.risk_score ?? 0));
        setRows(mapped);
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e : new Error("Failed to load transactions"));
          setRows([]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [selectedRunId, tierConfig]);

  const paged = useMemo(() => {
    const start = (page - 1) * pageSize;
    return rows.slice(start, start + pageSize);
  }, [rows, page]);

  const totalPages = Math.max(1, Math.ceil(rows.length / pageSize));

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl font-bold text-[#e6edf3]">
            Transactions
          </h1>
          <p className="font-data text-sm text-[var(--color-aegis-muted)]">
            Suspicious transactions from the selected pipeline run
            {focus && (
              <span className="ml-2 text-[var(--color-aegis-green)]">
                · focus {focus}
              </span>
            )}
          </p>
        </div>
        <RunSelectorDropdown
          runs={runs}
          selectedRunId={selectedRunId}
          onSelect={(id) => setSelectedRunId(id)}
        />
      </div>

      {loading && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-[var(--color-aegis-border)] bg-[#0d1117] py-16">
          <Loader2
            className="h-8 w-8 animate-spin text-[var(--color-aegis-green)]"
            aria-hidden
          />
          <p className="mt-3 font-data text-sm text-[var(--color-aegis-muted)]">
            Loading transactions…
          </p>
        </div>
      )}

      {!loading && error && (
        <div className="rounded-xl border border-red-500/30 bg-red-950/20 p-4 font-data text-sm text-red-300">
          {error.message}
        </div>
      )}

      {!loading && !error && rows.length === 0 && (
        <div className="rounded-xl border border-[var(--color-aegis-border)] bg-[#0d1117] px-6 py-12 text-center">
          <p className="font-data text-sm text-[#9aa7b8]">
            No suspicious transactions found for this run.
          </p>
        </div>
      )}

      {!loading && !error && rows.length > 0 && (
        <>
          <TransactionTable
            transactions={paged}
            variant="standard"
            onSelect={(id) =>
              navigate(`/dashboard/transactions?focus=${encodeURIComponent(id)}`)
            }
          />
          <div className="flex flex-wrap items-center justify-between gap-3 font-data text-xs text-[var(--color-aegis-muted)]">
            <span>
              Page {page} / {totalPages} · {rows.length} suspicious transactions
            </span>
            <div className="flex gap-2">
              <button
                type="button"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="rounded border border-[var(--color-aegis-border)] px-3 py-1.5 text-[#e6edf3] disabled:opacity-40"
              >
                Previous
              </button>
              <button
                type="button"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                className="rounded border border-[var(--color-aegis-border)] px-3 py-1.5 text-[#e6edf3] disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}

      {!loading && !error && rows.length > 0 && (
        <p className="font-data text-[11px] text-[var(--color-aegis-muted)]">
          <Link
            className="text-[var(--color-aegis-green)] hover:underline"
            to="/dashboard/explorer"
          >
            Open Flow Explorer
          </Link>{" "}
          <Eye className="inline h-3 w-3" aria-hidden />
        </p>
      )}
    </div>
  );
}
