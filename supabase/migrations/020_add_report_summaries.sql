-- Add LLM-generated summary columns to run_reports
ALTER TABLE public.run_reports
  ADD COLUMN IF NOT EXISTS summary_text TEXT,
  ADD COLUMN IF NOT EXISTS summary_model TEXT,
  ADD COLUMN IF NOT EXISTS summary_generated_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS summary_prompt_version TEXT;

-- Polymorphic summary table for case reports and other report types
CREATE TABLE IF NOT EXISTS public.report_ai_summaries (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  target_table TEXT NOT NULL CHECK (target_table IN ('run_report', 'case_report', 'audit')),
  target_id UUID NOT NULL,
  summary_text TEXT NOT NULL,
  summary_model TEXT,
  summary_prompt_version TEXT,
  generated_at TIMESTAMPTZ DEFAULT NOW(),
  created_by UUID REFERENCES auth.users(id)
);

-- RLS: users can see summaries for reports they own
ALTER TABLE public.report_ai_summaries ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read their own summaries"
  ON public.report_ai_summaries
  FOR SELECT
  USING (
    created_by = auth.uid()
    OR EXISTS (
      SELECT 1 FROM public.run_reports rr
      JOIN public.pipeline_runs pr ON pr.id = rr.run_id
      WHERE rr.id = report_ai_summaries.target_id
        AND pr.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert summaries for their reports"
  ON public.report_ai_summaries
  FOR INSERT
  WITH CHECK (
    created_by = auth.uid()
    OR EXISTS (
      SELECT 1 FROM public.run_reports rr
      JOIN public.pipeline_runs pr ON pr.id = rr.run_id
      WHERE rr.id = report_ai_summaries.target_id
        AND pr.user_id = auth.uid()
    )
  );
