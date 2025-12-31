-- =====================================================
-- v3.1 세션 테이블 project_type 컬럼 추가
-- =====================================================

-- sessions 테이블에 project_type 컬럼 추가
ALTER TABLE sessions 
ADD COLUMN IF NOT EXISTS project_type TEXT CHECK (project_type IN ('general', 'legal', 'dev_project')) DEFAULT 'general';

-- 기존 데이터 마이그레이션 (case_type이 있으면 legal, 아니면 general)
UPDATE sessions 
SET project_type = 'legal' 
WHERE case_type IS NOT NULL;

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_sessions_project_type ON sessions(project_type);
