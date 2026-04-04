import { useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Eye, Loader2 } from "lucide-react";
import { useTransactions } from "@/hooks/useTransactions";
import TransactionTable from "@/components/TransactionTable";
import FiltersBar from "@/components/FiltersBar";
import type { TransactionQueueRow } from "@/types/transaction";

export default function TransactionsPage() {
  const navigate = useNavigate();
  const { transactions, loading, error } = useTransactions();
  const [searchParams] = useSearchParams();
  const focus = searchParams.get("focus");
  const [page, setPage] = useState(1);
  const pageSize = 25;

  const rows: TransactionQueueRow[] = useMemo(
    () =>
      transactions.map((t) => ({
        ...t,
        typology_tag: t.label ?? undefined,
        lens_scores: undefined,
      })),
    [transactions],
  );

  const paged = useMemo(() => {
    const start = (page - 1) * pageSize;
    return rows.slice(start, start + pageSize);
  }, [rows, page]);

  const totalPages = Math.max(1, Math.ceil(rows.length / pageSize));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-[#e6edf3]">
          Transactions
        </h1>
        <p className="font-data text-sm text-[var(--color-aegis-muted)]">
          Sortable queue with risk scores and lens signals
          {focus && (
            <span className="ml-2 text-[var(--color-aegis-green)]">
              · focus {focus}
            </span>
          )}
        </p>
      </div>

      <FiltersBar onFilter={() => {}} />

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

      {!loading && !error && (
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
              Page {page} / {totalPages} · {rows.length} rows
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
