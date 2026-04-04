import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { FlowCanvas, type FlowHoverPayload } from "@/components/flow-explorer/FlowCanvas";
import type { FlowCluster } from "@/types/flowExplorer";
import type { RunCluster } from "@/types/run";
import { useRunContext } from "@/contexts/useRunContext";
import {
  fetchClusterGraph,
  fetchRunClusters,
  fetchRunSuspicious,
} from "@/api/runs";
import { buildFlowClusterFromSnapshot } from "@/utils/flowExplorerFromRun";

const CLUSTER_TAB_HUES = ["#EF4444", "#F97316", "#F59E0B", "#34d399", "#a78bfa", "#7dd3fc"];

function formatRunHash(id: string): string {
  if (id.length <= 12) return id;
  return `${id.slice(0, 6)}…${id.slice(-4)}`;
}

const EMPTY_LIVE_CLUSTER: FlowCluster = {
  key: "empty",
  name: "No clusters in this run",
  typology: "—",
  typologyShort: "—",
  risk: 0,
  riskColor: "#6b7c90",
  riskLabel: "—",
  wallets: 0,
  tx: 0,
  totalAmount: "—",
  heuristics: [],
  wlist: [],
  txlist: [],
  nodes: [],
  edges: [],
};

const NO_COMPLETED_RUNS_CLUSTER: FlowCluster = {
  key: "no-completed-runs",
  name: "Complete a pipeline run first",
  typology: "—",
  typologyShort: "—",
  risk: 0,
  riskColor: "#6b7c90",
  riskLabel: "—",
  wallets: 0,
  tx: 0,
  totalAmount: "—",
  heuristics: [],
  wlist: [],
  txlist: [],
  nodes: [],
  edges: [],
};

export default function FlowExplorerPage() {
  const navigate = useNavigate();
  const { runs, selectRun } = useRunContext();
  const completed = useMemo(
    () => runs.filter((r) => r.status === "completed"),
    [runs],
  );

  const [runIdx, setRunIdx] = useState(0);
  const [clusterIdx, setClusterIdx] = useState(0);
  const [clustersForRun, setClustersForRun] = useState<RunCluster[]>([]);
  const [liveCluster, setLiveCluster] = useState<FlowCluster | null>(null);
  const [loadingLive, setLoadingLive] = useState(false);

  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [walletRowAddr, setWalletRowAddr] = useState<string | null>(null);
  const [hover, setHover] = useState<FlowHoverPayload | null>(null);

  const hasCompletedRuns = completed.length > 0;
  const activeRunId = useMemo(() => {
    if (!hasCompletedRuns) return undefined;
    const i = Math.min(runIdx, completed.length - 1);
    return completed[i]?.id;
  }, [hasCompletedRuns, runIdx, completed]);

  useEffect(() => {
    setRunIdx((i) =>
      completed.length === 0 ? 0 : Math.min(i, completed.length - 1),
    );
  }, [completed.length]);

  useEffect(() => {
    if (!activeRunId) return;
    selectRun(activeRunId);
  }, [activeRunId, selectRun]);

  useEffect(() => {
    if (!activeRunId) {
      setClustersForRun([]);
      setLiveCluster(null);
      return;
    }
    setClusterIdx(0);
    let cancel = false;
    (async () => {
      setLoadingLive(true);
      try {
        const list = await fetchRunClusters(activeRunId);
        if (cancel) return;
        setClustersForRun(list);
      } catch {
        if (!cancel) setClustersForRun([]);
      } finally {
        if (!cancel) setLoadingLive(false);
      }
    })();
    return () => {
      cancel = true;
    };
  }, [activeRunId]);

  useEffect(() => {
    if (clustersForRun.length === 0) return;
    setClusterIdx((i) => Math.min(i, clustersForRun.length - 1));
  }, [clustersForRun]);

  useEffect(() => {
    if (!activeRunId || clustersForRun.length === 0) {
      setLiveCluster(null);
      return;
    }
    const idx = Math.min(clusterIdx, clustersForRun.length - 1);
    const c = clustersForRun[idx];
    if (!c) return;
    let cancel = false;
    (async () => {
      setLoadingLive(true);
      try {
        const [snap, sus] = await Promise.all([
          fetchClusterGraph(activeRunId, c.id),
          fetchRunSuspicious(activeRunId),
        ]);
        const susC = sus.filter((t) => t.cluster_id === c.id);
        if (!cancel) setLiveCluster(buildFlowClusterFromSnapshot(c, snap, susC));
      } catch {
        if (!cancel) setLiveCluster(null);
      } finally {
        if (!cancel) setLoadingLive(false);
      }
    })();
    return () => {
      cancel = true;
    };
  }, [activeRunId, clusterIdx, clustersForRun]);

  const cluster: FlowCluster = useMemo(() => {
    if (!hasCompletedRuns) {
      return NO_COMPLETED_RUNS_CLUSTER;
    }
    if (clustersForRun.length === 0) {
      if (loadingLive) {
        return { ...EMPTY_LIVE_CLUSTER, name: "Loading clusters…" };
      }
      return EMPTY_LIVE_CLUSTER;
    }
    if (liveCluster) return liveCluster;
    if (loadingLive) {
      return { ...EMPTY_LIVE_CLUSTER, name: "Loading graph…" };
    }
    return EMPTY_LIVE_CLUSTER;
  }, [hasCompletedRuns, clustersForRun.length, liveCluster, loadingLive]);

  useEffect(() => {
    setWalletRowAddr(null);
  }, [cluster.key]);

  const onWalletRowClick = useCallback(
    (addr: string) => {
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
    [cluster.nodes],
  );

  useEffect(() => {
    if (!selectedNodeId) {
      setWalletRowAddr(null);
      return;
    }
    const n = cluster.nodes.find((x) => x.id === selectedNodeId);
    if (n) setWalletRowAddr(n.label);
  }, [selectedNodeId, cluster.nodes]);

  const inactiveTab =
    "border-[var(--color-aegis-border)] bg-transparent hover:border-[#34d399]/35";

  const clusterTabs = useMemo(() => {
    if (!hasCompletedRuns) {
      return [{ i: 0, label: "No runs", cr: undefined as RunCluster | undefined }];
    }
    if (clustersForRun.length === 0) {
      return [
        {
          i: 0,
          label: loadingLive ? "Loading…" : "No clusters",
          cr: undefined as RunCluster | undefined,
        },
      ];
    }
    return clustersForRun.map((cr, i) => ({
      i,
      label: cr.label ?? `Cluster ${i + 1}`,
      cr,
    }));
  }, [hasCompletedRuns, clustersForRun, loadingLive]);

  return (
    <div className="flex h-full min-h-0 flex-col bg-[#060810] text-[#e6edf3]">
      <div className="flex shrink-0 items-stretch gap-2 border-b border-[var(--color-aegis-border)] px-3 py-1.5">
        <div className="flex min-w-0 flex-1 gap-1.5 overflow-x-auto">
          {clusterTabs.map((tab, tabIndex) => {
            const active = tabIndex === clusterIdx;
            const activeRing = active
              ? "border-[#34d399]/55 bg-[#34d399]/10"
              : inactiveTab;
            const cr = tab.cr;
            const typology = cr?.typology ?? "—";
            const wallets = cr?.wallet_count ?? 0;
            const tx = cr?.tx_count ?? 0;
            const hue = CLUSTER_TAB_HUES[tabIndex % CLUSTER_TAB_HUES.length]!;
            return (
              <button
                key={cr?.id ?? `tab-${tabIndex}`}
                type="button"
                onClick={() => {
                  setClusterIdx(tabIndex);
                  setSelectedNodeId(null);
                  setWalletRowAddr(null);
                }}
                className={`min-w-0 flex-1 rounded-lg border px-2 py-1.5 text-left transition-colors ${activeRing}`}
              >
                <span
                  className="font-display text-[12px] font-bold leading-tight"
                  style={{ color: hue }}
                >
                  {tab.label}
                </span>
                <p className="mt-0.5 truncate font-data text-[9px] text-[#6b7c90]">
                  {typology} · {wallets}w · {tx}tx
                </p>
              </button>
            );
          })}
        </div>
        <label className="flex shrink-0 items-center gap-1.5 self-center">
          <span className="hidden font-data text-[10px] text-[#6b7c90] sm:inline">
            Run
          </span>
          <select
            value={hasCompletedRuns ? runIdx : 0}
            onChange={(e) => {
              const v = Number(e.target.value);
              setRunIdx(v);
              if (completed[v]) selectRun(completed[v]!.id);
            }}
            disabled={!hasCompletedRuns}
            className="max-w-[200px] cursor-pointer rounded-lg border border-[var(--color-aegis-border)] bg-[#0d1117] px-2 py-1.5 font-data text-[11px] text-[#e6edf3] hover:border-[#34d399]/35 disabled:cursor-not-allowed disabled:opacity-40"
            aria-label="Select pipeline run"
          >
            {hasCompletedRuns ? (
              completed.map((r, i) => (
                <option key={r.id} value={i}>
                  {formatRunHash(r.id)}
                  {r.label ? ` · ${r.label}` : ""}
                </option>
              ))
            ) : (
              <option value={0}>No completed runs</option>
            )}
          </select>
        </label>
        {loadingLive && (
          <span className="self-center font-data text-[10px] text-[#6b7c90]">
            Loading…
          </span>
        )}
      </div>

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

          <div className="mt-4">
            <p className="text-[11px] text-[#6b7c90]">Heuristics triggered</p>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {cluster.heuristics.length === 0 ? (
                <span className="font-data text-[10px] text-[#6b7c90]">
                  {hasCompletedRuns ? "See run report for details" : "—"}
                </span>
              ) : (
                cluster.heuristics.map((h) => (
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
                ))
              )}
            </div>
          </div>

          <div className="mt-4">
            <p className="text-[11px] text-[#6b7c90]">Wallets in cluster</p>
            <ul className="mt-2 space-y-1">
              {cluster.wlist.length === 0 ? (
                <li className="font-data text-[10px] text-[#6b7c90]">
                  {cluster.nodes.length === 0 && hasCompletedRuns
                    ? "No graph snapshot for this cluster."
                    : "—"}
                </li>
              ) : (
                cluster.wlist.map((w) => {
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
                })
              )}
            </ul>
          </div>

          <div className="mt-4">
            <p className="text-[11px] text-[#6b7c90]">Suspicious transactions</p>
            <ul className="mt-2 space-y-1">
              {cluster.txlist.length === 0 ? (
                <li className="font-data text-[10px] text-[#6b7c90]">—</li>
              ) : (
                cluster.txlist.map((t) => (
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
                ))
              )}
            </ul>
          </div>

          <button
            type="button"
            onClick={() => navigate("/dashboard/reports")}
            className="mt-4 w-full rounded-lg border border-[#34d399]/35 bg-[#34d399]/10 py-2.5 font-data text-[13px] font-medium text-[#6ee7b7] hover:border-[#34d399]/55"
          >
            Generate SAR
          </button>
        </aside>
      </div>

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
