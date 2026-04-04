import type { FlowCluster, FlowEdge, FlowExplorerNode, FlowTxRow, FlowWalletRow } from "@/types/flowExplorer";
import type { RunCluster, RunGraphSnapshot, RunSuspiciousTx } from "@/types/run";

function formatWallet(id: string): string {
  const s = String(id);
  if (s.length <= 12) return s;
  return `${s.slice(0, 6)}…${s.slice(-4)}`;
}

function formatAmount(v: unknown): string {
  if (v == null) return "—";
  const n = typeof v === "number" ? v : parseFloat(String(v));
  if (!Number.isFinite(n)) return String(v);
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}m`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(1)}k`;
  return `$${n.toFixed(0)}`;
}

function riskLabelFromScore(r: number): string {
  if (r >= 0.85) return "Critical";
  if (r >= 0.65) return "High";
  if (r >= 0.45) return "Elevated";
  return "Moderate";
}

function riskColorFromScore(r: number): string {
  if (r >= 0.85) return "#EF4444";
  if (r >= 0.65) return "#F97316";
  if (r >= 0.45) return "#F59E0B";
  return "#34d399";
}

/**
 * Assign `source` (entry) and `exit` roles using subgraph edge degrees.
 * Guarantees at least one entry and one exit when there are ≥2 nodes (cycles use proxies).
 */
function assignEntryExitRoles(
  nodeIds: string[],
  inCount: Map<string, number>,
  outCount: Map<string, number>,
): Map<string, FlowExplorerNode["type"]> {
  const roles = new Map<string, FlowExplorerNode["type"]>();
  for (const id of nodeIds) roles.set(id, "layer");

  if (nodeIds.length === 0) return roles;

  if (nodeIds.length === 1) {
    roles.set(nodeIds[0]!, "source");
    return roles;
  }

  const entries = nodeIds.filter((id) => (inCount.get(id) ?? 0) === 0);
  const exits = nodeIds.filter((id) => (outCount.get(id) ?? 0) === 0);

  for (const id of entries) {
    roles.set(id, "source");
  }
  for (const id of exits) {
    if (roles.get(id) !== "source") {
      roles.set(id, "exit");
    }
  }

  const hasEntry = [...roles.values()].some((t) => t === "source");
  const hasExit = [...roles.values()].some((t) => t === "exit");

  if (!hasEntry) {
    const pick = [...nodeIds].sort(
      (a, b) =>
        (inCount.get(a) ?? 0) - (inCount.get(b) ?? 0) || a.localeCompare(b),
    )[0]!;
    roles.set(pick, "source");
  }

  if (!hasExit) {
    const pick = [...nodeIds].sort(
      (a, b) =>
        (outCount.get(a) ?? 0) - (outCount.get(b) ?? 0) || a.localeCompare(b),
    )[0]!;
    const entryId = [...roles.entries()].find(([, t]) => t === "source")?.[0];
    if (pick === entryId && nodeIds.length > 1) {
      const alt = [...nodeIds]
        .filter((id) => id !== pick)
        .sort(
          (a, b) =>
            (outCount.get(a) ?? 0) - (outCount.get(b) ?? 0) || a.localeCompare(b),
        )[0];
      if (alt) roles.set(alt, "exit");
    } else {
      roles.set(pick, "exit");
    }
  }

  return roles;
}

function roleToDisplayType(role: FlowExplorerNode["type"]): string {
  if (role === "source") return "Entry";
  if (role === "exit") return "Exit";
  return role.charAt(0).toUpperCase() + role.slice(1);
}

/** Place nodes on a circle so the canvas fit logic works. */
function layoutCircle(ids: string[]): Map<string, { rx: number; ry: number }> {
  const n = ids.length;
  const m = new Map<string, { rx: number; ry: number }>();
  if (n === 0) return m;
  for (let i = 0; i < n; i++) {
    const angle = (2 * Math.PI * i) / n - Math.PI / 2;
    m.set(ids[i]!, {
      rx: 0.5 + 0.38 * Math.cos(angle),
      ry: 0.5 + 0.38 * Math.sin(angle),
    });
  }
  return m;
}

const NODE_COLORS: Record<FlowExplorerNode["type"], string> = {
  source: "#EF4444",
  layer: "#34d399",
  exit: "#8B5CF6",
  feeder: "#34d399",
  collector: "#34d399",
  out: "#34d399",
};

/**
 * Build a FlowCluster for FlowCanvas from a saved Cytoscape snapshot + cluster row.
 */
export function buildFlowClusterFromSnapshot(
  cluster: RunCluster,
  snapshot: RunGraphSnapshot | null,
  suspiciousForCluster: RunSuspiciousTx[] = [],
): FlowCluster {
  const elements = snapshot?.elements ?? [];
  const nodeIdSet = new Set<string>();
  const nodeMeta = new Map<
    string,
    { inDeg: number; outDeg: number; meta?: number; riskLevel?: string }
  >();

  const edgesRaw: { source: string; target: string; amount: string }[] = [];

  for (const el of elements) {
    const raw = el as { data?: Record<string, unknown> };
    const d = raw.data;
    if (!d) continue;
    const src = d.source;
    const tgt = d.target;
    if (typeof src === "string" && typeof tgt === "string") {
      const amt = d.amount ?? d.weight ?? d.label;
      edgesRaw.push({
        source: src,
        target: tgt,
        amount: formatAmount(amt),
      });
      nodeIdSet.add(src);
      nodeIdSet.add(tgt);
    } else if (typeof d.id === "string") {
      const id = d.id;
      nodeIdSet.add(id);
      const ms = d.meta_score;
      const meta =
        typeof ms === "number" ? ms : ms != null ? parseFloat(String(ms)) : undefined;
      nodeMeta.set(id, {
        inDeg: typeof d.in_degree === "number" ? d.in_degree : 0,
        outDeg: typeof d.out_degree === "number" ? d.out_degree : 0,
        meta: Number.isFinite(meta) ? meta : undefined,
        riskLevel: typeof d.risk_level === "string" ? d.risk_level : undefined,
      });
    }
  }

  const nodeIds = [...nodeIdSet];

  // Degree counts from edges if not in node data
  const inCount = new Map<string, number>();
  const outCount = new Map<string, number>();
  for (const e of edgesRaw) {
    outCount.set(e.source, (outCount.get(e.source) ?? 0) + 1);
    inCount.set(e.target, (inCount.get(e.target) ?? 0) + 1);
  }
  for (const id of nodeIds) {
    const ex = nodeMeta.get(id);
    const inD = ex?.inDeg ?? inCount.get(id) ?? 0;
    const outD = ex?.outDeg ?? outCount.get(id) ?? 0;
    nodeMeta.set(id, {
      inDeg: inD,
      outDeg: outD,
      meta: ex?.meta,
      riskLevel: ex?.riskLevel,
    });
  }

  const roleById = assignEntryExitRoles(nodeIds, inCount, outCount);

  const layout = layoutCircle(nodeIds);
  const nodes: FlowExplorerNode[] = nodeIds.map((id) => {
    const meta = nodeMeta.get(id)!;
    const typ = roleById.get(id) ?? "layer";
    const risk =
      typeof meta.meta === "number" && Number.isFinite(meta.meta)
        ? Math.min(1, Math.max(0, meta.meta))
        : Math.min(1, Math.max(0, cluster.risk_score ?? 0.5));
    const pos = layout.get(id) ?? { rx: 0.5, ry: 0.5 };
    return {
      id,
      label: formatWallet(id),
      type: typ,
      color: NODE_COLORS[typ],
      rx: pos.rx,
      ry: pos.ry,
      risk,
    };
  });

  const edges: FlowEdge[] = edgesRaw.map((e) => [e.source, e.target, e.amount] as FlowEdge);

  const wlist: FlowWalletRow[] = nodeIds.slice(0, 24).map((id) => {
    const typ = roleById.get(id) ?? "layer";
    return {
      addr: formatWallet(id),
      type: roleToDisplayType(typ),
      badge:
        typ === "source" ? "Entry" : typ === "exit" ? "Exit" : "Hop",
      badgeColor: NODE_COLORS[typ],
    };
  });

  const txlist: FlowTxRow[] = suspiciousForCluster.slice(0, 12).map((t) => ({
    hash: formatWallet(t.transaction_id),
    route: t.typology ?? t.risk_level ?? "—",
    amount: t.meta_score != null ? `${(t.meta_score * 100).toFixed(0)}% risk` : "—",
  }));

  const risk = Math.min(1, Math.max(0, cluster.risk_score ?? 0.5));
  const rc = riskColorFromScore(risk);

  return {
    key: cluster.id,
    name: cluster.label ?? `Cluster ${cluster.id.slice(0, 8)}`,
    typology: cluster.typology ?? "Network cluster",
    typologyShort: (cluster.typology ?? "Cluster").slice(0, 18),
    risk,
    riskColor: rc,
    riskLabel: riskLabelFromScore(risk),
    wallets: cluster.wallet_count,
    tx: cluster.tx_count,
    totalAmount: formatAmount(cluster.total_amount),
    heuristics: [],
    wlist,
    txlist,
    nodes,
    edges,
  };
}
