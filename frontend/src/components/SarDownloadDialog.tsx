import { FileWarning, Download, X, CheckCircle2, Loader2 } from "lucide-react";

interface Props {
  open: boolean;
  onClose: () => void;
  onDownload: () => void;
  sarId: string;
  isDownloading?: boolean;
}

export default function SarDownloadDialog({
  open,
  onClose,
  onDownload,
  sarId,
  isDownloading = false,
}: Props) {
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 px-4 backdrop-blur-[2px]"
      role="presentation"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="sar-download-title"
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-md rounded-xl border border-[var(--color-aegis-border)] bg-[#0d1117] shadow-xl"
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[var(--color-aegis-border)] px-5 py-4">
          <div className="flex items-center gap-2">
            <div className="rounded-lg bg-[#34d399]/10 p-2">
              <CheckCircle2 className="h-5 w-5 text-[#34d399]" />
            </div>
            <h2
              id="sar-download-title"
              className="font-display text-lg font-semibold text-[#e6edf3]"
            >
              SAR Report Ready
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1 text-[#9aa7b8] hover:text-[#e6edf3] transition-colors"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Body */}
        <div className="space-y-4 px-5 py-5">
          {/* Success message */}
          <div className="flex items-start gap-3 rounded-lg border border-[#34d399]/30 bg-[#34d399]/5 px-4 py-3">
            <FileWarning className="mt-0.5 h-5 w-5 shrink-0 text-[#34d399]" />
            <div className="flex-1">
              <p className="font-display text-sm font-medium text-[#e6edf3]">
                Suspicious Activity Report Generated
              </p>
              <p className="mt-1 font-data text-xs text-[#9aa7b8]">
                Your SAR PDF has been successfully generated and is ready for
                download.
              </p>
            </div>
          </div>

          {/* SAR ID */}
          <div className="rounded-lg border border-[var(--color-aegis-border)] bg-[#060810] px-4 py-3">
            <p className="font-data text-[11px] uppercase tracking-wide text-[#6b7c90]">
              SAR ID
            </p>
            <p className="mt-1 font-mono text-sm text-[#e6edf3] break-all">
              {sarId}
            </p>
          </div>

          {/* Info notice */}
          <div className="rounded-lg border border-[var(--color-aegis-border)] bg-[#060810] px-4 py-3">
            <p className="font-data text-xs text-[#9aa7b8] leading-relaxed">
              This report contains sensitive information. Ensure it is handled
              in accordance with your organization's compliance and security
              policies.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-2 border-t border-[var(--color-aegis-border)] px-5 py-4">
          <button
            type="button"
            onClick={onClose}
            disabled={isDownloading}
            className="rounded-lg border border-[var(--color-aegis-border)] bg-[#060810] px-4 py-2 font-data text-sm text-[#e6edf3] hover:border-[#34d399]/35 transition-colors disabled:opacity-40"
          >
            Close
          </button>
          <button
            type="button"
            onClick={onDownload}
            disabled={isDownloading}
            className="inline-flex items-center gap-2 rounded-lg border border-[#34d399]/40 bg-[#34d399]/10 px-4 py-2 font-data text-sm font-medium text-[#6ee7b7] hover:bg-[#34d399]/15 transition-colors disabled:opacity-40"
          >
            {isDownloading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Downloading…
              </>
            ) : (
              <>
                <Download className="h-4 w-4" />
                Download PDF
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
