import { useMemo } from "react";
import Plot from "react-plotly.js";
import type { Data, Layout } from "plotly.js";
import type { ModelPerformanceMetric } from "@/types/dashboard";

export interface ModelPerformanceChartProps {
  metrics: ModelPerformanceMetric[];
}

/** Map FP/1k to 0–1 for shared axis (lower FP is better; invert for visual as “quality”) */
function fpNorm(fp: number): number {
  return Math.max(0, Math.min(1, 1 - fp / 40));
}

export default function ModelPerformanceChart({
  metrics,
}: ModelPerformanceChartProps) {
  const { data, layout } = useMemo(() => {
    const names = metrics.map((m) => m.name);
    const fpRaw = metrics.map((m) => m.fpPer1k);
    const traces: Data[] = [
      {
        type: "bar",
        name: "PR-AUC",
        orientation: "h",
        y: names,
        x: metrics.map((m) => m.prAuc),
        marker: { color: "#00e5a0" },
      },
      {
        type: "bar",
        name: "Recall@50",
        orientation: "h",
        y: names,
        x: metrics.map((m) => m.recall50),
        marker: { color: "#7c5cfc" },
      },
      {
        type: "bar",
        name: "Precision@50",
        orientation: "h",
        y: names,
        x: metrics.map((m) => m.precision50),
        marker: { color: "#f59e0b" },
      },
      {
        type: "bar",
        name: "F1",
        orientation: "h",
        y: names,
        x: metrics.map((m) => m.f1),
        marker: { color: "#38bdf8" },
      },
      {
        type: "bar",
        name: "FP/1k (inv. scale)",
        orientation: "h",
        y: names,
        x: metrics.map((m) => fpNorm(m.fpPer1k)),
        marker: { color: "#ff4d6d" },
        customdata: fpRaw,
        hovertemplate:
          "%{y}<br>FP/1k: %{customdata:.1f} (chart uses 1−fp/40)<extra></extra>",
      },
    ];

    const plotLayout: Partial<Layout> = {
      paper_bgcolor: "#0d1117",
      plot_bgcolor: "#0d1117",
      font: { color: "#9aa7b8", family: "DM Mono, monospace", size: 10 },
      margin: { l: 100, r: 24, t: 32, b: 48 },
      barmode: "group",
      legend: {
        orientation: "h",
        y: -0.22,
        x: 0,
      },
      xaxis: {
        gridcolor: "rgba(255,255,255,0.06)",
        zerolinecolor: "rgba(255,255,255,0.06)",
        range: [0, 1],
      },
      yaxis: { automargin: true },
      annotations: [
        {
          showarrow: false,
          x: 0,
          y: -0.28,
          xref: "paper",
          yref: "paper",
          text: "FP/1k bar: higher on chart = fewer false positives (inverted scale). Hover for raw FP/1k.",
          font: { size: 9, color: "#5c6b7f" },
        },
      ],
    };

    return { data: traces, layout: plotLayout };
  }, [metrics]);

  return (
    <div className="rounded-xl border border-[var(--color-aegis-border)] bg-[#0d1117] p-3">
      <h3 className="mb-2 px-2 font-display text-sm font-semibold text-[#e6edf3]">
        Model performance
      </h3>
      <Plot
        data={data}
        layout={layout}
        config={{ displayModeBar: false, responsive: true }}
        style={{ width: "100%", height: 400 }}
        useResizeHandler
      />
    </div>
  );
}
