-- D-1: Prevent duplicate edges for the same transaction
CREATE UNIQUE INDEX IF NOT EXISTS idx_edges_unique_tx
  ON public.edges (sender_wallet, receiver_wallet, transaction_id);

-- D-2: Index on meta_score for risk-filtered queries
CREATE INDEX IF NOT EXISTS idx_transaction_scores_meta_score
  ON public.transaction_scores (meta_score);

-- D-3: Prevent duplicate metric rows for the same measurement window
CREATE UNIQUE INDEX IF NOT EXISTS idx_model_metrics_unique_window
  ON public.model_metrics (model_name, cohort_key, metric_name, window_start);

-- D-7: wallet_address should never be null on a tag
ALTER TABLE public.address_tags ALTER COLUMN wallet_address SET NOT NULL;
