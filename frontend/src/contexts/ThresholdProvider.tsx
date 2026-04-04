import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { fetchModelThreshold, type ThresholdResponse } from "@/api/runs";
import type { RiskTierConfig } from "@/utils/riskTiers";

interface ThresholdContextValue {
  config: RiskTierConfig | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

const ThresholdCtx = createContext<ThresholdContextValue | null>(null);

function toConfig(
  t: ThresholdResponse["threshold"],
): RiskTierConfig | null {
  if (!t) return null;
  return {
    lowRiskCeiling: t.low_risk_ceiling,
    decisionThreshold: t.decision_threshold,
    highRiskThreshold: t.high_risk_threshold,
  };
}

export function ThresholdProvider({ children }: { children: ReactNode }) {
  const [config, setConfig] = useState<RiskTierConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetchModelThreshold();
      setConfig(toConfig(resp.threshold));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load thresholds");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const value = useMemo<ThresholdContextValue>(
    () => ({ config, loading, error, refresh: load }),
    [config, loading, error, load],
  );

  return (
    <ThresholdCtx.Provider value={value}>{children}</ThresholdCtx.Provider>
  );
}

export function useThresholds(): ThresholdContextValue {
  const ctx = useContext(ThresholdCtx);
  if (!ctx) {
    throw new Error("useThresholds must be used within ThresholdProvider");
  }
  return ctx;
}
