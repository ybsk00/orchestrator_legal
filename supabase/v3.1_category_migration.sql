-- v3.1 마이그레이션: legal 및 dev_project 카테고리 추가
-- 실행 전에 백업을 권장합니다.

-- 1. 먼저 NOT NULL 제약조건을 느슨하게 변경 (category가 NULL인 기존 데이터 허용)
ALTER TABLE sessions ALTER COLUMN category DROP NOT NULL;

-- 2. 기존 CHECK 제약조건 삭제
ALTER TABLE sessions DROP CONSTRAINT IF EXISTS sessions_category_check;

-- 3. 새로운 CHECK 제약조건 추가 (legal, dev_project 포함, NULL도 허용)
ALTER TABLE sessions ADD CONSTRAINT sessions_category_check 
CHECK (category IS NULL OR category IN ('newbiz', 'marketing', 'dev', 'domain', 'legal', 'dev_project'));

-- 4. 기존 데이터 업데이트: 개발 프로젝트 세션에 category 설정
UPDATE sessions 
SET category = 'dev_project' 
WHERE project_type = 'dev_project' AND (category IS NULL OR category = '');

-- 5. 기존 데이터 업데이트: 법무 세션에 category 설정
UPDATE sessions 
SET category = 'legal' 
WHERE project_type = 'legal' AND (category IS NULL OR category = '');

-- 확인 쿼리
SELECT id, topic, category, project_type FROM sessions ORDER BY created_at DESC;
