import { useContext } from "react";
import { NotificationCtx, type NotificationContextValue } from "@/contexts/notificationContext";

export function useNotifications(): NotificationContextValue {
  const ctx = useContext(NotificationCtx);
  if (!ctx) throw new Error("useNotifications must be inside <NotificationProvider>");
  return ctx;
}
