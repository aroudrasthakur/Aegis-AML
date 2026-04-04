import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { FlowCanvas, type FlowHoverPayload } from "@/components/flow-explorer/FlowCanvas";
import NodeInspectPanel from "@/components/flow-explorer/NodeInspectPanel";
import RunSelectorDropdown from "@/components/RunSelectorDropdown";
import type { FlowCluster, FlowExplorerNode, FlowEdge } from "@/types/flowExplorer";
import { useRunContext } from "@/contexts/useRunContext";
import { useThresholds } from "@/contexts/ThresholdProvider";
import {
  fetchRunClusters,
  fetchClusterGraph,
  fetchClusterMembers,
} from "@/api/runs";
import type { RunCluster, RunGraphSnapshot } from "@/types/run";
import { riskColorFromScore, resolveRiskTier, riskTierLabel } from "@/utils/riskTiers";

const RISK_COLORS: Record<string, string> = {
  high: "#EF4444",
  medium: "#F97316",
  "medium-low": "#F59E0B",
  low: "#22C55E",
};

function buildFlowCluster(
  idx: number,
  cluster: RunCluster,
  graph: RunGraphSnapshot | null,
  members: { wallet_address: string }[],
  tierConfig: import("@/utils/riskTiers").RiskTierConfig | null,
): FlowCluster {
  const tier = resolveRiskTier(cluster.risk_score, tierConfig) ?? "medium";
  const color = RISK_COLORS[tier] ?? "#F97316";

  const nodes: FlowExplorerNode[] = [];
  const edges: FlowEdge[] = [];

  if (graph?.elements && Array.isArray(graph.elements)) {
    const elNodes = graph.elements.filter(
      (e: Record<string, unknown>) => e.group === "nodes" || (e.data && !("source" in (e.data as Record<string, unknown>))),
    );
    const elEdges = graph.elements.filter(
      (e: Record<string, unknown>) => e.group === "edges" || (e.data && "source" in (e.data as Record<string, unknown>)),
    );

    const count = Math.max(elNodes.length, 1);
    elNodes.forEach((el: Record<string, unknown>, i: number) => {
      const d = (el.data ?? el) as Record<string, unknown>;
      const id = String(d.id ?? i);
      const label = String(d.label ?? d.id ?? `Node ${i}`);
      const riskScore = typeof d.risk_score === "number" ? d.risk_score : 0.5;
      nodes.push({
        id,
        label,
        type: "layer",
        color: riskColorFromScore(riskScore, tierConfig),
        rx: ((i % Math.ceil(Math.sqrt(count))) + 0.5) / Math.ceil(Math.sqrt(count)),
        ry: (Math.floor(i / Math.ceil(Math.sqrt(count))) + 0.5) / Math.max(Math.ceil(count / Math.ceil(Math.sqrt(count))), 1),
        risk: riskScore,
      });
    });

    elEdges.forEach((el: Record<string, unknown>) => {
      const d = (el.data ?? el) as Record<string, unknown>;
      const src = String(d.source ?? "");
      const tgt = String(d.target ?? "");
      const amt = typeof d.weight === "number" ? `$${d.weight.toLocaleString()}` : typeof d.amount === "number" ? `$${d.amount.toLocaleString()}` : "";
      if (src && tgt) edges.push([src, tgt, amt]);
    });
  } else if (members.length > 0) {
    const count = members.length;
    members.forEach((m, i) => {
      nodes.push({
        id: `m-${i}`,
        label: m.wallet_address,
        type: "layer",
        color: riskColorFromScore(cluster.risk_score, tierConfig),
        rx: ((i % Math.ceil(Math.sqrt(count))) + 0.5) / Math.ceil(Math.sqrt(count)),
        ry: (Math.floor(i / Math.ceil(Math.sqrt(count))) + 0.5) / Math.max(Math.ceil(count / Math.ceil(Math.sqrt(count))), 1),
        risk: cluster.risk_score,
      });
    });
  }

  const keys = ["A", "B", "C", "D", "E", "F", "G", "H"] as const;
  type ValidKey = (typeof keys)[number];
  const key: ValidKey = (keys[idx % keys.length] ?? "A") as ValidKey;

  return {
    key: key as FlowCluster["key"],
    name: cluster.label ?? `Cluster ${idx + 1}`,
    typology: cluster.typology ?? "Unknown",
    typologyShort: cluster.typology ?? "Unknown",
    risk: cluster.risk_score,
    riskColor: color,
    riskLabel: riskTierLabel(tier).toUpperCase(),
    wallets: cluster.wallet_count,
    tx: cluster.tx_count,
    totalAmount: `$${cluster.total_amount.toLocaleString()}`,
    heuristics: cluster.typology
      ? [{ label: cluster.typology, color, bg: `${color}14`, border: `${color}55` }]
      : [],
    wlist: members.map((m) => ({
      addr: m.wallet_address,
      type: "wallet",
      badge: riskTierLabel(tier),
      badgeColor: color,
    })),
    txlist: [],
    nodes,
    edges,
  };
}

export default function FlowExplorerPage() {
  const navigate = useNavigate();
  const { runs } = useRunContext();
  const { config: tierConfig } = useThresholds();

  const completedRuns = useMemo(
    () => runs.filter((r) => r.status === "completed"),
    [runs],
  );
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [clusters, setClusters] = useState<FlowCluster[]>([]);
  const [clusterIdx, setClusterIdx] = useState(0);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [walletRowAddr, setWalletRowAddr] = useState<string | null>(null);
  const [hover, setHover] = useState<FlowHoverPayload | null>(null);
  const [loadingClusters, setLoadingClusters] = useState(false);

  useEffect(() => {
    if (!selectedRunId && completedRuns.length > 0) {
      setSelectedRunId(completedRuns[0].id);
    }
  }, [completedRuns, selectedRunId]);

  useEffect(() => {
    if (!selectedRunId) {
      setClusters([]);
      return;
    }
    let cancelled = false;
    setLoadingClusters(true);
    setClusters([]);
    setClusterIdx(0);

    (async () => {
      try {
        const runClusters = await fetchRunClusters(selectedRunId);
        if (cancelled || runClusters.length === 0) {
          if (!cancelled) {
            setClusters([]);
            setLoadingClusters(false);
          }
          return;
        }

        const built: FlowCluster[] = [];
        for (let i = 0; i < runClusters.length; i++) {
          const rc = runClusters[i];
          const [graph, members] = await Promise.all([
            fetchClusterGraph(selectedRunId, rc.id).catch(() => null),
            fetchClusterMembers(selectedRunId, rc.id).catch(() => []),
          ]);
          if (cancelled) return;
          built.push(buildFlowCluster(i, rc, graph, members, tierConfig));
        }
        if (!cancelled) setClusters(built);
      } catch {
        if (!cancelled) setClusters([]);
      } finally {
        if (!cancelled) setLoadingClusters(false);
      }
    })();
    return () => { cancelled = true; };
  }, [selectedRunId, tierConfig]);

  const cluster = clusters[clusterIdx] ?? null;

  useEffect(() => {
    setWalletRowAddr(null);
    setSelectedNodeId(null);
  }, [clusterIdx]);

  const onWalletRowClick = useCallback(
    (addr: string) => {
      if (!cluster) return;
      setWalletRowAddr((prev) => {
        if (prev === addr) {
          setSelectedNodeId(null);
          return null;
        }
        const node = cluster.nodes.find((n) => n.label === addr);
        setSelectedNodeId(node?.id ?? null);
        return addr;
      });
    },
    [cluster],
  );

  useEffect(() => {
    if (!selectedNodeId || !cluster) {
      setWalletRowAddr(null);
      return;
    }
    const n = cluster.nodes.find((x) => x.id === selectedNodeId);
    if (n) setWalletRowAddr(n.label);
  }, [selectedNodeId, cluster]);

  const inactiveTab =
    "border-[var(--color-aegis-border)] bg-transparent hover:border-[#34d399]/35";

  if (!selectedRunId || (clusters.length === 0 && !loadingClusters)) {
    return (
      <div className="flex h-full min-h-0 flex-col bg-[#060810] text-[#e6edf3]">
        <div className="flex shrink-0 items-center gap-4 border-b border-[var(--color-aegis-border)] px-3 py-2">
          <RunSelectorDropdown
            runs={runs}
            selectedRunId={selectedRunId}
            onSelect={setSelectedRunId}
          />
        </div>
        <div className="flex flex-1 flex-col items-center justify-center gap-3 p-8">
          <p className="font-display text-lg font-semibold text-[#9aa7b8]">
            No cluster data available
          </p>
          <p className="max-w-md text-center font-data text-sm text-[var(--color-aegis-muted)]">
            {completedRuns.length === 0
              ? "Upload transaction data and run the pipeline to see cluster graphs here."
              : "The selected run did not produce any clusters. Try a different run."}
          </p>
        </div>
      </div>
    );
  }

  if (loadingClusters) {
    return (
      <div className="flex h-full min-h-0 flex-col bg-[#060810] text-[#e6edf3]">
        <div className="flex shrink-0 items-center gap-4 border-b border-[var(--color-aegis-border)] px-3 py-2">
          <RunSelectorDropdown
            runs={runs}
            selectedRunId={selectedRunId}
            onSelect={setSelectedRunId}
          />
        </div>
        <div className="flex flex-1 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-[#34d399]" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full min-h-0 flex-col bg-[#060810] text-[#e6edf3]">
      <div className="flex shrink-0 items-stretch gap-2 border-b border-[var(--color-aegis-border)] px-3 py-1.5">
        <div className="flex min-w-0 flex-1 gap-1.5">
          {clusters.map((cl, i) => {
            const active = i === clusterIdx;
            const activeRing = active
              ? "border-[#34d399]/55 bg-[#34d399]/10"
              : inactiveTab;
            return (
              <button
                key={cl.key + i}
                type="button"
                onClick={() => {
                  setClusterIdx(i);
                  setSelectedNodeId(null);
                  setWalletRowAddr(null);
                }}
                className={`min-w-0 flex-1 rounded-lg border px-2 py-1.5 text-left transition-colors ${activeRing}`}
              >
                <span
                  className="font-display text-[12px] font-bold leading-tight"
                  style={{ color: cl.riskColor }}
                >
                  {cl.name}
                </span>
                <p className="mt-0.5 truncate font-data text-[9px] text-[#6b7c90]">
                  {cl.typology} · {cl.wallets}w · {cl.tx}tx
                </p>
              </button>
            );
          })}
        </div>
        <RunSelectorDropdown
          runs={runs}
          selectedRunId={selectedRunId}
          onSelect={setSelectedRunId}
          className="self-center"
        />
      </div>

      {cluster && (
        <div className="flex min-h-0 flex-1">
          <FlowCanvas
            cluster={cluster}
            selectedNodeId={selectedNodeId}
            onSelectNode={setSelectedNodeId}
            onHover={setHover}
            walletFocusAddr={walletRowAddr}
            typologyBadge={cluster.typologyShort}
          />

          <aside className="aegis-scroll flex w-[295px] shrink-0 flex-col overflow-y-auto border-l border-[var(--color-aegis-border)] bg-[#0d1117] p-4">
            <p className="font-data text-[9px] text-[#6b7c90]">{cluster.typology}</p>
            <h2 className="font-display text-[15px] font-bold text-[#e6edf3]">
              {cluster.name}
            </h2>
            <p className="mt-1 text-[12px] text-[#9aa7b8]">
              {cluster.wallets} wallets · {cluster.tx} transactions
            </p>

            <div className="mt-4 flex items-center justify-between gap-2">
              <span
                className="font-data text-[22px] font-semibold tabular-nums"
                style={{ color: cluster.riskColor }}
              >
                {(cluster.risk * 100).toFixed(0)}%
              </span>
              <span
                className="rounded-[6px] border px-2 py-0.5 font-data text-[10px]"
                style={{
                  color: cluster.riskColor,
                  borderColor: `${cluster.riskColor}55`,
                  background: `${cluster.riskColor}14`,
                }}
              >
                {cluster.riskLabel}
              </span>
              <span className="ml-auto font-data text-[12px] tabular-nums text-[#e6edf3]">
                {cluster.totalAmount}
              </span>
            </div>

            <div className="mt-2 h-[4px] overflow-hidden rounded-full bg-[#34d399]/15">
              <div
                className="h-full rounded-full transition-[width] duration-500 ease-out"
                style={{
                  width: `${Math.min(100, cluster.risk * 100)}%`,
                  backgroundColor: cluster.riskColor,
                }}
              />
            </div>

            <div className="mt-4 grid grid-cols-2 gap-2">
              {[
                { k: "Wallets", v: String(cluster.wallets) },
                { k: "Transactions", v: String(cluster.tx) },
                { k: "Heuristics fired", v: String(cluster.heuristics.length) },
                { k: "Typology", v: cluster.typology },
              ].map((cell) => (
                <div
                  key={cell.k}
                  className="rounded-lg border border-[var(--color-aegis-border)] bg-[#060810] px-2.5 py-2"
                >
                  <p className="text-[10px] text-[#6b7c90]">{cell.k}</p>
                  <p className="mt-0.5 font-data text-[12px] text-[#e6edf3]">
                    {cell.v}
                  </p>
                </div>
              ))}
            </div>

            {cluster.heuristics.length > 0 && (
              <div className="mt-4">
                <p className="text-[11px] text-[#6b7c90]">Heuristics triggered</p>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {cluster.heuristics.map((h) => (
                    <span
                      key={h.label}
                      className="rounded-[6px] border px-2 py-0.5 font-data text-[10px]"
                      style={{
                        color: h.color,
                        backgroundColor: h.bg,
                        borderColor: h.border,
                      }}
                    >
                      {h.label}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {cluster.wlist.length > 0 && (
              <div className="mt-4">
                <p className="text-[11px] text-[#6b7c90]">Wallets in cluster</p>
                <ul className="mt-2 space-y-1">
                  {cluster.wlist.map((w) => {
                    const active = walletRowAddr === w.addr;
                    return (
                      <li key={w.addr}>
                        <button
                          type="button"
                          onClick={() => onWalletRowClick(w.addr)}
                          className={`flex w-full items-center justify-between gap-2 rounded-[8px] border px-2 py-2 text-left transition-colors ${
                            active
                              ? "border-[#34d399]/45 bg-[#34d399]/10"
                              : "border-[var(--color-aegis-border)] bg-[#060810] hover:border-[#34d399]/35"
                          }`}
                        >
                          <div className="min-w-0">
                            <p className="truncate font-data text-[10.5px] text-[#e6edf3]">
                              {w.addr}
                            </p>
                            <p className="text-[10px] text-[#6b7c90]">{w.type}</p>
                          </div>
                          <span
                            className="shrink-0 rounded-[6px] border px-1.5 py-0.5 font-data text-[9px]"
                            style={{
                              color: w.badgeColor,
                              borderColor: `${w.badgeColor}55`,
                              background: `${w.badgeColor}12`,
                            }}
                          >
                            {w.badge}
                          </span>
                        </button>
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}

            {cluster.txlist.length > 0 && (
              <div className="mt-4">
                <p className="text-[11px] text-[#6b7c90]">Suspicious transactions</p>
                <ul className="mt-2 space-y-1">
                  {cluster.txlist.map((t) => (
                    <li
                      key={t.hash}
                      className="flex items-center justify-between gap-2 rounded-lg border border-[var(--color-aegis-border)] bg-[#060810] px-2 py-1.5"
                    >
                      <div className="min-w-0">
                        <p className="truncate font-data text-[10.5px] text-[#6ee7b7]">
                          {t.hash}
                        </p>
                        <p className="truncate text-[10px] text-[#9aa7b8]">{t.route}</p>
                      </div>
                      <span className="shrink-0 font-data text-[10.5px] tabular-nums text-[#f87171]">
                        {t.amount}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <button
              type="button"
              onClick={() => navigate("/dashboard/reports")}
              className="mt-4 w-full rounded-lg border border-[#34d399]/35 bg-[#34d399]/10 py-2.5 font-data text-[13px] font-medium text-[#6ee7b7] hover:border-[#34d399]/55"
            >
              Generate SAR
            </button>
          </aside>

          {selectedNodeId && selectedRunId && cluster && (() => {
            const node = cluster.nodes.find((n) => n.id === selectedNodeId);
            if (!node) return null;
            return (
              <aside className="flex w-[300px] shrink-0 flex-col border-l border-[var(--color-aegis-border)] bg-[#0d1117]">
                <NodeInspectPanel
                  runId={selectedRunId}
                  nodeLabel={node.label}
                  nodeType={node.type}
                  nodeRisk={node.risk}
                  onClose={() => setSelectedNodeId(null)}
                />
              </aside>
            );
          })()}
        </div>
      )}

      {hover && (
        <div
          className="pointer-events-none fixed z-50 rounded-lg border border-[var(--color-aegis-border)] bg-[#0d1117] px-3 py-2 font-data text-[11px] text-[#e6edf3]"
          style={{ left: hover.clientX + 14, top: hover.clientY + 14 }}
        >
          <p className="text-[#e6edf3]">{hover.label}</p>
          <p className="text-[#9aa7b8]">{hover.type}</p>
          <p className="tabular-nums text-[#34d399]">
            Risk {(hover.risk * 100).toFixed(0)}%
          </p>
        </div>
      )}
    </div>
  );
}
