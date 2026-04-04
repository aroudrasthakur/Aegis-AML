import { useEffect, useMemo, useState } from "react";
import { fetchHeuristicStats } from "@/api/heuristics";

function normalizeToCellKey(raw: string): string | null {
  const k = raw.trim();
  const m = /^T-(\d{1,3})\b/i.exec(k);
  if (m) {
    const n = parseInt(m[1], 10);
    if (n >= 1 && n <= 90) return `T-${String(n).padStart(3, "0")}`;
  }
  if (/^T-\d{3}$/i.test(k)) {
    const n = parseInt(k.slice(2), 10);
    if (n >= 1 && n <= 90) return `T-${String(n).padStart(3, "0")}`;
  }
  return null;
}

/** 90-cell grid T-001 … T-090 from `heuristic_results.top_typology` counts in Supabase. */
export default function TypologyHeatmap() {
  const [freqByCell, setFreqByCell] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchHeuristicStats();
        const merged: Record<string, number> = {};
        const raw = data.typology_frequency ?? {};
        for (const [key, count] of Object.entries(raw)) {
          const cell = normalizeToCellKey(key);
          if (cell) {
            merged[cell] = (merged[cell] ?? 0) + (typeof count === "number" ? count : 0);
          }
        }
        if (!cancelled) setFreqByCell(merged);
      } catch {
        if (!cancelled) {
          setFreqByCell({});
          setError("Could not load typology stats");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const maxFreq = useMemo(
    () => Math.max(1, ...Object.values(freqByCell)),
    [freqByCell],
  );

  const cells = useMemo(
    () =>
      Array.from({ length: 90 }, (_, i) => {
        const n = i + 1;
        const key = `T-${String(n).padStart(3, "0")}`;
        const raw = freqByCell[key] ?? 0;
        const intensity = raw / maxFreq;
        return { key, intensity };
      }),
    [freqByCell, maxFreq],
  );

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
      {loading ? (
        <p className="font-data text-[11px] text-[var(--color-aegis-muted)]">Loading…</p>
      ) : error ? (
        <p className="font-data text-[11px] text-[#f87171]/90">{error}</p>
      ) : (
        <>
          <div
            className="grid grid-cols-[repeat(15,minmax(0,1fr))] gap-1"
            onMouseLeave={() => setTip(null)}
          >
            {cells.map(({ key, intensity }) => (
              <button
                key={key}
                type="button"
                className="aspect-square rounded-sm border border-[var(--color-aegis-border)] transition-colors hover:ring-1 hover:ring-[var(--color-aegis-green)]/50"
                style={{
                  backgroundColor: `rgba(0, 229, 160, ${0.08 + intensity * 0.55})`,
                }}
                title={key}
                onMouseEnter={() =>
                  setTip(
                    `${key} · ${(intensity * maxFreq).toFixed(0)} hits (${(intensity * 100).toFixed(0)}% of max)`,
                  )
                }
              />
            ))}
          </div>
          {tip && (
            <p className="mt-3 font-data text-[11px] text-[var(--color-aegis-muted)]">{tip}</p>
          )}
        </>
      )}
    </div>
  );
}
