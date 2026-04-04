import { useEffect, useMemo, useRef, useState } from "react";
import CytoscapeComponent from "react-cytoscapejs";
import type {
  Core,
  ElementDefinition,
  EventObject,
  StylesheetJsonBlock,
} from "cytoscape";
import type { CytoscapeElement } from "../types/graph";

export interface NetworkGraphProps {
  elements: CytoscapeElement[];
  onNodeClick?: (id: string) => void;
  onNodeHover?: (
    id: string,
    position: { x: number; y: number },
    data: Record<string, unknown>,
  ) => void;
  onNodeHoverOut?: () => void;
  minHeight?: number;
}

const DARK_BG = "#060810";

export default function NetworkGraph({
  elements,
  onNodeClick,
  onNodeHover,
  onNodeHoverOut,
  minHeight = 420,
}: NetworkGraphProps) {
  const [cyInstance, setCyInstance] = useState<Core | null>(null);
  const onNodeClickRef = useRef(onNodeClick);
  const onNodeHoverRef = useRef(onNodeHover);
  const onNodeHoverOutRef = useRef(onNodeHoverOut);
  onNodeClickRef.current = onNodeClick;
  onNodeHoverRef.current = onNodeHover;
  onNodeHoverOutRef.current = onNodeHoverOut;

  const stylesheet = useMemo<StylesheetJsonBlock[]>(
    () => [
      {
        selector: "node",
        style: {
          label: "data(label)",
          "background-color": "data(color)",
          color: "#e5e7eb",
          "text-outline-color": DARK_BG,
          "text-outline-width": 2,
          "font-size": 10,
          width: 28,
          height: 28,
        },
      },
      {
        selector: "node[?suspicious]",
        style: {
          "border-width": 3,
          "border-color": "#f87171",
          "background-color": "#f87171",
          width: 34,
          height: 34,
        },
      },
      {
        selector: "node[risk_level = 'high']",
        style: {
          "border-width": 3,
          "border-color": "#f87171",
          "background-color": "#991b1b",
        },
      },
      {
        selector: "node[risk_level = 'medium']",
        style: {
          "border-width": 2,
          "border-color": "#facc15",
          "background-color": "#854d0e",
        },
      },
      {
        selector: "edge",
        style: {
          width: "mapData(weight, 0, 1000000, 1, 12)",
          "line-color": "#4b5563",
          "target-arrow-color": "#4b5563",
          "target-arrow-shape": "triangle",
          "curve-style": "bezier",
          opacity: 0.85,
        },
      },
    ],
    [],
  );

  const layout = useMemo(
    () => ({
      name: "cose",
      animate: true,
      padding: 24,
      nodeRepulsion: 8000,
      idealEdgeLength: 100,
      componentSpacing: 60,
    }),
    [],
  );

  useEffect(() => {
    if (!cyInstance) return;

    const tapHandler = (evt: EventObject) => {
      onNodeClickRef.current?.(evt.target.id());
    };
    const overHandler = (evt: EventObject) => {
      const node = evt.target;
      const pos = node.renderedPosition();
      onNodeHoverRef.current?.(node.id(), { x: pos.x, y: pos.y }, node.data());
    };
    const outHandler = () => {
      onNodeHoverOutRef.current?.();
    };

    cyInstance.on("tap", "node", tapHandler);
    cyInstance.on("mouseover", "node", overHandler);
    cyInstance.on("mouseout", "node", outHandler);

    return () => {
      cyInstance.removeListener("tap", "node", tapHandler);
      cyInstance.removeListener("mouseover", "node", overHandler);
      cyInstance.removeListener("mouseout", "node", outHandler);
    };
  }, [cyInstance]);

  // Assign default color/label to nodes that don't have one
  const normalizedElements = useMemo(() => {
    return elements.map((el) => {
      const data = { ...el.data };
      if (!data.source && !data.target) {
        if (!data.color) data.color = "#34d399";
        if (!data.label) data.label = String(data.id ?? "").slice(0, 10);
      }
      if (data.amount != null && data.weight == null) {
        data.weight = data.amount;
      }
      return { ...el, data };
    });
  }, [elements]);

  return (
    <div
      className="h-full w-full overflow-hidden rounded-xl border border-[var(--color-aegis-border)] bg-[#0d1117]"
      style={{ backgroundColor: DARK_BG, minHeight }}
    >
      <CytoscapeComponent
        elements={CytoscapeComponent.normalizeElements(
          normalizedElements as ElementDefinition[],
        )}
        stylesheet={stylesheet}
        layout={layout}
        style={{ width: "100%", height: "100%", minHeight }}
        cy={(cy) => setCyInstance(cy)}
        wheelSensitivity={0.2}
      />
    </div>
  );
}
