import { Loader2, Search, Wallet as WalletIcon, Network } from "lucide-react";
import { useParams } from "react-router-dom";
import { useWallet } from "@/hooks/useWallet";
import WalletDetailPanel from "@/components/WalletDetailPanel";
import FlowTimeline from "@/components/FlowTimeline";
import ExplanationPanel from "@/components/ExplanationPanel";

export default function WalletPage() {
  const { address } = useParams<{ address: string }>();
  const { wallet, loading, error } = useWallet(address);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-[#e6edf3]">
          Wallet investigation
        </h1>
        <p className="font-data text-sm text-[var(--color-aegis-muted)]">
          Address, flow timeline, risk tier, heuristic badges
        </p>
      </div>

      {!address && (
        <div className="max-w-xl rounded-xl border border-[var(--color-aegis-border)] bg-[#0d1117] p-6">
          <label
            htmlFor="wallet-search"
            className="mb-2 block font-data text-sm font-medium text-[#c8d4e0]"
          >
            Look up a wallet
          </label>
          <div className="relative">
            <Search
              className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-aegis-muted)]"
              aria-hidden
            />
            <input
              id="wallet-search"
              type="search"
              placeholder="Paste address or open from transaction links…"
              className="w-full rounded-lg border border-[var(--color-aegis-border)] bg-[#060810] py-2.5 pl-10 pr-4 font-data text-sm text-[#e6edf3] placeholder:text-[#5c6b7f] focus:border-[var(--color-aegis-green)]/40 focus:outline-none focus:ring-1 focus:ring-[var(--color-aegis-green)]/30"
            />
          </div>
          <p className="mt-3 font-data text-xs text-[var(--color-aegis-muted)]">
            Navigate to{" "}
            <span className="font-mono text-[#9aa7b8]">
              /dashboard/wallets/&lt;address&gt;
            </span>
          </p>
        </div>
      )}

      {address && (
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1fr_340px]">
          <div className="min-w-0 space-y-6">
            <div className="rounded-xl border border-[var(--color-aegis-border)] bg-[#0d1117] p-5">
              <div className="mb-4 flex items-start gap-3">
                <WalletIcon className="mt-0.5 h-6 w-6 shrink-0 text-[var(--color-aegis-green)]" />
                <div>
                  <h2 className="font-display text-lg font-semibold text-[#e6edf3]">
                    Overview
                  </h2>
                  <p className="mt-1 break-all font-data text-xs text-[#9aa7b8]">
                    {address}
                  </p>
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
                <p className="font-data text-sm text-[var(--color-aegis-muted)]">
                  Wallet not found.
                </p>
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
                  <FlowTimeline transactions={[]} />
                </div>

                <ExplanationPanel
                  transactionId={address}
                  explanation={null}
                />
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
                score={null}
                triggeredHeuristicIds={[]}
                heuristicExplanations={{}}
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
