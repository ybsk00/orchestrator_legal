-- =====================================================
-- RLS 정책 복원 SQL
-- 임시 공개 정책 제거 + 인증 기반 정책 활성화
-- =====================================================

-- 1. 임시 공개 정책 제거
-- =====================================================
DROP POLICY IF EXISTS "Allow public read messages" ON messages;
DROP POLICY IF EXISTS "Allow public read case_files" ON case_files;
DROP POLICY IF EXISTS "Allow public read sessions" ON sessions;
DROP POLICY IF EXISTS "Anyone can read messages" ON messages;

-- 2. 기존 인증 기반 정책 확인 (이미 존재하면 무시됨)
-- =====================================================

-- sessions 테이블 RLS 정책
DROP POLICY IF EXISTS "Users can view their own sessions" ON sessions;
CREATE POLICY "Users can view their own sessions"
ON sessions FOR SELECT
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can create their own sessions" ON sessions;
CREATE POLICY "Users can create their own sessions"
ON sessions FOR INSERT
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their own sessions" ON sessions;
CREATE POLICY "Users can update their own sessions"
ON sessions FOR UPDATE
USING (auth.uid() = user_id);

-- messages 테이블 RLS 정책
DROP POLICY IF EXISTS "Users can view messages in their sessions" ON messages;
CREATE POLICY "Users can view messages in their sessions"
ON messages FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM sessions
        WHERE sessions.id = messages.session_id
        AND sessions.user_id = auth.uid()
    )
);

DROP POLICY IF EXISTS "Users can create messages in their sessions" ON messages;
CREATE POLICY "Users can create messages in their sessions"
ON messages FOR INSERT
WITH CHECK (
    EXISTS (
        SELECT 1 FROM sessions
        WHERE sessions.id = messages.session_id
        AND sessions.user_id = auth.uid()
    )
);

-- case_files 테이블 RLS 정책
DROP POLICY IF EXISTS "Users can view case_files for their sessions" ON case_files;
CREATE POLICY "Users can view case_files for their sessions"
ON case_files FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM sessions
        WHERE sessions.id = case_files.session_id
        AND sessions.user_id = auth.uid()
    )
);

DROP POLICY IF EXISTS "Users can update case_files for their sessions" ON case_files;
CREATE POLICY "Users can update case_files for their sessions"
ON case_files FOR UPDATE
USING (
    EXISTS (
        SELECT 1 FROM sessions
        WHERE sessions.id = case_files.session_id
        AND sessions.user_id = auth.uid()
    )
);

DROP POLICY IF EXISTS "Users can insert case_files for their sessions" ON case_files;
CREATE POLICY "Users can insert case_files for their sessions"
ON case_files FOR INSERT
WITH CHECK (
    EXISTS (
        SELECT 1 FROM sessions
        WHERE sessions.id = case_files.session_id
        AND sessions.user_id = auth.uid()
    )
);

-- final_reports 테이블 RLS 정책
DROP POLICY IF EXISTS "Users can view final_reports for their sessions" ON final_reports;
CREATE POLICY "Users can view final_reports for their sessions"
ON final_reports FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM sessions
        WHERE sessions.id = final_reports.session_id
        AND sessions.user_id = auth.uid()
    )
);

-- =====================================================
-- RLS 정책 복원 완료!
-- 이제 로그인한 사용자만 자신의 데이터에 접근 가능합니다.
-- =====================================================
