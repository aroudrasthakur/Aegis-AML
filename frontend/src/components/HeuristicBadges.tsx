import { useMemo, useState } from "react";

export interface HeuristicBadgesProps {
  triggeredIds: number[];
  explanations: Record<string, string>;
  limit?: number;
}

type EnvGroup = "traditional" | "blockchain" | "hybrid" | "ai_enabled" | "unknown";

function environmentForId(id: number): EnvGroup {
  if (id >= 1 && id <= 90) return "traditional";
  if (id >= 91 && id <= 142) return "blockchain";
  if ((id >= 143 && id <= 155) || (id >= 176 && id <= 185)) return "hybrid";
  if (id >= 156 && id <= 175) return "ai_enabled";
  return "unknown";
}

function badgeClasses(env: EnvGroup): string {
  switch (env) {
    case "traditional":
      return "border-[var(--color-aegis-amber)]/50 bg-[#f59e0b]/10 text-[#fcd34d]";
    case "blockchain":
      return "border-[#38bdf8]/40 bg-[#38bdf8]/10 text-[#7dd3fc]";
    case "hybrid":
      return "border-[var(--color-aegis-purple)]/50 bg-[#7c5cfc]/10 text-[#c4b5fd]";
    case "ai_enabled":
      return "border-[var(--color-aegis-red)]/45 bg-[#ff4d6d]/10 text-[#fda4af]";
    default:
      return "border-[var(--color-aegis-border)] bg-[#060810] text-[#c8d4e0]";
  }
}

export default function HeuristicBadges({
  triggeredIds,
  explanations,
  limit = 8,
}: HeuristicBadgesProps) {
  const [expanded, setExpanded] = useState(false);

  const uniqueSorted = useMemo(() => {
    return [...new Set(triggeredIds)].sort((a, b) => a - b);
  }, [triggeredIds]);

  const visible = expanded ? uniqueSorted : uniqueSorted.slice(0, limit);
  const hiddenCount = Math.max(0, uniqueSorted.length - limit);

  if (uniqueSorted.length === 0) {
    return (
      <p className="font-data text-sm text-[var(--color-aegis-muted)]">
        No heuristics triggered.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap gap-2">
        {visible.map((id) => {
          const key = String(id);
          const tip = explanations[key] ?? explanations[id] ?? `Heuristic ${id}`;
          const env = environmentForId(id);
          return (
            <span
              key={id}
              title={tip}
              className={`inline-flex cursor-default rounded-md border px-2 py-0.5 font-data text-xs font-medium tabular-nums ${badgeClasses(env)}`}
            >
              H-{id}
            </span>
          );
        })}
      </div>
      {!expanded && hiddenCount > 0 && (
        <button
          type="button"
          onClick={() => setExpanded(true)}
          className="self-start font-data text-xs font-medium text-[var(--color-aegis-green)] hover:underline"
        >
          Show more ({hiddenCount})
        </button>
      )}
    </div>
  );
}
