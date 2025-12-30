-- ======================================
-- AI 오케스트레이터 v2.2 스키마 마이그레이션
-- Supabase SQL Editor에서 실행하세요
-- ======================================

-- 1. sessions 테이블 status 제약 조건 수정 (waiting 상태 허용)
ALTER TABLE sessions DROP CONSTRAINT IF EXISTS sessions_status_check;
ALTER TABLE sessions ADD CONSTRAINT sessions_status_check 
CHECK (status IN ('active', 'waiting', 'completed', 'finalized', 'cancelled', 'paused'));

-- 2. messages 테이블 role 제약 조건 수정 (verifier 추가)
ALTER TABLE messages DROP CONSTRAINT IF EXISTS messages_role_check;
ALTER TABLE messages ADD CONSTRAINT messages_role_check
CHECK (role IN ('user', 'agent1', 'agent2', 'agent3', 'verifier', 'system'));

-- 3. case_files 테이블에 v2.2 관련 컬럼 추가
-- criticisms_so_far: 세션 누적 비판 태그
-- criticisms_last_round: 직전 라운드 비판 태그
-- schema_version: 스키마 버전
ALTER TABLE case_files 
ADD COLUMN IF NOT EXISTS criticisms_so_far JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS criticisms_last_round JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS schema_version TEXT DEFAULT '2.2';

-- 4. sessions 테이블에 phase 컬럼 확인 (이미 있을 수 있음)
-- phase: 현재 phase 상태 (A1_R1_PLAN, A2_R1_CRIT, WAIT_USER, FINALIZE_DONE 등)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'sessions' AND column_name = 'phase'
    ) THEN
        ALTER TABLE sessions ADD COLUMN phase TEXT DEFAULT 'WAIT_USER';
    END IF;
END $$;

-- 5. 인덱스 추가 (성능 최적화)
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_case_files_session_id ON case_files(session_id);

-- ======================================
-- 완료! 이제 v2.2 기능을 사용할 수 있습니다.
-- ======================================
