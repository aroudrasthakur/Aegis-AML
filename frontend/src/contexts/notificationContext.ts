import { createContext } from "react";
import type { ToastVariant } from "@/contexts/toastContext";

export interface NotificationItem {
  id: string;
  variant: ToastVariant;
  title: string;
  description?: string;
  addedAt: number;
  read: boolean;
}

export interface NotificationContextValue {
  notifications: NotificationItem[];
  unreadCount: number;
  pushNotification: (n: Omit<NotificationItem, "id" | "addedAt" | "read">) => void;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  clearNotification: (id: string) => void;
  clearAll: () => void;
}

export const NotificationCtx = createContext<NotificationContextValue | null>(null);
