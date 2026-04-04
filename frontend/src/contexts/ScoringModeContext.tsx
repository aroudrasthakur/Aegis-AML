import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { ScoringMetrics, ScoringMode } from "@/types/dashboard";

interface ScoringModeContextValue {
  mode: ScoringMode;
  setMode: (m: ScoringMode) => void;
  metrics: ScoringMetrics;
  setMetrics: (m: ScoringMetrics) => void;
}

const defaultMetrics: ScoringMetrics = {
  precisionAt50: 0.88,
  recallAt50: 0.91,
  prAuc: 0.934,
};

const ScoringModeContext = createContext<ScoringModeContextValue | null>(null);

export function ScoringModeProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<ScoringMode>("FULL_SCORING");
  const [metrics, setMetricsState] = useState<ScoringMetrics>(defaultMetrics);

  const setMetrics = useCallback((m: ScoringMetrics) => {
    setMetricsState(m);
  }, []);

  const value = useMemo(
    () => ({ mode, setMode, metrics, setMetrics }),
    [mode, metrics, setMetrics],
  );

  return (
    <ScoringModeContext.Provider value={value}>
      {children}
    </ScoringModeContext.Provider>
  );
}

export function useScoringMode() {
  const ctx = useContext(ScoringModeContext);
  if (!ctx) {
    throw new Error("useScoringMode must be used within ScoringModeProvider");
  }
  return ctx;
}
