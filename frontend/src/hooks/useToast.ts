import { useContext } from "react";
import { ToastCtx, type ToastContextValue } from "@/contexts/toastContext";

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastCtx);
  if (!ctx) throw new Error("useToast must be inside <ToastProvider>");
  return ctx;
}
