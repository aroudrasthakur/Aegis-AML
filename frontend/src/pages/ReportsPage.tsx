import { Download, FileJson, FileText } from "lucide-react";

export default function ReportsPage() {
  const reports: {
    id: string;
    title: string;
    caseName: string;
    generatedAt: string;
  }[] = [];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl font-bold text-[#e6edf3]">
            Reports & SAR
          </h1>
          <p className="font-data text-sm text-[var(--color-aegis-muted)]">
            Case reports, SAR generation, JSON / PDF export
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className="inline-flex items-center gap-2 rounded-lg border border-[var(--color-aegis-border)] bg-[#0d1117] px-4 py-2 font-data text-xs text-[#e6edf3] hover:border-[var(--color-aegis-green)]/40"
          >
            <FileText className="h-4 w-4" aria-hidden />
            Generate SAR
          </button>
        </div>
      </div>

      <div className="rounded-xl border border-[var(--color-aegis-border)] bg-[#0d1117] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--color-aegis-border)] bg-[#060810]/80 text-left font-data text-[11px] uppercase tracking-wide text-[var(--color-aegis-muted)]">
                <th className="px-4 py-3">Report</th>
                <th className="px-4 py-3">Case</th>
                <th className="px-4 py-3">Generated</th>
                <th className="px-4 py-3">Export</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--color-aegis-border)] font-data text-[#c8d4e0]">
              {reports.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-4 py-16 text-center">
                    <FileText
                      className="mx-auto mb-3 h-10 w-10 text-[var(--color-aegis-muted)]"
                      aria-hidden
                    />
                    <p className="font-display font-medium text-[#c8d4e0]">
                      No reports generated
                    </p>
                    <p className="mx-auto mt-2 max-w-sm text-sm text-[#9aa7b8]">
                      Generate SAR or export investigation packages to list them
                      here.
                    </p>
                  </td>
                </tr>
              ) : (
                reports.map((r) => (
                  <tr key={r.id} className="hover:bg-[#060810]/90">
                    <td className="px-4 py-3 font-medium text-[#e6edf3]">
                      {r.title}
                    </td>
                    <td className="px-4 py-3">{r.caseName}</td>
                    <td className="px-4 py-3 text-[var(--color-aegis-muted)]">
                      {r.generatedAt}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-2">
                        <button
                          type="button"
                          className="inline-flex items-center gap-1 rounded border border-[var(--color-aegis-border)] bg-[#060810] px-2 py-1 text-[11px] text-[#e6edf3] hover:border-[var(--color-aegis-green)]/40"
                        >
                          <FileJson className="h-3.5 w-3.5" aria-hidden />
                          JSON
                        </button>
                        <button
                          type="button"
                          className="inline-flex items-center gap-1 rounded border border-[var(--color-aegis-border)] bg-[#060810] px-2 py-1 text-[11px] text-[#e6edf3] hover:border-[var(--color-aegis-green)]/40"
                        >
                          <Download className="h-3.5 w-3.5" aria-hidden />
                          PDF
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
