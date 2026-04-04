/** Deterministic mini sparkline from a numeric seed (0–1ish) for mock deltas */
export function SparklineBars({
  seed,
  colorClass,
}: {
  seed: number;
  colorClass: string;
}) {
  const n = 12;
  const bars = Array.from({ length: n }, (_, i) => {
    const t = (Math.sin(seed * 7 + i * 0.9) + 1) / 2;
    return Math.max(0.15, t);
  });
  const max = Math.max(...bars);
  return (
    <div className="mt-3 flex h-8 items-end gap-px">
      {bars.map((h, i) => (
        <div
          key={i}
          className={`w-1.5 rounded-sm ${colorClass} opacity-90`}
          style={{ height: `${(h / max) * 100}%` }}
        />
      ))}
    </div>
  );
}
