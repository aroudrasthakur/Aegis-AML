import { ChevronDown } from "lucide-react";
import type { PipelineRun } from "@/types/run";

export interface RunSelectorDropdownProps {
  runs: PipelineRun[];
  selectedRunId: string | null;
  onSelect: (runId: string) => void;
  /** Only show completed runs by default */
  filterCompleted?: boolean;
  className?: string;
}

export default function RunSelectorDropdown({
  runs,
  selectedRunId,
  onSelect,
  filterCompleted = true,
  className = "",
}: RunSelectorDropdownProps) {
  const eligible = filterCompleted
    ? runs.filter((r) => r.status === "completed")
    : runs;

  if (eligible.length === 0) {
    return (
      <div
        className={`inline-flex items-center gap-2 rounded-lg border border-[var(--color-aegis-border)] bg-[#060810] px-3 py-1.5 font-data text-xs text-[var(--color-aegis-muted)] ${className}`}
      >
        No completed runs
      </div>
    );
  }

  return (
    <div className={`relative inline-block ${className}`}>
      <label htmlFor="run-selector" className="sr-only">
        Select pipeline run
      </label>
      <div className="relative">
        <select
          id="run-selector"
          value={selectedRunId ?? ""}
          onChange={(e) => onSelect(e.target.value)}
          className="appearance-none rounded-lg border border-[var(--color-aegis-border)] bg-[#060810] py-1.5 pl-3 pr-8 font-data text-xs text-[#e6edf3] focus:border-[#34d399]/40 focus:outline-none focus:ring-1 focus:ring-[#34d399]/30"
        >
          {eligible.map((r) => {
            const label = r.label ?? `Run ${r.id.slice(0, 8)}`;
            const ts = r.completed_at
              ? new Date(r.completed_at).toLocaleDateString("en-US", {
                  month: "short",
                  day: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                })
              : "";
            return (
              <option key={r.id} value={r.id}>
                {label}
                {ts ? ` — ${ts}` : ""}
              </option>
            );
          })}
        </select>
        <ChevronDown className="pointer-events-none absolute right-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[var(--color-aegis-muted)]" />
      </div>
    </div>
  );
}
