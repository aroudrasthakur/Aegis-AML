import { useCallback, useEffect, useState, type ReactNode } from "react";
import { NotificationCtx, type NotificationItem } from "@/contexts/notificationContext";

const STORAGE_KEY = "aegis_notifications";

export function NotificationProvider({ children }: { children: ReactNode }) {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);

  // Load from local storage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        setNotifications(JSON.parse(stored));
      }
    } catch {
      // fallback silent
    }
  }, []);

  // Sync back to local storage
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(notifications));
    } catch {
      // fallback silent
    }
  }, [notifications]);

  const pushNotification = useCallback(
    (incoming: Omit<NotificationItem, "id" | "addedAt" | "read">) => {
      const id = `notif-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
      const item: NotificationItem = { ...incoming, id, addedAt: Date.now(), read: false };
      setNotifications((prev) => [item, ...prev].slice(0, 50)); // keep up to 50
    },
    [],
  );

  const markAsRead = useCallback((id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n)),
    );
  }, []);

  const markAllAsRead = useCallback(() => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  }, []);

  const clearNotification = useCallback((id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  }, []);

  const clearAll = useCallback(() => {
    setNotifications([]);
  }, []);

  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <NotificationCtx.Provider
      value={{
        notifications,
        unreadCount,
        pushNotification,
        markAsRead,
        markAllAsRead,
        clearNotification,
        clearAll,
      }}
    >
      {children}
    </NotificationCtx.Provider>
  );
}
