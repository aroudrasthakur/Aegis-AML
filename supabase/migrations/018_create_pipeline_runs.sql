-- Pipeline runs: first-class batch run entity with run-scoped result tables.

CREATE TABLE public.pipeline_runs (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  label         TEXT,
  status        TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending','running','completed','failed')),
  created_at    TIMESTAMPTZ DEFAULT now(),
  started_at    TIMESTAMPTZ,
  completed_at  TIMESTAMPTZ,
  error_message TEXT,
  progress_pct  INT DEFAULT 0,
  total_files   INT DEFAULT 0,
  total_txns    INT DEFAULT 0,
  suspicious_tx_count      INT DEFAULT 0,
  suspicious_cluster_count INT DEFAULT 0
);

CREATE TABLE public.run_transactions (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id          UUID NOT NULL REFERENCES public.pipeline_runs(id) ON DELETE CASCADE,
  transaction_id  TEXT NOT NULL,
  sender_wallet   TEXT NOT NULL,
  receiver_wallet TEXT NOT NULL,
  amount          NUMERIC NOT NULL,
  timestamp       TIMESTAMPTZ NOT NULL,
  tx_hash         TEXT,
  asset_type      TEXT,
  chain_id        TEXT,
  fee             NUMERIC,
  label           TEXT,
  label_source    TEXT
);
CREATE INDEX idx_run_transactions_run ON public.run_transactions(run_id);

CREATE TABLE public.run_scores (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id                UUID NOT NULL REFERENCES public.pipeline_runs(id) ON DELETE CASCADE,
  transaction_id        TEXT NOT NULL,
  behavioral_score      FLOAT,
  behavioral_anomaly    FLOAT,
  graph_score           FLOAT,
  entity_score          FLOAT,
  temporal_score        FLOAT,
  offramp_score         FLOAT,
  meta_score            FLOAT,
  risk_level            TEXT,
  predicted_label       TEXT,
  explanation_summary   TEXT,
  heuristic_triggered   JSONB DEFAULT '[]',
  heuristic_top_typo    TEXT,
  heuristic_top_conf    FLOAT
);
CREATE INDEX idx_run_scores_run ON public.run_scores(run_id);

CREATE TABLE public.run_suspicious_txns (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id          UUID NOT NULL REFERENCES public.pipeline_runs(id) ON DELETE CASCADE,
  transaction_id  TEXT NOT NULL,
  meta_score      FLOAT,
  risk_level      TEXT,
  typology        TEXT,
  cluster_id      UUID
);
CREATE INDEX idx_run_sus_txns_run ON public.run_suspicious_txns(run_id);

CREATE TABLE public.run_clusters (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id       UUID NOT NULL REFERENCES public.pipeline_runs(id) ON DELETE CASCADE,
  label        TEXT,
  typology     TEXT,
  risk_score   FLOAT,
  total_amount NUMERIC,
  wallet_count INT,
  tx_count     INT
);
CREATE INDEX idx_run_clusters_run ON public.run_clusters(run_id);

CREATE TABLE public.run_cluster_members (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cluster_id     UUID NOT NULL REFERENCES public.run_clusters(id) ON DELETE CASCADE,
  wallet_address TEXT NOT NULL
);

CREATE TABLE public.run_reports (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id       UUID NOT NULL REFERENCES public.pipeline_runs(id) ON DELETE CASCADE,
  title        TEXT,
  content      JSONB NOT NULL DEFAULT '{}',
  generated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE public.run_graph_snapshots (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id     UUID NOT NULL REFERENCES public.pipeline_runs(id) ON DELETE CASCADE,
  cluster_id UUID REFERENCES public.run_clusters(id) ON DELETE CASCADE,
  elements   JSONB NOT NULL DEFAULT '[]'
);
CREATE INDEX idx_run_graphs_run ON public.run_graph_snapshots(run_id);
