import type { CytoscapeElement } from "../types/graph";

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

function riskToColor(score: number | undefined): string {
  if (score === undefined) return "#6b7280";
  if (score >= 0.75) return "#ef4444";
  if (score >= 0.5) return "#f97316";
  if (score >= 0.25) return "#eab308";
  return "#22c55e";
}

export function apiGraphToCytoscape(graph: ApiGraph): CytoscapeElement[] {
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
        color: riskToColor(risk_score),
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
