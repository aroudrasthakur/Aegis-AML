import type { NetworkCase } from "@/types/network";
import { formatCurrency, formatDate } from "@/utils/formatters";
import { useThresholds } from "@/contexts/ThresholdProvider";
import { resolveRiskTier, riskTierLabel } from "@/utils/riskTiers";

export interface CaseReportCardProps {
  case: NetworkCase;
}

export default function CaseReportCard({ case: networkCase }: CaseReportCardProps) {
  const { config: tierConfig } = useThresholds();
  const risk = networkCase.risk_score ?? null;
  const tier = resolveRiskTier(risk, tierConfig, null);

  const excerptSource = networkCase.explanation ?? "";
  const excerpt =
    excerptSource.length > 200
      ? `${excerptSource.slice(0, 200)}...`
      : excerptSource;

  const rangeStart = networkCase.start_time
    ? formatDate(networkCase.start_time)
    : "-";
  const rangeEnd = networkCase.end_time
    ? formatDate(networkCase.end_time)
    : "-";

  return (
    <article className="rounded-xl border border-[var(--color-aegis-border)] bg-[#0d1117] p-6 text-[#e6edf3]">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="font-display text-lg font-semibold text-[#e6edf3]">
            {networkCase.case_name}
          </h2>
          <div className="mt-2 flex flex-wrap gap-2">
            {networkCase.typology ? (
              <span className="inline-flex rounded-md border border-[var(--color-aegis-purple)]/40 bg-[#7c5cfc]/10 px-2 py-0.5 font-data text-xs font-medium text-[#c4b5fd]">
                {networkCase.typology}
              </span>
            ) : (
              <span className="font-data text-xs text-[var(--color-aegis-muted)]">
                No typology
              </span>
            )}
            {networkCase.status && (
              <span className="rounded border border-[var(--color-aegis-border)] bg-[#060810] px-2 py-0.5 font-data text-[10px] uppercase text-[#9aa7b8]">
                {networkCase.status.replace(/_/g, " ")}
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="mt-6">
        <div className="flex items-center justify-between gap-2 font-data text-sm">
          <span className="text-[var(--color-aegis-muted)]">Risk level</span>
          <span className="tabular-nums text-[#e6edf3]">
            {tier ? riskTierLabel(tier) : "Unknown"}
          </span>
        </div>
      </div>

      <dl className="mt-6 grid gap-3 font-data text-sm sm:grid-cols-2">
        <div>
          <dt className="text-[var(--color-aegis-muted)]">Total amount</dt>
          <dd className="mt-0.5 tabular-nums text-[#e6edf3]">
            {networkCase.total_amount == null
              ? "-"
              : formatCurrency(networkCase.total_amount)}
          </dd>
        </div>
        <div>
          <dt className="text-[var(--color-aegis-muted)]">Time range</dt>
          <dd className="mt-0.5 text-[#c8d4e0]">
            {rangeStart} -&gt; {rangeEnd}
          </dd>
        </div>
      </dl>

      {excerpt && (
        <p className="mt-6 font-data text-sm leading-relaxed text-[#9aa7b8]">
          {excerpt}
        </p>
      )}

      <div className="mt-6 flex flex-wrap gap-2">
        <button
          type="button"
          className="rounded-lg border border-[var(--color-aegis-border)] bg-[#060810] px-4 py-2 font-data text-sm font-medium text-[#e6edf3] hover:border-[var(--color-aegis-green)]/40"
        >
          View details
        </button>
        <button
          type="button"
          className="rounded-lg border border-[var(--color-aegis-green)]/30 bg-[#00e5a0]/10 px-4 py-2 font-data text-sm text-[var(--color-aegis-green)]"
        >
          Download report
        </button>
      </div>
    </article>
  );
}
