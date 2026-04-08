import { useEffect, useRef, useState } from "react";
import { Bell, CheckCircle2, Info, AlertTriangle, XCircle, X, Trash2, Timer } from "lucide-react";
import { useNotifications } from "@/hooks/useNotifications";

const ICONS = {
  success: <CheckCircle2 className="h-4 w-4 text-[#34d399]" />,
  info: <Info className="h-4 w-4 text-[#60a5fa]" />,
  warning: <AlertTriangle className="h-4 w-4 text-[#f59e0b]" />,
  error: <XCircle className="h-4 w-4 text-[#f87171]" />,
};

function TimeAgo({ addedAt }: { addedAt: number }) {
  const [, setTick] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setTick((n) => n + 1), 60000);
    return () => clearInterval(id);
  }, []);

  const s = Math.max(0, Math.floor((Date.now() - addedAt) / 1000));
  if (s < 60) return <span>just now</span>;
  const m = Math.floor(s / 60);
  if (m < 60) return <span>{m}m ago</span>;
  const h = Math.floor(m / 60);
  if (h < 24) return <span>{h}h ago</span>;
  return <span>{Math.floor(h / 24)}d ago</span>;
}

export default function NotificationDropdown() {
  const {
    notifications,
    unreadCount,
    markAllAsRead,
    markAsRead,
    clearNotification,
    clearAll,
  } = useNotifications();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    if (open) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => {
          if (!open) markAllAsRead();
          setOpen((prev) => !prev);
        }}
        className={`relative rounded-lg border p-2 transition-colors ${
          open
            ? "border-[#34d399]/30 bg-[#0d1117] text-[#e6edf3]"
            : "border-[var(--color-aegis-border)] bg-transparent text-[#9aa7b8] hover:text-[#e6edf3]"
        }`}
        aria-label="Notifications"
      >
        <Bell className="h-5 w-5" />
        {unreadCount > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-[16px] items-center justify-center rounded-full bg-[#f87171] px-1 font-data text-[10px] text-white animate-pulse">
            {unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-2 w-80 max-h-[85vh] overflow-hidden rounded-xl border border-[var(--color-aegis-border)] bg-[#0d1117]/95 shadow-2xl shadow-[#060810]/50 backdrop-blur-xl flex flex-col z-[100]">
          <div className="flex items-center justify-between border-b border-[var(--color-aegis-border)] px-4 py-3 bg-[#060810]/50">
            <h3 className="font-display text-sm font-semibold text-[#e6edf3]">Notifications</h3>
            {notifications.length > 0 && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  clearAll();
                }}
                className="group flex items-center gap-1.5 rounded pr-1 font-data text-[11px] font-medium text-[#7d8a99] transition-colors hover:text-[#f87171]"
              >
                <Trash2 className="h-3.5 w-3.5 group-hover:bg-[#f87171]/10 rounded p-0.5 transition-colors" />
                Clear All
              </button>
            )}
          </div>

          <div className="aegis-scroll flex-1 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="px-4 py-8 text-center">
                <Bell className="mx-auto h-8 w-8 text-[#5c6b7e]/50 mb-2" />
                <p className="font-data text-sm text-[#7d8a99]">You're all caught up.</p>
              </div>
            ) : (
              <div className="divide-y divide-[var(--color-aegis-border)]">
                {notifications.map((n) => (
                  <div
                    key={n.id}
                    className={`group relative flex gap-3 p-4 transition-colors hover:bg-[#060810]/60 ${
                      n.read ? "opacity-75" : "bg-gradient-to-r from-[#34d399]/[0.03] to-transparent"
                    }`}
                    onMouseEnter={() => !n.read && markAsRead(n.id)}
                  >
                    {!n.read && (
                      <span className="absolute left-1.5 top-5 h-1.5 w-1.5 rounded-full bg-[#34d399]" />
                    )}
                    <div className="shrink-0 mt-0.5 ml-2">{ICONS[n.variant]}</div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-start justify-between gap-2">
                        <p className="font-display text-sm font-semibold text-[#e6edf3] leading-snug">
                          {n.title}
                        </p>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            clearNotification(n.id);
                          }}
                          className="shrink-0 rounded text-[#5c6b7e] opacity-0 transition-all hover:text-[#e6edf3] group-hover:opacity-100"
                        >
                          <X className="h-3.5 w-3.5" />
                        </button>
                      </div>
                      {n.description && (
                        <p className="mt-1 font-data text-xs leading-relaxed text-[#8b9cb3]">
                          {n.description}
                        </p>
                      )}
                      <p className="mt-2 flex items-center gap-1.5 font-mono text-[10px] text-[#5c6b7e]">
                        <Timer className="h-3 w-3" />
                        <TimeAgo addedAt={n.addedAt} />
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
