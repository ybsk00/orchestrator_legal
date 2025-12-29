-- Supabase 데이터베이스 스키마
-- 3 에이전트 오케스트레이터용

-- 세션 테이블
CREATE TABLE sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    category TEXT NOT NULL CHECK (category IN ('newbiz', 'marketing', 'dev', 'domain')),
    topic TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'finalizing', 'finalized')),
    round_index INTEGER NOT NULL DEFAULT 0,
    phase TEXT NOT NULL DEFAULT 'idle',
    ended_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 메시지 테이블
CREATE TABLE messages (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'agent1', 'agent2', 'agent3', 'system')),
    content_text TEXT NOT NULL,
    content_json JSONB,
    reasoning_summary TEXT[],
    round_index INTEGER NOT NULL,
    phase TEXT NOT NULL,
    event_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 케이스 파일 테이블 (누적 메모리)
CREATE TABLE case_files (
    session_id UUID PRIMARY KEY REFERENCES sessions(id) ON DELETE CASCADE,
    facts TEXT[] DEFAULT '{}',
    goals TEXT[] DEFAULT '{}',
    constraints TEXT[] DEFAULT '{}',
    decisions TEXT[] DEFAULT '{}',
    open_issues TEXT[] DEFAULT '{}',
    assumptions TEXT[] DEFAULT '{}',
    next_experiments TEXT[] DEFAULT '{}',
    summary_text TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 최종 리포트 테이블
CREATE TABLE final_reports (
    session_id UUID PRIMARY KEY REFERENCES sessions(id) ON DELETE CASCADE,
    report_json JSONB NOT NULL,
    report_md TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 인덱스
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_messages_session_id ON messages(session_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);

-- RLS (Row Level Security) 정책

-- sessions 테이블 RLS
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own sessions"
ON sessions FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own sessions"
ON sessions FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own sessions"
ON sessions FOR UPDATE
USING (auth.uid() = user_id);

-- messages 테이블 RLS
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view messages in their sessions"
ON messages FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM sessions
        WHERE sessions.id = messages.session_id
        AND sessions.user_id = auth.uid()
    )
);

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

CREATE POLICY "Users can view case_files for their sessions"
ON case_files FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM sessions
        WHERE sessions.id = case_files.session_id
        AND sessions.user_id = auth.uid()
    )
);

-- final_reports 테이블 RLS
ALTER TABLE final_reports ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view final_reports for their sessions"
ON final_reports FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM sessions
        WHERE sessions.id = final_reports.session_id
        AND sessions.user_id = auth.uid()
    )
);

-- updated_at 자동 업데이트 함수
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 트리거
CREATE TRIGGER update_sessions_updated_at
    BEFORE UPDATE ON sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_case_files_updated_at
    BEFORE UPDATE ON case_files
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
