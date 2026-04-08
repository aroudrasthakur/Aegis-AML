import { useMemo, useState, type KeyboardEvent } from "react";
import { ArrowDown, ArrowUp } from "lucide-react";
import type { TransactionQueueRow } from "@/types/transaction";
import {
  formatCurrency,
  formatDate,
  truncateAddress,
} from "@/utils/formatters";
import { useThresholds } from "@/contexts/ThresholdProvider";
import {
  resolveRiskTier,
  riskTierLabel,
  riskTierRank,
  riskBarClassFromScore,
  riskBadgeClassFromScore,
} from "@/utils/riskTiers";
import { LensDots } from "./LensDots";

export interface TransactionTableProps {
  transactions: TransactionQueueRow[];
  onSelect?: (id: string) => void;
  /** Highlights the selected row (queue UX). */
  selectedId?: string | null;
  /** Queue layout: typology + lens dots + combined id/wallet column */
  variant?: "standard" | "queue";
  /** Tighter rows/padding for dense views (e.g. paginated full-screen table). */
  compact?: boolean;
  /** No outer card border/radius (use inside a parent panel). */
  embedded?: boolean;
}

type SortKey =
  | "transaction_id"
  | "sender_wallet"
  | "receiver_wallet"
  | "amount"
  | "risk_level"
  | "heuristics_count"
  | "timestamp"
  | "typology_tag";

export default function TransactionTable({
  transactions,
  onSelect,
  selectedId = null,
  variant = "standard",
  compact = false,
  embedded = false,
}: TransactionTableProps) {
  const cellY = compact ? "py-2" : "py-3";
  const cellX = compact ? "px-3" : "px-4";
  const thClass = `font-data text-[11px] font-medium uppercase tracking-wide text-[var(--color-aegis-muted)] ${cellX} ${cellY}`;
  const { config: tierConfig } = useThresholds();
  const [sortKey, setSortKey] = useState<SortKey>(
    variant === "queue" ? "risk_level" : "timestamp",
  );
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const sorted = useMemo(() => {
    const dir = sortDir === "asc" ? 1 : -1;
    return [...transactions].sort((a, b) => {
      if (sortKey === "risk_level") {
        const aTier = resolveRiskTier(a.risk_score ?? null, tierConfig, a.risk_level);
        const bTier = resolveRiskTier(b.risk_score ?? null, tierConfig, b.risk_level);
        return (riskTierRank(aTier) - riskTierRank(bTier)) * dir;
      }

      const av = a[sortKey];
      const bv = b[sortKey];
      if (av == null && bv == null) return 0;
      if (av == null) return 1;
      if (bv == null) return -1;
      if (typeof av === "number" && typeof bv === "number") {
        return (av - bv) * dir;
      }
      return String(av).localeCompare(String(bv)) * dir;
    });
  }, [transactions, sortKey, sortDir, tierConfig]);

  function toggleSort(key: SortKey) {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir(key === "timestamp" || key === "risk_level" ? "desc" : "asc");
    }
  }

  function SortHeader({
    label,
    columnKey,
  }: {
    label: string;
    columnKey: SortKey;
  }) {
    const active = sortKey === columnKey;
    return (
      <th className={thClass}>
        <button
          type="button"
          onClick={() => toggleSort(columnKey)}
          className="inline-flex items-center gap-1 hover:text-[#e6edf3]"
        >
          {label}
          {active &&
            (sortDir === "asc" ? (
              <ArrowUp className="h-3.5 w-3.5" aria-hidden />
            ) : (
              <ArrowDown className="h-3.5 w-3.5" aria-hidden />
            ))}
        </button>
      </th>
    );
  }

  const colSpan = variant === "queue" ? 4 : 7;
  const tdC = `${cellX} ${cellY}`;

  return (
    <div
      className={
        embedded
          ? "overflow-hidden bg-transparent text-[#e6edf3]"
          : "overflow-hidden rounded-xl border border-[var(--color-aegis-border)] bg-[#0d1117] text-[#e6edf3]"
      }
    >
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b border-[var(--color-aegis-border)] bg-[#060810]/80 text-left">
              {variant === "queue" ? (
                <>
                  <SortHeader label="Transaction" columnKey="transaction_id" />
                  <SortHeader label="Risk Level" columnKey="risk_level" />
                  <SortHeader label="Typology" columnKey="typology_tag" />
                  <th className={thClass}>Lens</th>
                </>
              ) : (
                <>
                  <SortHeader label="TX ID" columnKey="transaction_id" />
                  <SortHeader label="Sender" columnKey="sender_wallet" />
                  <SortHeader label="Receiver" columnKey="receiver_wallet" />
                  <SortHeader label="Amount" columnKey="amount" />
                  <SortHeader label="Risk Level" columnKey="risk_level" />
                  <SortHeader label="Heuristics" columnKey="heuristics_count" />
                  <SortHeader label="Timestamp" columnKey="timestamp" />
                </>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--color-aegis-border)] font-data text-xs text-[#c8d4e0]">
            {sorted.length === 0 ? (
              <tr>
                <td
                  colSpan={colSpan}
                  className={`${cellX} py-12 text-center text-[var(--color-aegis-muted)]`}
                >
                  No transactions to display.
                </td>
              </tr>
            ) : (
              sorted.map((tx) => {
                const risk = tx.risk_score ?? null;
                const tier = resolveRiskTier(risk, tierConfig, tx.risk_level);
                const defaultLens = {
                  behavioral: 0.2,
                  graph: 0.2,
                  entity: 0.2,
                  temporal: 0.2,
                  offramp: 0.2,
                };
                const lens = tx.lens_scores ?? defaultLens;

                const selected = selectedId != null && tx.id === selectedId;
                const rowBase =
                  onSelect != null
                    ? "cursor-pointer hover:bg-[#060810]/90 focus-visible:bg-[#060810]/90 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[#34d399]/40"
                    : "";
                const rowSelected = selected
                  ? "bg-[#060810]/95 ring-1 ring-inset ring-[#34d399]/35"
                  : "";

                const rowProps = onSelect
                  ? {
                      onClick: () => onSelect(tx.id),
                      onKeyDown: (e: KeyboardEvent<HTMLTableRowElement>) => {
                        if (e.key === "Enter" || e.key === " ") {
                          e.preventDefault();
                          onSelect(tx.id);
                        }
                      },
                      tabIndex: 0 as const,
                      role: "button" as const,
                      className: `${rowBase} ${rowSelected}`.trim(),
                    }
                  : {};

                if (variant === "queue") {
                  return (
                    <tr key={tx.id} {...rowProps}>
                      <td className={tdC}>
                        <div className="font-mono text-[11px] text-[#e6edf3]">
                          {tx.display_ref ?? truncateAddress(tx.transaction_id, 10)}
                        </div>
                        <div className="mt-0.5 font-mono text-[10px] text-[var(--color-aegis-muted)]">
                          {truncateAddress(tx.transaction_id, 5)}...{tx.transaction_id.slice(-3)}
                        </div>
                      </td>
                      <td className={tdC}>
                        <div className="flex flex-col gap-1.5 min-w-[120px]">
                          <span className={`inline-flex w-fit rounded-full px-2.5 py-0.5 text-[10px] font-medium ${riskBadgeClassFromScore(risk, tierConfig, tx.risk_level)}`}>
                            {tier ? riskTierLabel(tier) : "Unknown"}
                          </span>
                          <div className="h-1.5 w-full max-w-[140px] overflow-hidden rounded-full bg-[#060810]">
                            <div
                              className={`h-full rounded-full transition-all ${riskBarClassFromScore(risk, tierConfig, tx.risk_level)}`}
                              style={{
                                width: `${Math.min(100, (risk ?? 0) * 100)}%`,
                              }}
                            />
                          </div>
                        </div>
                      </td>
                      <td className={tdC}>
                        <span className="rounded-full border border-[var(--color-aegis-border)] bg-[#060810] px-2.5 py-0.5 text-[10px] text-[#a5b4c8]">
                          {(tx.typology_tag ?? "-").replace(/^T-\d+\s*/, "")}
                        </span>
                      </td>
                      <td className={tdC}>
                        <LensDots scores={lens} />
                      </td>
                    </tr>
                  );
                }

                return (
                  <tr key={tx.id} {...rowProps}>
                    <td className={`${tdC} font-mono text-[11px] text-[#e6edf3]`}>
                      {truncateAddress(tx.transaction_id, 8)}
                    </td>
                    <td className={`${tdC} font-mono`}>
                      {truncateAddress(tx.sender_wallet, 6)}
                    </td>
                    <td className={`${tdC} font-mono`}>
                      {truncateAddress(tx.receiver_wallet, 6)}
                    </td>
                    <td className={`${tdC} tabular-nums text-[#e6edf3]`}>
                      {formatCurrency(tx.amount)}
                    </td>
                    <td className={tdC}>
                      <span
                        className={`inline-flex rounded-full px-2.5 py-0.5 text-[10px] font-medium ${riskBadgeClassFromScore(risk, tierConfig, tx.risk_level)}`}
                      >
                        {tier ? riskTierLabel(tier) : "Unknown"}
                      </span>
                    </td>
                    <td className={tdC}>
                      <span className="inline-flex min-w-[2rem] justify-center rounded-md border border-[var(--color-aegis-border)] bg-[#060810] px-2 py-0.5 text-[11px] font-medium tabular-nums">
                        {tx.heuristics_count ?? "-"}
                      </span>
                    </td>
                    <td className={`${tdC} text-[var(--color-aegis-muted)]`}>
                      {formatDate(tx.timestamp)}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
