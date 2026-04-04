-- Denormalized count from inference (mirrors len(heuristic_triggered)); used when JSONB shape varies by client.
ALTER TABLE public.run_scores
  ADD COLUMN IF NOT EXISTS heuristic_triggered_count INTEGER;

COMMENT ON COLUMN public.run_scores.heuristic_triggered_count IS
  'Number of heuristics that fired for this transaction (from inference pipeline)';
