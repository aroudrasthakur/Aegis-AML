import { useState } from "react";

/** 90-cell grid T-001 … T-090 with intensity from mock frequency */
export default function TypologyHeatmap() {
  const cells = Array.from({ length: 90 }, (_, i) => {
    const id = i + 1;
    const t = (Math.sin(id * 0.31) + 1) / 2;
    return { id, intensity: t };
  });

  const [tip, setTip] = useState<string | null>(null);

  return (
    <div className="rounded-xl border border-[var(--color-aegis-border)] bg-[#0d1117] p-5">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-display text-sm font-semibold text-[#e6edf3]">
          Typology heatmap
        </h3>
        <span className="font-data text-[10px] text-[var(--color-aegis-muted)]">
          T-001 — T-090
        </span>
      </div>
      <div
        className="grid grid-cols-[repeat(15,minmax(0,1fr))] gap-1"
        onMouseLeave={() => setTip(null)}
      >
        {cells.map(({ id, intensity }) => (
          <button
            key={id}
            type="button"
            className="aspect-square rounded-sm border border-[var(--color-aegis-border)] transition-colors hover:ring-1 hover:ring-[var(--color-aegis-green)]/50"
            style={{
              backgroundColor: `rgba(0, 229, 160, ${0.08 + intensity * 0.55})`,
            }}
            title={`T-${String(id).padStart(3, "0")}`}
            onMouseEnter={() =>
              setTip(`T-${String(id).padStart(3, "0")} · fire rate ${(intensity * 100).toFixed(0)}%`)
            }
          />
        ))}
      </div>
      {tip && (
        <p className="mt-3 font-data text-[11px] text-[var(--color-aegis-muted)]">{tip}</p>
      )}
    </div>
  );
}
