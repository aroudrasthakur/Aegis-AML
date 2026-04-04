import { useCallback, useMemo, useState } from "react";
import { GitBranch, Info, Minus, Plus } from "lucide-react";
import NetworkGraph from "@/components/NetworkGraph";
import type { CytoscapeElement } from "@/types/graph";

const MOCK_ELEMENTS: CytoscapeElement[] = [
  { data: { id: "w1", label: "Wallet A", color: "#00e5a0" } },
  { data: { id: "w2", label: "Mixer", color: "#7c5cfc" } },
  { data: { id: "w3", label: "Exchange", color: "#f59e0b" } },
  { data: { id: "e1", source: "w1", target: "w2", weight: 500000 } },
  { data: { id: "e2", source: "w2", target: "w3", weight: 120000 } },
];

export default function FlowExplorerPage() {
  const [kHop, setKHop] = useState(2);
  const [selected, setSelected] = useState<string | null>(null);

  const elements = useMemo(() => MOCK_ELEMENTS, []);

  const onNodeClick = useCallback((id: string) => {
    setSelected(id);
  }, []);

  return (
    <div className="flex min-h-[calc(100vh-8rem)] flex-col gap-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-[#e6edf3]">
          Flow Explorer
        </h1>
        <p className="font-data text-sm text-[var(--color-aegis-muted)]">
          Cytoscape graph · k-hop expansion (UI)
        </p>
      </div>

      <div className="flex flex-1 flex-col gap-4 lg:flex-row lg:min-h-0">
        <div className="flex min-h-[480px] flex-1 flex-col gap-4">
          <div className="flex flex-wrap items-center gap-3 rounded-xl border border-[var(--color-aegis-border)] bg-[#0d1117] px-4 py-3 font-data text-xs text-[#9aa7b8]">
            <GitBranch className="h-4 w-4 text-[var(--color-aegis-green)]" aria-hidden />
            <span>k-hop</span>
            <div className="flex items-center gap-2">
              <button
                type="button"
                className="rounded border border-[var(--color-aegis-border)] p-1 hover:text-[#e6edf3]"
                onClick={() => setKHop((k) => Math.max(0, k - 1))}
                aria-label="Decrease hops"
              >
                <Minus className="h-4 w-4" />
              </button>
              <span className="min-w-[2ch] tabular-nums text-[#e6edf3]">{kHop}</span>
              <button
                type="button"
                className="rounded border border-[var(--color-aegis-border)] p-1 hover:text-[#e6edf3]"
                onClick={() => setKHop((k) => Math.min(5, k + 1))}
                aria-label="Increase hops"
              >
                <Plus className="h-4 w-4" />
              </button>
            </div>
          </div>
          <div className="min-h-[420px] flex-1">
            <NetworkGraph elements={elements} onNodeClick={onNodeClick} />
          </div>
        </div>

        <aside className="w-full shrink-0 rounded-xl border border-[var(--color-aegis-border)] bg-[#0d1117] p-5 lg:w-80">
          <div className="flex items-center gap-2">
            <Info className="h-4 w-4 text-[var(--color-aegis-muted)]" aria-hidden />
            <h2 className="font-display text-sm font-semibold text-[#e6edf3]">
              Node / edge inspection
            </h2>
          </div>
          {selected ? (
            <dl className="mt-4 space-y-2 font-data text-xs text-[#c8d4e0]">
              <dt className="text-[var(--color-aegis-muted)]">Selected</dt>
              <dd className="break-all font-mono text-[11px] text-[var(--color-aegis-green)]">
                {selected}
              </dd>
            </dl>
          ) : (
            <p className="mt-4 font-data text-sm leading-relaxed text-[#9aa7b8]">
              Tap a node to inspect id, volume, and risk signals. Expand hops to
              pull neighbors into view.
            </p>
          )}
        </aside>
      </div>
    </div>
  );
}
