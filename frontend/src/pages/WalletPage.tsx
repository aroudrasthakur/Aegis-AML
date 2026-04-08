import { useEffect, useMemo, useState } from "react";
import { Loader2, Wallet as WalletIcon, Network } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import { useWallet } from "@/hooks/useWallet";
import WalletDetailPanel from "@/components/WalletDetailPanel";
import FlowTimeline from "@/components/FlowTimeline";
import ExplanationPanel from "@/components/ExplanationPanel";
import RunSelectorDropdown from "@/components/RunSelectorDropdown";
import { useRunContext } from "@/contexts/useRunContext";
import { useThresholds } from "@/contexts/ThresholdProvider";
import { fetchRunWallets, fetchRunSuspicious, fetchRunScores, type RunWallet } from "@/api/runs";
import type { ExplanationDetail } from "@/types/explanation";
import {
  resolveRiskTier,
  riskTierLabel,
  riskBadgeClassFromScore,
  riskTierRank,
} from "@/utils/riskTiers";

function WalletListView() {
  const { runs } = useRunContext();
  const { config: tierConfig } = useThresholds();
  const navigate = useNavigate();

  const completedRuns = useMemo(
    () => runs.filter((r) => r.status === "completed"),
    [runs],
  );
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [wallets, setWallets] = useState<RunWallet[]>([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const pageSize = 25;

  useEffect(() => {
    if (!selectedRunId && completedRuns.length > 0) {
      setSelectedRunId(completedRuns[0].id);
    }
  }, [completedRuns, selectedRunId]);

  useEffect(() => {
    if (!selectedRunId) {
      setWallets([]);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setPage(1);
    (async () => {
      try {
        const data = await fetchRunWallets(selectedRunId);
        if (!cancelled) {
          data.sort((a, b) => riskTierRank(b.risk_level) - riskTierRank(a.risk_level));
          setWallets(data);
        }
      } catch {
        if (!cancelled) setWallets([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [selectedRunId]);

  const paged = useMemo(() => {
    const start = (page - 1) * pageSize;
    return wallets.slice(start, start + pageSize);
  }, [wallets, page]);
  const totalPages = Math.max(1, Math.ceil(wallets.length / pageSize));

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl font-bold text-[#e6edf3]">Wallets</h1>
          <p className="font-data text-sm text-[var(--color-aegis-muted)]">
            Wallet-level aggregation from the selected pipeline run
          </p>
        </div>
        <RunSelectorDropdown
          runs={runs}
          selectedRunId={selectedRunId}
          onSelect={setSelectedRunId}
        />
      </div>

      {loading && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-[var(--color-aegis-border)] bg-[#0d1117] py-16">
          <Loader2 className="h-8 w-8 animate-spin text-[var(--color-aegis-green)]" aria-hidden />
          <p className="mt-3 font-data text-sm text-[var(--color-aegis-muted)]">Loading wallets…</p>
        </div>
      )}

      {!loading && wallets.length === 0 && (
        <div className="rounded-xl border border-[var(--color-aegis-border)] bg-[#0d1117] px-6 py-12 text-center">
          <p className="font-data text-sm text-[#9aa7b8]">
            No wallet data for this run. Run a pipeline to populate wallet aggregations.
          </p>
        </div>
      )}

      {!loading && wallets.length > 0 && (
        <>
          <div className="overflow-hidden rounded-xl border border-[var(--color-aegis-border)] bg-[#0d1117] text-[#e6edf3]">
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b border-[var(--color-aegis-border)] bg-[#060810]/80 text-left">
                    <th className="px-4 py-3 font-data text-[11px] font-medium uppercase tracking-wide text-[var(--color-aegis-muted)]">Wallet</th>
                    <th className="px-4 py-3 font-data text-[11px] font-medium uppercase tracking-wide text-[var(--color-aegis-muted)]">Risk Level</th>
                    <th className="px-4 py-3 font-data text-[11px] font-medium uppercase tracking-wide text-[var(--color-aegis-muted)]">Suspicious TXs</th>
                    <th className="px-4 py-3 font-data text-[11px] font-medium uppercase tracking-wide text-[var(--color-aegis-muted)]">Clusters</th>
                    <th className="px-4 py-3 font-data text-[11px] font-medium uppercase tracking-wide text-[var(--color-aegis-muted)]">Top Heuristic</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--color-aegis-border)] font-data text-xs text-[#c8d4e0]">
                  {paged.map((w) => {
                    const tier = resolveRiskTier(w.risk_score, tierConfig, w.risk_level);
                    return (
                      <tr
                        key={w.wallet_address}
                        className="cursor-pointer hover:bg-[#060810]/90"
                        onClick={() => navigate(`/dashboard/wallets/${encodeURIComponent(w.wallet_address)}`)}
                      >
                        <td className="px-4 py-3 font-mono text-[11px] text-[#e6edf3]">
                          {w.wallet_address.length > 16
                            ? `${w.wallet_address.slice(0, 8)}…${w.wallet_address.slice(-6)}`
                            : w.wallet_address}
                        </td>
                        <td className="px-4 py-3">
                          <span className={`inline-flex rounded-full px-2.5 py-0.5 text-[10px] font-medium ${riskBadgeClassFromScore(w.risk_score, tierConfig, w.risk_level)}`}>
                            {tier ? riskTierLabel(tier) : w.risk_level}
                          </span>
                        </td>
                        <td className="px-4 py-3 tabular-nums">{w.suspicious_tx_count}</td>
                        <td className="px-4 py-3 tabular-nums">{w.cluster_count}</td>
                        <td className="px-4 py-3">
                          <span className="rounded-full border border-[var(--color-aegis-border)] bg-[#060810] px-2.5 py-0.5 text-[10px] text-[#a5b4c8]">
                            {w.top_heuristic ?? "—"}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
          <div className="flex flex-wrap items-center justify-between gap-3 font-data text-xs text-[var(--color-aegis-muted)]">
            <span>Page {page} / {totalPages} · {wallets.length} wallets</span>
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
    </div>
  );
}

function WalletDetailView({ address }: { address: string }) {
  const { wallet, loading: wLoading, error } = useWallet(address);
  const { runs } = useRunContext();

  const completedRuns = useMemo(
    () => runs.filter((r) => r.status === "completed"),
    [runs]
  );
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedRunId && completedRuns.length > 0) {
      setSelectedRunId(completedRuns[0].id);
    }
  }, [completedRuns, selectedRunId]);

  const [walletTxs, setWalletTxs] = useState<any[]>([]);
  const [explanation, setExplanation] = useState<ExplanationDetail | null>(null);
  const [uniqueHeuristics, setUniqueHeuristics] = useState<number[]>([]);
  const [walletScore, setWalletScore] = useState<any>(null);
  const [loadingContext, setLoadingContext] = useState(false);

  useEffect(() => {
    if (!wallet || !selectedRunId) return;
    let cancelled = false;
    setLoadingContext(true);
    (async () => {
      try {
        const [sus, scores] = await Promise.all([
          fetchRunSuspicious(selectedRunId),
          fetchRunScores(selectedRunId),
        ]);
        if (!cancelled) {
          const filtered = sus.filter(
            (t) => t.sender_wallet === address || t.receiver_wallet === address
          );
          setWalletTxs(filtered);

          const matchedScore = scores.find(
            (s: any) =>
              s.transaction_id === address ||
              s.sender_wallet === address ||
              s.receiver_wallet === address
          );
          setWalletScore(matchedScore ?? null);
          const summary = matchedScore?.explanation_summary as string | null | undefined;
          setExplanation(summary ? { summary } : null);

          // We use heuristic_triggered instead of rebuilding logic. It is array of IDs.
          const heuristics = filtered.flatMap((t: any) => t.heuristic_triggered || []);
          setUniqueHeuristics([...new Set(heuristics)]);
        }
      } catch (e) {
        console.error(e);
      } finally {
        if (!cancelled) setLoadingContext(false);
      }
    })();
    return () => { cancelled = true; };
  }, [wallet, selectedRunId, address]);

  const loading = wLoading || loadingContext;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl font-bold text-[#e6edf3]">
            Wallet investigation
          </h1>
          <p className="font-data text-sm text-[var(--color-aegis-muted)]">
            Address, flow timeline, risk tier, heuristic badges
          </p>
        </div>
        <RunSelectorDropdown
          runs={runs}
          selectedRunId={selectedRunId}
          onSelect={setSelectedRunId}
        />
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1fr_340px]">
        <div className="min-w-0 space-y-6">
          <div className="rounded-xl border border-[var(--color-aegis-border)] bg-[#0d1117] p-5">
            <div className="mb-4 flex items-start gap-3">
              <WalletIcon className="mt-0.5 h-6 w-6 shrink-0 text-[var(--color-aegis-green)]" />
              <div>
                <h2 className="font-display text-lg font-semibold text-[#e6edf3]">Overview</h2>
                <p className="mt-1 break-all font-data text-xs text-[#9aa7b8]">{address}</p>
              </div>
            </div>

            {loading && (
              <div className="flex flex-col items-center justify-center py-12 text-[var(--color-aegis-muted)]">
                <Loader2 className="h-8 w-8 animate-spin text-[var(--color-aegis-green)]" />
                <p className="mt-3 font-data text-sm">Loading wallet…</p>
              </div>
            )}

            {!loading && error && (
              <p className="font-data text-sm text-red-400">{error.message}</p>
            )}

            {!loading && !error && !wallet && (
              <p className="font-data text-sm text-[var(--color-aegis-muted)]">Wallet not found.</p>
            )}
          </div>

          {!loading && wallet && (
            <>
              <div>
                <div className="mb-3 flex items-center gap-2">
                  <Network className="h-5 w-5 text-[var(--color-aegis-purple)]" aria-hidden />
                  <h2 className="font-display text-base font-semibold text-[#e6edf3]">
                    Transaction history
                  </h2>
                </div>
                <FlowTimeline transactions={walletTxs} />
              </div>
              <ExplanationPanel transactionId={address} explanation={explanation} />
            </>
          )}
        </div>

        <div className="min-w-0 xl:max-w-[340px]">
          {loading && (
            <div className="flex min-h-[200px] items-center justify-center rounded-xl border border-[var(--color-aegis-border)] bg-[#0d1117] p-6">
              <Loader2 className="h-8 w-8 animate-spin text-[var(--color-aegis-green)]" />
            </div>
          )}
          {!loading && error && (
            <div className="rounded-xl border border-red-500/30 bg-red-950/20 p-4 font-data text-sm text-red-300">
              {error.message}
            </div>
          )}
          {!loading && !error && wallet && (
            <WalletDetailPanel
              wallet={wallet}
              score={walletScore}
              triggeredHeuristicIds={uniqueHeuristics}
              heuristicExplanations={{}}
            />
          )}
        </div>
      </div>
    </div>
  );
}

export default function WalletPage() {
  const { address } = useParams<{ address: string }>();

  if (address) {
    return <WalletDetailView address={address} />;
  }

  return <WalletListView />;
}
