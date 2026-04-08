import {
  useCallback,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { ToastCtx, type ToastItem } from "@/contexts/toastContext";
import { useNotifications } from "@/hooks/useNotifications";

const MAX_VISIBLE = 5;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const timers = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());
  const { pushNotification } = useNotifications();

  const dismiss = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
    const timer = timers.current.get(id);
    if (timer) {
      clearTimeout(timer);
      timers.current.delete(id);
    }
  }, []);

  const push = useCallback(
    (incoming: Omit<ToastItem, "id" | "addedAt">) => {
      const id = `toast-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
      const item: ToastItem = { ...incoming, id, addedAt: Date.now() };
      const ttl = incoming.ttl ?? 6000;

      pushNotification({
        variant: incoming.variant,
        title: incoming.title,
        description: incoming.description,
      });

      setToasts((prev) => {
        const next = [item, ...prev];
        // evict oldest beyond limit
        if (next.length > MAX_VISIBLE) {
          const evicted = next.slice(MAX_VISIBLE);
          evicted.forEach((e) => {
            const t = timers.current.get(e.id);
            if (t) { clearTimeout(t); timers.current.delete(e.id); }
          });
          return next.slice(0, MAX_VISIBLE);
        }
        return next;
      });

      const timer = setTimeout(() => dismiss(id), ttl);
      timers.current.set(id, timer);
    },
    [dismiss, pushNotification],
  );

  return (
    <ToastCtx.Provider value={{ toasts, push, dismiss }}>
      {children}
    </ToastCtx.Provider>
  );
}
