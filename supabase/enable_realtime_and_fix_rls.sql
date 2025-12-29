-- 1. Realtime 활성화 (필수)
-- messages 테이블의 변경사항을 실시간으로 구독하려면 replication에 추가해야 합니다.
ALTER PUBLICATION supabase_realtime ADD TABLE messages;
ALTER PUBLICATION supabase_realtime ADD TABLE sessions;
ALTER PUBLICATION supabase_realtime ADD TABLE case_files;

-- 2. RLS 정책 수정 (익명 접근 허용)
-- 이미 실행했다면 에러가 날 수 있으니 DROP 후 다시 생성합니다.

-- messages 테이블
DROP POLICY IF EXISTS "Users can view messages in their sessions" ON messages;
DROP POLICY IF EXISTS "Users can create messages in their sessions" ON messages;
DROP POLICY IF EXISTS "Anyone can view messages" ON messages;
DROP POLICY IF EXISTS "Anyone can create messages" ON messages;

CREATE POLICY "Anyone can view messages" ON messages FOR SELECT USING (true);
CREATE POLICY "Anyone can create messages" ON messages FOR INSERT WITH CHECK (true);

-- case_files 테이블
DROP POLICY IF EXISTS "Users can view case_files for their sessions" ON case_files;
DROP POLICY IF EXISTS "Anyone can view case_files" ON case_files;

CREATE POLICY "Anyone can view case_files" ON case_files FOR SELECT USING (true);

-- final_reports 테이블
DROP POLICY IF EXISTS "Users can view final_reports for their sessions" ON final_reports;
DROP POLICY IF EXISTS "Anyone can view final_reports" ON final_reports;

CREATE POLICY "Anyone can view final_reports" ON final_reports FOR SELECT USING (true);

-- sessions 테이블 (이미 되어있을 수 있지만 확인)
DROP POLICY IF EXISTS "Allow anonymous session creation" ON sessions;
DROP POLICY IF EXISTS "Anyone can view sessions by id" ON sessions;
DROP POLICY IF EXISTS "Anyone can update sessions" ON sessions;

CREATE POLICY "Allow anonymous session creation" ON sessions FOR INSERT WITH CHECK (true);
CREATE POLICY "Anyone can view sessions by id" ON sessions FOR SELECT USING (true);
CREATE POLICY "Anyone can update sessions" ON sessions FOR UPDATE USING (true);
