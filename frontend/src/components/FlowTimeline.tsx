import { useMemo } from "react";
import Plot from "react-plotly.js";
import type { Data, Layout } from "plotly.js";
import type { Transaction } from "@/types/transaction";

export interface FlowTimelineProps {
  transactions: Transaction[];
}

const PLOT_BG = "#0d1117";
const TEXT = "#9aa7b8";
const GRID = "rgba(255,255,255,0.06)";

function riskToColor(score: number | null | undefined): string {
  if (score == null) return "#5c6b7f";
  if (score >= 0.75) return "#ff4d6d";
  if (score >= 0.5) return "#f59e0b";
  if (score >= 0.25) return "#fbbf24";
  return "#00e5a0";
}

export default function FlowTimeline({ transactions }: FlowTimelineProps) {
  const { data, layout } = useMemo(() => {
    const xs = transactions.map((t) => t.timestamp);
    const ys = transactions.map((t) => t.amount);
    const colors = transactions.map((t) => riskToColor(t.risk_score ?? null));
    const ids = transactions.map((t) => t.transaction_id);

    const trace: Partial<Data> = {
      type: "scatter",
      mode: "markers",
      x: xs,
      y: ys,
      text: ids,
      hovertemplate:
        "<b>%{text}</b><br>Time: %{x}<br>Amount: $%{y:,.2f}<extra></extra>",
      marker: {
        size: 10,
        color: colors,
        line: { color: "#060810", width: 1 },
      },
    };

    const plotLayout: Partial<Layout> = {
      paper_bgcolor: PLOT_BG,
      plot_bgcolor: PLOT_BG,
      font: { color: TEXT, family: "DM Mono, monospace", size: 11 },
      margin: { l: 56, r: 24, t: 24, b: 48 },
      xaxis: {
        title: { text: "Timestamp" },
        gridcolor: GRID,
        zerolinecolor: GRID,
        showgrid: true,
      },
      yaxis: {
        title: { text: "Amount" },
        gridcolor: GRID,
        zerolinecolor: GRID,
        tickprefix: "$",
      },
      showlegend: false,
    };

    return { data: [trace], layout: plotLayout };
  }, [transactions]);

  if (transactions.length === 0) {
    return (
      <div className="flex min-h-[360px] items-center justify-center rounded-xl border border-[var(--color-aegis-border)] bg-[#0d1117] font-data text-sm text-[var(--color-aegis-muted)]">
        No transactions for timeline.
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-[var(--color-aegis-border)] bg-[#0d1117] p-2">
      <Plot
        data={data}
        layout={layout}
        config={{ displayModeBar: false, responsive: true }}
        style={{ width: "100%", height: 380 }}
        useResizeHandler
      />
    </div>
  );
}
