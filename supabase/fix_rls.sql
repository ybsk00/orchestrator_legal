-- 익명 세션 지원을 위한 RLS 정책 수정

-- 1. messages 테이블 정책 수정
DROP POLICY IF EXISTS "Users can view messages in their sessions" ON messages;
DROP POLICY IF EXISTS "Users can create messages in their sessions" ON messages;

-- 모든 사용자가 메시지 조회 가능 (익명 세션 포함)
CREATE POLICY "Anyone can view messages"
ON messages FOR SELECT
USING (true);

-- 모든 사용자가 메시지 생성 가능 (익명 세션 포함)
CREATE POLICY "Anyone can create messages"
ON messages FOR INSERT
WITH CHECK (true);

-- 2. case_files 테이블 정책 수정
DROP POLICY IF EXISTS "Users can view case_files for their sessions" ON case_files;

CREATE POLICY "Anyone can view case_files"
ON case_files FOR SELECT
USING (true);

-- 3. final_reports 테이블 정책 수정
DROP POLICY IF EXISTS "Users can view final_reports for their sessions" ON final_reports;

CREATE POLICY "Anyone can view final_reports"
ON final_reports FOR SELECT
USING (true);
