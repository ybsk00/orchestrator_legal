-- =====================================================
-- 법무 오케스트레이터 통합 스키마 (v3.0)
-- 기존 테이블 + 법무 시뮬레이터 필드 포함
-- =====================================================

-- 1. 세션 테이블
-- =====================================================
CREATE TABLE IF NOT EXISTS sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    -- 일반 토론용 카테고리 (nullable - 법무 시뮬레이션은 case_type 사용)
    category TEXT CHECK (category IS NULL OR category IN ('newbiz', 'marketing', 'dev', 'domain')),
    -- 법무 시뮬레이션용 필드
    case_type TEXT CHECK (case_type IS NULL OR case_type IN ('criminal', 'civil')),
    jurisdiction TEXT,
    facts_stipulated BOOLEAN DEFAULT FALSE,
    -- 공통 필드
    topic TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'finalizing', 'finalized')),
    round_index INTEGER NOT NULL DEFAULT 0,
    phase TEXT NOT NULL DEFAULT 'idle',
    ended_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. 메시지 테이블
-- =====================================================
CREATE TABLE IF NOT EXISTS messages (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    -- 일반 에이전트 + 법무 에이전트 role
    role TEXT NOT NULL CHECK (role IN (
        'user', 'agent1', 'agent2', 'agent3', 'verifier', 'system',
        'judge', 'claimant', 'opposing'
    )),
    content_text TEXT NOT NULL,
    content_json JSONB,
    reasoning_summary TEXT[],
    round_index INTEGER NOT NULL,
    phase TEXT NOT NULL,
    event_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. 케이스 파일 테이블 (누적 메모리)
-- =====================================================
CREATE TABLE IF NOT EXISTS case_files (
    session_id UUID PRIMARY KEY REFERENCES sessions(id) ON DELETE CASCADE,
    -- 일반 토론용 필드
    facts TEXT[] DEFAULT '{}',
    goals TEXT[] DEFAULT '{}',
    constraints TEXT[] DEFAULT '{}',
    decisions TEXT[] DEFAULT '{}',
    open_issues TEXT[] DEFAULT '{}',
    assumptions TEXT[] DEFAULT '{}',
    next_experiments TEXT[] DEFAULT '{}',
    summary_text TEXT,
    -- 법무 시뮬레이션용 필드
    confirmed_facts TEXT[] DEFAULT '{}',
    disputed_facts TEXT[] DEFAULT '{}',
    missing_facts_questions TEXT[] DEFAULT '{}',
    case_overview TEXT,
    parties JSONB DEFAULT '[]',
    legal_steering JSONB DEFAULT '{}',
    criticisms_so_far TEXT[] DEFAULT '{}',
    criticisms_last_round TEXT[] DEFAULT '{}',
    -- 공통
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. 최종 리포트 테이블
-- =====================================================
CREATE TABLE IF NOT EXISTS final_reports (
    session_id UUID PRIMARY KEY REFERENCES sessions(id) ON DELETE CASCADE,
    report_json JSONB NOT NULL,
    report_md TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. 인덱스
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_case_type ON sessions(case_type);
CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);

-- 6. RLS (Row Level Security) 정책
-- =====================================================

-- sessions 테이블 RLS
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;

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

-- messages 테이블 RLS
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

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

-- case_files 테이블 RLS
ALTER TABLE case_files ENABLE ROW LEVEL SECURITY;

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

-- final_reports 테이블 RLS
ALTER TABLE final_reports ENABLE ROW LEVEL SECURITY;

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

-- 7. updated_at 자동 업데이트 함수
-- =====================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 8. 트리거
-- =====================================================
DROP TRIGGER IF EXISTS update_sessions_updated_at ON sessions;
CREATE TRIGGER update_sessions_updated_at
    BEFORE UPDATE ON sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_case_files_updated_at ON case_files;
CREATE TRIGGER update_case_files_updated_at
    BEFORE UPDATE ON case_files
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 9. Realtime 활성화
-- =====================================================
-- messages 테이블 Realtime 활성화 (에러 발생시 무시)
DO $$
BEGIN
    ALTER PUBLICATION supabase_realtime ADD TABLE messages;
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- =====================================================
-- 스키마 생성 완료!
-- =====================================================
