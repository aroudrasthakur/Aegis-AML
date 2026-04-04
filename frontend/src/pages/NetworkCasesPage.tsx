import { Loader2, Network } from "lucide-react";
import { useNetworkCases } from "@/hooks/useNetworkCases";
import CaseReportCard from "@/components/CaseReportCard";
import NetworkGraph from "@/components/NetworkGraph";
import type { CytoscapeElement } from "@/types/graph";

function previewForCase(id: string): CytoscapeElement[] {
  const seed = id.split("").reduce((a, c) => a + c.charCodeAt(0), 0);
  return [
    { data: { id: `${id}-a`, label: "A", color: "#00e5a0" } },
    { data: { id: `${id}-b`, label: "B", color: "#7c5cfc" } },
    { data: { id: `${id}-c`, label: "C", color: "#f59e0b" } },
    {
      data: {
        id: `${id}-e1`,
        source: `${id}-a`,
        target: `${id}-b`,
        weight: 100000 + seed * 100,
      },
    },
    {
      data: {
        id: `${id}-e2`,
        source: `${id}-b`,
        target: `${id}-c`,
        weight: 50000,
      },
    },
  ];
}

export default function NetworkCasesPage() {
  const { cases, loading, error } = useNetworkCases();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-[#e6edf3]">
          Network cases
        </h1>
        <p className="font-data text-sm text-[var(--color-aegis-muted)]">
          Case cards with graph preview and investigation status
        </p>
      </div>

      {loading && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-[var(--color-aegis-border)] bg-[#0d1117] py-16">
          <Loader2
            className="h-8 w-8 animate-spin text-[var(--color-aegis-green)]"
            aria-hidden
          />
          <p className="mt-3 font-data text-sm text-[var(--color-aegis-muted)]">
            Loading network cases…
          </p>
        </div>
      )}

      {!loading && error && (
        <div className="rounded-xl border border-red-500/30 bg-red-950/20 p-4 font-data text-sm text-red-300">
          {error.message}
        </div>
      )}

      {!loading && !error && cases.length === 0 && (
        <div className="rounded-xl border border-[var(--color-aegis-border)] bg-[#0d1117] p-12 text-center">
          <Network
            className="mx-auto mb-4 h-12 w-12 text-[var(--color-aegis-muted)]"
            aria-hidden
          />
          <p className="font-display font-medium text-[#c8d4e0]">
            No network cases yet
          </p>
          <p className="mx-auto mt-2 max-w-md font-data text-sm text-[#9aa7b8]">
            Run network detection or import cases to see typologies, risk scores,
            and graph previews here.
          </p>
        </div>
      )}

      {!loading && !error && cases.length > 0 && (
        <ul className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {cases.map((c) => (
            <li key={c.id} className="space-y-3">
              <div className="overflow-hidden rounded-xl border border-[var(--color-aegis-border)]">
                <NetworkGraph elements={previewForCase(c.id)} minHeight={200} />
              </div>
              <CaseReportCard case={c} />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
