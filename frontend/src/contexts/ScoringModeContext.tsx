import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { ScoringMetrics, ScoringMode } from "@/types/dashboard";
import { fetchModelMetrics, fetchModelThreshold } from "@/api/runs";

interface ScoringModeContextValue {
  mode: ScoringMode;
  setMode: (m: ScoringMode) => void;
  metrics: ScoringMetrics;
  setMetrics: (m: ScoringMetrics) => void;
}

const fallbackMetrics: ScoringMetrics = {
  precisionAt50: 0,
  recallAt50: 0,
  prAuc: 0,
};

const ScoringModeContext = createContext<ScoringModeContextValue | null>(null);

export function ScoringModeProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<ScoringMode>("FULL_SCORING");
  const [metrics, setMetricsState] = useState<ScoringMetrics>(fallbackMetrics);

  useEffect(() => {
    (async () => {
      try {
        const [mm, tc] = await Promise.all([
          fetchModelMetrics().catch(() => ({ metrics: null })),
          fetchModelThreshold().catch(() => ({ threshold: null })),
        ]);
        const prAuc = mm.metrics?.pr_auc ?? 0;
        const recall = tc.threshold?.recall_at_threshold ?? 0;
        const precision = tc.threshold?.precision_at_threshold ?? 0;
        setMetricsState({ precisionAt50: precision, recallAt50: recall, prAuc });
      } catch {
        /* keep fallback */
      }
    })();
  }, []);

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
