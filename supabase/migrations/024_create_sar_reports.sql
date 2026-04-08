-- Create SAR reports table for storing Suspicious Activity Report metadata
-- This table tracks generated SAR PDFs and their filing status

CREATE TABLE IF NOT EXISTS public.sar_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL,
    case_id TEXT NOT NULL,  -- TEXT to support both UUID and synthetic IDs (e.g., "run-{uuid}")
    sar_path TEXT NOT NULL,
    filing_date TIMESTAMP WITH TIME ZONE,
    status TEXT NOT NULL CHECK (status IN ('draft', 'filed', 'rejected')),
    bsa_id TEXT,  -- BSA Identifier assigned by FinCEN (format: XXXXXXXX-XXX-XXXXX)
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    generated_by UUID,  -- References auth.users(id) but not enforced with FK
    UNIQUE(report_id)  -- One SAR per report
);

-- Create indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_sar_reports_report_id ON public.sar_reports(report_id);
CREATE INDEX IF NOT EXISTS idx_sar_reports_case_id ON public.sar_reports(case_id);
CREATE INDEX IF NOT EXISTS idx_sar_reports_status ON public.sar_reports(status);
CREATE INDEX IF NOT EXISTS idx_sar_reports_generated_at ON public.sar_reports(generated_at DESC);

-- Ensure one SAR per report even if table pre-existed without the inline UNIQUE.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'sar_reports_report_id_key'
          AND conrelid = 'public.sar_reports'::regclass
    ) THEN
        ALTER TABLE public.sar_reports
            ADD CONSTRAINT sar_reports_report_id_key UNIQUE (report_id);
    END IF;
END $$;

-- Add comment to table
COMMENT ON TABLE public.sar_reports IS 'Stores metadata for generated Suspicious Activity Report (SAR) PDFs';

-- Add comments to columns
COMMENT ON COLUMN public.sar_reports.id IS 'Unique identifier for the SAR record';
COMMENT ON COLUMN public.sar_reports.report_id IS 'Reference to source report UUID (supports both reports.id and run_reports.id)';
COMMENT ON COLUMN public.sar_reports.case_id IS 'Reference to the network case (UUID) or synthetic case ID (TEXT) for run reports';
COMMENT ON COLUMN public.sar_reports.sar_path IS 'File path to the generated SAR PDF';
COMMENT ON COLUMN public.sar_reports.filing_date IS 'Date when the SAR was filed with FinCEN';
COMMENT ON COLUMN public.sar_reports.status IS 'Current status: draft, filed, or rejected';
COMMENT ON COLUMN public.sar_reports.bsa_id IS 'BSA identifier assigned by FinCEN after filing';
COMMENT ON COLUMN public.sar_reports.generated_at IS 'Timestamp when the SAR was generated';
COMMENT ON COLUMN public.sar_reports.generated_by IS 'User ID who generated the SAR (for audit trail)';
