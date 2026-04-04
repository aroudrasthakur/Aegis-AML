-- Scope pipeline runs to the owning user (profiles.id = auth.uid()).

ALTER TABLE public.pipeline_runs
  ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE;

COMMENT ON COLUMN public.pipeline_runs.user_id IS 'Owner; same UUID as auth.users.id / profiles.id';

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_user_id ON public.pipeline_runs (user_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_user_created ON public.pipeline_runs (user_id, created_at DESC);

-- RLS: users see only their runs (API also filters; defense in depth for direct PostgREST).
ALTER TABLE public.pipeline_runs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "pipeline_runs_select_own"
  ON public.pipeline_runs FOR SELECT TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "pipeline_runs_insert_own"
  ON public.pipeline_runs FOR INSERT TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "pipeline_runs_update_own"
  ON public.pipeline_runs FOR UPDATE TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "pipeline_runs_delete_own"
  ON public.pipeline_runs FOR DELETE TO authenticated
  USING (auth.uid() = user_id);

-- Child tables: visibility follows parent run owner.
ALTER TABLE public.run_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.run_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.run_suspicious_txns ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.run_clusters ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.run_cluster_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.run_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.run_graph_snapshots ENABLE ROW LEVEL SECURITY;

CREATE POLICY "run_transactions_select_own"
  ON public.run_transactions FOR SELECT TO authenticated
  USING (EXISTS (
    SELECT 1 FROM public.pipeline_runs pr
    WHERE pr.id = run_transactions.run_id AND pr.user_id = auth.uid()
  ));

CREATE POLICY "run_scores_select_own"
  ON public.run_scores FOR SELECT TO authenticated
  USING (EXISTS (
    SELECT 1 FROM public.pipeline_runs pr
    WHERE pr.id = run_scores.run_id AND pr.user_id = auth.uid()
  ));

CREATE POLICY "run_suspicious_txns_select_own"
  ON public.run_suspicious_txns FOR SELECT TO authenticated
  USING (EXISTS (
    SELECT 1 FROM public.pipeline_runs pr
    WHERE pr.id = run_suspicious_txns.run_id AND pr.user_id = auth.uid()
  ));

CREATE POLICY "run_clusters_select_own"
  ON public.run_clusters FOR SELECT TO authenticated
  USING (EXISTS (
    SELECT 1 FROM public.pipeline_runs pr
    WHERE pr.id = run_clusters.run_id AND pr.user_id = auth.uid()
  ));

CREATE POLICY "run_cluster_members_select_own"
  ON public.run_cluster_members FOR SELECT TO authenticated
  USING (EXISTS (
    SELECT 1 FROM public.run_clusters rc
    JOIN public.pipeline_runs pr ON pr.id = rc.run_id
    WHERE rc.id = run_cluster_members.cluster_id AND pr.user_id = auth.uid()
  ));

CREATE POLICY "run_reports_select_own"
  ON public.run_reports FOR SELECT TO authenticated
  USING (EXISTS (
    SELECT 1 FROM public.pipeline_runs pr
    WHERE pr.id = run_reports.run_id AND pr.user_id = auth.uid()
  ));

CREATE POLICY "run_graph_snapshots_select_own"
  ON public.run_graph_snapshots FOR SELECT TO authenticated
  USING (EXISTS (
    SELECT 1 FROM public.pipeline_runs pr
    WHERE pr.id = run_graph_snapshots.run_id AND pr.user_id = auth.uid()
  ));
