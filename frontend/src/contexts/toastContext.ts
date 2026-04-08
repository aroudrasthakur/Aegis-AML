import { createContext } from "react";

export type ToastVariant = "success" | "info" | "warning" | "error";

export interface ToastItem {
  id: string;
  variant: ToastVariant;
  title: string;
  description?: string;
  /** e.g. "2m 14s" */
  duration?: string;
  /** Unix ms when it was added — used for the "just now / Xs ago" chip */
  addedAt: number;
  /** auto-dismiss delay in ms (default 6000) */
  ttl?: number;
}

export interface ToastContextValue {
  toasts: ToastItem[];
  push: (toast: Omit<ToastItem, "id" | "addedAt">) => void;
  dismiss: (id: string) => void;
}

export const ToastCtx = createContext<ToastContextValue | null>(null);
