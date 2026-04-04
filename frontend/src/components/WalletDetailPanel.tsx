import type { Wallet, WalletScore } from "@/types/wallet";
import { formatCurrency, formatDate, formatNumber } from "@/utils/formatters";
import HeuristicBadges from "./HeuristicBadges";

export interface WalletDetailPanelProps {
  wallet: Wallet | null;
  score?: WalletScore | null;
  /** Heuristic IDs to show as badges (e.g. from last investigation) */
  triggeredHeuristicIds?: number[];
  /** Tooltip text keyed by heuristic id string */
  heuristicExplanations?: Record<string, string>;
}

function scoreBarColor(value: number): string {
  if (value >= 0.75) return "bg-[var(--color-aegis-red)]";
  if (value >= 0.5) return "bg-[var(--color-aegis-amber)]";
  if (value >= 0.25) return "bg-[#fbbf24]";
  return "bg-[var(--color-aegis-green)]";
}

function riskTier(risk: number | null): string {
  if (risk == null) return "UNSCORED";
  if (risk >= 0.75) return "CRITICAL";
  if (risk >= 0.5) return "HIGH";
  if (risk >= 0.25) return "ELEVATED";
  return "LOW";
}

function SubScoreRow({
  label,
  value,
}: {
  label: string;
  value: number | null | undefined;
}) {
  if (value == null) {
    return (
      <div className="flex items-center justify-between gap-2 font-data text-sm">
        <span className="text-[var(--color-aegis-muted)]">{label}</span>
        <span className="text-[#5c6b7f]">—</span>
      </div>
    );
  }
  const pct = Math.min(100, Math.max(0, value * 100));
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between gap-2 font-data text-sm">
        <span className="text-[#9aa7b8]">{label}</span>
        <span className="tabular-nums text-[#e6edf3]">
          {formatNumber(value, 2)}
        </span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-[#060810]">
        <div
          className={`h-full rounded-full ${scoreBarColor(value)}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export default function WalletDetailPanel({
  wallet,
  score,
  triggeredHeuristicIds = [],
  heuristicExplanations = {},
}: WalletDetailPanelProps) {
  if (!wallet) {
    return (
      <aside className="h-full rounded-xl border border-[var(--color-aegis-border)] bg-[#0d1117] p-6">
        <p className="font-data text-sm text-[var(--color-aegis-muted)]">
          Select a wallet to view details.
        </p>
      </aside>
    );
  }

  const risk = score?.risk_score ?? null;
  const riskPct = risk == null ? 0 : Math.min(100, Math.max(0, risk * 100));
  const netFlow = wallet.total_in - wallet.total_out;

  return (
    <aside className="h-full rounded-xl border border-[var(--color-aegis-border)] bg-[#0d1117] p-6">
      <h2 className="font-display text-lg font-semibold text-[#e6edf3]">Wallet</h2>
      <p className="mt-2 break-all font-data text-xs text-[#c8d4e0]">
        {wallet.wallet_address}
      </p>
      {wallet.chain_id && (
        <p className="mt-1 font-data text-[11px] text-[var(--color-aegis-muted)]">
          Chain: {wallet.chain_id}
        </p>
      )}

      <div className="mt-4 inline-flex rounded border border-[var(--color-aegis-border)] bg-[#060810] px-2 py-1 font-data text-[10px] font-medium uppercase tracking-wide text-[var(--color-aegis-amber)]">
        Risk tier · {riskTier(risk)}
      </div>

      <dl className="mt-6 space-y-3 font-data text-sm">
        <div className="flex justify-between gap-2">
          <dt className="text-[var(--color-aegis-muted)]">First seen</dt>
          <dd className="text-right text-[#e6edf3]">
            {wallet.first_seen ? formatDate(wallet.first_seen) : "—"}
          </dd>
        </div>
        <div className="flex justify-between gap-2">
          <dt className="text-[var(--color-aegis-muted)]">Last seen</dt>
          <dd className="text-right text-[#e6edf3]">
            {wallet.last_seen ? formatDate(wallet.last_seen) : "—"}
          </dd>
        </div>
        <div className="flex justify-between gap-2">
          <dt className="text-[var(--color-aegis-muted)]">Total in</dt>
          <dd className="tabular-nums text-[#e6edf3]">
            {formatCurrency(wallet.total_in)}
          </dd>
        </div>
        <div className="flex justify-between gap-2">
          <dt className="text-[var(--color-aegis-muted)]">Total out</dt>
          <dd className="tabular-nums text-[#e6edf3]">
            {formatCurrency(wallet.total_out)}
          </dd>
        </div>
        <div className="flex justify-between gap-2 border-t border-[var(--color-aegis-border)] pt-3">
          <dt className="text-[var(--color-aegis-muted)]">Net flow</dt>
          <dd className="tabular-nums text-[#e6edf3]">
            {formatCurrency(netFlow)}
          </dd>
        </div>
      </dl>

      <div className="mt-8">
        <h3 className="font-data text-xs font-medium uppercase tracking-wide text-[var(--color-aegis-muted)]">
          Risk score
        </h3>
        {risk == null ? (
          <p className="mt-2 font-data text-sm text-[var(--color-aegis-muted)]">
            No score available.
          </p>
        ) : (
          <>
            <div className="mt-2 flex items-baseline justify-between gap-2">
              <span className="font-display text-2xl font-semibold tabular-nums text-[#e6edf3]">
                {(risk * 100).toFixed(0)}%
              </span>
              <span className="font-data text-xs text-[var(--color-aegis-muted)]">0–100</span>
            </div>
            <div className="mt-2 h-2 overflow-hidden rounded-full bg-[#060810]">
              <div
                className={`h-full rounded-full ${scoreBarColor(risk)}`}
                style={{ width: `${riskPct}%` }}
              />
            </div>
          </>
        )}
      </div>

      {score && (
        <div className="mt-8 space-y-4 border-t border-[var(--color-aegis-border)] pt-6">
          <h3 className="font-data text-xs font-medium uppercase tracking-wide text-[var(--color-aegis-muted)]">
            Score breakdown
          </h3>
          <SubScoreRow label="Fan-in" value={score.fan_in_score} />
          <SubScoreRow label="Fan-out" value={score.fan_out_score} />
          <SubScoreRow label="Velocity" value={score.velocity_score} />
          <SubScoreRow label="Exposure" value={score.exposure_score} />
        </div>
      )}

      <div className="mt-8 border-t border-[var(--color-aegis-border)] pt-6">
        <h3 className="font-data text-xs font-medium uppercase tracking-wide text-[var(--color-aegis-muted)]">
          Heuristic badges
        </h3>
        <div className="mt-3">
          <HeuristicBadges
            triggeredIds={triggeredHeuristicIds}
            explanations={heuristicExplanations}
            limit={12}
          />
        </div>
      </div>
    </aside>
  );
}
