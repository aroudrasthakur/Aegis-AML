-- Allow SAR records for both legacy reports and run_reports.
-- Existing FK to public.reports(id) blocks run_report IDs.

ALTER TABLE public.sar_reports
    DROP CONSTRAINT IF EXISTS sar_reports_report_id_fkey;

COMMENT ON COLUMN public.sar_reports.report_id
IS 'Reference to source report UUID (supports both reports.id and run_reports.id)';
