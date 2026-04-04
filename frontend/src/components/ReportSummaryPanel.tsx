import { useCallback, useEffect, useState } from "react";
import { Loader2, RefreshCw, Sparkles } from "lucide-react";
import {
  fetchReportSummary,
  generateReportSummary,
  type ReportSummary,
} from "@/api/runs";

interface ReportSummaryPanelProps {
  runId: string;
}

export default function ReportSummaryPanel({ runId }: ReportSummaryPanelProps) {
  const [summary, setSummary] = useState<ReportSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    setSummary(null);

    fetchReportSummary(runId)
      .then((data) => {
        if (!cancelled) setSummary(data);
      })
      .catch(() => {
        /* no summary yet — that's fine */
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [runId]);

  const handleGenerate = useCallback(
    async (force = false) => {
      setGenerating(true);
      setError(null);
      try {
        const data = await generateReportSummary(runId, force);
        setSummary(data);
      } catch (e) {
        const msg =
          e instanceof Error ? e.message : "Failed to generate summary";
        setError(msg);
      } finally {
        setGenerating(false);
      }
    },
    [runId],
  );

  if (loading) {
    return (
      <div className="rounded-xl border border-[var(--color-aegis-border)] bg-[#0d1117] p-5">
        <div className="flex items-center gap-2 text-[var(--color-aegis-muted)]">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span className="font-data text-xs">Checking for summary…</span>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-[var(--color-aegis-border)] bg-[#0d1117] p-5">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-[#34d399]" />
          <h3 className="font-display text-sm font-semibold text-[#e6edf3]">
            AI Summary
          </h3>
        </div>
        {summary && (
          <button
            type="button"
            disabled={generating}
            onClick={() => handleGenerate(true)}
            className="flex items-center gap-1.5 rounded-lg border border-[var(--color-aegis-border)] px-2.5 py-1 font-data text-[10px] text-[#9aa7b8] transition-colors hover:border-[#34d399]/40 hover:text-[#e6edf3] disabled:opacity-50"
          >
            <RefreshCw className={`h-3 w-3 ${generating ? "animate-spin" : ""}`} />
            Regenerate
          </button>
        )}
      </div>

      {error && (
        <p className="mt-3 font-data text-xs text-red-400">{error}</p>
      )}

      {!summary && !generating && (
        <div className="mt-4">
          <p className="font-data text-xs text-[var(--color-aegis-muted)]">
            No summary has been generated for this report yet.
          </p>
          <button
            type="button"
            onClick={() => handleGenerate(false)}
            className="mt-3 rounded-lg border border-[#34d399]/35 bg-[#34d399]/10 px-4 py-2 font-data text-xs font-medium text-[#6ee7b7] hover:border-[#34d399]/55"
          >
            Generate summary
          </button>
        </div>
      )}

      {generating && !summary && (
        <div className="mt-4 flex items-center gap-2 text-[var(--color-aegis-muted)]">
          <Loader2 className="h-4 w-4 animate-spin text-[#34d399]" />
          <span className="font-data text-xs">Generating AI summary…</span>
        </div>
      )}

      {summary && (
        <div className="mt-4">
          <p className="whitespace-pre-wrap font-data text-xs leading-relaxed text-[#c8d4e0]">
            {summary.summary_text}
          </p>
          <div className="mt-3 flex flex-wrap gap-4 font-data text-[10px] text-[var(--color-aegis-muted)]">
            {summary.summary_model && (
              <span>Model: {summary.summary_model}</span>
            )}
            {summary.summary_generated_at && (
              <span>
                Generated:{" "}
                {new Date(summary.summary_generated_at).toLocaleString("en-US", {
                  month: "short",
                  day: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
