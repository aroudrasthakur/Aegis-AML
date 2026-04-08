-- Allow SAR records for both network_cases and run-based synthetic/derived case IDs.
-- Existing FK to public.network_cases(id) blocks run IDs and synthetic IDs.

ALTER TABLE public.sar_reports
    DROP CONSTRAINT IF EXISTS sar_reports_case_id_fkey;

-- Normalize to TEXT to support UUID case IDs and synthetic IDs uniformly.
ALTER TABLE public.sar_reports
    ALTER COLUMN case_id TYPE TEXT USING case_id::text;

COMMENT ON COLUMN public.sar_reports.case_id
IS 'Reference to network case UUID or run-derived/synthetic case ID';
