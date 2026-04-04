import type { CytoscapeElement } from "../types/graph";
import { riskColorFromScore, type RiskTierConfig } from "./riskTiers";

interface ApiNode {
  id: string;
  risk_score?: number;
  label?: string;
  [key: string]: unknown;
}

interface ApiEdge {
  source: string;
  target: string;
  amount?: number;
  [key: string]: unknown;
}

interface ApiGraphSeparate {
  nodes: ApiNode[];
  edges: ApiEdge[];
}

interface ApiGraphFlat {
  elements: CytoscapeElement[];
}

type ApiGraph = ApiGraphSeparate | ApiGraphFlat;

export type { CytoscapeElement } from "../types/graph";

export function apiGraphToCytoscape(
  graph: ApiGraph,
  tierConfig?: RiskTierConfig | null,
): CytoscapeElement[] {
  if ("elements" in graph && Array.isArray(graph.elements)) {
    return graph.elements;
  }

  const { nodes, edges } = graph as ApiGraphSeparate;
  const elements: CytoscapeElement[] = [];

  for (const node of nodes) {
    const { id, label, risk_score, ...rest } = node;
    elements.push({
      data: {
        ...rest,
        id,
        label: label ?? id,
        color: riskColorFromScore(risk_score, tierConfig ?? null),
      },
    });
  }

  for (const edge of edges) {
    const { source, target, amount, ...rest } = edge;
    elements.push({
      data: {
        ...rest,
        source,
        target,
        weight: amount ?? 1,
      },
    });
  }

  return elements;
}
