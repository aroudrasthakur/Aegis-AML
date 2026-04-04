/** Mini bar chart from recent run metrics (no synthetic seed). */
export function SparklineBars({
  values,
  colorClass,
}: {
  /** Length typically ≤ 12; heights normalized to max value. */
  values?: number[];
  colorClass: string;
}) {
  if (!values?.length) {
    return null;
  }
  const max = Math.max(...values, 1e-9);
  const bars = values.map((v) => Math.max(0.12, v / max));
  const hMax = Math.max(...bars);
  return (
    <div className="mt-3 flex h-8 items-end gap-px">
      {bars.map((h, i) => (
        <div
          key={i}
          className={`w-1.5 rounded-sm ${colorClass} opacity-90`}
          style={{ height: `${(h / hMax) * 100}%` }}
        />
      ))}
    </div>
  );
}
