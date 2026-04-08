import { useEffect, useState } from "react";
import {
  CheckCircle2,
  Info,
  AlertTriangle,
  XCircle,
  X,
  Timer,
} from "lucide-react";
import { useToast } from "@/hooks/useToast";
import type { ToastVariant, ToastItem } from "@/contexts/toastContext";

/* ── colour + icon per variant ────────────────────────────── */

const VARIANT_STYLES: Record<
  ToastVariant,
  {
    border: string;
    glow: string;
    iconColor: string;
    Icon: typeof CheckCircle2;
  }
> = {
  success: {
    border: "border-[#34d399]/30",
    glow: "shadow-[0_0_24px_-4px_rgba(52,211,153,.18)]",
    iconColor: "text-[#34d399]",
    Icon: CheckCircle2,
  },
  info: {
    border: "border-[#60a5fa]/30",
    glow: "shadow-[0_0_24px_-4px_rgba(96,165,250,.18)]",
    iconColor: "text-[#60a5fa]",
    Icon: Info,
  },
  warning: {
    border: "border-[#f59e0b]/30",
    glow: "shadow-[0_0_24px_-4px_rgba(245,158,11,.18)]",
    iconColor: "text-[#f59e0b]",
    Icon: AlertTriangle,
  },
  error: {
    border: "border-[#f87171]/30",
    glow: "shadow-[0_0_24px_-4px_rgba(248,113,113,.18)]",
    iconColor: "text-[#f87171]",
    Icon: XCircle,
  },
};

/* ── relative‐time chip ─────────────────────────────────── */

function Ago({ addedAt }: { addedAt: number }) {
  const [, setTick] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setTick((n) => n + 1), 1000);
    return () => clearInterval(id);
  }, []);

  const s = Math.max(0, Math.round((Date.now() - addedAt) / 1000));
  const label = s < 5 ? "just now" : s < 60 ? `${s}s ago` : `${Math.floor(s / 60)}m ago`;

  return (
    <span className="inline-flex items-center gap-1 font-mono text-[10px] text-[#5c6b7e]">
      <Timer className="h-3 w-3" />
      {label}
    </span>
  );
}

/* ── single toast card ───────────────────────────────────── */

function Toast({
  item,
  onDismiss,
}: {
  item: ToastItem;
  onDismiss: () => void;
}) {
  const { border, glow, iconColor, Icon } = VARIANT_STYLES[item.variant];

  return (
    <div
      className={`pointer-events-auto relative flex w-[370px] items-start gap-3 overflow-hidden rounded-xl border ${border} ${glow} bg-[#0d1117]/95 px-4 py-3.5 backdrop-blur-md animate-slide-in-right`}
      role="status"
      aria-live="polite"
    >
      {/* Accent bar */}
      <div
        className={`absolute inset-y-0 left-0 w-[3px] ${iconColor.replace("text-", "bg-")}`}
      />

      <Icon className={`mt-0.5 h-5 w-5 shrink-0 ${iconColor}`} aria-hidden />

      <div className="min-w-0 flex-1">
        <div className="flex items-start justify-between gap-2">
          <p className="font-display text-sm font-semibold text-[#e6edf3] leading-snug">
            {item.title}
          </p>
          <button
            type="button"
            onClick={onDismiss}
            className="shrink-0 rounded p-0.5 text-[#5c6b7e] hover:text-[#e6edf3] transition-colors"
            aria-label="Dismiss"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>

        {item.description && (
          <p className="mt-0.5 font-data text-xs leading-relaxed text-[#8b9cb3]">
            {item.description}
          </p>
        )}

        <div className="mt-1.5 flex items-center gap-3">
          {item.duration && (
            <span className="inline-flex items-center gap-1 rounded-full border border-[var(--color-aegis-border)] bg-[#060810] px-2 py-0.5 font-mono text-[10px] text-[#9aa7b8]">
              <Timer className="h-3 w-3 text-[#5c6b7e]" />
              {item.duration}
            </span>
          )}
          <Ago addedAt={item.addedAt} />
        </div>
      </div>
    </div>
  );
}

/* ── toast viewport (bottom‑right) ───────────────────────── */

export default function ToastViewport() {
  const { toasts, dismiss } = useToast();

  if (toasts.length === 0) return null;

  return (
    <div className="pointer-events-none fixed bottom-4 right-4 z-[200] flex flex-col-reverse items-end gap-3">
      {toasts.map((t) => (
        <Toast key={t.id} item={t} onDismiss={() => dismiss(t.id)} />
      ))}
    </div>
  );
}
