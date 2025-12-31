-- =====================================================
-- v3.2 개발 프로젝트 전용 필드 추가
-- =====================================================

ALTER TABLE case_files
ADD COLUMN IF NOT EXISTS decisions_so_far TEXT[] DEFAULT '{}',
ADD COLUMN IF NOT EXISTS scope_in TEXT[] DEFAULT '{}',
ADD COLUMN IF NOT EXISTS scope_out TEXT[] DEFAULT '{}',
ADD COLUMN IF NOT EXISTS risks_so_far TEXT[] DEFAULT '{}',
ADD COLUMN IF NOT EXISTS ux_artifacts_summary JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS tech_artifacts_summary JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS steering_history JSONB DEFAULT '[]',
ADD COLUMN IF NOT EXISTS committed_steering_snapshot JSONB DEFAULT '{}';
